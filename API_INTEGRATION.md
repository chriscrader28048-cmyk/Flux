# FLUX.1-Kontext-dev API Integration Guide

## Server Information

Khi khởi động server, bạn sẽ thấy:
```
==================================================
FLUX.1-Kontext-dev API Server
==================================================
Local:   http://localhost:8000
Network: http://192.168.x.x:8000
==================================================
```

**Sử dụng địa chỉ Network cho client từ xa.**

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Kiểm tra trạng thái server |
| `/generate` | POST | Tạo ảnh từ text (text-to-image) |
| `/edit` | POST | Chỉnh sửa ảnh (image-to-image) |

---

## Authentication

Thêm header `X-API-Key` nếu server có cấu hình API key:
```
X-API-Key: your-api-key
```

---

## 1. Health Check

### cURL
```bash
curl http://SERVER_IP:8000/health
```

### Python
```python
import requests

response = requests.get("http://SERVER_IP:8000/health")
print(response.json())
# {"status": "healthy", "model_loaded": true}
```

---

## 2. Generate Image (Text-to-Image)

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | required | Mô tả ảnh cần tạo |
| `width` | int | 1024 | Chiều rộng (256-2048) |
| `height` | int | 1024 | Chiều cao (256-2048) |
| `num_inference_steps` | int | 50 | Số bước inference (1-100) |
| `guidance_scale` | float | 2.5 | Độ mạnh guidance (0-20) |
| `seed` | int | random | Seed để tái tạo kết quả |
| `output_format` | string | "png" | "png", "jpeg", "base64" |

### cURL
```bash
# Lưu trực tiếp thành file PNG
curl -X POST http://SERVER_IP:8000/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "prompt": "A beautiful sunset over mountains, photorealistic",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 50,
    "guidance_scale": 2.5,
    "output_format": "png"
  }' --output result.png

# Nhận base64
curl -X POST http://SERVER_IP:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cat wearing sunglasses",
    "output_format": "base64"
  }'
```

### Python
```python
import requests
import base64
from pathlib import Path

API_URL = "http://SERVER_IP:8000"
API_KEY = "your-api-key"  # Bỏ qua nếu không có

headers = {"X-API-Key": API_KEY} if API_KEY else {}

# Generate image
response = requests.post(
    f"{API_URL}/generate",
    headers=headers,
    json={
        "prompt": "A futuristic city at night with neon lights",
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 50,
        "guidance_scale": 2.5,
        "seed": 42,  # Optional: để tái tạo kết quả
        "output_format": "base64"
    },
    timeout=300  # 5 phút timeout
)

if response.status_code == 200:
    result = response.json()

    # Decode và lưu ảnh
    img_data = base64.b64decode(result["image_base64"])
    Path("output.png").write_bytes(img_data)

    print(f"Image saved! Seed: {result.get('seed')}")
else:
    print(f"Error: {response.text}")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');
const fs = require('fs');

const API_URL = 'http://SERVER_IP:8000';

async function generateImage(prompt) {
    const response = await axios.post(`${API_URL}/generate`, {
        prompt: prompt,
        width: 1024,
        height: 1024,
        output_format: 'base64'
    }, {
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'your-api-key'
        },
        timeout: 300000
    });

    const imgBuffer = Buffer.from(response.data.image_base64, 'base64');
    fs.writeFileSync('output.png', imgBuffer);
    console.log('Image saved!');
}

generateImage('A beautiful landscape');
```

---

## 3. Edit Image (Image-to-Image)

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | required | Mô tả chỉnh sửa |
| `input_image` | string | null | Ảnh gốc (base64) |
| `image_url` | string | null | URL ảnh gốc |
| `num_inference_steps` | int | 50 | Số bước inference |
| `guidance_scale` | float | 2.5 | Độ mạnh guidance |
| `seed` | int | random | Seed |
| `output_format` | string | "png" | Format output |

**Lưu ý:** Phải có `input_image` HOẶC `image_url`

### cURL
```bash
# Với URL ảnh
curl -X POST http://SERVER_IP:8000/edit \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Change the sky to a beautiful sunset",
    "image_url": "https://example.com/photo.jpg",
    "output_format": "png"
  }' --output edited.png

# Với base64 (dùng script để encode)
IMAGE_BASE64=$(base64 -w 0 input.png)
curl -X POST http://SERVER_IP:8000/edit \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"Add snow to the scene\",
    \"input_image\": \"$IMAGE_BASE64\",
    \"output_format\": \"png\"
  }" --output edited.png
```

