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
    vehicles_out_driving: Dict[int, Tuple] = {}
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
                        "vehicle_type": vehicle_type,
                        "state_of_charge": 0.8,
                        "walk_in": walk_in
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

            self.publish_to_queue('reservations', 'reservations')
            self.reservations = {}


    def process_driving_vehicle_for_future_arrival(self):
        # scan vehicles for driving status
        vehicles_already_processed = [vehicle_id for vehicle_id in self.vehicles_out_driving.keys()]
        for vehicle in self.vehicles.values():
            if vehicle.status == 'driving' and vehicle.id not in vehicles_already_processed:
                # assign a return datetime
                # use normal dist parameters to assign an arrival timestamp
                hours_out_driving = np.random.normal(
                    loc=self.config.mean_reservation_duration_hours,
                    scale=self.config.stdev_reservation_hours
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
                vehicle.state_of_charge = max(0.05, round(kwh_on_arrival/vehicle.energy_capacity_kwh, 1))

                arrival_datetime = self.current_datetime + timedelta(hours=hours_out_driving)

                ArrivalVehicle = namedtuple('ArrivalVehicle', ['arrival_datetime', 'vehicle'])
                self.vehicles_out_driving[vehicle.id] = ArrivalVehicle(arrival_datetime, vehicle)


    def send_qr_scans_upon_vehicle_arrival(self):

        vehicles_qr_scanned = []
        # when current timestamp == arrival then send msg to QR queue
        for arrival_meta in self.vehicles_out_driving.values():
            if arrival_meta.arrival_datetime <= self.current_datetime:
                self.publish_object_to_queue(arrival_meta.vehicle, 'scan_events')
                vehicles_qr_scanned.append(arrival_meta.vehicle.id)

        # remove vehicle from self.vehicles and self.vehicles_out_driving
        for vehicle_id in vehicles_qr_scanned:
            del self.vehicles[vehicle_id]
            del self.vehicles_out_driving[vehicle_id]


    def run_interval(self):

        self.subscribe_to_queue('vehicles', 'vehicle', 'vehicles_demand_sim')

        self.process_driving_vehicle_for_future_arrival()

        n_res = self.get_event('reservation', self.current_datetime)

        n_walk_ins = self.get_event('walk_in', self.current_datetime)

        self.generate_reservations_at_midnight()
        self.send_qr_scans_upon_vehicle_arrival()

        if n_walk_ins > 0:
            # walk ins objects are just treated as reservations that are 15 minutes ahead and occur in real time
            self.make_reservations(n_res, self.current_datetime + timedelta(minutes=15), walk_in=True)
