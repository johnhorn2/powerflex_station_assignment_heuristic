from typing import List, Dict

from pydantic import BaseModel

from src.asset_simulator.reservation.reservation import Reservation
from src.asset_simulator.vehicle.vehicle import Vehicle
from src.asset_simulator.station.station import Station


class MockQueue(BaseModel):
    scan_events: List[str]
    reservations: List[str]
    reservation_assignments: List[str]
    move_charge: List[str]
    departures: List[str]
    walk_in_events: List[str]
    vehicles: List[str]
    stations: List[str]