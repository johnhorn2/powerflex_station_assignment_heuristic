from datetime import datetime, timedelta

from pydantic import BaseModel


class Vehicle(BaseModel):
    id: int
    connected_station_id: int = None
    type: str
    state_of_charge: float
    energy_capacity_kwh: int
    status: str
    # ['parked' | 'charging' | 'finished_charging']


    def charge(self, seconds, power_kw):
        hours = seconds/3600
        charged_kwh = power_kw * hours
        current_energy_kwh = self.state_of_charge * self.energy_capacity_kwh

        # charge up to max capacity
        new_energy_kwh = min(self.energy_capacity_kwh, current_energy_kwh + charged_kwh)
        self.state_of_charge = new_energy_kwh / self.energy_capacity_kwh
        self.update_status()

    def is_plugged_in(self):
        return isinstance(self.connected_station_id, int)

    def update_status(self):
        if self.is_plugged_in():
            if self.state_of_charge < 1:
                self.status = 'charging'
            elif self.state_of_charge == 1:
                self.status = 'finished_charging'
        else:
            # todo: need to determine if parked or out on a job
            self.status == 'other'



    def plugin(self, station_id: int):
        self.connected_station_id = station_id
        self.update_status()

    def unplug(self):
        self.connected_station_id = None
        self.update_status()

    def park(self):
        self.depot.parking_lot.vehicles.append(self.id)

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

