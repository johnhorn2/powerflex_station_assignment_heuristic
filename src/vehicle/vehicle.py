from datetime import datetime, timedelta

from pydantic import BaseModel


class Vehicle(BaseModel):
    id: int
    connected_station_id: int
    type: str
    state_of_charge: float
    energy_capacity_kwh: int

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

    def can_meet_reservation_deadline_at_l2(self, reservation_id, padding_seconds):
        deadline = self.depot.schedule.reservations[reservation_id].departure_timestamp_utc
        final_deadline = deadline - timedelta(seconds=padding_seconds)
        current_timestamp_utc = datetime.now()
        charging_time_hours = (final_deadline - current_timestamp_utc).seconds / 3600
        l2_charging_rate = self.depot.l2_charging_rate_kw
        current_soc_kwh = self.state_of_charge*self.energy_capacity_kwh
        end_goal_soc_kwh = 0.8*self.energy_capacity_kwh
        energy_kwh_delta = end_goal_soc_kwh - current_soc_kwh
        if charging_time_hours * l2_charging_rate > energy_kwh_delta:
            return True
        else:
            return False

    def get_reservation_id(self):
        for reservation in self.depot.reservations.values():
            if reservation.assigned_vehicle_id == self.id:
                return reservation.assigned_vehicle_id
        return None

    def scan(self):

        # Check for unassigned reservations
        if self.depot.unassigned_reservation_exists:
            self.depot.schedule.assign_vehicle_to_reservation_with_earliest_departure(self.id)
            reservation_id = self.get_reservation_id(self.id)
            if self.can_meet_reservation_deadline_at_l2(reservation_id):
                self.prefer_l2()
            else:
                self.prefer_dcfc()
        # no unassigned reservations
        else:
            # We have enough walk in ready vehicles ready to absorb this walk in
            if self.depot.walk_in_pool_meets_minimum_critiera():
                self.prefer_l2()
            # We don't have enough walk in ready vehicles per our criteria and need to fast charge
            else:
                self.prefer_dcfc()

