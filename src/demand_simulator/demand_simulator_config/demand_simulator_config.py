from typing import Dict

from pydantic import BaseModel


class DemandSimulatorConfig(BaseModel):
    horizon_length_hours: int
    interval_seconds: int

    mean_walk_in_hour_of_day: int
    stdev_walk_in_hours: int
    mean_walk_ins_per_day: int
    stdev_walk_ins_per_day: int

    mean_vehicle_departure_hour_of_day: int
    stdev_vehicle_departure_hours: int
    mean_reservations_per_day: int
    stdev_reservations_per_day: int

    mean_reservation_duration_hours: int
    stdev_reservation_hours: int
    reservation_types: Dict