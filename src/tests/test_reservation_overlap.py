from datetime import datetime
import json
import os
import unittest

from src.demand_simulator.demand_simulator_config.demand_simulator_config import DemandSimulatorConfig
from src.demand_simulator.demand_simulator.demand_simulator import DemandSimulator
from src.mock_queue.mock_queue import MockQueue
from src.asset_simulator.reservation.reservation import Reservation
from src.asset_simulator.vehicle.vehicle import Vehicle
from src.tests.test_veh_res_assignment import TestVehicleReservationAssignment

class TestReservationOverlap(unittest.TestCase):

    @classmethod
    def assigned_overlaps_exist(self, reservation_assignment_snapshot):
        for veh_id, reservation_list in reservation_assignment_snapshot.items():
            # test every combination of reservation to see if there are any overlaps at all
            for res in reservation_list:
                for res_compare in reservation_assignment_snapshot[veh_id]:
                    # don't test equality on the same res
                    if res.id != res_compare.id:
                        overlaps = DemandSimulator.reservation_does_overlap(
                            res,
                            res_compare.departure_timestamp_utc,
                            res_compare.arrival_timestamp_utc
                        )
                        if overlaps:
                            return (True, res, res_compare)
        return (False, None, None)

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


    def get_demand_simulator(self):
        mock_queue = MockQueue()

        n_days = 7
        script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
        demand_sim_config = '../demand_simulator/demand_simulator_config/configs/5days_15min_40res_per_day.json'
        demand_sim_path = os.path.join(script_dir, demand_sim_config)

        # setup demand_simulator
        with open(demand_sim_path) as f:
            demand_sim_config = json.load(f)

            demand_sim_config['horizontal_length_hours'] = n_days * 24

            demand_simulator_config = DemandSimulatorConfig(**demand_sim_config)
            demand_simulator = DemandSimulator(config=demand_simulator_config, queue=mock_queue)
        return demand_simulator

    def test_overlapping_reservation_detection_1(self):
        """
        make sure we can detect if two reservations are overlapping
        :return:
        """
        res1 = self.get_reservation(
            id=1,
            departure=datetime(year=2022,month=1,day=1,hour=1),
            arrival=datetime(year=2022,month=1,day=1,hour=6),
            vehicle_type='sedan',
            walk_in=False
        )
        res2 = self.get_reservation(
            id=1,
            departure=datetime(year=2022,month=1,day=1,hour=1),
            arrival=datetime(year=2022,month=1,day=1,hour=6),
            vehicle_type='sedan',
            walk_in=False
        )

        demand_sim = self.get_demand_simulator()
        demand_sim.reservations[res1.id] = res1
        demand_sim.reservations[res2.id] = res2

        is_overlap = demand_sim.reservation_does_overlap(res1, res2.departure_timestamp_utc, res2.arrival_timestamp_utc)
        assert is_overlap == True

    def test_overlapping_reservation_detection_2(self):
        """
        make sure we can detect if two reservations are overlapping
        :return:
        """
        res1 = self.get_reservation(
            id=1,
            departure=datetime(year=2022,month=1,day=2,hour=1),
            arrival=datetime(year=2022,month=1,day=2,hour=6),
            vehicle_type='sedan',
            walk_in=False
        )
        res2 = self.get_reservation(
            id=1,
            departure=datetime(year=2022,month=1,day=2,hour=6),
            arrival=datetime(year=2022,month=1,day=2,hour=9),
            vehicle_type='sedan',
            walk_in=False
        )

        demand_sim = self.get_demand_simulator()
        demand_sim.reservations[res1.id] = res1
        demand_sim.reservations[res2.id] = res2

        is_overlap = demand_sim.reservation_does_overlap(res1, res2.departure_timestamp_utc, res2.arrival_timestamp_utc)
        assert is_overlap == True


    def test_overlapping_reservation_detection_3(self):
        """
        make sure we can detect if two reservations are overlapping
        :return:
        """
        res1 = self.get_reservation(
            id=1,
            departure=datetime(year=2022,month=1,day=2,hour=1),
            arrival=datetime(year=2022,month=1,day=2,hour=6),
            vehicle_type='sedan',
            walk_in=False
        )
        res2 = self.get_reservation(
            id=1,
            departure=datetime(year=2022,month=1,day=2,hour=3),
            arrival=datetime(year=2022,month=1,day=2,hour=9),
            vehicle_type='sedan',
            walk_in=False
        )

        demand_sim = self.get_demand_simulator()
        demand_sim.reservations[res1.id] = res1
        demand_sim.reservations[res2.id] = res2

        is_overlap = demand_sim.reservation_does_overlap(res1, res2.departure_timestamp_utc, res2.arrival_timestamp_utc)
        assert is_overlap == True

    def test_overlapping_reservation_detection_4(self):
        """
        make sure we can detect if two reservations are overlapping
        :return:
        """
        res1 = self.get_reservation(
            id=1,
            departure=datetime(year=2022,month=1,day=2,hour=8,minute=30),
            arrival=datetime(year=2022,month=1,day=3,hour=11),
            vehicle_type='sedan',
            walk_in=False
        )
        res2 = self.get_reservation(
            id=1,
            departure=datetime(year=2022,month=1,day=3,hour=8,minute=45),
            arrival=datetime(year=2022,month=1,day=4,hour=9,minute=45),
            vehicle_type='sedan',
            walk_in=False
        )

        demand_sim = self.get_demand_simulator()
        demand_sim.reservations[res1.id] = res1
        demand_sim.reservations[res2.id] = res2

        is_overlap = demand_sim.reservation_does_overlap(res1, res2.departure_timestamp_utc, res2.arrival_timestamp_utc)
        assert is_overlap == True


    def test_overlapping_reservation_detection_5(self):
        """
        make sure we can detect if two reservations are overlapping
        :return:
        """
        res1 = self.get_reservation(
            id=1,
            departure=datetime(year=2022,month=1,day=2,hour=16),
            arrival=datetime(year=2022,month=1,day=3,hour=14,minute=15),
            vehicle_type='sedan',
            walk_in=False
        )
        res2 = self.get_reservation(
            id=1,
            departure=datetime(year=2022,month=1,day=3,hour=7,minute=30),
            arrival=datetime(year=2022,month=1,day=4,hour=9,minute=15),
            vehicle_type='sedan',
            walk_in=False
        )

        # make sure the algo function to detect prior reservations is working
        algo_depot = TestVehicleReservationAssignment.get_algo_depot()
        algo_depot.past_reservation_assignments = {res1.id: res1}
        overlapping_vehicles = algo_depot.get_vehicles_with_overlapping_reservations(res2)
        print(overlapping_vehicles)


    def test_non_overlapping_reservation_detection_1(self):
        """
        make sure we can detect if two reservations are overlapping
        :return:
        """
        res1 = self.get_reservation(
            id=1,
            departure=datetime(year=2022, month=1, day=2, hour=1),
            arrival=datetime(year=2022, month=1, day=2, hour=6),
            vehicle_type='sedan',
            walk_in=False
        )
        res2 = self.get_reservation(
            id=1,
            departure=datetime(year=2022, month=1, day=1, hour=3),
            arrival=datetime(year=2022, month=1, day=1, hour=9),
            vehicle_type='sedan',
            walk_in=False
        )

        demand_sim = self.get_demand_simulator()
        demand_sim.reservations[res1.id] = res1
        demand_sim.reservations[res2.id] = res2

        is_overlap = demand_sim.reservation_does_overlap(res1, res2.departure_timestamp_utc, res2.arrival_timestamp_utc)
        assert is_overlap != True

    def test_non_overlapping_reservation_detection_2(self):
        """
        make sure we can detect if two reservations are overlapping
        :return:
        """
        res1 = self.get_reservation(
            id=1,
            departure=datetime(year=2022, month=1, day=2, hour=1),
            arrival=datetime(year=2022, month=1, day=2, hour=6),
            vehicle_type='sedan',
            walk_in=False
        )
        res2 = self.get_reservation(
            id=1,
            departure=datetime(year=2022, month=1, day=3, hour=3),
            arrival=datetime(year=2022, month=1, day=3, hour=9),
            vehicle_type='sedan',
            walk_in=False
        )

        demand_sim = self.get_demand_simulator()
        demand_sim.reservations[res1.id] = res1
        demand_sim.reservations[res2.id] = res2

        is_overlap = demand_sim.reservation_does_overlap(res1, res2.departure_timestamp_utc, res2.arrival_timestamp_utc)
        assert is_overlap != True

    def test_available_vehicles_non_overlapping_1(self):
        """
        make sure we can detect if two reservations are overlapping
        :return:
        """
        res1 = self.get_reservation(
            id=1,
            departure=datetime(year=2022, month=1, day=2, hour=1),
            arrival=datetime(year=2022, month=1, day=6, hour=1),
            vehicle_type='sedan',
            walk_in=False,
            assigned_vehicle_id=1
        )
        res2 = self.get_reservation(
            id=2,
            departure=datetime(year=2022, month=1, day=3, hour=1),
            arrival=datetime(year=2022, month=1, day=6, hour=1),
            vehicle_type='sedan',
            walk_in=False,
            assigned_vehicle_id=2
        )
        res3 = self.get_reservation(
            id=3,
            departure=datetime(year=2022, month=1, day=9, hour=1),
            arrival=datetime(year=2022, month=1, day=13, hour=1),
            vehicle_type='sedan',
            walk_in=False,
            assigned_vehicle_id=3
        )

        vehicle_ids = [1,2,3,4]
        vehicles = {}

        for vehicle_idx in vehicle_ids:
            vehicles[vehicle_idx] = \
                Vehicle(
                    id=vehicle_idx,
                    connected_station_id=None,
                    type='sedan',
                    state_of_charge=0.8,
                    energy_capacity_kwh=40,
                    status='NA'
                )

        demand_sim = self.get_demand_simulator()
        demand_sim.reservations[res1.id] = res1
        demand_sim.reservations[res2.id] = res2
        demand_sim.reservations[res3.id] = res3

        demand_sim.vehicles = vehicles

        future_dept = datetime(year=2022,month=1,day=3,hour=1)
        future_arrival = datetime(year=2022,month=1,day=8,hour=1)
        available_vehicles = demand_sim.get_available_vehicles(departure=future_dept,arrival=future_arrival)
        for veh in available_vehicles:
            assert veh.id in (3,4)


if __name__ == '__main__':
    unittest.main()