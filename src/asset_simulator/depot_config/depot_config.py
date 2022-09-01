from typing import Dict

from pydantic import BaseModel


class AssetDepotConfig(BaseModel):
    interval_seconds: int
    vehicles: Dict[str, Dict[str, int]]
    n_l2_stations: int
    n_dcfc_stations: int
    l2_max_power_kw: float
    dcfc_max_power_kw: float