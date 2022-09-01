from datetime import datetime, timedelta
import random
import uuid

import numpy as np
from pydantic import BaseModel

from src.demand_simulator.demand_simulator_config.demand_simulator_config import DemandSimulatorConfig
from src.mock_queue.mock_queue import MockQueue


class DemandSimulator(BaseModel):
    current_datetime: datetime = datetime(year=2022, month=1, day=1, hour=0)
    config: DemandSimulatorConfig
    queue: MockQueue

    def increment_interval(self):
        interval_seconds = self.config.interval_seconds
        self.current_datetime = self.current_datetime + timedelta(seconds=interval_seconds)

    def get_event(self, type, current_datetime) -> int:
        if type == 'walk_in':
            loc_name = 'mean_walk_ins_per_day'
            scale_name = 'stdev_walk_ins_per_day'

            loc_hour_name = 'mean_walk_in_hour_of_day'
            scale_hour_name = 'stdev_walk_in_hours'

        elif type == 'reservation':
            loc_name = 'mean_reservations_per_day'
            scale_name = 'stdev_reservations_per_day'

            loc_hour_name = 'mean_vehicle_departure_hour_of_day'
            scale_hour_name ='stdev_vehicle_departure_hours'

        # n events per day
        n_events_per_day = int(np.random.normal(
            loc=getattr(self.config, loc_name),
            scale=getattr(self.config, scale_name),
            size=1
        ))


        # bootstrap n times based on hour of day
        random_hour = np.random.normal(
            loc=getattr(self.config, loc_hour_name),
            scale=getattr(self.config, scale_hour_name),
            size=n_events_per_day
        )

        # assumes timesteps for simulations between 1 minute and 1 hour
        hour = current_datetime.hour
        min = current_datetime.minute
        fractional_hour = hour + (min/60)
        next_fractional_hour = fractional_hour + (self.config.interval_seconds/3600)

        # count number of events between fractional_hour and next_fractional_hour to return number of random events at time of call
        events_in_current_interval = [x for x in random_hour if (x > fractional_hour and x < next_fractional_hour)]

        return len(events_in_current_interval)



    def get_reservations(self, n_reservations, res_datetime):
        random_reservation_type_weights = [type_ratio for type_ratio in self.config.reservation_types.values()]
        vehicle_types=random.choices(list(self.config.reservation_types.keys()), weights=random_reservation_type_weights, k=n_reservations)
        reservation_list = []
        for vehicle_type in vehicle_types:
            reservation_list.append(
                {
                    "id": str(uuid.uuid4()),
                    "departure_timestamp_utc": res_datetime,
                    "vehicle_type": vehicle_type,
                    "state_of_charge": 0.8
                }
            )

        return reservation_list

    def generate_reservations_24_hours_ahead(self, current_datetime):
        # if init the sim then generate the reservations 24 hours ahead
            # first 24 hours of reservations pre-populated
            future_datetime = current_datetime
            reservation_list = []
            for interval in range(0, int((24*3600)/self.config.interval_seconds)):
                # increment by timestep
                future_datetime = future_datetime + timedelta(seconds=self.config.interval_seconds)

                n_res = self.get_event('reservation', future_datetime)
                reservations = self.get_reservations(n_res, future_datetime)
                for res in reservations:
                    reservation_list.append(res)
            return reservation_list


    def run_interval(self):
        n_res = self.get_event('reservation', self.current_datetime)

        n_walk_ins = self.get_event('walk_in', self.current_datetime)

        # at midnight generate new batch of reservations
        if self.current_datetime.hour == 0 and self.current_datetime.minute == 0 and self.current_datetime.second == 0:
            reservations = self.generate_reservations_24_hours_ahead(self.current_datetime)
            for reservation in reservations:
                self.queue.reservation_events.append(reservation)

        if n_walk_ins > 0:
            # walk ins objects are just treated as reservations that are 15 minutes ahead and occur in real time
            walk_ins = self.get_reservations(n_res, self.current_datetime + timedelta(minutes=15))
            for walk_in in walk_ins:
                self.queue.walk_in_events.append(walk_in)
