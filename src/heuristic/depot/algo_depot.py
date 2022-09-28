from collections import namedtuple
from datetime import timedelta
import copy
from operator import attrgetter
import random
from typing import Optional, Dict, List

from src.asset_simulator.depot.asset_depot import AssetDepot
from src.asset_simulator.reservation.reservation import Reservation
from src.asset_simulator.vehicle.vehicle import Vehicle
from src.demand_simulator.demand_simulator.demand_simulator import DemandSimulator

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

    def run_interval(self, random_sort=False):

        # collect any instructions from the queue
        self.poll_queues()

        # filter out vehicles driving
        # we actually should reserve vehicles out driving so long as their res does not overlap
        # self.fleet_manager.vehicle_fleet.vehicles = self.fleet_manager.vehicle_fleet.get_available_vehicles_at_depot()

        # scan QR events - adds newly available vehicles
        self.get_qr_scan_events()

        # calculate our walk in pool
        self.allocate_vehicles_to_walk_in_pool()

        # filter out vehicles driving and expired reservations
        self.reservations = self.filter_out_expired_reservations(self.reservations)

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
        self.assign_vehicles_reservations_by_type_and_highest_soc(random_sort=random_sort)

        # assign charging station/vehicle pairs
        self.assign_charging_stations_to_reservations()
        self.assign_charging_station_to_walk_in_pool()
        self.assign_charging_stations_to_remaining_vehicles()

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

    def get_vehicles_with_overlapping_reservations(self, new_reservation):
        exclude_overlapping_vehicles = []
        for past_res in self.past_reservation_assignments.values():
            overlap = DemandSimulator.reservation_does_overlap(
                new_reservation,
                past_res.departure_timestamp_utc,
                past_res.arrival_timestamp_utc
            )
            if overlap:
                exclude_overlapping_vehicles.append(past_res.assigned_vehicle_id)
        return exclude_overlapping_vehicles

    def get_vehicle_for_reservation(self, vehicle_ids, exclude_vehicle_ids, assigned_vehicle_ids):
        _vehicle_ids = set(vehicle_ids)
        _exclude = set(exclude_vehicle_ids)
        _assigned_vehicle_ids = set(assigned_vehicle_ids)
        _available_ids = (_vehicle_ids.difference(_exclude))
        total_available_ids = list(_available_ids.difference(_assigned_vehicle_ids))

        # because vehicle_ids preserves the order in descending soc we need to cycle in that order
        # and check if available veh id is in total available ids
        for veh_id in vehicle_ids:
            if veh_id != None:
                if veh_id in total_available_ids:
                    return veh_id
        return None


    def assign_vehicles_reservations_by_type_and_highest_soc(self, random_sort=False):
        # create a list of all possible vehicle types
        vehicle_types = list(set([vehicle.type for vehicle in self.vehicles.values()]))

        for vehicle_type in vehicle_types:

            vehicles_soc_sorted = self.fleet_manager.vehicle_fleet.sort_vehicles_highest_soc_first_by_type(self.vehicles.values(), vehicle_type)
            vehicles_soc_sorted_ids = [veh.id for veh in vehicles_soc_sorted]
            reservations_departure_sorted = self.sort_departures_earliest_first(vehicle_type)

            if random_sort:
                # shuffle in place to mimic random assignment of vehicle to reservation
                random.shuffle(vehicles_soc_sorted)
                random.shuffle(reservations_departure_sorted)

            # no vehicle / reservations to assign
            if len(vehicles_soc_sorted) == 0 or len(reservations_departure_sorted) == 0:
                pass
            else:
                # we need to keep track of vehicles assigned
                assigned_vehicles = []
                for idx, reservation in enumerate(reservations_departure_sorted):

                    # for this given reservation we need a list of vehicles to exclude due to overlapping res

                    if self.reservation_is_new(reservation) or self.reservation_is_unique(reservation):

                        exclude_vehicle_ids = self.get_vehicles_with_overlapping_reservations(reservation)

                        # cycle through sorted vehicles for assignment
                        target_vehicle_id = self.get_vehicle_for_reservation(vehicles_soc_sorted_ids, exclude_vehicle_ids, assigned_vehicles)

                        if target_vehicle_id != None:

                            # move the reservation to the assigned pile
                            self.reservation_assignments[reservation.id] = self.reservations[reservation.id]

                            # need to keep a record of past reservation assignments so we don't send redundant requests
                            self.past_reservation_assignments[reservation.id] = self.reservations[reservation.id]


                            # add the assignment timestamp
                            self.reservation_assignments[reservation.id].assigned_at_timestamp_utc = self.current_datetime
                            # add the vehicle id to be assigned
                            self.reservation_assignments[reservation.id].assigned_vehicle_id = target_vehicle_id

                            # need to keep a record of past reservation assignments so we don't send redundant requests
                            self.past_reservation_assignments[reservation.id] = self.reservation_assignments[reservation.id]

                            # we successfully found a vehicle
                            assigned_vehicles.append(target_vehicle_id)

                        else:
                            # no vehicle assigned to reservation thus no assignment being sent off
                            pass

                        # else:
                            # We have to assign reservations None Vehicle ID because if we previously assigned a reservation a vehicle id we need to overwrite that in some cases
                            # if self.reservation_is_new(reservation) == False and self.reservation_is_unique(reservation) == True:
                            #     self.reservation_assignments[reservation.id].assigned_vehicle_id = None
                            #     self.reservation_assignments[reservation.id].status = 'vehicle_reassignment'

                                # need to keep a record of past reservation assignments so we don't send redundant requests
                                # self.past_reservation_assignments[reservation.id] = self.reservation_assignments[reservation.id]
                            # else:
                                # only send reervations with no vehicles if there was an update made
                                # pass

                vehs_listed = [res.assigned_vehicle_id for res in self.reservation_assignments.values()]
                uniq_vehs_listed = list(set(vehs_listed))
                if len(vehs_listed) != len(uniq_vehs_listed):
                    print('double assigned')

    def is_vehicle_reservation_overlap(self):
        ### See if we can detect an overlap here
        vehs = []
        for res in self.past_reservation_assignments.values():
            vehs.append(res.assigned_vehicle_id)

        uniq_vehicles = list(set(vehs))

        for veh_id in uniq_vehicles:
            veh_res_list = []
            overlaps = []
            overlap = False
            for res in self.past_reservation_assignments.values():
                if res.assigned_vehicle_id == veh_id:
                    veh_res_list.append(res)

            for res in veh_res_list:
                for res_compare in veh_res_list:
                    if res.id != res_compare.id:
                        if DemandSimulator.reservation_does_overlap(res,
                                                                    res_compare.departure_timestamp_utc,
                                                                    res_compare.arrival_timestamp_utc):
                            overlaps.append((res, res_compare))
                            overlap = True
                        return overlap
        return False

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
            # enforce a 5 min wait period after an evse has been unplugged to simulate unplugging and moving prior vehicle from station, otherwise we get teleporting station/vehicle pairs
            if station.is_available() and station.is_l2() and not self.is_station_reserved(station.id) and self.current_datetime > station.last_unplugged + timedelta(minutes=15):
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
            # enforce a 5 min wait period after an evse has been unplugged to simulate unplugging and moving prior vehicle from station, otherwise we get teleporting station/vehicle pairs
            if station.is_available() and station.is_dcfc() and not self.is_station_reserved(station.id) and self.current_datetime > station.last_unplugged + timedelta(minutes=15):
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
            # vehicle.status = 'parked'
            vehicle.park(self.current_datetime)
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
        # walk-ins would naturally get prioritized here since they have the soonest departures
        sorted_reservation_assignments = sorted(self.reservation_assignments.values(), key=lambda x: x.departure_timestamp_utc)

        # cycle through starting with earliest departure and assign a station per reservation and status charging
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

    def assign_charging_station_to_walk_in_pool(self):

        # Are there stations available?
        if (self.l2_is_available() or self.dcfc_is_available()):

            vehicles = self.fleet_manager.vehicle_fleet.walk_in_pool.values()

            # sort our vehicles by highest SOC first so we have vehicles ready soonest
            ordered_vehicle = self.fleet_manager.vehicle_fleet.sort_vehicles_highest_soc_first_by_type(
                vehicles=vehicles,
                vehicle_type='any'
            )

            for vehicle in ordered_vehicle:

                # soc < 80, isn't currently charging, and don't have a charge command in the queue for said vehicle
                if vehicle.is_below_minimum_soc() and vehicle.status != 'charging' and vehicle.id not in self.move_charge.keys():

                    if self.l2_is_available():
                        available_l2_station_id = self.prefer_l2()
                        vehicle.connected_station_id = available_l2_station_id
                        self.move_charge[vehicle.id] = vehicle
                        # need to locally simulate the plugin so we know the station and vehicle will be plugged in
                        self.fleet_manager.plugin(vehicle.id, available_l2_station_id)

                    elif self.dcfc_is_available():
                        available_dcfc_station_id = self.prefer_dcfc()
                        vehicle.connected_station_id = available_dcfc_station_id
                        self.move_charge[vehicle.id] = vehicle
                        # need to locally simulate the plugin so we know the station and vehicle will be plugged in
                        self.fleet_manager.plugin(vehicle.id, available_dcfc_station_id)

    def assign_charging_stations_to_remaining_vehicles(self):

        # Do we have any available charging stations
        if self.l2_is_available() or self.dcfc_is_available():
            sorted_vehicles = self.fleet_manager.vehicle_fleet.sort_vehicles_highest_soc_first_by_type(
                vehicles=self.vehicles.values(),
                vehicle_type='any'
            )
            for vehicle in sorted_vehicles:

                # soc < 80, isn't currently charging, and don't have a charge command in the queue for said vehicle
                if vehicle.is_below_minimum_soc() and vehicle.status != 'charging' and vehicle.id not in self.move_charge.keys():

                    if self.l2_is_available():
                        available_l2_station_id = self.prefer_l2()
                        vehicle.connected_station_id = available_l2_station_id
                        self.move_charge[vehicle.id] = vehicle
                        # need to locally simulate the plugin so we know the station and vehicle will be plugged in
                        self.fleet_manager.plugin(vehicle.id, available_l2_station_id)

                    elif self.dcfc_is_available():
                        available_dcfc_station_id = self.prefer_dcfc()
                        vehicle.connected_station_id = available_dcfc_station_id
                        self.move_charge[vehicle.id] = vehicle
                        # need to locally simulate the plugin so we know the station and vehicle will be plugged in
                        self.fleet_manager.plugin(vehicle.id, available_dcfc_station_id)


    @classmethod
    def build_depot(cls, config, queue):
        interval_seconds, queue, fleet_manager, schedule, vehicle_snapshot = cls.prep_build_depot(config, queue)
        depot = AlgoDepot(
            interval_seconds=config.interval_seconds,
            queue=queue,
            fleet_manager=fleet_manager,
            schedule=schedule,
            vehicle_snapshot={}
        )
        return depot