from pydantic import BaseModel


class Vehicle(BaseModel):
    id: int
    connected_station_id: int
    type: str
    state_of_charge: float

    def plugin(self, station_id: int):
        self.connected_station = station_id
        # log which vehicle the evse is plugged to
        self.depot.stations[station_id].connected_vehicle = self.id

    def unplug(self):
        # unassign vehicle
        self.depot.stations[self.connected_station_id].connected_vehicle = None

    def prefer_l2(self):
        l2_available, station_id = self.depot.l2_is_available()
        # L2 is available
        if l2_available:
            self.connected_station = station_id
        else:
            dcfc_available, station_id = self.depot.dcfc_is_available()
            # DCFC is available
            if dcfc_available:
                self.connected_station = station_id
            # Need to park as no L2 nor DCFC available
            else:
                self.connected_station = None


    def prefer_dcfc(self):
        dcfc_available, station_id = self.depot.dcfc_is_available()
        # DCFC Available
        if dcfc_available:
            self.connected_station = station_id

        #todo: move vehicles to make room for DCFC

        else:
            # Check if L2 available
            l2_available, station_id = self.depot.l2_is_available()

            # L2 is available
            if l2_available:
                self.connected_station = station_id
            # Need to park as no L2 nor DCFC available
            else:
                self.connected_station = None

    def park(self):
        self.depot.parking_lot.vehicles.append(self.id)

    def scan(self):

        # Check for unassigned reservations
        if self.depot.unassigned_reservation_exists:
            self.depot.schedule.assign_vehicle_to_reservation_with_earliest_departure(self.id)