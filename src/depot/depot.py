from collections import namedtuple
from typing import List, Optional, Dict


import pydantic

from src.station.station import Station
from src.parking_lot.parking_lot import ParkingLot
from src.vehicle.vehicle import Vehicle
from src.reservation.reservation import Reservation


class Depot:
    stations: Optional[Dict[int: Station]] = {}
    vehicles: Optional[Dict[int: Vehicle]] = {}
    reservations: Optional[ Dict[int: Reservation]] = {}
    parking_lot: ParkingLot
    minimum_ready_vehicle_pool: int

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