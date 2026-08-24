from pydantic import BaseModel, field_serializer
from typing import List, Optional
from datetime import datetime

class ReservationCreate(BaseModel):
    show_id: int
    seats: List[str]

class SeatReservationResponse(BaseModel):
    id: int
    seat_id: str
    show_id: int
    status: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime) -> str:
        return dt.isoformat() + "Z" if dt.tzinfo is None else dt.isoformat()

    class Config:
        from_attributes = True

class ReservationGroupResponse(BaseModel):
    id: int
    user_id: int
    show_id: int
    reservation_token: str
    reserved_at: datetime
    expires_at: datetime
    status: str
    created_at: datetime
    reserved_seats: List[SeatReservationResponse] = []

    @field_serializer("reserved_at", "expires_at", "created_at")
    def serialize_datetimes(self, dt: datetime) -> str:
        return dt.isoformat() + "Z" if dt.tzinfo is None else dt.isoformat()

    class Config:
        from_attributes = True

class ReservationConfirmRequest(BaseModel):
    reservation_ids: List[int]
