from pydantic import BaseModel


class Station(BaseModel):
    id: int
    type: str
    connected_vehicle_id: int = None
    max_power_kw: float

    def is_l2(self):
        return self.type == 'L2'

    def is_dcfc(self):
        return self.type == 'DCFC'

    def is_available(self):
        return isinstance(self.connected_vehicle_id, int) == False

    def plugin(self, vehicle_id):
        self.connected_vehicle_id = vehicle_id

    def _unplug(self):
        self.connected_vehicle_id = None