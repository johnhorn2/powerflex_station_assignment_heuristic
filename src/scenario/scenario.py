from datetime import datetime
import math
import random

import numpy as np
from pydantic import BaseModel, Field


from src.depot.depot import Depot
from src.reservation.reservation import Reservation
from src.scenario.scenario_config import ScenarioConfig
from src.schedule.schedule import Schedule
from src.station.station import Station
from src.vehicle.vehicle import Vehicle

class Scenario(BaseModel):
    current_timestamp: datetime = Field(
        description="the first timestamp in the simulation",
        default=datetime.now()
    )

    config: ScenarioConfig
    depot: Depot = None


    def intialize(self):
        self.depot = self.build_depot()
        n_days = (math.ceil(self.config.horizon_length_hours/24))

        # pre-calculate random walk ins
        n_walk_ins_per_day = self.get_n_samples_per_day(n_days, 'walk_in')
        daily_walk_ins = self.get_daily_samples(n_walk_ins_per_day, n_days, 'walk_in')

        # pre-calculate random reservations
        n_reservations_per_day = self.get_n_samples_per_day(n_days, 'reservation')
        daily_reservations = self.get_daily_samples(n_reservations_per_day, n_days, 'reservation')

        print('init complete')

    def get_n_samples_per_day(self, n_days, type):
        # random samples per day
        if type == 'walk_in':
            loc_name = 'mean_walk_ins_per_day'
            scale_name = 'stdev_walk_ins_per_day'
        elif type == 'reservation':
            loc_name = 'mean_reservations_per_day'
            scale_name = 'stdev_reservations_per_day'


        n_samples = np.random.normal(
            loc=self.config.random_parameters[loc_name],
            scale=self.config.random_parameters[scale_name],
            # ceiling number of days
            size=n_days
        )
        #replace negative values with zero
        n_samples[n_samples < 0] = 0

        # round to samples per day
        n_samples= (n_samples).astype(int)

        return n_samples

    def get_daily_samples(self, n_samples_per_day, n_days, type):

        if type == 'walk_in':
            loc_name = 'mean_walk_in_hour_of_day'
            scale_name = 'stdev_walk_in_hours'
        elif type == 'reservation':
            loc_name = 'mean_vehicle_departure_hour_of_day'
            scale_name = 'stdev_vehicle_departure_hours'

        daily_samples = []
        for day in range(0, n_days):

            samples = np.random.normal(
                loc=self.config.random_parameters[loc_name],
                scale=self.config.random_parameters[scale_name],
                size=n_samples_per_day[day]
            )
            # round walk in samples to hour of day
            #min is 0 and max is 24
            samples[samples < 0] = 0
            samples[samples > 23] = 23
            daily_samples.append(samples)

        return daily_samples

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

        n_init_reservations = self.config.random_parameters['mean_reservations_per_day']

        reservations = {}
        for res_idx in range(0, n_init_reservations):
            hour_depart = int(np.random.normal(
                loc=self.config.random_parameters['mean_vehicle_departure_hour_of_day'],
                scale=self.config.random_parameters['stdev_vehicle_departure_hours'],
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

    def is_walk_in_random(self):
        pass


    def run(self):
        # n_intervals = (self.config.horizon_length_hours*3600) / self.config.horizon_interval_seconds
        # for interval in range(0, n_intervals):
        pass