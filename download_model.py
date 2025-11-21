#!/usr/bin/env python3
"""
Script to download FLUX.1-Kontext-dev model from Hugging Face
With sequential download and retry mechanism
"""

import os
import time
from huggingface_hub import hf_hub_download, list_repo_files, login
from pathlib import Path

def download_flux_model(
    model_id: str = "black-forest-labs/FLUX.1-Kontext-dev",
    local_dir: str = "./models/flux-kontext-dev",
    token: str = None,
    max_retries: int = 5,
    retry_delay: int = 3
):
    """
    Download FLUX.1-Kontext-dev model from Hugging Face

    Args:
        model_id: Hugging Face model ID
        local_dir: Local directory to save model
        token: Hugging Face token (required for gated models)
        max_retries: Maximum retry attempts per file
        retry_delay: Delay between retries in seconds
    """

    # Create directory if not exists
    Path(local_dir).mkdir(parents=True, exist_ok=True)

    # Login if token provided
    if token:
        login(token=token)
    elif os.environ.get("HF_TOKEN"):
        login(token=os.environ.get("HF_TOKEN"))
    else:
        print("Warning: No HF_TOKEN provided. FLUX.1-Kontext-dev is a gated model.")
        print("Please set HF_TOKEN environment variable or pass token parameter.")
        print("Get your token at: https://huggingface.co/settings/tokens")
        return None

    print(f"Downloading {model_id} to {local_dir}...")

    try:
        # Get list of files in repository
        print("Fetching file list from repository...")
        files = list_repo_files(repo_id=model_id, token=token)

        # Filter out unnecessary files
        skip_patterns = ['.md', '.txt', '.gitattributes']
        files_to_download = [
            f for f in files
            if not any(f.endswith(p) for p in skip_patterns)
        ]

        total_files = len(files_to_download)
        print(f"Found {total_files} files to download\n")

        downloaded = 0
        failed = []

        # Download files sequentially with retry
        for i, filename in enumerate(files_to_download, 1):
            print(f"[{i}/{total_files}] Downloading: {filename}")

            success = False
            for attempt in range(1, max_retries + 1):
                try:
                    local_path = hf_hub_download(
                        repo_id=model_id,
                        filename=filename,
                        local_dir=local_dir,
                        token=token,
                        local_dir_use_symlinks=False
                    )
                    print(f"  ✓ Success: {local_path}")
                    downloaded += 1
                    success = True
                    break

                except Exception as e:
                    print(f"  ✗ Attempt {attempt}/{max_retries} failed: {e}")
                    if attempt < max_retries:
                        print(f"    Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        print(f"  ✗ Failed after {max_retries} attempts")
                        failed.append(filename)

            print()

        # Summary
        print("=" * 50)
        print(f"Download Summary:")
        print(f"  Total files: {total_files}")
        print(f"  Downloaded: {downloaded}")
        print(f"  Failed: {len(failed)}")

        if failed:
            print(f"\nFailed files:")
            for f in failed:
                print(f"  - {f}")
            print("\nRun the script again to retry failed downloads.")
            return None
        else:
            print(f"\nModel downloaded successfully to: {local_dir}")
            return local_dir

    except Exception as e:
        print(f"Error: {e}")
        raise

def verify_and_redownload(
    model_id: str = "black-forest-labs/FLUX.1-Kontext-dev",
    local_dir: str = "./models/flux-kontext-dev",
    token: str = None,
    max_retries: int = 5
):
    """
    Verify downloaded files and re-download missing ones
    """

    if token:
        login(token=token)
    elif os.environ.get("HF_TOKEN"):
        login(token=os.environ.get("HF_TOKEN"))

    print("Verifying downloaded files...")

    # Get list of files in repository
    files = list_repo_files(repo_id=model_id, token=token)
    skip_patterns = ['.md', '.txt', '.gitattributes']
    expected_files = [
        f for f in files
        if not any(f.endswith(p) for p in skip_patterns)
    ]

    # Check which files are missing
    missing = []
    for filename in expected_files:
        local_path = Path(local_dir) / filename
        if not local_path.exists():
            missing.append(filename)

    if not missing:
        print("All files are present!")
        return True

    print(f"Found {len(missing)} missing files:")
    for f in missing:
        print(f"  - {f}")

    print("\nRe-downloading missing files...")

    for i, filename in enumerate(missing, 1):
        print(f"\n[{i}/{len(missing)}] Downloading: {filename}")

        for attempt in range(1, max_retries + 1):
            try:
                hf_hub_download(
                    repo_id=model_id,
                    filename=filename,
                    local_dir=local_dir,
                    token=token,
                    local_dir_use_symlinks=False
                )
                print(f"  ✓ Success")
                break
            except Exception as e:
                print(f"  ✗ Attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    time.sleep(3)

    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download FLUX.1-Kontext-dev model")
    parser.add_argument("--token", type=str, help="Hugging Face token")
    parser.add_argument("--output", type=str, default="./models/flux-kontext-dev",
                        help="Output directory")
    parser.add_argument("--verify", action="store_true",
                        help="Verify and re-download missing files only")
    parser.add_argument("--retries", type=int, default=5,
                        help="Max retries per file")

    args = parser.parse_args()

    if args.verify:
        verify_and_redownload(
            local_dir=args.output,
            token=args.token,
            max_retries=args.retries
        )
    else:
        download_flux_model(
            local_dir=args.output,
            token=args.token,
            max_retries=args.retries
        )
