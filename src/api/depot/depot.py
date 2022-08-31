import random
from typing import Optional, Dict

import numpy as np

from src.api.reservation.reservation import Reservation




from pydantic import BaseModel

from src.api.station.station import Station
from src.api.vehicle.vehicle import Vehicle
from src.api.schedule.schedule import Schedule


class Depot(BaseModel):
    stations: Optional[Dict[int, Station]] = {}
    vehicles: Optional[Dict[int, Vehicle]] = {}
    walk_in_pool: Optional[Dict[int, Vehicle]] = {}
    schedule: Schedule
    minimum_ready_vehicle_pool: Dict
    l2_charging_rate_kw: float = 12
    dcfc_charging_rate_kw: float = 150

    @classmethod
    def build_depot(self):
        # the folling are attribute that live within depot

        # setup stations
        stations = {}
        station_id = -1
        for l2_station in range(0, self.config.n_l2_stations):
            station_id += 1
            stations[station_id] = (Station(id=station_id, type='L2'))

        for dcfc_station in range(0, self.config.n_dcfc_stations):
            station_id += 1
            stations[station_id] = (Station(id=station_id, type='DCFC'))

        # setup vehicles
        vehicles = {}
        vehicle_idx = -1
        for vehicle_type, vehicle_settings in self.config.vehicles.items():
            for vehicle in range(0, vehicle_settings['n']):
                vehicle_idx += 1
                vehicle = Vehicle(
                    id=vehicle_idx,
                    connected_station_id=None,
                    type=vehicle_type,
                    #todo: need to randomly set this
                    state_of_charge=0.8,
                    energy_capacity_kwh= vehicle_settings['kwh_capacity']
                )
                vehicles[vehicle_idx] = vehicle

        # setup walk-in pool
        walk_in_pool = {}

        # setup init schedule

        # seed random
        np.random.seed(seed=42)

        n_init_reservations = self.config.mean_reservations_per_day

        reservations = {}
        for res_idx in range(0, n_init_reservations):
            hour_depart = int(np.random.normal(
                loc=self.config.mean_vehicle_departure_hour_of_day,
                scale=self.config.stdev_vehicle_departure_hours,
                size=1
            ))

            random_reservation_type_weights = [veh_settings['n'] for veh_settings in self.config.vehicles.values()]
            reservations[res_idx] = \
                Reservation(
                    id=res_idx,
                    departure_timestamp_utc=datetime(year=2022, month=1, day=1, hour=hour_depart),
                    vehicle_type=random.choices(list(self.config.vehicles.keys()), weights=random_reservation_type_weights)[0],
                    state_of_charge=0.8,
                    assigned_vehicle_id=res_idx
                )

            schedule = Schedule(reservations=reservations)



        depot = Depot(
            stations=stations,
            vehicles=vehicles,
            walk_in_pool=walk_in_pool,
            schedule=schedule,
            minimum_ready_vehicle_pool=self.config.minimum_ready_vehicle_pool
        )

        return depot

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