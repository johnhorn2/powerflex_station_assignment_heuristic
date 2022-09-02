from datetime import datetime, timedelta
import json
from typing import Optional, Dict

from pydantic import BaseModel

from src.asset_simulator.station.station import Station
from src.asset_simulator.vehicle.vehicle import Vehicle
from src.asset_simulator.schedule.schedule import Schedule
from src.asset_simulator.reservation.reservation import Reservation
from src.mock_queue.mock_queue import MockQueue


class AssetDepot(BaseModel):
    interval_seconds: int
    current_datetime: datetime = datetime(year=2022, month=1, day=1, hour=0)
    stations: Optional[Dict[int, Station]] = {}
    vehicles: Optional[Dict[int, Vehicle]] = {}
    schedule: Schedule
    queue: MockQueue
    l2_charging_rate_kw: float = 12
    dcfc_charging_rate_kw: float = 150
    minimum_ready_vehicle_pool: Optional[Dict[str, int]]

    # Msg Broker Functions
    def publish_to_vehicle_queue(self):
        # this would be telematics data that the heuristic depends on
        for vehicle in self.vehicles.values():
            vehicle_json = json.dumps(vehicle.dict(), default=str)
            self.queue.vehicles.append(vehicle_json)

    def publish_to_station_queue(self):
        # this would be station statuses that the heuristic depends on
        for station in self.stations.values():
            station_json = json.dumps(station.dict(), default=str)
            self.queue.stations.append(station_json)

    def increment_interval(self):
        interval_seconds = self.interval_seconds
        self.current_datetime = self.current_datetime + timedelta(seconds=interval_seconds)


    def poll_queues(self):
    #     # update reservations
    #     for idx, res_msg in enumerate(self.queue.reservation_events):
    #         reservation = json.loads(res_msg)
    #         self.schedule.reservations[reservation['id']] = Reservation(
    #             **reservation
    #         )
    #         # read and remove msg from queue
    #         self.queue.reservation_events.pop(idx)
    #
    #
    #     # update walk_ins
    #     for idx, walk_in_msg in enumerate(self.queue.walk_in_events):
    #         walk_in = json.loads(walk_in_msg)
    #         self.schedule.reservations[walk_in['id']] = Reservation(
    #             **walk_in
    #         )
    #         # read and remove msg from queue
    #         self.queue.walk_in_events.pop(idx)

        # update vehicle scans
        # todo: make object class for this
        pass

    def charge_vehicles(self):
        plugged_in_vehicle_station = [(vehicle.id, vehicle.connected_station_id) for vehicle in self.vehicles.values() if vehicle.status == 'charging']
        for vehicle_id, station_id in plugged_in_vehicle_station:
            max_power_kw = self.stations[station_id].max_power_kw
            self.vehicles[vehicle_id].charge(self.interval_seconds, max_power_kw)

    def depart_vehicles(self):
        # if the current timestamp matches the departure AND vehicle_id matches reservation then unplug
        #todo: we don't have vehicle assignments though because the heuristic does that
        pass

    def move_vehicles(self):
        # todo based on heuristic commands
        pass

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


        # increment time and actions including:
        """
        charge any vehicles plugged in and not fully charged yet
        decrease soc of any vehicles out on a job based on interval
        """

        self.depart_vehicles()
        self.move_vehicles()
        self.charge_vehicles()

        # push status of all vehicles/stations to the queue at end of interval to update the heuristic
        self.publish_to_vehicle_queue()
        self.publish_to_station_queue()

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