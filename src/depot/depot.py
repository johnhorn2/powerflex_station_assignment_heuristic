from typing import List, Optional

import pydantic

from src.station.station import Station
from src.parking_lot.parking_lot import ParkingLot
from src.vehicle.vehicle import Vehicle


class Depot:
    stations: Optional[List[Station]] = []
    vehicles: Optional[List[Vehicle]] = []
    parking_lot: ParkingLot
    minimum_ready_vehicle_pool: int
    reservations: Optional[ List[]]

    def l2_is_available(self):
        # return first L2 station available
        for station in self.stations:
            if station.is_available() and station.is_l2():
                return (True, station.id)
        return (False, None)

    def dcfc_is_available(self):
        # return first DCFC station available
        for station in self.station_list:
            if station.is_available() and station.is_dcfc():
                return (True, station.id)
        return (False, None)
