from pydantic import BaseModel
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

    class Config:
        from_attributes = True

class ReservationConfirmRequest(BaseModel):
    reservation_ids: List[int]
