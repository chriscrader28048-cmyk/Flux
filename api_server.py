#!/usr/bin/env python3
"""
FLUX.1-dev API Server
FastAPI-based REST API for image generation
"""

import os
import io
import base64
import torch
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional
from PIL import Image
import uvicorn

app = FastAPI(
    title="FLUX.1-dev API",
    description="API for generating images with FLUX.1-dev model",
    version="1.0.0"
)

# CORS for client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your clients
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

class GenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for image generation")
    negative_prompt: Optional[str] = Field("", description="Negative prompt")
    width: int = Field(1024, ge=256, le=2048, description="Image width")
    height: int = Field(1024, ge=256, le=2048, description="Image height")
    num_inference_steps: int = Field(50, ge=1, le=100, description="Number of inference steps")
    guidance_scale: float = Field(3.5, ge=0, le=20, description="Guidance scale")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    output_format: str = Field("png", description="Output format: png, jpeg, base64")

class GenerationResponse(BaseModel):
    success: bool
    message: str
    image_base64: Optional[str] = None
    seed: Optional[int] = None

def load_model(model_path: str = "./models/flux-dev"):
    """Load FLUX model"""
    global pipe

    try:
        from diffusers import FluxPipeline

        print(f"Loading FLUX model from {model_path}...")

        pipe = FluxPipeline.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32
        )

        if torch.cuda.is_available():
            pipe = pipe.to("cuda")
            print("Model loaded on CUDA")
        else:
            print("CUDA not available, using CPU (will be slow)")

        # Enable memory optimizations
        pipe.enable_attention_slicing()

        print("Model loaded successfully!")
        return True

    except Exception as e:
        print(f"Error loading model: {e}")
        return False

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    import os
    model_path = os.environ.get("FLUX_MODEL_PATH", "./models/flux-dev")
    if not load_model(model_path):
        print("Warning: Model not loaded. Please ensure model is downloaded.")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "model_loaded": pipe is not None,
        "cuda_available": torch.cuda.is_available()
    }

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "model_loaded": pipe is not None}

@app.post("/generate", response_model=GenerationResponse)
async def generate_image(request: GenerationRequest, auth: bool = Depends(verify_api_key)):
    """Generate image from text prompt"""
    global pipe

    if pipe is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Set seed for reproducibility
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

        # Convert to requested format
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
            # Return image directly
            buffered = io.BytesIO()
            fmt = "PNG" if request.output_format == "png" else "JPEG"
            image.save(buffered, format=fmt)
            buffered.seek(0)

            media_type = f"image/{request.output_format}"
            return Response(content=buffered.getvalue(), media_type=media_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/batch")
async def generate_batch(prompts: list[str], settings: Optional[GenerationRequest] = None):
    """Generate multiple images from prompts"""
    global pipe

    if pipe is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    results = []
    for prompt in prompts:
        try:
            result = pipe(
                prompt=prompt,
                height=settings.height if settings else 1024,
                width=settings.width if settings else 1024,
                num_inference_steps=settings.num_inference_steps if settings else 50,
                guidance_scale=settings.guidance_scale if settings else 3.5,
            )

            image = result.images[0]
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            results.append({
                "prompt": prompt,
                "success": True,
                "image_base64": img_base64
            })
        except Exception as e:
            results.append({
                "prompt": prompt,
                "success": False,
                "error": str(e)
            })

    return {"results": results}

def main():
    """Run API server"""
    import argparse

    parser = argparse.ArgumentParser(description="FLUX API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--model-path", type=str, default="./models/flux-dev",
                        help="Path to FLUX model")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    import os
    os.environ["FLUX_MODEL_PATH"] = args.model_path

    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()
