from collections import namedtuple
import copy
from operator import attrgetter
from typing import Optional, Dict, List

from src.asset_simulator.depot.asset_depot import AssetDepot
from src.asset_simulator.reservation.reservation import Reservation
from src.asset_simulator.vehicle.vehicle import Vehicle


class AlgoDepot(AssetDepot):
    walk_in_pool: Optional[Dict[int, Vehicle]] = {}
    reservation_assignments: Dict[str, Reservation] = {}
    past_reservation_assignments: Dict[str, Reservation] = {}
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

        # scan QR events - adds newly available vehicles
        self.get_qr_scan_events()

        # calculate our walk in pool
        self.allocate_vehicles_to_walk_in_pool()

        # filter out vehicles driving
        self.fleet_manager.vehicle_fleet.vehicles = self.fleet_manager.vehicle_fleet.get_available_vehicles_at_depot()

        # filter out vehicles driving and expired reservations
        self.reservations = self.filter_out_expired_reservations(self.reservations)

        # we need to estimate if the vehicle is departed internally so as not to assign it
        # self.depart_vehicles()

        # if vehicles are 80% or more filled up then move to parking lot
        # todo: hold off on move commands for this V1
        # self.free_up_ready_vehicles()



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

        # assign charging station/vehicle pairs
        self.assign_charging_stations_to_reservations()
        # self.assign_charging_station_to_walk_ins()

        # push status of all vehicles/stations to the queue at end of interval to update the heuristic


        self.publish_to_queue('reservation_assignments', 'reservation_assignments')

        # after each submission of reservation assignments we wipe the local memory of reservation assignments
        self.reservation_assignments = {}


        # send the move/charge instructions to the asset depot simulator
        self.publish_to_queue('move_charge', 'move_charge')

        # after each submission we wipe move_charge local
        self.move_charge = {}

    # vehicle to job assignment
    def sort_departures_earliest_first(self, vehicle_type):
        # we need all vehicles sorted by departure ascending
        if vehicle_type == 'any':
            return sorted(self.reservations.values(), key=lambda x: x.departure_timestamp_utc)
        else:
            # we need a subset of vehicles sorted by departure ascending
            subset_by_vehicle_type = [res for res in self.reservations.values() if res.vehicle_type == vehicle_type]
            return sorted(subset_by_vehicle_type, key=lambda x: x.departure_timestamp_utc)

    def filter_out_expired_reservations(self, reservations):
        current_reservations = {reservation.id: reservation for reservation in reservations.values() \
                                if reservation.departure_timestamp_utc > self.current_datetime}
        return current_reservations


    # depot related functions



    def assign_vehicles_reservations_by_type_and_highest_soc(self):
        # create a list of all possible vehicle types
        vehicle_types = list(set([vehicle.type for vehicle in self.vehicles.values()]))

        for vehicle_type in vehicle_types:

            vehicles_soc_sorted = self.fleet_manager.vehicle_fleet.sort_vehicles_highest_soc_first_by_type(self.vehicles.values(), vehicle_type)
            reservations_departure_sorted = self.sort_departures_earliest_first(vehicle_type)

            # remove any vehicles that are dedicated to the walk in pool
            # vehicles_soc_sorted = [vehicle for vehicle in vehicles_soc_sorted if not self.fleet_manager.vehicle_fleet.vehicle_in_walk_in_pool(vehicle.id)]

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

                    if self.reservation_is_new(reservation) or self.reservation_is_unique(reservation):
                    # if self.new_unique_reservation(reservation):

                        # move the reservation to the assigned pile
                        self.reservation_assignments[reservation.id] = self.reservations[reservation.id]

                        # need to keep a record of past reservation assignments so we don't send redundant requests
                        self.past_reservation_assignments[reservation.id] = self.reservations[reservation.id]


                        # fill in the assigned vehicle_id
                        if vehicles_soc_sorted[idx]:
                            # add the assignment timestamp
                            self.reservation_assignments[reservation.id].assigned_at_timestamp_utc = self.current_datetime
                            # add the vehicle id to be assigned
                            self.reservation_assignments[reservation.id].assigned_vehicle_id = vehicles_soc_sorted[idx].id

                            # need to keep a record of past reservation assignments so we don't send redundant requests
                            self.past_reservation_assignments[reservation.id] = self.reservation_assignments[reservation.id]
                        else:
                            # We have to assign reservations None Vehicle ID because if we previously assigned a reservation a vehicle id we need to overwrite that in some cases
                            if self.reservation_is_new(reservation) == False and self.reservation_is_unique(reservation) == True:
                                self.reservation_assignments[reservation.id].assigned_vehicle_id = None
                                self.reservation_assignments[reservation.id].status = 'vehicle_reassignment'

                                # need to keep a record of past reservation assignments so we don't send redundant requests
                                self.past_reservation_assignments[reservation.id] = self.reservation_assignments[reservation.id]
                            else:
                                # only send reervations with no vehicles if there was an update made
                                pass



    def reservation_is_new(self, reservation):
        try:
           self.past_reservation_assignments[reservation.id]
           return False
        except KeyError:
            return True


    def reservation_is_unique(self, reservation):
        if (self.past_reservation_assignments[reservation.id].assigned_vehicle_id == reservation.assigned_vehicle_id) \
                and (self.past_reservation_assignments[reservation.id].departure_timestamp_utc == reservation.departure_timestamp_utc):
            return False
        else:
            # either the departure date and/or the vehicle has changed for this departure so send an update
            return True


    def new_unique_reservation(self, reservation):
        # if the reservation has already been assigned to this vehicle and the departure date is the same then no need to update it
        # make the API calls less chatty
        try:
            if (self.past_reservation_assignments[reservation.id].assigned_vehicle_id == reservation.assigned_vehicle_id) \
                and (self.past_reservation_assignments[reservation.id].departure_timestamp_utc == reservation.departure_timestamp_utc):
                return False
            else:
                # either the departure date and/or the vehicle has changed for this departure so send an update
                return True
        except KeyError:
            # this reservation has not been assigned before
            return True

    # def walk_in_pool_meets_minimum_critiera(self):
    #     walk_in_ready = [vehicle for vehicle in self.walk_in_pool if vehicle.state_of_charge >= 0.8]
    #     if len(walk_in_ready) > self.minimum_ready_vehicle_pool:
    #         return True
    #     else:
    #         return False

    def l2_is_available(self):
        available_l2_station = self.get_available_l2_station()
        if isinstance(available_l2_station, int):
            return True
        else:
            return False

    def is_station_reserved(self, station_id):
        # determine if we assigned this station to a reservation in flight
        for instruction in self.move_charge.values():
            if instruction.connected_station_id == station_id:
                return True
        return False

    def get_available_l2_station(self):
        # return first L2 station available
        for station in self.stations.values():
            if station.is_available() and station.is_l2() and not self.is_station_reserved(station.id):
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
            if station.is_available() and station.is_dcfc() and not self.is_station_reserved(station.id):
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

    def assign_charging_stations_to_reservations(self):

        # create ordered list of assigned reservations by departure date ascending
        sorted_reservation_assignments = sorted(self.reservation_assignments.values(), key=lambda x: x.departure_timestamp_utc)

        # cycle through starting with soonest departure and assign a station per reservation and status charging
        for reservation in sorted_reservation_assignments:

            # no need to assign the charging station since no vehicle being assigned
            if reservation.assigned_vehicle_id == None:
                continue

            # pull the vehicle from the reservation
            vehicle = self.vehicles[reservation.assigned_vehicle_id]

            # If the vehicle is ~ 80% full we don't need to charge it
            if vehicle.state_of_charge < 0.8:

                # determine if L2 can charge fast enough
                l2_capable = vehicle.can_meet_reservation_deadline_at_l2(
                    depature_datetime=reservation.departure_timestamp_utc,
                    charging_rate_kw=self.l2_charging_rate_kw,
                    # 15 minute padding
                    padding_seconds=60 * 15
                )

                if l2_capable and self.l2_is_available():
                    # assign the station to the vehicle
                    vehicle.connected_station_id = self.prefer_l2()
                    vehicle.status = 'charging'
                    # we add the current timestamp so we can plot when the msg was sent later
                    vehicle.updated_at = self.current_datetime
                    self.move_charge[vehicle.id] = vehicle

                elif self.dcfc_is_available():

                    # prefer DCFC
                    # if we could not find an L2 nor a DCFC then we can't assign a charging station
                    # assign the station to the vehicle
                    vehicle.connected_station_id = self.prefer_dcfc()
                    vehicle.status = 'charging'
                    # we add the current timestamp so we can plot when the msg was sent later
                    vehicle.updated_at = self.current_datetime
                    self.move_charge[vehicle.id] = vehicle

    def vehicle_is_currently_reserved(self, vehicle_id):
        for reservation in self.reservation_assignments.values():
            if reservation.assigned_vehicle_id == vehicle_id:
                return True
        return False


    def vehicle_assigned_move_charge_instruction(self, vehicle_id):
        for instruction in self.move_charge.values():
            if vehicle_id == instruction.id:
                return True
        return False

    def get_vehicles_free_for_walk_ins(self):
        # This removes vehicles:
        # - assigned to reservations
        # - assigned a move/charge instruction

        available_vehicle_ids = []
        for vehicle in self.vehicles.values():
            if not self.vehicle_is_currently_reserved(vehicle.id) and not self.vehicle_assigned_move_charge_instruction(vehicle.id) and not self.fleet_manager.vehicle_fleet.vehicle_in_walk_in_pool(vehicle.id) and vehicle.status != 'driving':
                available_vehicle_ids.append(vehicle)
        return available_vehicle_ids

    def get_walk_in_deficit(self):
        # create a list of stations left over not already assigned a reservation
        walk_in_pool = self.fleet_manager.vehicle_fleet.walk_in_pool

        minimum_ready_vehicle_pool = self.fleet_manager.vehicle_fleet.minimum_ready_vehicle_pool
        distinct_vehicle_types_for_walk_in = list(set(minimum_ready_vehicle_pool.keys()))

        available_vehicle_cnt_by_type  = {type: 0 for type in distinct_vehicle_types_for_walk_in}

        # create a count of our walk in pool by type
        for vehicle in walk_in_pool.values():
            available_vehicle_cnt_by_type[vehicle.type] += 1

        walk_in_deficit = minimum_ready_vehicle_pool

        # subtract our walk in pool counts from our minimum ready vehicle requirement, don't allow negative values
        for vehicle_type, n_req in walk_in_deficit.items():
            walk_in_deficit[vehicle_type] = max(0, n_req - available_vehicle_cnt_by_type[vehicle_type])

        return walk_in_deficit

    def is_walk_in_deficit(self):
        walk_in_deficit = self.get_walk_in_deficit()
        for deficit in walk_in_deficit.values():
            if deficit > 0:
                return True
        return False


    def allocate_vehicles_to_walk_in_pool(self):
        if self.is_walk_in_deficit():
            vehicle_candidates = self.get_vehicles_free_for_walk_ins()

            # assign the highest soc vehicles to walk in pool by type
            for type, amt_needed in self.get_walk_in_deficit().items():
                vehicles_soc_sorted_by_type = self.fleet_manager.vehicle_fleet.sort_vehicles_highest_soc_first_by_type(vehicle_candidates, type)
                target_vehicles = vehicles_soc_sorted_by_type[0:amt_needed]
                for vehicle in target_vehicles:
                    self.fleet_manager.vehicle_fleet.allocate_to_walk_in_pool(vehicle)

    def assign_charging_station_to_walk_ins(self):

        # Are there stations available?
        if (self.l2_is_available() or self.dcfc_is_available()):

            for vehicle in self.fleet_manager.vehicle_fleet.walk_in_pool.values():

                if vehicle.is_below_minimum_soc():

                    if self.l2_is_available():
                        available_l2_station = self.prefer_l2()
                        vehicle.connected_station_id = available_l2_station
                        self.move_charge[vehicle.id] = vehicle
                        # need to locally simulate the plugin so we know the station and vehicle will be plugged in
                        self.fleet_manager.plugin(vehicle.id, available_l2_station.id)

                    elif self.dcfc_is_available():
                        available_dcfc_station = self.prefer_dcfc()
                        vehicle.connected_station_id = available_dcfc_station
                        self.move_charge[vehicle.id] = vehicle
                        # need to locally simulate the plugin so we know the station and vehicle will be plugged in
                        self.fleet_manager.plugin(vehicle.id, available_dcfc_station.id)

    # def assign_charging_stations_to_remaining_vehicles(self):

    #     Do we have any available charging stations
    #     if self.l2_is_available() or self.dcfc_is_available():
    #         pass

