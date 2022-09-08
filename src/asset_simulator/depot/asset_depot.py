from datetime import datetime, timedelta
import json
from typing import Optional, Dict

from pydantic import BaseModel

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
    reservations: Optional[Dict[int, Reservation]] = {}
    schedule: Schedule
    l2_charging_rate_kw: float = 12
    dcfc_charging_rate_kw: float = 150
    minimum_ready_vehicle_pool: Optional[Dict[str, int]]

    def increment_interval(self):
        interval_seconds = self.interval_seconds
        self.current_datetime = self.current_datetime + timedelta(seconds=interval_seconds)


    def charge_vehicles(self):
        plugged_in_vehicle_station = [(vehicle.id, vehicle.connected_station_id) for vehicle in self.vehicles.values() if vehicle.status == 'charging']
        for vehicle_id, station_id in plugged_in_vehicle_station:
            max_power_kw = self.stations[station_id].max_power_kw
            self.vehicles[vehicle_id].charge(self.interval_seconds, max_power_kw)

    def depart_vehicles(self):
        # if the current timestamp matches the departure AND vehicle_id matches reservation then unplug
        #todo: we don't have vehicle assignments though because the heuristic does that

        # for any assigned reservations if the departure datetime is <= current_datetime
        # then change vehicle status to 'driving'
        departures = [reservation for reservation in self.reservations.values() if reservation.departure_timestamp_utc <= self.current_datetime]
        for reservation in departures:
            # if we have as assigned vehicle id and it is time to depart then depart
            if isinstance(reservation.assigned_vehicle_id, int):
                # need to unplug otherwise state gets overwritten as 'finished charging' instead of 'driving'
                self.vehicles[reservation.assigned_vehicle_id].unplug()
                self.vehicles[reservation.assigned_vehicle_id].status = 'driving'
            else:
                print('missed departure')

    def move_vehicles(self):
        # todo based on heuristic commands
        pass

    def is_duplicate_vehicle_assignments(self):
        # determine if that vehicle id is already assigned to a different reservation
        # by creatig a dictionary of {vehicle_id: reservations) and ensuring a match on res_id
        reserved_vehicle_ids = [res.assigned_vehicle_id for res in self.reservations.values() if res.assigned_vehicle_id != None]
        return len(set(reserved_vehicle_ids)) != len(reserved_vehicle_ids)



    def run_interval(self):
        # important to depart vehicles first thing so that we don't assign the vehicles other tasks afterwards when it should be gone
        self.depart_vehicles()


        # the heuristic has assigned a veh id to the reservation
        # we overwrite the current reservation with that assigned res
        self.subscribe_to_queue('reservations', 'reservation', 'reservation_assignments')

        #todo: overwrite vehicles connected station id using the move/charge instructions in the move/charge queue
        # self.subscribe_to_queue('vehicles', vehicle', 'move_charge')


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

    def plugin(self, vehicle_id, station_id):
        self.vehicles[vehicle_id].plugin(station_id)
        self.stations[station_id].plugin(vehicle_id)

    def unplug(self, vehicle_id):
        # cycle through stations to unplug based on vehicle id
        for station in self.stations:
            if station.connected_vehicle_id == vehicle_id:
                self.stations[station.id].unplug()
        self.vehicles[vehicle_id].unplug()

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

        # if the minimum_ready_vehicle_pool is empty then default to empty dict

        depot = AssetDepot(
            interval_seconds=config.interval_seconds,
            queue=queue,
            stations=stations,
            vehicles=vehicles,
            schedule=schedule,
            minimum_ready_vehicle_pool=config.minimum_ready_vehicle_pool
        )

        return depot