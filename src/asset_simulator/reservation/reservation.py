from datetime import datetime

from pydantic import BaseModel


class Reservation(BaseModel):
    id: int
    departure_timestamp_utc: datetime
    vehicle_type: str
    state_of_charge: float
    assigned_vehicle_id: int = None

