from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Reservation(BaseModel):
    id: str
    departure_timestamp_utc: datetime
    created_at_timestamp_utc: datetime
    assigned_at_timestamp_utc: Optional[datetime] = None
    updated_at_timestamp_utc: Optional[datetime]
    vehicle_type: str
    state_of_charge: float
    assigned_vehicle_id: int = None
    walk_in: bool = False
    status: str


