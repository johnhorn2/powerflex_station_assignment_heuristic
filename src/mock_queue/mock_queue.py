from typing import List, Dict

from pydantic import BaseModel

from src.asset_simulator.reservation.reservation import Reservation


class MockQueue(BaseModel):
    scan_events: List[int]
    reservation_events: List[Reservation]
    walk_in_events: List[Reservation]