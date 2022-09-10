from collections import namedtuple
import copy
from operator import attrgetter
from typing import Optional, Dict, List

from src.asset_simulator.depot.asset_depot import AssetDepot
from src.asset_simulator.reservation.reservation import Reservation
from src.asset_simulator.vehicle.vehicle import Vehicle


class AlgoDepot(AssetDepot):
    walk_in_pool: Optional[Dict[int, Vehicle]] = {}
    minimum_ready_vehicle_pool: Dict
    reservation_assignments: Dict[str, Reservation] = {}
    qr_scans: Optional[Dict[int, Vehicle]] = {}
    move_charge: Optional[Dict[int, Vehicle]] = {}

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
        # self.depart_vehicles()

        # if vehicles are 80% or more filled up then move to parking lot
        self.free_up_ready_vehicles()

        # scan QR events
        self.get_qr_scan_events()

        # filter out vehicles driving
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
        self.assign_vehicles_reservations_by_type_and_highest_soc()


        # push status of all vehicles/stations to the queue at end of interval to update the heuristic


        self.publish_to_queue('reservation_assignments', 'reservation_assignments')

        # after each submission of reservation assignments we wipe the local memory of reservation assignments
        self.reservation_assignments = {}

        # assign charging station/vehicle pairs
        self.assign_charging_stations()

        # send the move/charge instructions to the asset depot simulator
        self.publish_to_queue('move_charge', 'move_charge')

    def assigned_dup_veh_ids_to_res(self):
        veh_id_list = []
        for res in self.reservation_assignments.values():
            veh_id_list.append(res.assigned_vehicle_id)

        return len(set(veh_id_list)) != len(veh_id_list)


    def sort_vehicles_highest_soc_first_by_type(self, vehicle_type):
        #todo: This doesn't seem to be working
        VehicleSOCSorted = namedtuple('VehicleSOCSorted', ['vehicle_id', 'state_of_charge'])


        vehicles_soc_sorted = []
        # need sorted lists to match up later
        for vehicle in self.vehicles.values():
            if vehicle.type == vehicle_type or vehicle_type == 'any':
                vehicles_soc_sorted.append(
                    VehicleSOCSorted(
                        vehicle_id=vehicle.id,
                        state_of_charge=vehicle.state_of_charge
                    )
                )
        # highest SOC first, reveres = desc
        sorted(vehicles_soc_sorted, key=attrgetter('state_of_charge'), reverse=True)
        return vehicles_soc_sorted

    def sort_departures_earliest_first(self, vehicle_type):
        ReservationDepartSorted = namedtuple('ReservationDepartSorted', ['reservation_id', 'departure_timestamp_utc'])

        reservations_departure_sorted = []
        for reservation in self.reservations.values():
            if reservation.vehicle_type == vehicle_type or vehicle_type == 'any':
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


    def assign_vehicles_reservations_by_type_and_highest_soc(self):
        # todo: need to make this by vehicle class

        # create a list of all possible vehicle types
        vehicle_types = list(set([vehicle.type for vehicle in self.vehicles.values()]))

        for vehicle_type in vehicle_types:

            vehicles_soc_sorted = self.sort_vehicles_highest_soc_first_by_type(vehicle_type)
            reservations_departure_sorted = self.sort_departures_earliest_first(vehicle_type)

            # need to assign remaining reservations assigned vehicle id of None explicitly to overwrite any previous requests
            delta_vehicles_reservations = len(reservations_departure_sorted) - len(vehicles_soc_sorted)

            # more reservations than vehicles
            if delta_vehicles_reservations > 0:
                vehicles_soc_sorted = vehicles_soc_sorted + [None]*delta_vehicles_reservations

            # no vehicle / reservations to assign
            if len(vehicles_soc_sorted) == 0 or len(reservations_departure_sorted) == 0:
                pass
            else:
                for idx, reservation in enumerate(reservations_departure_sorted):
                    # move the reservation to the assigned pile
                    self.reservation_assignments[reservation.reservation_id] = self.reservations[reservation.reservation_id]
                    # fill in the assigned vehicle_id
                    if vehicles_soc_sorted[idx]:
                        self.reservation_assignments[reservation.reservation_id].assigned_vehicle_id = vehicles_soc_sorted[idx].vehicle_id
                    else:
                        # We have to assign reservations None Vehicle ID because if we previously assigned a reservation a vehicle id we need to overwrite that in some cases
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

    def unassigned_reservation_exists(self):
        for reservation in self.reservations.values():
            if isinstance(reservation.assigned_vehicle_id, int) == False:
                return True
        return False

    def get_earliest_unassigned_reservation(self):

        ReservationDepartSorted = namedtuple('ReservationDepartSorted', ['reservation_id', 'departure_timestamp_utc'])

        reservations_departure_sorted = []
        for reservation in self.reservations.values():
            if isinstance(reservation.assigned_vehicle_id, int) == False:
                reservations_departure_sorted.append(
                    ReservationDepartSorted(
                        reservation_id=reservation.id,
                        departure_timestamp_utc=reservation.departure_timestamp_utc
                    )
                )
        # earliest departure time first or asc
        sorted(reservations_departure_sorted, key=attrgetter('departure_timestamp_utc'))

        return reservations_departure_sorted[0]

    def get_qr_scan_events(self):
        self.subscribe_to_queue('qr_scans', 'vehicle', 'scan_events')
        for vehicle in self.qr_scans.values():
            # update our out driving vehicles with arrivals that have been scanned to 'parked'
            # otherwise if status set to 'driving' it will be excluded from reservation assignments
            vehicle.status = 'parked'
            self.vehicles[vehicle.id] = vehicle

        # wipe out the internal qr events after moving these vehicles from 'driving' to 'parked'
        # we will assign these vehicles a charging station and reservation later
        self.qr_scans = {}

    def prefer_l2(self):
        # L2 is available
        if self.l2_is_available():
            return self.get_available_l2_station()
        # DCFC available
        elif self.dcfc_is_available():
            return self.get_available_dcfc_station()
        # Need to park as no L2 nor DCFC available
        else:
            return None

    def prefer_dcfc(self):
        # DCFC available
        if self.dcfc_is_available():
            return self.get_available_dcfc_station()
        #todo: move vehicles to make room for DCFC

        # L2 is available
        elif self.l2_is_available():
            return self.get_available_l2_station()
        else:
            return None


    def free_up_ready_vehicles(self):
        # if a vehicle is finished charging or 80% done then park it instead of charge it
        for vehicle in self.vehicles.values():
            if vehicle.state_of_charge >= 0.8 and vehicle.status in ('charging', 'finished_charging'):
                vehicle.connected_station_id = None
                vehicle.status = 'parked'
                self.move_charge[vehicle.id] = vehicle


    # todo: need to change this code to look at assigned_reservations and assign a station because sorted soc vehicles already done and assigned
    # todo: also need to fix the get_sorted vehicles function since it is not sorting
    def assign_charging_stations(self):
        """
        sort through the earliest departure reservations and prioritize those assigned vehicles first:
            if vehicle can meet reservation on L2 then prefer_L2 else prefer_DCFC and repeat

            if we pair a vehicle with the res then pop that vehicle out of our available list
        """
        vehicles_soc_sorted = self.sort_vehicles_highest_soc_first_by_type(vehicle_type='any')
        reservations_departure_sorted = self.sort_departures_earliest_first(vehicle_type='any')

        # loop starting with reservation departing first and the highest SOC vehicle
        # make sure we have available vehicles before assignment
        if len(vehicles_soc_sorted) > 0:
            for res_idx, reservation in enumerate(reservations_departure_sorted):

                # make sure we have available vehicles before assignment
                if len(vehicles_soc_sorted) == 0:
                    break


                # more vehicles than reservations, lets us cycle through all the reservations
                # the first vehicle in the sorted list will always be the highest SOC vehicle available
                vehicle = self.vehicles[vehicles_soc_sorted[0].vehicle_id]

                l2_capable = vehicle.can_meet_reservation_deadline_at_l2(
                    depature_datetime=reservation.departure_timestamp_utc,
                    charging_rate_kw=self.l2_charging_rate_kw,
                    # 15 minute padding
                    padding_seconds=60*15
                )

                # we don't need to optimized charging stations if the vehicle already has > 80% soc,
                # 0.79 in case of rounding error on charging time cycle
                if vehicle.state_of_charge < 0.79:
                    # if the vehicle can charge up in time with L2
                    if l2_capable:
                        available_l2_station = self.prefer_l2()
                        # if we could not find an L2 nor a DCFC then we can't assign a charging station
                        if isinstance(available_l2_station, int):
                            vehicle.connected_station_id = available_l2_station
                            vehicle.status = 'charging'
                            self.move_charge[vehicle.id] = vehicle
                            # remove the first vehicle from our available list
                            vehicles_soc_sorted.pop(0)
                    else:
                        available_dcfc_station = self.prefer_dcfc()
                        # if we could not find an L2 nor a DCFC then we can't assign a charging station
                        if isinstance(available_dcfc_station, int):
                            vehicle.connected_station_id = available_dcfc_station
                            vehicle.status = 'charging'
                            self.move_charge[vehicle.id] = vehicle
                            # remove the first vehicle from our available list
                            vehicles_soc_sorted.pop(0)
