from collections import namedtuple
import copy
from operator import attrgetter
from typing import Optional, Dict

from src.asset_simulator.depot.asset_depot import AssetDepot
from src.asset_simulator.reservation.reservation import Reservation
from src.asset_simulator.vehicle.vehicle import Vehicle


class AlgoDepot(AssetDepot):
    walk_in_pool: Optional[Dict[int, Vehicle]] = {}
    minimum_ready_vehicle_pool: Dict
    reservation_assignments: Dict[str, Reservation] = {}

    # Msg Broker Functions
    def poll_queues(self):
        self.subscribe_to_queue('vehicles', 'vehicle', 'vehicles_heuristic')
        self.subscribe_to_queue('stations','station', 'stations')
        # We need to consider all the active reservations and keep them in the queue for the algorithm
        # to re-assign assigned reservations as we get new information on vehicles and reservations
        self.subscribe_to_queue('reservations','reservation', 'reservations')

    def run_interval(self):

        # collect any instructions from the queue
        self.poll_queues()

        # filter out vehicles driving and expired reservations
        self.reservations = self.filter_out_expired_reservations(self.reservations)

        # we need to estimate if the vehicle is departed internally so as not to assign it
        self.depart_vehicles()

        self.vehicles = self.get_available_vehicles(self.vehicles)

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


        dup_veh_res = self.assigned_dup_veh_ids_to_res()
        self.publish_to_queue('reservation_assignments', 'reservation_assignments')

        # after each submission of reservation assignments we wipe the local memory of reservation assignments
        self.reservation_assignments = {}

    def assigned_dup_veh_ids_to_res(self):
        veh_id_list = []
        for res in self.reservation_assignments.values():
            veh_id_list.append(res.assigned_vehicle_id)

        return len(set(veh_id_list)) != len(veh_id_list)


    def sort_vehicles_highest_soc_first(self):
        VehicleSOCSorted = namedtuple('VehicleSOCSorted', ['vehicle_id', 'state_of_charge'])

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
        return vehicles_soc_sorted

    def sort_departures_earliest_first(self):
        ReservationDepartSorted = namedtuple('ReservationDepartSorted', ['reservation_id', 'departure_timestamp_utc'])

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

        return reservations_departure_sorted

    def filter_out_expired_reservations(self, reservations):
        current_reservations = {reservation.id: reservation for reservation in reservations.values() \
                                if reservation.departure_timestamp_utc > self.current_datetime}
        return current_reservations


    def get_available_vehicles(self, vehicles):
        available_vehicles = {vehicle.id:vehicle for vehicle in vehicles.values() if vehicle.status != 'driving'}
        return available_vehicles


    def assign_vehicles_reservations(self):
        vehicles_soc_sorted = self.sort_vehicles_highest_soc_first()
        reservations_departure_sorted = self.sort_departures_earliest_first()

        # need to assign remaining reservations assigned vehicle id of None explicitly to overwrite any previous requests
        delta_vehicles_reservations = len(reservations_departure_sorted) - len(vehicles_soc_sorted)
        vehicles_soc_sorted = vehicles_soc_sorted + []*delta_vehicles_reservations

        # no vehicle / reservations to assign
        if len(vehicles_soc_sorted) == 0 or len(reservations_departure_sorted) == 0:
            pass
        #  vehicles >= reservations
        # elif len(vehicles_soc_sorted) >= len(reservations_departure_sorted):
        else:
            for idx, reservation in enumerate(reservations_departure_sorted):
                # move the reservation to the assigned pile
                self.reservation_assignments[reservation.reservation_id] = self.reservations[reservation.reservation_id]
                if idx < len(vehicles_soc_sorted):
                    # fill in the assigned vehicle_id
                    self.reservation_assignments[reservation.reservation_id].assigned_vehicle_id = vehicles_soc_sorted[idx].vehicle_id
                else:
                    self.reservation_assignments[reservation.reservation_id].assigned_vehicle_id = None

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