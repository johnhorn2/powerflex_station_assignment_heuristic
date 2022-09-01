from datetime import datetime, timedelta
from typing import Optional, Dict

from pydantic import BaseModel

from src.asset_simulator.station.station import Station
from src.asset_simulator.vehicle.vehicle import Vehicle
from src.asset_simulator.schedule.schedule import Schedule
from src.asset_simulator.reservation.reservation import Reservation
from src.mock_queue.mock_queue import MockQueue


class Depot(BaseModel):
    interval_seconds: int
    current_datetime: datetime = datetime(year=2022, month=1, day=1, hour=0)
    stations: Optional[Dict[int, Station]] = {}
    vehicles: Optional[Dict[int, Vehicle]] = {}
    schedule: Schedule
    queue: MockQueue
    l2_charging_rate_kw: float = 12
    dcfc_charging_rate_kw: float = 150

    def increment_interval(self):
        interval_seconds = self.interval_seconds
        self.current_datetime = self.current_datetime + timedelta(seconds=interval_seconds)


    def pull_from_queue(self):
        # update reservations
        for res_msg in self.queue.reservation_events:
            self.schedule.reservations[res_msg['id']] = Reservation(
                id=res_msg['id'],
                departure_timestamp_utc=res_msg['departure_timestamp_utc'],
                vehicle_type=res_msg['vehicle_type'],
                state_of_charge=res_msg['state_of_charge']
            )


        # update walk_ins
        for walk_in_msg in self.queue.walk_in_events:
            self.schedule.reservations[walk_in_msg['id']] = Reservation(
                id=walk_in_msg['id'],
                departure_timestamp_utc=walk_in_msg['departure_timestamp_utc'],
                vehicle_type=walk_in_msg['vehicle_type'],
                state_of_charge=walk_in_msg['state_of_charge']
            )

        # update vehicle scans
        # todo: make object class for this

    def run_interval(self):

        # collect any instructions from the queue
        self.pull_from_queue()

        # update assets based on those instructions
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

        # push status of all vehicles/stations to the queue at end of interval to update the heuristic

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

        # setup stations
        stations = {}
        station_id = -1
        for l2_station in range(0, config.n_l2_stations):
            station_id += 1
            stations[station_id] = (Station(id=station_id, type='L2'))

        for dcfc_station in range(0, config.n_dcfc_stations):
            station_id += 1
            stations[station_id] = (Station(id=station_id, type='DCFC'))

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

        depot = Depot(
            interval_seconds=config.interval_seconds,
            queue=queue,
            stations=stations,
            vehicles=vehicles,
            schedule=schedule
        )

        return depot