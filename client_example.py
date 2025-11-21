#!/usr/bin/env python3
"""
Client examples for FLUX.1-Kontext-dev API Server
Supports both text-to-image and image editing
"""

import requests
import base64
from pathlib import Path

# API Server Configuration
API_URL = "http://localhost:8000"
API_KEY = ""  # Set your API key here or use --api-key argument

def check_health():
    """Check if API server is running"""
    try:
        response = requests.get(f"{API_URL}/health")
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Cannot connect to server"}

def generate_image(
    prompt: str,
    output_path: str = "output.png",
    width: int = 1024,
    height: int = 1024,
    steps: int = 50,
    guidance_scale: float = 2.5,
    seed: int = None
):
    """
    Generate image from text prompt (text-to-image)
    """
    payload = {
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_inference_steps": steps,
        "guidance_scale": guidance_scale,
        "output_format": "base64"
    }

    if seed is not None:
        payload["seed"] = seed

    try:
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY

        response = requests.post(
            f"{API_URL}/generate",
            json=payload,
            headers=headers,
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("image_base64"):
                img_data = base64.b64decode(result["image_base64"])
                Path(output_path).write_bytes(img_data)
                return {
                    "success": True,
                    "message": f"Image saved to {output_path}",
                    "seed": result.get("seed")
                }

        return {"success": False, "message": f"Error: {response.text}"}

    except requests.exceptions.Timeout:
        return {"success": False, "message": "Request timed out"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def edit_image(
    prompt: str,
    input_image_path: str = None,
    image_url: str = None,
    output_path: str = "output.png",
    steps: int = 50,
    guidance_scale: float = 2.5,
    seed: int = None
):
    """
    Edit an existing image with text prompt (image-to-image)
    """
    payload = {
        "prompt": prompt,
        "num_inference_steps": steps,
        "guidance_scale": guidance_scale,
        "output_format": "base64"
    }

    # Load input image
    if input_image_path:
        img_data = Path(input_image_path).read_bytes()
        payload["input_image"] = base64.b64encode(img_data).decode()
    elif image_url:
        payload["image_url"] = image_url
    else:
        return {"success": False, "message": "Either input_image_path or image_url is required"}

    if seed is not None:
        payload["seed"] = seed

    try:
        headers = {}
        if API_KEY:
            headers["X-API-Key"] = API_KEY

        response = requests.post(
            f"{API_URL}/edit",
            json=payload,
            headers=headers,
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("image_base64"):
                img_data = base64.b64decode(result["image_base64"])
                Path(output_path).write_bytes(img_data)
                return {
                    "success": True,
                    "message": f"Edited image saved to {output_path}",
                    "seed": result.get("seed")
                }

        return {"success": False, "message": f"Error: {response.text}"}

    except requests.exceptions.Timeout:
        return {"success": False, "message": "Request timed out"}
    except Exception as e:
        return {"success": False, "message": str(e)}


# === CURL Examples ===
"""
# Health check
curl http://localhost:8000/health

# Generate image (text-to-image)
curl -X POST http://localhost:8000/generate \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: your-api-key" \\
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 50,
    "guidance_scale": 2.5,
    "output_format": "base64"
  }'

# Edit image with URL (image-to-image)
curl -X POST http://localhost:8000/edit \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: your-api-key" \\
  -d '{
    "prompt": "Change the sky to sunset colors",
    "image_url": "https://example.com/image.jpg",
    "output_format": "png"
  }' --output edited.png

# Edit image with base64
curl -X POST http://localhost:8000/edit \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: your-api-key" \\
  -d '{
    "prompt": "Add a rainbow to the sky",
    "input_image": "<base64_encoded_image>",
    "output_format": "base64"
  }'
"""


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FLUX Kontext API Client")
    # Common arguments (must come first)
    parser.add_argument("--server", type=str, default="http://localhost:8000")
    parser.add_argument("--api-key", type=str, default="")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate image from text")
    gen_parser.add_argument("prompt", type=str, help="Text prompt")
    gen_parser.add_argument("--output", "-o", type=str, default="output.png")
    gen_parser.add_argument("--width", type=int, default=1024)
    gen_parser.add_argument("--height", type=int, default=1024)
    gen_parser.add_argument("--steps", type=int, default=50)
    gen_parser.add_argument("--guidance", type=float, default=2.5)
    gen_parser.add_argument("--seed", type=int, default=None)

    # Edit command
    edit_parser = subparsers.add_parser("edit", help="Edit existing image")
    edit_parser.add_argument("prompt", type=str, help="Edit prompt")
    edit_parser.add_argument("--input", "-i", type=str, help="Input image path")
    edit_parser.add_argument("--url", type=str, help="Input image URL")
    edit_parser.add_argument("--output", "-o", type=str, default="output.png")
    edit_parser.add_argument("--steps", type=int, default=50)
    edit_parser.add_argument("--guidance", type=float, default=2.5)
    edit_parser.add_argument("--seed", type=int, default=None)

    args = parser.parse_args()

    API_URL = args.server
    API_KEY = args.api_key

    # Check server
    health = check_health()
    print(f"Server status: {health}")

    if health.get("status") != "healthy":
        print("Server is not available")
        exit(1)

    if args.command == "generate":
        print(f"Generating image: {args.prompt}")
        result = generate_image(
            prompt=args.prompt,
            output_path=args.output,
            width=args.width,
            height=args.height,
            steps=args.steps,
            guidance_scale=args.guidance,
            seed=args.seed
        )
        print(result)

    elif args.command == "edit":
        print(f"Editing image: {args.prompt}")
        result = edit_image(
            prompt=args.prompt,
            input_image_path=args.input,
            image_url=args.url,
            output_path=args.output,
            steps=args.steps,
            guidance_scale=args.guidance,
            seed=args.seed
        )
        print(result)

    else:
        parser.print_help()
