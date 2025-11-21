#!/usr/bin/env python3
"""
Client examples for FLUX API Server
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
    guidance_scale: float = 3.5,
    seed: int = None
):
    """
    Generate an image using the FLUX API

    Args:
        prompt: Text description of the image
        output_path: Path to save the generated image
        width: Image width (256-2048)
        height: Image height (256-2048)
        steps: Number of inference steps (1-100)
        guidance_scale: Guidance scale (0-20)
        seed: Random seed for reproducibility

    Returns:
        dict with result information
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
            timeout=300  # 5 minutes timeout for generation
        )

        if response.status_code == 200:
            result = response.json()

            if result.get("image_base64"):
                # Decode and save image
                img_data = base64.b64decode(result["image_base64"])
                Path(output_path).write_bytes(img_data)

                return {
                    "success": True,
                    "message": f"Image saved to {output_path}",
                    "seed": result.get("seed")
                }

        return {
            "success": False,
            "message": f"Error: {response.text}"
        }

    except requests.exceptions.Timeout:
        return {"success": False, "message": "Request timed out"}
    except Exception as e:
        return {"success": False, "message": str(e)}

def generate_image_direct(prompt: str, output_path: str = "output.png"):
    """Generate image and get PNG directly (no base64)"""

    payload = {
        "prompt": prompt,
        "output_format": "png"
    }

    response = requests.post(
        f"{API_URL}/generate",
        json=payload,
        timeout=300
    )

    if response.status_code == 200:
        Path(output_path).write_bytes(response.content)
        return {"success": True, "message": f"Image saved to {output_path}"}

    return {"success": False, "message": response.text}


# === CURL Examples ===
"""
# Health check
curl http://localhost:8000/health

# Generate image (returns base64)
curl -X POST http://localhost:8000/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "A beautiful sunset over mountains",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 50,
    "guidance_scale": 3.5,
    "output_format": "base64"
  }'

# Generate image (returns PNG directly)
curl -X POST http://localhost:8000/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "A futuristic city at night",
    "output_format": "png"
  }' --output image.png

# Generate with specific seed
curl -X POST http://localhost:8000/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "A cat sitting on a windowsill",
    "seed": 42,
    "output_format": "base64"
  }'
"""


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FLUX API Client")
    parser.add_argument("prompt", type=str, help="Image prompt")
    parser.add_argument("--output", "-o", type=str, default="output.png",
                        help="Output file path")
    parser.add_argument("--width", type=int, default=1024, help="Image width")
    parser.add_argument("--height", type=int, default=1024, help="Image height")
    parser.add_argument("--steps", type=int, default=50, help="Inference steps")
    parser.add_argument("--guidance", type=float, default=3.5, help="Guidance scale")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--server", type=str, default="http://localhost:8000",
                        help="API server URL")
    parser.add_argument("--api-key", type=str, default="", help="API key for authentication")

    args = parser.parse_args()

    API_URL = args.server
    API_KEY = args.api_key

    # Check server health
    health = check_health()
    print(f"Server status: {health}")

    if health.get("status") == "healthy":
        # Generate image
        print(f"Generating image for: {args.prompt}")
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
    else:
        print("Server is not available")
