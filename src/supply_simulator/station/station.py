from pydantic import BaseModel


class Station(BaseModel):
    id: int
    type: str
    connected_vehicle_id: int = None
    max_pow_kw: float = 12.0

    def is_l2(self):
        return self.type == 'L2'

    def is_dcfc(self):
        return self.type == 'DCFC'

    def is_available(self):
        return self.connected_vehicle == None