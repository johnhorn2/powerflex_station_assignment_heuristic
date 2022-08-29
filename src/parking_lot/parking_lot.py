from typing import Optional, List

from pydantic import BaseModel

from src.vehicle.vehicle import Vehicle


class ParkingLot(BaseModel):
    id: int
    vehicles: Optional[ List[Vehicle]] = None