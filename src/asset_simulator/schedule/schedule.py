from pydantic import BaseModel
from typing import Dict

from src.asset_simulator.reservation.reservation import Reservation


class Schedule(BaseModel):
    reservations: Dict[int, Reservation] = {}