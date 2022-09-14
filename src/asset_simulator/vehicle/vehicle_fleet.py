from typing import Dict, List

from pydantic import BaseModel

from src.asset_simulator.vehicle.vehicle import Vehicle
from src.asset_simulator.reservation.reservation import Reservation



class VehicleFleet(BaseModel):
    vehicles: Dict[int, Vehicle] = {}
    walk_in_pool: Dict[int, Vehicle] = {}
    minimum_ready_vehicle_pool: Dict[str, int] = {}

    def get_available_vehicles_at_depot(self):
        available_vehicles = {vehicle.id: vehicle for vehicle in self.vehicles.values() if vehicle.status != 'driving'}
        return available_vehicles

    def allocate_to_walk_in_pool(self, vehicle: Vehicle):
        self.walk_in_pool[vehicle.id] = vehicle

    @classmethod
    def sort_vehicles_highest_soc_first_by_type(self, vehicles, vehicle_type):
        # we need all vehicles sorted by SOC Descending
        if vehicle_type == 'any':
            return sorted(vehicles.values(), key=lambda x: x.state_of_charge, reverse=True)
        else:
            # we need a subset of vehicles sorted by departure ascending
            subset_by_vehicle_type = [vehicle for vehicle in vehicles if vehicle.type == vehicle_type]
            return sorted(subset_by_vehicle_type, key=lambda x: x.state_of_charge, reverse=True)

    def vehicle_in_walk_in_pool(self, vehicle_id):
        for vehicle in self.walk_in_pool.values():
            if vehicle.id == vehicle_id:
                return True
        return False