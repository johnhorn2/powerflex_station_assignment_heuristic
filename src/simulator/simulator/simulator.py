from datetime import datetime, timedelta

import numpy as np
from pydantic import BaseModel

from src.simulator.simulator_config.simulator_config import SimulatorConfig


class Simulator(BaseModel):
    config: SimulatorConfig

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

    def run(self):
        current_datetime = datetime(year=2022, month=1, day=1, hour=1)
        n_intervals = int((self.config.horizon_length_hours * 3600) / self.config.interval_seconds)

        for interval in range(0, n_intervals):
            # increment by timestep
            current_datetime = current_datetime + timedelta(seconds=self.config.interval_seconds)

            n_res = self.get_event('reservation', current_datetime)
            n_walk_ins = self.get_event('walk_in', current_datetime)

            if n_res > 0:
                msg = 'res' + ' ' + str(current_datetime) + ' ' + str(n_res)
                print(msg)

            if n_walk_ins > 0:
                msg = 'walk_ins' + ' ' + str(current_datetime) + ' ' + str(n_walk_ins)
                print(msg)
