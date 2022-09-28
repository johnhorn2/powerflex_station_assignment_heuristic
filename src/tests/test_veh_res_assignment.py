from datetime import datetime
import json
import os
import unittest

from src.demand_simulator.demand_simulator_config.demand_simulator_config import DemandSimulatorConfig
from src.demand_simulator.demand_simulator.demand_simulator import DemandSimulator
from src.mock_queue.mock_queue import MockQueue
from src.asset_simulator.depot.asset_depot import AssetDepot
from src.heuristic.depot.algo_depot import AlgoDepot
from src.asset_simulator.reservation.reservation import Reservation
from src.asset_simulator.vehicle.vehicle import Vehicle
from src.asset_simulator.depot_config.depot_config import AssetDepotConfig
from src.asset_simulator.vehicle.vehicle_fleet import VehicleFleet
from src.asset_simulator.station.station_fleet import StationFleet
from src.asset_simulator.depot.fleet_manager import FleetManager


class TestVehicleReservationAssignment(unittest.TestCase):

    def get_algo_depot(self):
        mock_queue = MockQueue(
            scan_events=[],
            reservations=[],
            reservation_assignments=[],
            move_charge=[],
            departures=[],
            walk_in_events=[],
            vehicles_demand_sim=[],
            vehicles_heuristic=[],
            stations=[],
        )

        script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
        demand_sim_config = '../demand_simulator/demand_simulator_config/configs/5days_15min_40res_per_day.json'
        demand_sim_path = os.path.join(script_dir, demand_sim_config)

        # setup demand_simulator
        with open(demand_sim_path) as f:
            demand_sim_config = json.load(f)

            asset_config = 'hiker_9_to_5.json'

            # demand_simulator_config = DemandSimulatorConfig(**demand_sim_config)
            # demand_simulator = DemandSimulator(config=demand_simulator_config, queue=mock_queue)

            # setup asset_simulator
            asset_sim_config = '../asset_simulator/depot_config/configs/' + asset_config
            asset_sim_path = os.path.join(script_dir, asset_sim_config)

            with open(asset_sim_path) as f:
                asset_sim_config = json.load(f)

            # override params
            asset_sim_config['vehicles']['sedan']['n'] = 20
            asset_sim_config['vehicles']['suv']['n'] = 0
            asset_sim_config['vehicles']['crossover']['n'] = 0
            asset_sim_config['n_l2_stations'] = 5
            asset_sim_config['n_dcfc_stations'] = 0

            # setup heuristic
            # add a few more algo specific configs
            asset_sim_config['minimum_ready_vehicle_pool'] = {
                'sedan': 2,
                'crossover': 2,
                'suv': 2
            }
            algo_depot_config = AssetDepotConfig(**asset_sim_config)

            algo_depot = AlgoDepot.build_depot(config=algo_depot_config, queue=mock_queue)

            return algo_depot

    def get_reservation(self, id, departure, arrival, vehicle_type, walk_in, assigned_vehicle_id=None):
        res_dict = \
            {
                "id": id,
                "departure_timestamp_utc": departure,
                "arrival_timestamp_utc": arrival,
                "created_at_timestamp_utc": datetime.now(),
                "vehicle_type": vehicle_type,
                "state_of_charge": 0.8,
                "walk_in": walk_in,
                "status": 'created',
                "assigned_vehicle_id": assigned_vehicle_id
            }
        return Reservation(**res_dict)

    def get_reservations(self):
        res1 = self.get_reservation(
            id=1,
            departure=datetime(year=2022, month=1, day=2, hour=1),
            arrival=datetime(year=2022, month=1, day=6, hour=1),
            vehicle_type='sedan',
            walk_in=False
        )
        res2 = self.get_reservation(
            id=2,
            departure=datetime(year=2022, month=1, day=3, hour=1),
            arrival=datetime(year=2022, month=1, day=6, hour=1),
            vehicle_type='sedan',
            walk_in=False
        )
        res3 = self.get_reservation(
            id=3,
            departure=datetime(year=2022, month=1, day=9, hour=1),
            arrival=datetime(year=2022, month=1, day=13, hour=1),
            vehicle_type='sedan',
            walk_in=False
        )

        reservations = [res1, res2, res3]

        return {res.id: res for res in reservations}

    def get_vehicles(self):
        vehicle_ids = [1, 2, 3, 4]
        vehicles = {}
        soc_list = [0.2, 0.9, 0.6, 0.8]

        for idx, vehicle_idx in enumerate(vehicle_ids):
            vehicles[vehicle_idx] = \
                Vehicle(
                    id=vehicle_idx,
                    connected_station_id=None,
                    type='sedan',
                    state_of_charge=soc_list[idx],
                    energy_capacity_kwh=40,
                    status='NA'
                )

        return vehicles

    def get_fleet_manager(self, vehicles):
        # vehicle_fleet = VehicleFleet(vehicles=vehicles, minimum_ready_vehicle_pool=config.minimum_ready_vehicle_pool)
        # fleet_manager = FleetManager(vehicle_fleet=vehicle_fleet, station_fleet=station_fleet)
        vehicle_fleet = VehicleFleet(vehicles=vehicles)
        station_fleet = StationFleet(stations={})

        fleet_manager = FleetManager(vehicle_fleet=vehicle_fleet, station_fleet=station_fleet)
        return fleet_manager

    def test_vehicle_reservations_1(self):
        algo_depot = self.get_algo_depot()
        algo_depot.reservations = self.get_reservations()

        # prep vehicles
        vehicles = self.get_vehicles()
        fleet_manager = self.get_fleet_manager(vehicles)
        algo_depot.fleet_manager = fleet_manager
        algo_depot.assign_vehicles_reservations_by_type_and_highest_soc()


        # test the proper sort order
        for res in algo_depot.past_reservation_assignments.values():
            if res.id == '1':
                assert res.assigned_vehicle_id == 2
            if res.id == '2':
                assert res.assigned_vehicle_id == 4
            if res.id == '3':
                assert res.assigned_vehicle_id == 3

        assert len(algo_depot.past_reservation_assignments) == 3


    def test_vehicle_reservations_2(self):
        # when we have more reservations then vehicles

        algo_depot = self.get_algo_depot()
        reservations = self.get_reservations()

        fourth_res = self.get_reservation(
            id=4,
            departure=datetime(year=2022, month=1, day=19, hour=1),
            arrival=datetime(year=2022, month=1, day=22, hour=1),
            vehicle_type='sedan',
            walk_in=False
        )

        fifth_res = self.get_reservation(
            id=5,
            departure=datetime(year=2022, month=1, day=23, hour=1),
            arrival=datetime(year=2022, month=1, day=25, hour=1),
            vehicle_type='sedan',
            walk_in=False
        )

        reservations['4'] = fourth_res
        reservations['5'] = fifth_res

        algo_depot.reservations = reservations

        # prep vehicles
        vehicles = self.get_vehicles()
        fleet_manager = self.get_fleet_manager(vehicles)
        algo_depot.fleet_manager = fleet_manager
        algo_depot.assign_vehicles_reservations_by_type_and_highest_soc()


        # test the proper sort order
        for res in algo_depot.past_reservation_assignments.values():
            if res.id == '1':
                assert res.assigned_vehicle_id == 2
            if res.id == '2':
                assert res.assigned_vehicle_id == 4
            if res.id == '3':
                assert res.assigned_vehicle_id == 3
            if res.id == '4':
                assert res.assigned_vehicle_id == 1

        # we only make assignments when vehicles are available
        assert len(algo_depot.past_reservation_assignments) == 4
