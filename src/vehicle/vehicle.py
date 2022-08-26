class Vehicle():

    def __init__(self, id, station_network, connected_station=None):
        self.id = id
        self.conected_station = connected_station
        self.station_network = station_network

    @property
    def connected(self):
        return self.connected_station == None

    def plugin(self, station):
        self.connected_station = station.id
        station.connected_vehicle = self.id

    def unplug(self):
        self.connected_station = None

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