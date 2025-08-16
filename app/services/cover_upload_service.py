from __future__ import annotations

import io
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple

from PIL import Image

from app.core.logger_config import setup_logger

logger = setup_logger(__name__)


ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
MIN_DIMENSIONS: Tuple[int, int] = (400, 600)
MAX_DIMENSIONS: Tuple[int, int] = (2000, 3000)


@dataclass
class ProcessedImage:
    content: bytes
    mime_type: str
    width: int
    height: int
    aspect_ratio: float
    ext: str


class CoverUploadService:
    """Validate and upload cover images to Supabase storage."""

    bucket_name: str = "covers"

    @staticmethod
    def _ensure_dimensions(img: Image.Image) -> Image.Image:
        """Resize down if the image exceeds MAX_DIMENSIONS while preserving aspect ratio."""
        max_w, max_h = MAX_DIMENSIONS
        if img.width <= max_w and img.height <= max_h:
            return img
        img = img.copy()
        img.thumbnail((max_w, max_h))
        return img

    @staticmethod
    def validate_and_process(image_bytes: bytes, mime_type: str) -> ProcessedImage:
        if not image_bytes:
            raise ValueError("Empty file upload")
        if len(image_bytes) > MAX_BYTES:
            raise ValueError("Image exceeds 10MB size limit")
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError("Unsupported file type. Allowed: JPG, PNG, WEBP")

        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("RGB")  # normalize
            if img.width < MIN_DIMENSIONS[0] or img.height < MIN_DIMENSIONS[1]:
                raise ValueError("Image is too small. Minimum 400x600")

            img = CoverUploadService._ensure_dimensions(img)

            # Determine output format
            if mime_type == "image/png":
                fmt = "PNG"
                ext = ".png"
                out_mime = "image/png"
            else:
                # prefer JPEG for covers (good compression + compatibility)
                fmt = "JPEG"
                ext = ".jpg"
                out_mime = "image/jpeg"

            buf = io.BytesIO()
            img.save(buf, format=fmt, quality=92, optimize=True)
            content = buf.getvalue()
            width, height = img.width, img.height
            aspect_ratio = round(width / float(height), 4) if height else 0.0

        return ProcessedImage(
            content=content,
            mime_type=out_mime,
            width=width,
            height=height,
            aspect_ratio=aspect_ratio,
            ext=ext,
        )

    @staticmethod
    def upload_to_supabase(supabase, user_id: str, story_id: int, processed: ProcessedImage) -> str:
        """Upload the processed image to Supabase storage and return a public URL."""
        # Try to ensure bucket exists
        try:
            storage_admin = getattr(supabase, "storage", None)
            if storage_admin:
                buckets = storage_admin.list_buckets() or []
                names = [b.get("name") if isinstance(b, dict) else getattr(b, "name", None) for b in buckets]
                if CoverUploadService.bucket_name not in (names or []):
                    try:
                        storage_admin.create_bucket(CoverUploadService.bucket_name, public=True)
                        logger.info("[COVER][UPLOAD] Created bucket '%s'", CoverUploadService.bucket_name)
                    except Exception:
                        pass
        except Exception:
            pass
        # Build deterministic path with timestamp to bust caches
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        path = f"{user_id}/{story_id}/cover_{timestamp}{processed.ext}"

        logger.info("[COVER][UPLOAD] Uploading to bucket '%s' path '%s'", CoverUploadService.bucket_name, path)

        # Supabase python client expects raw bytes or a file path; provide bytes
        file_bytes = processed.content

        storage = supabase.storage
        bucket = storage.from_(CoverUploadService.bucket_name)

        # Use upsert to overwrite any previous file with same name
        resp = bucket.upload(path=path, file=file_bytes, file_options={"contentType": processed.mime_type, "upsert": "true"})
        if getattr(resp, "error", None):
            raise RuntimeError(f"Supabase upload failed: {resp.error}")

        # Get public URL
        public_url = bucket.get_public_url(path)
        if isinstance(public_url, dict):
            public_url = public_url.get("publicUrl") or public_url.get("public_url") or ""
        if not public_url:
            raise RuntimeError("Failed to obtain public URL for uploaded cover")

        return public_url


