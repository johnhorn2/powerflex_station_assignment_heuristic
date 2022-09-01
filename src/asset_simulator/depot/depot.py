from typing import Optional, Dict

from pydantic import BaseModel

from src.asset_simulator.station.station import Station
from src.asset_simulator.vehicle.vehicle import Vehicle
from src.asset_simulator.schedule.schedule import Schedule


class Depot(BaseModel):
    stations: Optional[Dict[int, Station]] = {}
    vehicles: Optional[Dict[int, Vehicle]] = {}
    schedule: Schedule
    l2_charging_rate_kw: float = 12
    dcfc_charging_rate_kw: float = 150

    def run_interval(self, current_datetime):

        # collect any instructions from the queue


        # update internal objects based on those instructions
        """
        plugin
        unplug
        depart
        move
        scan
        walk_in
        """


        # increment time and actions including:
        """
        charge any vehicles plugged in and not fully charged yet
        decrease soc of any vehicles out on a job based on interval
        """

        # push status of all vehicles/stations to the queue at end of interval to update the heuristic



    @classmethod
    def build_depot(cls, config):
        # the folling are attribute that live within depot

        # setup stations
        stations = {}
        station_id = -1
        for l2_station in range(0, config.n_l2_stations):
            station_id += 1
            stations[station_id] = (Station(id=station_id, type='L2'))

        for dcfc_station in range(0, config.n_dcfc_stations):
            station_id += 1
            stations[station_id] = (Station(id=station_id, type='DCFC'))

        # setup vehicles
        vehicles = {}
        vehicle_idx = -1
        for vehicle_type, vehicle_settings in config.vehicles.items():
            for vehicle in range(0, vehicle_settings['n']):
                vehicle_idx += 1
                vehicle = Vehicle(
                    id=vehicle_idx,
                    connected_station_id=None,
                    type=vehicle_type,
                    #todo: need to randomly set this
                    state_of_charge=0.8,
                    energy_capacity_kwh= vehicle_settings['kwh_capacity']
                )
                vehicles[vehicle_idx] = vehicle

        # schedule = Schedule(reservations=reservations)
        schedule = {}

        depot = Depot(
            stations=stations,
            vehicles=vehicles,
            schedule=schedule
        )

        return depot