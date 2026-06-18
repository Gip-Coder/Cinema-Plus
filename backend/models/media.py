from sqlalchemy import Column, Integer, String, DateTime
from backend.database import Base
from datetime import datetime

class MediaAsset(Base):
    __tablename__ = "media_assets"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    storage_provider = Column(String(50), default="local") # local, s3, cdn, external
    storage_key = Column(String(255))
    public_url = Column(String(1000))
    mime_type = Column(String(100))
    size_bytes = Column(Integer)
    asset_type = Column(String(50)) # poster, banner, screen_preview
    thumbnail_url = Column(String(1000))
    medium_url = Column(String(1000))
    source_type = Column(String(50), default="upload") # upload, external_url
    original_source_url = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
