from pydantic import BaseModel
from typing import List

from src.asset_simulator.vehicle.vehicle import Vehicle
from src.asset_simulator.vehicle.vehicle_fleet import VehicleFleet
from src.asset_simulator.station.station_fleet import StationFleet



class FleetManager(BaseModel):
    vehicle_fleet: VehicleFleet
    station_fleet: StationFleet

    @property
    def vehicles(self):
        return self.vehicle_fleet.vehicles

    @vehicles.setter
    def vehicles(self, vehicles):
        self.vehicle_fleet.vehicles = vehicles

    @property
    def stations(self):
        return self.station_fleet.stations

    @stations.setter
    def stations(self, stations):
        self.station_fleet.stations = stations

    def plugin(self, vehicle_id, station_id):
        self.vehicles[vehicle_id].plugin(station_id)
        self.stations[station_id].plugin(vehicle_id)

    def unplug(self, vehicle_id):
        # cycle through stations to unplug based on vehicle id
        for station in self.stations.values():
            if station.connected_vehicle_id == vehicle_id:
                self.stations[station.id].unplug()
        self.vehicles[vehicle_id].unplug()

    def park(self, vehicle_id):
        if self.vehicles[vehicle_id].is_plugged_in():
            self.vehicles[vehicle_id].unplug(vehicle_id)
        self.vehicles[vehicle_id].status = 'parked'

    def free_up_ready_vehicles(self):
        # if a vehicle is finished charging or 80% done then park it instead of charge it
        for vehicle in self.vehicles.values():
            if vehicle.state_of_charge >= 0.8 and vehicle.status in ('charging', 'finished_charging'):
                vehicle.unplug()
                vehicle.status = 'parked'

    # todo: move to vehicle_fleet method
    def get_available_vehicles_at_depot(self, vehicles):
        available_vehicles = {vehicle.id: vehicle for vehicle in self.vehicles.values() if vehicle.status != 'driving'}
        return available_vehicles

    def move_vehicle_to_charging_station(self, vehicle: Vehicle):
        # only applies to vehicles that are parked or charging
        if vehicle.status == 'charging' and self.vehicles[vehicle.id].status in ('charging', 'parked'):
            self.plugin(vehicle.id, vehicle.connected_station_id)


    def move_vehicles_to_charging_station(self, vehicles: List[Vehicle]):
        moved_to_charger = []

        for vehicle in vehicles:
            self.move_vehicle_to_charging_station(vehicle)
            moved_to_charger.append(vehicle)

        for vehicle in moved_to_charger:
            del self.move_charge[vehicle]




