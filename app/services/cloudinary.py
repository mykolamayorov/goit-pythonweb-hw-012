import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError

from app.config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET


def _ensure_cloudinary_config() -> None:
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
    Adds basic transformation: crop to 250x250 (fill).
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