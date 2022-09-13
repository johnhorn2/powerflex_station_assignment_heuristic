from typing import Dict

from pydantic import BaseModel

from src.asset_simulator.vehicle.vehicle import Vehicle



class VehicleFleet(BaseModel):
    vehicles: Dict[int, Vehicle] = {}