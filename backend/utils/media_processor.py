import os
import uuid
import shutil
from PIL import Image
from fastapi import UploadFile, HTTPException, status
from typing import Dict, Tuple

MAX_FILE_SIZE = 2 * 1024 * 1024 # 2MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_RESOLUTION = (4000, 4000)

MEDIA_DIR = os.path.join("backend", "uploads", "media")
THUMB_DIR = os.path.join(MEDIA_DIR, "thumbnails")
MEDIUM_DIR = os.path.join(MEDIA_DIR, "medium")
ORIG_DIR = os.path.join(MEDIA_DIR, "original")

# Ensure upload dirs exist
os.makedirs(THUMB_DIR, exist_ok=True)
os.makedirs(MEDIUM_DIR, exist_ok=True)
os.makedirs(ORIG_DIR, exist_ok=True)

def validate_and_process_image(file: UploadFile, asset_type: str) -> Dict[str, str]:
    """
    Validates uploaded image and generates Original, Medium, and Thumbnail versions safely.
    Returns storage URLs dict.
    """
    # 1. Path traversal protection: secure filename
    filename = os.path.basename(file.filename)
    
    # 2. MIME type validation
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MIME type. Only JPEG, PNG, and WEBP are allowed."
        )
        
    # Read file content for validation
    content = file.file.read()
    file_size = len(content)
    
    # 3. Size validation
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 2MB limit."
        )
        
    # Reset file pointer
    file.file.seek(0)
    
    # 4. Actual image header validation (Pillow scan)
    try:
        img = Image.open(file.file)
        img.verify() # scan headers
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file or corrupt headers."
        )
        
    # Reset file pointer again for editing
    file.file.seek(0)
    img = Image.open(file.file)
    
    # 5. Max resolution check
    if img.width > MAX_RESOLUTION[0] or img.height > MAX_RESOLUTION[1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image resolution exceeds the limit of {MAX_RESOLUTION[0]}x{MAX_RESOLUTION[1]}."
        )
        
    # 6. Generate UUID filenames
    ext = filename.split('.')[-1] if '.' in filename else 'jpg'
    unique_id = uuid.uuid4().hex
    unique_filename = f"{unique_id}.{ext}"
    
    # Define save paths
    orig_path = os.path.join(ORIG_DIR, unique_filename)
    medium_path = os.path.join(MEDIUM_DIR, unique_filename)
    thumb_path = os.path.join(THUMB_DIR, unique_filename)
    
    # 7. Generate Original, Medium, and Thumbnail versions
    # Original
    img.save(orig_path)
    
    # Medium (Max width/height 800)
    img_medium = img.copy()
    img_medium.thumbnail((800, 800))
    img_medium.save(medium_path)
    
    # Thumbnail (Max width/height 150)
    img_thumb = img.copy()
    img_thumb.thumbnail((150, 150))
    img_thumb.save(thumb_path)
    
    # Return mapping URLs
    return {
        "filename": filename,
        "storage_key": unique_filename,
        "public_url": f"/static/media/original/{unique_filename}",
        "medium_url": f"/static/media/medium/{unique_filename}",
        "thumbnail_url": f"/static/media/thumbnails/{unique_filename}"
    }

def delete_processed_image(storage_key: str):
    """Safely deletes the original, medium, and thumbnail images from disk."""
    for folder in [ORIG_DIR, MEDIUM_DIR, THUMB_DIR]:
        path = os.path.join(folder, storage_key)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error removing file {path}: {e}")

import urllib.parse
import httpx

def validate_external_image_url(url: str) -> Dict[str, str]:
    """
    Validates that the external URL is a valid HTTP/HTTPS image URL,
    accessible, has a valid MIME type, and holds correct image headers.
    """
    # 1. URL scheme security check
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL scheme. Only http:// and https:// protocols are allowed."
        )
        
    # Prevent common script injection attempts in URL string
    if "javascript:" in url.lower() or "data:" in url.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsafe URL protocol or source type."
        )

    # 2. Check extension & MIME by streaming the content
    try:
        # Timeout at 5.0 seconds to prevent hanging
        with httpx.Client(follow_redirects=True, timeout=5.0) as client:
            with client.stream("GET", url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"External image is not accessible. HTTP Status: {response.status_code}"
                    )
                    
                content_type = response.headers.get("Content-Type", "").lower()
                allowed_mimes = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
                
                if not any(mime in content_type for mime in allowed_mimes):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"URL does not point to a valid image MIME type. Content-Type: {content_type}"
                    )
                    
                # Read first chunk of bytes to verify image headers using Pillow
                content = b""
                for chunk in response.iter_bytes(max_chunk_size=1024):
                    content += chunk
                    if len(content) > 50 * 1024:  # 50KB is more than enough for image headers
                        break
                        
                from PIL import Image
                import io
                try:
                    img = Image.open(io.BytesIO(content))
                    img.verify()  # Validate image headers
                except Exception:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Corrupted or invalid image headers on the external URL."
                    )
                    
                filename = url.split("/")[-1].split("?")[0] or "external_image.jpg"
                allowed_exts = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg")
                if not any(filename.lower().endswith(ext) for ext in allowed_exts):
                    ext = content_type.split("/")[-1] if "/" in content_type else "jpg"
                    filename = f"{filename}.{ext}"
                    
                return {
                    "filename": filename,
                    "mime_type": content_type,
                    "size_bytes": len(content),
                    "public_url": url,
                }
            
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch external URL: {str(e)}"
        )
