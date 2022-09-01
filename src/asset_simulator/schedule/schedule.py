from pydantic import BaseModel
from typing import Dict

from src.asset_simulator.reservation.reservation import Reservation


class Schedule(BaseModel):
    reservations: Dict[int, Reservation] = None

    def get_unassigned_reservations(self):
        unassigned_reservations = []
        for reservation in self.reservations.values():
            if reservation.assigned_vehicle_id == None:
                unassigned_reservations.append(reservation.assigned_vehicle_id)
        return unassigned_reservations

    def unassigned_reservation_exists(self):
        unassigned_reservations = self.get_unassigned_reservations()
        if len(unassigned_reservations) > 0:
            return True
        else:
            return False

    def get_unassigned_reservation_with_earliest_departure(self):
        unassigned_reservations = self.get_unassigned_reservations()
        # sort list by departure date asscending
        sorted_reservations = sorted(unassigned_reservations, key=lambda res: res.departure_timestamp)

        try:
            return sorted_reservations[0].id
        except IndexError as e:
            return None

    def assign_vehicle_to_reservation_with_earliest_departure(self, vehicle_id: int):
        earliest_reservation_id = self.get_unassigned_reservation_with_earliest_departure()
        self.reservations[earliest_reservation_id].assigned_vehicle_id = vehicle_id


