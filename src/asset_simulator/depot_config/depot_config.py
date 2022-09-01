from typing import Dict

from pydantic import BaseModel


class DepotConfig(BaseModel):
    interval_seconds: int
    vehicles: Dict[str, Dict[str, int]]
    n_l2_stations: int
    n_dcfc_stations: int