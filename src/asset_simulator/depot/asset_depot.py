from collections import namedtuple
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, List, Tuple

from pydantic import BaseModel
import numpy as np

from src.asset_simulator.station.station import Station
from src.asset_simulator.vehicle.vehicle import Vehicle
from src.asset_simulator.schedule.schedule import Schedule
from src.mock_queue.msg_broker import MsgBroker
from src.asset_simulator.reservation.reservation import Reservation
from src.mock_queue.mock_queue import MockQueue


class AssetDepot(MsgBroker):
    interval_seconds: int
    current_datetime: datetime = datetime(year=2022, month=1, day=1, hour=0)
    stations: Optional[Dict[int, Station]] = {}
    vehicles: Optional[Dict[int, Vehicle]] = {}
    move_charge: Optional[Dict[int, Vehicle]] = {}
    reservations: Optional[Dict[int, Reservation]] = {}
    schedule: Schedule
    l2_charging_rate_kw: float = 12
    dcfc_charging_rate_kw: float = 150
    minimum_ready_vehicle_pool: Optional[Dict[str, int]]
    vehicle_soc_snapshot: Dict[str, List] = {}
    vehicle_status_snapshot: Dict[str, List] = {}
    departure_snapshot: Dict[str, List] = {}
    vehicles_out_driving: Dict[int, Tuple] = {}
    trip_config: Dict

    def increment_interval(self):
        # capture the current values for plotting later
        self.capture_vehicle_snapshot()


        interval_seconds = self.interval_seconds
        self.current_datetime = self.current_datetime + timedelta(seconds=interval_seconds)


    def capture_vehicle_snapshot(self):

        # initialize dictionary
        if len(self.vehicle_soc_snapshot) == 0:
            self.vehicle_soc_snapshot['datetime'] = []
            for vehicle_id in self.vehicles.keys():
                self.vehicle_soc_snapshot[vehicle_id] = []

            self.vehicle_status_snapshot['datetime'] = []
            for vehicle_id in self.vehicles.keys():
                self.vehicle_status_snapshot[vehicle_id] = []

            # init value_type column

        # add vehicle soc
        self.vehicle_soc_snapshot['datetime'].append(self.current_datetime)
        for vehicle in self.vehicles.values():
            self.vehicle_soc_snapshot[vehicle.id].append(vehicle.state_of_charge)


        # add vehicle status
        self.vehicle_status_snapshot['datetime'].append(self.current_datetime)
        for vehicle in self.vehicles.values():
            # if not driving log the SOC
            self.vehicle_status_snapshot[vehicle.id].append(vehicle.status)


    def capture_departure_snapshot(self, reservation_id, vehicle_id, on_time_departure, scheduled_departure_datetime, state_of_charge):

        # initialize dictionary
        if len(self.departure_snapshot) == 0:
            self.departure_snapshot['scheduled_departure_datetime'] = []
            self.departure_snapshot['actual_departure_datetime'] = []
            self.departure_snapshot['reservation_id'] = []
            self.departure_snapshot['vehicle_id'] = []
            self.departure_snapshot['on_time_departure'] = []
            self.departure_snapshot['state_of_charge'] = []

        # add vehicle soc
        # self.vehicle_snapshot['datetime'].append(self.current_datetime)
        self.departure_snapshot['scheduled_departure_datetime'].append(scheduled_departure_datetime)
        self.departure_snapshot['actual_departure_datetime'].append(self.current_datetime)
        self.departure_snapshot['reservation_id'].append(reservation_id)
        self.departure_snapshot['vehicle_id'].append(vehicle_id)
        self.departure_snapshot['on_time_departure'].append(on_time_departure)
        self.departure_snapshot['state_of_charge'].append(state_of_charge)

    def charge_vehicles(self):
        plugged_in_vehicle_station = [(vehicle.id, vehicle.connected_station_id) for vehicle in self.vehicles.values() if vehicle.status == 'charging']
        for vehicle_id, station_id in plugged_in_vehicle_station:
            max_power_kw = self.stations[station_id].max_power_kw
            self.vehicles[vehicle_id].charge(self.interval_seconds, max_power_kw)

    def depart_vehicles(self):
        # if the current timestamp matches the departure AND vehicle_id matches reservation then unplug
        #todo: we don't have vehicle assignments though because the heuristic does that

        # for any assigned reservations if:
        # - we are on or past the departure time
        # - the soc is >= minimum (assuming 80%)
        # - the vehicles isn't already departed
        # then change vehicle status to 'driving'


        """
        departures = [reservation for reservation in self.reservations.values() \
                      if self.current_datetime >= reservation.departure_timestamp_utc \
                      # if no assigned vehicle then below will default to 0 >= 0.8 or false and we won't add entry to departures
                      and getattr(self.vehicles[reservation.assigned_vehicle_id], 'state_of_charge', 0) >= 0.8 \
                      # if no assigned vehicle then below will default to 'driving' and entry won't be added to departures
                      and getattr(self.vehicles[reservation.assigned_vehicle_id], 'status', 'driving') != 'driving'
                      ]
        """

        departures = []
        for reservation in self.reservations.values():
            if reservation.assigned_vehicle_id != None:
                if (self.current_datetime >= reservation.departure_timestamp_utc) and \
                (self.vehicles[reservation.assigned_vehicle_id].state_of_charge >= 0.8) and \
                (self.vehicles[reservation.assigned_vehicle_id].status != 'driving'):
                    departures.append(reservation)


        for reservation in departures:
            # if we have as assigned vehicle id and it is time to depart then depart
            if isinstance(reservation.assigned_vehicle_id, int):
                # need to unplug otherwise state gets overwritten as 'finished charging' instead of 'driving'
                self.vehicles[reservation.assigned_vehicle_id].unplug()
                self.vehicles[reservation.assigned_vehicle_id].status = 'driving'
                # log the succesful departure for plotting later
                self.capture_departure_snapshot(
                    reservation_id=reservation.id,
                    vehicle_id=reservation.assigned_vehicle_id,
                    on_time_departure=True,
                    scheduled_departure_datetime=reservation.departure_timestamp_utc,
                    state_of_charge=self.vehicles[reservation.assigned_vehicle_id].state_of_charge
                )

            else:
                try:
                    soc_at_departure = self.vehicles[reservation.assigned_vehicle_id].state_of_charge
                except KeyError:
                    soc_at_departure = None
                # log the unsuccesful departure for plotting later
                self.capture_departure_snapshot(
                    reservation_id=reservation.id,
                    vehicle_id=reservation.assigned_vehicle_id,
                    on_time_departure=False,
                    scheduled_departure_datetime=reservation.departure_timestamp_utc,
                    state_of_charge=soc_at_departure
                )
                # print('missed departure')

    def move_vehicles(self):
        # todo based on heuristic commands
        pass

    def is_duplicate_vehicle_assignments(self):
        # determine if that vehicle id is already assigned to a different reservation
        # by creatig a dictionary of {vehicle_id: reservations) and ensuring a match on res_id
        reserved_vehicle_ids = [res.assigned_vehicle_id for res in self.reservations.values() if res.assigned_vehicle_id != None]
        return len(set(reserved_vehicle_ids)) != len(reserved_vehicle_ids)



    def run_interval(self):
        #todo: only doing simple moves to parking for now, need to do moves to stations
        self.subscribe_to_queue('move_charge', 'vehicle', 'move_charge')

        # important to depart vehicles first thing so that we don't assign the vehicles other tasks afterwards when it should be gone
        self.depart_vehicles()

        # listen to any instructions to move vehicles
        self.execute_move_charge_instructions()

        # register the arrival of newly departed vehicles at soc drop rate
        self.process_driving_vehicle_for_future_arrival()

        # decrease the soc of vehicles driving
        self.decrease_soc_of_vehicles_driving()

        # check for vehicle arrivals
        self.send_qr_scans_upon_vehicle_arrival()

        # the heuristic has assigned a veh id to the reservation
        # we overwrite the current reservation with that assigned res
        self.subscribe_to_queue('reservations', 'reservation', 'reservation_assignments')



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


        # increment time and actions including:
        """
        charge any vehicles plugged in and not fully charged yet
        decrease soc of any vehicles out on a job based on interval
        """

        self.move_vehicles()
        self.charge_vehicles()

        # push status of all vehicles/stations to the queue at end of interval to update the heuristic
        self.publish_to_queue('vehicles', 'vehicles_demand_sim')
        self.publish_to_queue('vehicles', 'vehicles_heuristic')
        self.publish_to_queue('stations', 'stations')


    def execute_move_charge_instructions(self):
        self.park_finished_vehicles()
        self.move_vehicle_to_charging_station()


    def move_vehicle_to_charging_station(self):
        moved_to_station = []
        for vehicle in self.move_charge.values():
            # only applies to vehicles that are parked or charging
            if vehicle.status == 'charging' and self.vehicles[vehicle.id].status in ('charging', 'parked'):
                self.plugin(vehicle.id, vehicle.connected_station_id)
                moved_to_station.append(vehicle.id)

        # remove item from move_charge instructions list
        for vehicle_id in moved_to_station:
            del self.move_charge[vehicle_id]


    def park_finished_vehicles(self):
        moved_to_parking_lot = []
        for vehicle in self.move_charge.values():
            # parking is easy because we don't need to free up anything to move a vehicle from charging to parked
            # we don't want to override a 'driving' status, so we limit transitions from charging and finished_charging
            if vehicle.status == 'parked' and self.vehicles[vehicle.id].status in ('charging', 'finished_charging'):
                self.park(vehicle.id)
                moved_to_parking_lot.append(vehicle.id)

        # remove item from move_charge instructions list
        for vehicle_id in moved_to_parking_lot:
            del self.move_charge[vehicle_id]

    def plugin(self, vehicle_id, station_id):
        self.vehicles[vehicle_id].plugin(station_id)
        self.stations[station_id].plugin(vehicle_id)

    def unplug(self, vehicle_id):
        # cycle through stations to unplug based on vehicle id
        for station in self.stations.values():
            if station.connected_vehicle_id == vehicle_id:
                self.stations[station.id].unplug()
        self.vehicles[vehicle_id].unplug()

    def park(self, vehicle_id):
        if self.vehicles[vehicle_id].is_plugged_in():
            self.unplug(vehicle_id)
        self.vehicles[vehicle_id].status = 'parked'

    def initialize_plugins(self):

        station_ids = [station_id for station_id in self.stations.keys()]
        vehicle_ids = [vehicle_id for vehicle_id in self.vehicles.keys()]

        # n vehicles >= stations
        if len(self.vehicles) >= len(self.stations):
            for idx in range(0, len(station_ids)):
                station_id = station_ids[idx]
                vehicle_id = vehicle_ids[idx]
                self.plugin(vehicle_id, station_id)

        # n vehicles < stations
        elif len(self.vehicles) < len(self.stations):
            for idx, vehicle_id in enumerate(self.vehicles.keys()):
                station_id = station_ids[idx]
                self.plugin(vehicle_id, station_id)


    def decrease_soc_of_vehicles_driving(self):
        for vehicle_id, driving_meta_data in self.vehicles_out_driving.items():
            self.vehicles[vehicle_id].state_of_charge -= driving_meta_data.soc_decrease_per_interval

    # Upon vehicle arrival send a QR code
    def send_qr_scans_upon_vehicle_arrival(self):

        vehicles_qr_scanned = []
        # when current timestamp == arrival then send msg to QR queue
        for vehicle_id, arrival_meta in self.vehicles_out_driving.items():
            if arrival_meta.arrival_datetime <= self.current_datetime:
                self.publish_object_to_queue(self.vehicles[vehicle_id], 'scan_events')
                vehicles_qr_scanned.append(vehicle_id)

        # remove vehicle from self.vehicles_out_driving
        # change status to parked while we await instructions
        for vehicle_id in vehicles_qr_scanned:
            self.vehicles[vehicle_id].status = 'parked'
            # del self.vehicles[vehicle_id]
            del self.vehicles_out_driving[vehicle_id]


    def process_driving_vehicle_for_future_arrival(self):
        # scan vehicles for driving status
        vehicles_already_processed = [vehicle_id for vehicle_id in self.vehicles_out_driving.keys()]
        for vehicle in self.vehicles.values():
            if vehicle.status == 'driving' and vehicle.id not in vehicles_already_processed:
                # assign a return datetime
                # use normal dist parameters to assign an arrival timestamp
                hours_out_driving = np.random.normal(
                    loc=self.trip_config['mean_reservation_duration_hours'],
                    scale=self.trip_config['stdev_reservation_hours']
                )

                # need to apply a floor to hours driving as normal dist will give negatives
                hours_out_driving = max(2, hours_out_driving)

                # use assumptions on miles/hour away and efficiency of vehicle to estimate soc on arrival
                # assume 0.346 kwh / miles
                # average 100 miles / day or 100/24 driving hrs ~ 4 miles / hr
                miles_driven = 4 * hours_out_driving
                kwh_consumed = miles_driven * 0.346
                current_kwh = vehicle.energy_capacity_kwh * vehicle.state_of_charge

                # can't have negative kwh for long trips
                kwh_on_arrival = max(0, current_kwh - kwh_consumed)

                # update the soc for on arrival soc
                # assume a minimum of 5 percent soc for this simulation
                # vehicle.state_of_charge = max(0.05, round(kwh_on_arrival/vehicle.energy_capacity_kwh, 1))
                soc_on_arrival = max(0.05, round(kwh_on_arrival/vehicle.energy_capacity_kwh, 1))

                # calculate the %soc change every period so we can deduct this on each run
                arrival_datetime = self.current_datetime + timedelta(hours=hours_out_driving)
                seconds_out_driving = hours_out_driving*3600
                n_intervals_till_arrival = seconds_out_driving/self.interval_seconds
                soc_decrease_per_interval = (vehicle.state_of_charge - soc_on_arrival) / n_intervals_till_arrival

                # ArrivalVehicle = namedtuple('ArrivalVehicle', ['arrival_datetime', 'vehicle'])
                ArrivalVehicle = namedtuple('ArrivalVehicle', ['arrival_datetime', 'soc_decrease_per_interval'])
                self.vehicles_out_driving[vehicle.id] = ArrivalVehicle(arrival_datetime, soc_decrease_per_interval)


    @classmethod
    def build_depot(cls, config, queue):
        # the folling are attribute that live within depot
        l2_max_power_kw = config.l2_max_power_kw
        dcfc_max_power_kw = config.dcfc_max_power_kw

        # setup stations
        stations = {}
        station_id = -1
        for l2_station in range(0, config.n_l2_stations):
            station_id += 1
            stations[station_id] = (Station(id=station_id, type='L2', max_power_kw=l2_max_power_kw))

        for dcfc_station in range(0, config.n_dcfc_stations):
            station_id += 1
            stations[station_id] = (Station(id=station_id, type='DCFC', max_power_kw=dcfc_max_power_kw))

        # setup vehicles
        vehicles = {}
        vehicle_idx = -1
        for vehicle_type, vehicle_settings in config.vehicles.items():
            for vehicle in range(0, vehicle_settings['n']):
                vehicle_idx += 1
                vehicle = Vehicle(
                    id=vehicle_idx,
                    connected_station_id=None,
                    type=vehicle_type,
                    #todo: need to randomly set this
                    state_of_charge=0.8,
                    energy_capacity_kwh= vehicle_settings['kwh_capacity'],
                    status='NA'
                )
                vehicles[vehicle_idx] = vehicle

        # schedule = Schedule(reservations=reservations)
        schedule = {}

        trip_config={
            'mean_reservation_duration_hours': config.mean_reservation_duration_hours,
            'stdev_reservation_hours': config.stdev_reservation_hours
        }

        # if the minimum_ready_vehicle_pool is empty then default to empty dict

        depot = AssetDepot(
            interval_seconds=config.interval_seconds,
            queue=queue,
            stations=stations,
            vehicles=vehicles,
            schedule=schedule,
            minimum_ready_vehicle_pool=config.minimum_ready_vehicle_pool,
            vehicle_snapshot={},
            trip_config=trip_config
        )

        return depot