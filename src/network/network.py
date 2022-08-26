class Network:

    def __init__(self, station_list, vehicle_list):
        self.station_list = station_list
        self.vehicle_list = vehicle_list

    def l2_is_available(self):
        for station in self.station_list:
            if station.is_available() and station.is_l2():
                return (True, station.id)
        return (False, None)

    def assign_vehicle_to_station(self, vehicle_id, station_id):
        vehicle = self.vehicle_list[vehicle_id]
        station = self.station_list[station_id]

    def dcfc_is_available(self):
        for station in self.station_list:
            if station.is_available() and station.is_dcfc():
                return (True, station.id)
        return (False, None)
