#!/usr/bin/env python3
"""
Script to download FLUX.1-dev model from Hugging Face
"""

import os
from huggingface_hub import snapshot_download, login
from pathlib import Path

def download_flux_model(
    model_id: str = "black-forest-labs/FLUX.1-dev",
    local_dir: str = "./models/flux-dev",
    token: str = None
):
    """
    Download FLUX.1-dev model from Hugging Face

    Args:
        model_id: Hugging Face model ID
        local_dir: Local directory to save model
        token: Hugging Face token (required for gated models)
    """

    # Create directory if not exists
    Path(local_dir).mkdir(parents=True, exist_ok=True)

    # Login if token provided
    if token:
        login(token=token)
    elif os.environ.get("HF_TOKEN"):
        login(token=os.environ.get("HF_TOKEN"))
    else:
        print("Warning: No HF_TOKEN provided. FLUX.1-dev is a gated model.")
        print("Please set HF_TOKEN environment variable or pass token parameter.")
        print("Get your token at: https://huggingface.co/settings/tokens")
        return None

    print(f"Downloading {model_id} to {local_dir}...")

    try:
        # Download model
        local_path = snapshot_download(
            repo_id=model_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            resume_download=True,
            ignore_patterns=["*.md", "*.txt"]  # Skip documentation files
        )

        print(f"Model downloaded successfully to: {local_path}")
        return local_path

    except Exception as e:
        print(f"Error downloading model: {e}")
        raise

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download FLUX.1-dev model")
    parser.add_argument("--token", type=str, help="Hugging Face token")
    parser.add_argument("--output", type=str, default="./models/flux-dev",
                        help="Output directory")

    args = parser.parse_args()

    download_flux_model(
        local_dir=args.output,
        token=args.token
    )
