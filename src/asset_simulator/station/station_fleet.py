from typing import Dict

from pydantic import BaseModel

from src.asset_simulator.station.station import Station



class StationFleet(BaseModel):
    stations: Dict[int, Station] = {}