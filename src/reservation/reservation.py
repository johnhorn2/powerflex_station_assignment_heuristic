from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from src.vehicle.vehicle import Vehicle
from src.station.station import Station



class Reservation(BaseModel):
    id: int
    departure_timestamp_utc: datetime
    vehicle_type: str
    state_of_charge: float
    assigned_vehicle_id: int = None


