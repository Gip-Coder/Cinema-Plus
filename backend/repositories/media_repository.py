from sqlalchemy.orm import Session
from typing import Optional, List
from backend.models.models import MediaAsset

class MediaAssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, asset_id: int) -> Optional[MediaAsset]:
        return self.db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[MediaAsset]:
        return self.db.query(MediaAsset).offset(skip).limit(limit).all()

    def create(self, asset: MediaAsset) -> MediaAsset:
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def delete(self, asset: MediaAsset) -> None:
        self.db.delete(asset)
        self.db.commit()
