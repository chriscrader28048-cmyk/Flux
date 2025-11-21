#!/usr/bin/env python3
"""
FLUX.1-Kontext-dev API Server
FastAPI-based REST API for image editing with context
"""

import os
import io
import base64
import torch
import requests as http_requests
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional
from PIL import Image
import uvicorn

app = FastAPI(
    title="FLUX.1-Kontext-dev API",
    description="API for image editing with FLUX.1-Kontext-dev model",
    version="1.0.0"
)

# CORS for client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
API_KEY = os.environ.get("FLUX_API_KEY", "")

async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key if configured"""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True

# Global model variable
pipe = None

class EditRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt describing the edit")
    input_image: Optional[str] = Field(None, description="Base64 encoded input image")
    image_url: Optional[str] = Field(None, description="URL of input image")
    num_inference_steps: int = Field(50, ge=1, le=100, description="Number of inference steps")
    guidance_scale: float = Field(2.5, ge=0, le=20, description="Guidance scale")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    output_format: str = Field("png", description="Output format: png, jpeg, base64")

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for image generation")
    width: int = Field(1024, ge=256, le=2048, description="Image width")
    height: int = Field(1024, ge=256, le=2048, description="Image height")
    num_inference_steps: int = Field(50, ge=1, le=100, description="Number of inference steps")
    guidance_scale: float = Field(2.5, ge=0, le=20, description="Guidance scale")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    output_format: str = Field("png", description="Output format: png, jpeg, base64")

class GenerationResponse(BaseModel):
    success: bool
    message: str
    image_base64: Optional[str] = None
    seed: Optional[int] = None

def load_model(model_path: str = "./models/flux-kontext-dev"):
    """Load FLUX Kontext model"""
    global pipe

    try:
        from diffusers import FluxKontextPipeline

        print(f"Loading FLUX Kontext model...")

        # Try loading from HuggingFace hub directly
        pipe = FluxKontextPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-Kontext-dev",
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            cache_dir=model_path
        )

        if torch.cuda.is_available():
            pipe = pipe.to("cuda")
            print("Model loaded on CUDA")
        else:
            print("CUDA not available, using CPU (will be slow)")

        print("Model loaded successfully!")
        return True

    except Exception as e:
        print(f"Error loading model: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    model_path = os.environ.get("FLUX_MODEL_PATH", "./models/flux-kontext-dev")
    if not load_model(model_path):
        print("Warning: Model not loaded. Please ensure model is downloaded.")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "model": "FLUX.1-Kontext-dev",
        "model_loaded": pipe is not None,
        "cuda_available": torch.cuda.is_available()
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "model_loaded": pipe is not None}

def load_image_from_source(input_image: str = None, image_url: str = None) -> Image.Image:
    """Load image from base64 or URL"""
    if input_image:
        # Decode base64 image
        img_data = base64.b64decode(input_image)
        return Image.open(io.BytesIO(img_data)).convert("RGB")
    elif image_url:
        # Download from URL
        response = http_requests.get(image_url, timeout=30)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")
    else:
        return None

@app.post("/edit", response_model=GenerationResponse)
async def edit_image(request: EditRequest, auth: bool = Depends(verify_api_key)):
    """Edit image with text prompt (image-to-image)"""
    global pipe

    if pipe is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.input_image and not request.image_url:
        raise HTTPException(status_code=400, detail="Either input_image or image_url is required")

    try:
        # Load input image
        input_img = load_image_from_source(request.input_image, request.image_url)

        # Set seed
        generator = None
        seed = request.seed
        if seed is not None:
            generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu")
            generator.manual_seed(seed)
        else:
            seed = torch.randint(0, 2**32, (1,)).item()

        # Generate edited image
        result = pipe(
            image=input_img,
            prompt=request.prompt,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            generator=generator
        )

        image = result.images[0]

        # Return result
        if request.output_format == "base64":
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            return GenerationResponse(
                success=True,
                message="Image edited successfully",
                image_base64=img_base64,
                seed=seed
            )
        else:
            buffered = io.BytesIO()
            fmt = "PNG" if request.output_format == "png" else "JPEG"
            image.save(buffered, format=fmt)
            buffered.seek(0)

            media_type = f"image/{request.output_format}"
            return Response(content=buffered.getvalue(), media_type=media_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate", response_model=GenerationResponse)
async def generate_image(request: GenerateRequest, auth: bool = Depends(verify_api_key)):
    """Generate image from text prompt (text-to-image)"""
    global pipe

    if pipe is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Set seed
        generator = None
        seed = request.seed
        if seed is not None:
            generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu")
            generator.manual_seed(seed)
        else:
            seed = torch.randint(0, 2**32, (1,)).item()

        # Generate image
        result = pipe(
            prompt=request.prompt,
            height=request.height,
            width=request.width,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            generator=generator
        )

        image = result.images[0]

        # Return result
        if request.output_format == "base64":
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            return GenerationResponse(
                success=True,
                message="Image generated successfully",
                image_base64=img_base64,
                seed=seed
            )
        else:
            buffered = io.BytesIO()
            fmt = "PNG" if request.output_format == "png" else "JPEG"
            image.save(buffered, format=fmt)
            buffered.seek(0)

            media_type = f"image/{request.output_format}"
            return Response(content=buffered.getvalue(), media_type=media_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Run API server"""
    import argparse

    parser = argparse.ArgumentParser(description="FLUX Kontext API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--model-path", type=str, default="./models/flux-kontext-dev",
                        help="Path to FLUX model")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    os.environ["FLUX_MODEL_PATH"] = args.model_path

    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()
