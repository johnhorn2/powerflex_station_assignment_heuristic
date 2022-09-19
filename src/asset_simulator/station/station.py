from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class Station(BaseModel):
    id: int
    type: str
    connected_vehicle_id: int = None
    max_power_kw: float
    last_unplugged: Optional[datetime]

    def is_l2(self):
        return self.type == 'L2'

    def is_dcfc(self):
        return self.type == 'DCFC'

    def is_available(self):
        return isinstance(self.connected_vehicle_id, int) == False

    def _plugin(self, vehicle_id):
        self.connected_vehicle_id = vehicle_id

    def _unplug(self, current_datetime):
        self.connected_vehicle_id = None
        self.last_unplugged = current_datetime