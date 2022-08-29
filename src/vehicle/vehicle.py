from pydantic import BaseModel


class Vehicle(BaseModel):
    id: int
    connected_station: int
    type: str
    state_of_charge: float

    def plugin(self, station_id: int):
        self.connected_station = station_id
        # log which vehicle the evse is plugged to
        for station in self.depot.stations:
            if station.id == station_id:
                station.connected_vehicle = self.id

    def unplug(self):
        # unassign vehicle
        for station_idx, station in enumerate(self.depot.stations):
            if station.id == self.station.connected_vehicle_id:
                # unplug vehicle and remove assignment
                self.depot.stations[station_idx].connected_vehicle_id = None

    def prefer_l2(self):
        l2_available, station_id = self.station_network.l2_is_available()
        # L2 is available
        if l2_available:
            self.connected_station = station_id
        else:
            dcfc_available, station_id = self.station_network.dcfc_is_available()
            # DCFC is available
            if dcfc_available:
                self.connected_station = station_id
            # Need to park as no L2 nor DCFC available
            else:
                self.connected_station = None


    def prefer_dcfc(self):
        dcfc_available, station_id = self.station_network.dcfc_is_available()
        # DCFC Available
        if dcfc_available:
            self.connected_station = station_id

        #todo: move vehicles to make room for DCFC

        else:
            # Check if L2 available
            l2_available, station_id = self.station_network.l2_is_available()

            # L2 is available
            if l2_available:
                self.connected_station = station_id
            # Need to park as no L2 nor DCFC available
            else:
                self.connected_station = None