### Python
```python
import requests
import base64
from pathlib import Path

API_URL = "http://SERVER_IP:8000"

def edit_image(input_path, prompt, output_path="edited.png"):
    # Đọc và encode ảnh gốc
    img_bytes = Path(input_path).read_bytes()
    img_base64 = base64.b64encode(img_bytes).decode()

    response = requests.post(
        f"{API_URL}/edit",
        json={
            "prompt": prompt,
            "input_image": img_base64,
            "num_inference_steps": 50,
            "guidance_scale": 2.5,
            "output_format": "base64"
        },
        timeout=300
    )

    if response.status_code == 200:
        result = response.json()
        img_data = base64.b64decode(result["image_base64"])
        Path(output_path).write_bytes(img_data)
        print(f"Edited image saved to {output_path}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

# Sử dụng
edit_image(
    input_path="photo.jpg",
    prompt="Make it look like winter with snow",
    output_path="winter_photo.png"
)
```

### Edit với URL
```python
import requests
import base64
from pathlib import Path

response = requests.post(
    "http://SERVER_IP:8000/edit",
    json={
        "prompt": "Add a rainbow in the sky",
        "image_url": "https://example.com/landscape.jpg",
        "output_format": "base64"
    },
    timeout=300
)

if response.status_code == 200:
    result = response.json()
    img_data = base64.b64decode(result["image_base64"])
    Path("rainbow.png").write_bytes(img_data)
```

---

## 4. Batch Processing

### Python - Xử lý nhiều ảnh
```python
import requests
import base64
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://SERVER_IP:8000"

def generate_single(prompt, output_name):
    response = requests.post(
        f"{API_URL}/generate",
        json={
            "prompt": prompt,
            "output_format": "base64"
        },
        timeout=300
    )

    if response.status_code == 200:
        result = response.json()
        img_data = base64.b64decode(result["image_base64"])
        Path(output_name).write_bytes(img_data)
        return f"Success: {output_name}"
    return f"Failed: {output_name}"

# Danh sách prompts
prompts = [
    ("A red sports car", "car.png"),
    ("A cozy cabin in the woods", "cabin.png"),
    ("A futuristic robot", "robot.png"),
]

# Xử lý tuần tự (an toàn cho VRAM)
for prompt, filename in prompts:
    result = generate_single(prompt, filename)
    print(result)
```

---

## 5. Error Handling

### Python
```python
import requests
from requests.exceptions import Timeout, ConnectionError

def safe_generate(prompt):
    try:
        response = requests.post(
            "http://SERVER_IP:8000/generate",
            json={"prompt": prompt, "output_format": "base64"},
            timeout=300
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise Exception("Invalid API key")
        elif response.status_code == 503:
            raise Exception("Model not loaded")
        else:
            raise Exception(f"Error {response.status_code}: {response.text}")

    except Timeout:
        raise Exception("Request timed out - try reducing steps")
    except ConnectionError:
        raise Exception("Cannot connect to server")

# Sử dụng
try:
    result = safe_generate("A beautiful sunset")
    print(f"Success! Seed: {result.get('seed')}")
except Exception as e:
    print(f"Error: {e}")
```

---

## 6. Client Script Có Sẵn

Server đi kèm `client_example.py`:

```bash
# Generate
python client_example.py --server http://SERVER_IP:8000 generate "A cat" -o cat.png

# Edit
python client_example.py --server http://SERVER_IP:8000 edit "Add snow" -i input.png -o output.png

# Với API key
python client_example.py --server http://SERVER_IP:8000 --api-key YOUR_KEY generate "A dog" -o dog.png
```

---

## Response Format

### Success (base64)
```json
{
  "success": true,
  "message": "Image generated successfully",
  "image_base64": "iVBORw0KGgo...",
  "seed": 42
}
```

### Error
```json
{
  "detail": "Error message here"
}
```

---

## Tips

1. **Timeout**: Đặt timeout ít nhất 5 phút (300s) vì generation có thể chậm
2. **Seed**: Lưu seed để tái tạo kết quả giống nhau
3. **Steps**: Giảm `num_inference_steps` (20-30) để nhanh hơn, tăng (50-100) để chất lượng cao hơn
4. **Guidance**: Tăng `guidance_scale` để ảnh theo prompt chặt hơn
5. **VRAM**: Server dùng CPU offload nên có thể chậm hơn GPU 24GB+
