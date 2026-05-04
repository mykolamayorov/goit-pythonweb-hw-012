"""
Cloudinary service utilities.

This module uploads user avatar images to Cloudinary and returns a secure URL.

Features:
- Validates Cloudinary configuration (from .env via app.config)
- Uploads images to folder "avatars"
- Overwrites by public_id (one avatar per user)
- Applies a basic transformation for avatars (250x250, crop fill)

Configuration (.env):
- CLOUDINARY_CLOUD_NAME
- CLOUDINARY_API_KEY
- CLOUDINARY_API_SECRET

Error handling:
- Raises RuntimeError with a helpful message on Cloudinary errors
"""

import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError

from app.config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET


def _ensure_cloudinary_config() -> None:
    """
    Ensure Cloudinary credentials exist in environment variables.

    Raises:
        RuntimeError: If any Cloudinary credential is missing.
    """
    if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_API_KEY or not CLOUDINARY_API_SECRET:
        raise RuntimeError("Cloudinary credentials are missing. Check .env CLOUDINARY_* variables.")


_ensure_cloudinary_config()

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_avatar(file_obj, public_id: str) -> str:
    """
    Upload avatar image to Cloudinary and return secure URL.

    Upload settings:
    - folder: avatars
    - public_id: provided (typically user_<id>)
    - overwrite: True
    - resource_type: image
    - transformation: 250x250 crop fill

    Args:
        file_obj: File-like object (e.g., UploadFile.file).
        public_id: Cloudinary public id for the image.

    Returns:
        Cloudinary secure_url for the uploaded image.

    Raises:
        RuntimeError: If Cloudinary upload fails or secure_url missing.
    """
    try:
        result = cloudinary.uploader.upload(
            file_obj,
            folder="avatars",
            public_id=public_id,
            overwrite=True,
            resource_type="image",
            transformation=[{"width": 250, "height": 250, "crop": "fill"}],
        )
    except CloudinaryError as e:
        raise RuntimeError(f"Cloudinary upload error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected upload error: {e}") from e

    url = result.get("secure_url")
    if not url:
        raise RuntimeError("Cloudinary did not return secure_url")
    return url