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
        self.vehicles[vehicle_id]._plugin(station_id)
        self.stations[station_id]._plugin(vehicle_id)

    def unplug(self, vehicle_id, current_datetime):
        # cycle through stations to unplug based on vehicle id
        for station in self.stations.values():
            if station.connected_vehicle_id == vehicle_id:
                self.stations[station.id]._unplug(current_datetime)
        self.vehicles[vehicle_id]._unplug()

    def park(self, vehicle_id, current_datetime):
        if self.vehicles[vehicle_id].is_plugged_in():
            self.unplug(vehicle_id, current_datetime)
        self.vehicles[vehicle_id].park()

    def free_up_ready_vehicles(self, current_datetime):
        # if it is business hours between 9am and 5pm and vehicles is finished charging
        if current_datetime.hour >= 9 and current_datetime.hour <= 17:

        # all hours of the day
        # if 1 == 1:

            # if a vehicle is finished charging or 80% done then park it instead of charge it
            for vehicle in self.vehicles.values():
                if vehicle.state_of_charge == 1.0 and vehicle.status in ('charging', 'finished_charging'):
                # if vehicle.state_of_charge >= 0.8 and vehicle.status in ('charging', 'finished_charging'):
                    self.unplug(vehicle.id, current_datetime)
                    vehicle.status = 'parked'

    # todo: move to vehicle_fleet method


    def move_vehicle_to_charging_station(self, vehicle: Vehicle):
        # only applies to vehicles that are parked or charging
        if vehicle.status == 'charging' and self.vehicles[vehicle.id].status in ('charging', 'parked'):
            self.plugin(vehicle.id, vehicle.connected_station_id)


    def move_vehicles_to_charging_station(self, vehicles: List[Vehicle]):
        moved_to_charger = []

        for vehicle in vehicles:
            self.move_vehicle_to_charging_station(vehicle)
            moved_to_charger.append(vehicle)