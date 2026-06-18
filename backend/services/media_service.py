from sqlalchemy.orm import Session
from fastapi import UploadFile
from typing import Optional, List, Dict
from backend.repositories.media_repository import MediaAssetRepository
from backend.models.models import MediaAsset, User
from backend.storage.local_storage import LocalStorageProvider
from backend.utils.media_processor import validate_and_process_image, validate_external_image_url, delete_processed_image
from backend.utils.audit_logger import log_action
from backend.exceptions.base import NotFoundException

class MediaService:
    def __init__(self, db: Session):
        self.media_repo = MediaAssetRepository(db)
        self.storage = LocalStorageProvider()
        self.db = db

    async def get_media_asset(self, asset_id: int) -> MediaAsset:
        asset = self.media_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundException("Media asset not found")
        return asset

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

    async def delete_media_asset(self, asset_id: int, current_user: User, client_ip: str) -> None:
        asset = self.media_repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundException("Media asset not found")
            
        old_val = {"filename": asset.filename, "storage_key": asset.storage_key}
        
        # Disk delete
        if asset.storage_key:
            delete_processed_image(asset.storage_key)
            
        self.media_repo.delete(asset)
        
        # Log action
        log_action(
            self.db, current_user.id, "media", asset_id, "delete",
            old_value=old_val, ip_address=client_ip
        )
