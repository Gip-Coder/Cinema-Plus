from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

class SeatPricingBase(BaseModel):
    theatre_id: int
    screen_id: Optional[int] = None
    seat_category: str # Premium, Executive, Normal
    base_price: float = Field(..., gt=0)
    currency: str = "INR"

class SeatPricingCreate(SeatPricingBase):
    pass

class SeatPricingUpdate(BaseModel):
    base_price: float = Field(..., gt=0)

class SeatPricingResponse(SeatPricingBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class PricingRuleBase(BaseModel):
    name: str
    rule_type: str # weekend, holiday, event, surge, time_based
    multiplier: float = Field(..., gt=0)
    priority: int = 0
    stackable: bool = True
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: bool = True
    theatre_id: Optional[int] = None
    screen_id: Optional[int] = None

class PricingRuleCreate(PricingRuleBase):
    pass

class PricingRuleUpdate(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[str] = None
    multiplier: Optional[float] = Field(None, gt=0)
    priority: Optional[int] = None
    stackable: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    is_active: Optional[bool] = None

class PricingRuleResponse(PricingRuleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class MediaAssetResponse(BaseModel):
    id: int
    filename: str
    storage_provider: str
    storage_key: Optional[str] = None
    public_url: Optional[str] = None
    mime_type: str
    size_bytes: int
    asset_type: str
    thumbnail_url: Optional[str] = None
    medium_url: Optional[str] = None
    source_type: str
    original_source_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    entity_type: str
    entity_id: int
    action: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True
