from collections import namedtuple
from operator import attrgetter
from typing import Optional, Dict

from src.asset_simulator.depot.asset_depot import AssetDepot
from src.asset_simulator.reservation.reservation import Reservation
from src.asset_simulator.vehicle.vehicle import Vehicle


class AlgoDepot(AssetDepot):
    walk_in_pool: Optional[Dict[int, Vehicle]] = {}
    minimum_ready_vehicle_pool: Dict
    reservations: Dict[str, Reservation] = {}
    reservation_assignments: Dict[str, Reservation] = {}

    # Msg Broker Functions
    def poll_queues(self):
        self.subscribe_to_queue('vehicles')
        self.subscribe_to_queue('stations')
        self.subscribe_to_queue('reservations')

    def run_interval(self):

        # collect any instructions from the queue
        self.poll_queues()

        # update assets based on those instructions
        # many of these actions will come from the heuristic algorithm
        """
        plugin
        unplug
        depart
        move
        scan
        walk_in
        """


        # calculate heuristics
        self.assign_vehicles_reservations()


        # push status of all vehicles/stations to the queue at end of interval to update the heuristic
        self.publish_to_queue('reservation_assignments')


    def sort_vehicles_highest_soc_first(self):
        VehicleSOCSorted = namedtuple('VehicleSOCSorted', ['vehicle_id', 'state_of_charge'])
        ReservationDepartSorted = namedtuple('ReservationDepartSorted', ['reservation_id', 'departure_timestamp_utc'])

        vehicles_soc_sorted = []
        # need sorted lists to match up later
        for vehicle in self.vehicles.values():
            vehicles_soc_sorted.append(
                VehicleSOCSorted(
                    vehicle_id=vehicle.id,
                    state_of_charge=vehicle.state_of_charge
                )
            )
        # highest SOC first, reveres = desc
        sorted(vehicles_soc_sorted, key=attrgetter('state_of_charge'), reverse=True)

        reservations_departure_sorted = []
        for reservation in self.reservations.values():
            reservations_departure_sorted.append(
                ReservationDepartSorted(
                    reservation_id=reservation.id,
                    departure_timestamp_utc=reservation.departure_timestamp_utc
                )
            )
        # earliest departure time first or asc
        sorted(reservations_departure_sorted, key=attrgetter('departure_timestamp_utc'))

        return (vehicles_soc_sorted, reservations_departure_sorted)

    def assign_vehicles_reservations(self):

        vehicles_soc_sorted, reservations_departure_sorted = self.sort_vehicles_highest_soc_first()

        if len(vehicles_soc_sorted) >= len(reservations_departure_sorted):
            #  vehicles >= reservations
            for idx, reservation in enumerate(reservations_departure_sorted):
                # move the reservation to the assigned pile
                self.reservation_assignments[reservation.reservation_id] = self.reservations[reservation.reservation_id]
                # fill in the assigned vehicle_id
                self.reservation_assignments[reservation.reservation_id].assigned_vehicle_id = vehicles_soc_sorted[idx].vehicle_id
                # remove the unassigned reservation from the reservation pile
                del self.reservations[reservation.reservation_id]

        elif len(vehicles_soc_sorted) < len(reservations_departure_sorted):
            #  vehicles < reservations
            for idx, vehicle in enumerate(vehicles_soc_sorted):
                reservation = reservations_departure_sorted[idx]
                # move the reservation to the assigned pile
                self.reservation_assignments[reservation.reservation_id] = self.reservations[reservation.reservation_id]
                # fill in the assigned vehicle_id
                self.reservation_assignments[reservation.reservation_id].assigned_vehicle_id = vehicles_soc_sorted[idx].vehicle_id
                # remove the unassigned reservation from the reservation pile
                del self.reservations[reservation.reservation_id]


    def walk_in_pool_meets_minimum_critiera(self):
        walk_in_ready = [vehicle for vehicle in self.walk_in_pool if vehicle.state_of_charge >= 0.8]
        if len(walk_in_ready) > self.minimum_ready_vehicle_pool:
            return True
        else:
            return False

    def l2_is_available(self):
        available_l2_station = self.get_available_l2_station()
        if isinstance(available_l2_station, int):
            return True
        else:
            return False

    def get_available_l2_station(self):
        # return first L2 station available
        for station in self.stations.values():
            if station.is_available() and station.is_l2():
                return station.id
        #No L2 available
        return None

    def dcfc_is_available(self):
        available_dcfc_station = self.get_available_dcfc_station()
        if isinstance(available_dcfc_station, int):
            return True
        else:
            return False

    def get_available_dcfc_station(self):
        # return first DCFC station available
        for station in self.stations.values():
            if station.is_available() and station.is_dcfc():
                return station.id
        #No DCFC available
        return None

    def get_walk_in_ready_vehicles(self, vehicle_class: str = None):
        pass

    def walk_in_available(self, vehicle_class: str = None):
        pass

    def can_free_up_dcfc(self, incoming_vehicle_id: int):
        pass

    def get_free_up_dcfc_instructions(self, incoming_vehicle_id: int):
        pass