from collections import namedtuple
from typing import List, Optional, Dict


import pydantic

from src.station.station import Station
from src.parking_lot.parking_lot import ParkingLot
from src.vehicle.vehicle import Vehicle
from src.schedule.schedule import Schedule


class Depot:
    stations: Optional[Dict[int: Station]] = {}
    vehicles: Optional[Dict[int: Vehicle]] = {}
    walk_in_pool: Optional[Dict[int: Vehicle]] = {}
    schedule: Schedule
    parking_lot: ParkingLot
    minimum_ready_vehicle_pool: int
    l2_charging_rate_kw: float
    dcfc_charging_rate_kw: float


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