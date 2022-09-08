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
    # walk ins are just treated as reservations with type = 'walk_in'
    # walk_in_events: List[str]
    vehicles_demand_sim: List[str]
    vehicles_heuristic: List[str]
    stations: List[str]