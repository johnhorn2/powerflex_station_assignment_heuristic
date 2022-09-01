from typing import Dict

from pydantic import BaseModel


class AlgoDepotConfig(BaseModel):
    minimum_ready_vehicle_pool: Dict[str, int]
    vehicles: Dict[str, Dict[str, int]]
    n_l2_stations: int
    n_dcfc_stations: int