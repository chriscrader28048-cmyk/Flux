# FLUX.1-Kontext-dev API Server

Local API server for FLUX.1-Kontext-dev image editing model.

## Features
- **Text-to-Image**: Generate images from text prompts
- **Image Editing**: Edit existing images with text instructions
- Sequential download with auto-retry
- API key authentication

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Download model

```bash
# Set token
set HF_TOKEN=your_token_here  # Windows
export HF_TOKEN=your_token_here  # Linux

# Download model (sequential with retry)
python download_model.py --token your_token

# Verify and re-download missing files
python download_model.py --verify --token your_token
```

### 3. Start API server

```bash
python api_server.py --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Generate Image (Text-to-Image)

```bash
curl -X POST http://SERVER_IP:8000/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "prompt": "A beautiful sunset",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 50,
    "guidance_scale": 2.5,
    "output_format": "png"
  }' --output image.png
```

### Edit Image (Image-to-Image)

```bash
# With image URL
curl -X POST http://SERVER_IP:8000/edit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "prompt": "Change the sky to sunset colors",
    "image_url": "https://example.com/image.jpg",
    "output_format": "png"
  }' --output edited.png

# With base64 image
curl -X POST http://SERVER_IP:8000/edit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "prompt": "Add a rainbow",
    "input_image": "<base64_encoded_image>",
    "output_format": "base64"
  }'
```

## Client Script Usage

```bash
# Generate image
python client_example.py generate "A cat in space" -o cat.png \
  --server http://SERVER_IP:8000 --api-key your-key

# Edit image
python client_example.py edit "Make it sunset" -i input.png -o output.png \
  --server http://SERVER_IP:8000 --api-key your-key
```

## Python Client

```python
import requests
import base64

# Generate
response = requests.post(
    "http://SERVER_IP:8000/generate",
    headers={"X-API-Key": "your-key"},
    json={
        "prompt": "A landscape",
        "output_format": "base64"
    }
)

# Edit
with open("input.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

response = requests.post(
    "http://SERVER_IP:8000/edit",
    headers={"X-API-Key": "your-key"},
    json={
        "prompt": "Add snow",
        "input_image": img_b64,
        "output_format": "base64"
    }
)
```

## Production Deployment

```bash
# Edit flux-api.service with your paths
sudo cp flux-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable flux-api
sudo systemctl start flux-api
```

## Requirements

- Python 3.10+
- CUDA GPU with 24GB+ VRAM
- ~30GB disk space for model
