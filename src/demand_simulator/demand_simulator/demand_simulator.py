from collections import namedtuple
from datetime import datetime, timedelta
import json
import random
import uuid

import numpy as np
from pydantic import BaseModel
from typing import Dict, Tuple

from src.demand_simulator.demand_simulator_config.demand_simulator_config import DemandSimulatorConfig
from src.asset_simulator.reservation.reservation import Reservation
from src.mock_queue.mock_queue import MockQueue
from src.mock_queue.msg_broker import MsgBroker
from src.asset_simulator.vehicle.vehicle import Vehicle


class DemandSimulator(MsgBroker):
    current_datetime: datetime = datetime(year=2022, month=1, day=1, hour=0)
    config: DemandSimulatorConfig
    vehicles: Dict[int, Vehicle] = {}
    # vehicles_out_driving: Dict[int, Tuple] = {}
    reservations: Dict[int, Reservation] = {}


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

        # can't have negative events per day
        n_events_per_day = max(0, n_events_per_day)


        # bootstrap n times based on hour of day
        random_hour = np.random.normal(
            loc=getattr(self.config, loc_hour_name),
            scale=getattr(self.config, scale_hour_name),
            size=n_events_per_day
        )

        # in case random hour selected is negative
        random_hour[random_hour < 0] = 0

        # assumes timesteps for simulations between 1 minute and 1 hour
        hour = current_datetime.hour
        min = current_datetime.minute
        fractional_hour = hour + (min/60)
        next_fractional_hour = fractional_hour + (self.config.interval_seconds/3600)

        # count number of events between fractional_hour and next_fractional_hour to return number of random events at time of call
        events_in_current_interval = [x for x in random_hour if (x > fractional_hour and x < next_fractional_hour)]

        return len(events_in_current_interval)

    def make_reservations(self, n_reservations, res_datetime, walk_in=False):
        if n_reservations > 0:
            # Currently assigning a vehicle type in the res based on the ratio in our fleet
            # todo: Make reservations based on AVAILABLE vehicles
            random_reservation_type_weights = [type_ratio for type_ratio in self.config.reservation_types.values()]
            vehicle_types=random.choices(list(self.config.reservation_types.keys()), weights=random_reservation_type_weights, k=n_reservations)
            for vehicle_type in vehicle_types:
                id = str(uuid.uuid4())
                res_dict = \
                    {
                        "id": id,
                        "departure_timestamp_utc": res_datetime,
                        "created_at_timestamp_utc": self.current_datetime,
                        "vehicle_type": vehicle_type,
                        "state_of_charge": 0.8,
                        "walk_in": walk_in,
                        "status": 'created'
                    }
                self.reservations[id] = Reservation(**res_dict)
        else:
            pass

    def generate_reservations_24_hours_ahead(self, current_datetime):
        # if init the sim then generate the reservations 24 hours ahead
            # first 24 hours of reservations pre-populated
            future_datetime = current_datetime
            for interval in range(0, int((24*3600)/self.config.interval_seconds)):
                # increment by timestep
                future_datetime = future_datetime + timedelta(seconds=self.config.interval_seconds)

                n_res = self.get_event('reservation', future_datetime)
                self.make_reservations(n_res, future_datetime)

    def generate_reservations_at_midnight(self):
        # at midnight generate new batch of reservations
        if self.current_datetime.hour == 0 and self.current_datetime.minute == 0 and self.current_datetime.second == 0:
            # self.reservations = self.generate_reservations_24_hours_ahead(self.current_datetime)
            self.generate_reservations_24_hours_ahead(self.current_datetime)

    def run_interval(self):

        self.subscribe_to_queue('vehicles', 'vehicle', 'vehicles_demand_sim')

        # self.process_driving_vehicle_for_future_arrival()

        # n_res = self.get_event('reservation', self.current_datetime)

        n_walk_ins = self.get_event('walk_in', self.current_datetime)

        # if the hour is midnight then this will fire and generate multiple reservations created at midnight a day ahead
        self.generate_reservations_at_midnight()
        # self.send_qr_scans_upon_vehicle_arrival()

        if n_walk_ins > 0:
            # walk ins objects are just treated as reservations that are 15 minutes ahead and occur in real time
            self.make_reservations(n_walk_ins, self.current_datetime + timedelta(minutes=15), walk_in=True)

        # publish any random reservations or walkins created
        self.publish_to_queue('reservations', 'reservations')
        # purge local memory of those newly generated reservations
        self.reservations = {}
