from datetime import datetime, timedelta

from src.asset_simulator.vehicle.vehicle import Vehicle


class AlgoVehicle(Vehicle):

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

