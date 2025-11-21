# FLUX.1-dev API Server

Local API server for FLUX.1-dev image generation model.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Download model

Get your Hugging Face token from https://huggingface.co/settings/tokens

```bash
# Set token
export HF_TOKEN="your_token_here"

# Download model
python download_model.py --output ./models/flux-dev
```

### 3. Start API server

```bash
python api_server.py --host 0.0.0.0 --port 8000
```

## API Usage

### Health Check

```bash
curl http://localhost:8000/health
```

### Generate Image

**Python:**

```python
import requests
import base64

response = requests.post("http://localhost:8000/generate", json={
    "prompt": "A beautiful sunset over mountains",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 50,
    "guidance_scale": 3.5,
    "output_format": "base64"
})

result = response.json()
img_data = base64.b64decode(result["image_base64"])
with open("output.png", "wb") as f:
    f.write(img_data)
```

**cURL:**

```bash
# Get PNG directly
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A cat in space", "output_format": "png"}' \
  --output image.png

# Get base64
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A futuristic city", "output_format": "base64"}'
```

### Client Script

```bash
python client_example.py "A beautiful landscape" --output result.png --steps 50
```

## API Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | string | required | Text description |
| width | int | 1024 | Image width (256-2048) |
| height | int | 1024 | Image height (256-2048) |
| num_inference_steps | int | 50 | Denoising steps (1-100) |
| guidance_scale | float | 3.5 | Guidance strength (0-20) |
| seed | int | random | Random seed |
| output_format | string | "png" | "png", "jpeg", "base64" |

## Requirements

- Python 3.10+
- CUDA GPU with 24GB+ VRAM (recommended)
- ~30GB disk space for model

## Remote Access

To access from other machines:

```bash
# On server
python api_server.py --host 0.0.0.0 --port 8000

# On client
python client_example.py "prompt" --server http://SERVER_IP:8000
```
