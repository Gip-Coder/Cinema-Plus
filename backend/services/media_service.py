from sqlalchemy.orm import Session
from fastapi import UploadFile
from backend.repositories.media_repository import MediaAssetRepository
from backend.models.models import MediaAsset, User
from backend.storage.local_storage import LocalStorageProvider
from backend.utils.media_processor import validate_and_process_image, validate_external_image_url
from backend.utils.audit_logger import log_action

class MediaService:
    """Backs the movie poster upload pipeline (POST /api/movies/upload-poster).

    NOTE: the standalone Admin Media Library (list/view/delete arbitrary
    media assets) was removed — it could not even list its own uploads and
    had no real consumer. `get_media_asset`/`delete_media_asset` were only
    ever called by that removed UI's backend routes and were removed with
    it. `media_assets` rows are still created here as an internal upload
    record (kept per product decision — not dropped), but nothing reads
    them back; the URL returned to the caller is what actually gets stored
    on Movie.poster_url.
    """

    def __init__(self, db: Session):
        self.media_repo = MediaAssetRepository(db)
        self.storage = LocalStorageProvider()
        self.db = db

    async def upload_local_media(self, file: UploadFile, asset_type: str, current_user: User, client_ip: str) -> MediaAsset:
        # Custom image validation & processing logic
        processed = validate_and_process_image(file, asset_type)
        new_asset = MediaAsset(
            filename=processed["filename"],
            storage_provider="local",
            storage_key=processed["storage_key"],
            public_url=processed["public_url"],
            mime_type=file.content_type or "image/jpeg",
            size_bytes=processed.get("size_bytes", 0),
            asset_type=asset_type,
            thumbnail_url=processed["thumbnail_url"],
            medium_url=processed["medium_url"],
            source_type="upload",
            original_source_url=None
        )
        asset = self.media_repo.create(new_asset)

        # Log action
        log_action(
            self.db, current_user.id, "media", asset.id, "upload",
            new_value={"public_url": asset.public_url, "source_type": asset.source_type},
            ip_address=client_ip
        )
        return asset

    async def register_external_media(self, image_url: str, asset_type: str, current_user: User, client_ip: str) -> MediaAsset:
        processed = validate_external_image_url(image_url)
        new_asset = MediaAsset(
            filename=processed["filename"],
            storage_provider="external",
            storage_key=None,
            public_url=processed["public_url"],
            mime_type=processed["mime_type"],
            size_bytes=processed["size_bytes"],
            asset_type=asset_type,
            thumbnail_url=processed["public_url"],
            medium_url=processed["public_url"],
            source_type="external_url",
            original_source_url=image_url
        )
        asset = self.media_repo.create(new_asset)

        # Log action
        log_action(
            self.db, current_user.id, "media", asset.id, "upload_url",
            new_value={"public_url": asset.public_url, "source_type": asset.source_type},
            ip_address=client_ip
        )
        return asset
