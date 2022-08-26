class Station:

    def __init__(self, id, type, max_pow_kw, vehicle=None):
        self.type = type
        self.id = id
        self.connected_vehicle = vehicle
        self.max_pow_kw

    def is_l2(self):
        return self.type == 'L2'

    def is_dcfc(self):
        return self.type == 'DCFC'

    def is_available(self):
        return self.connected_vehicle == None