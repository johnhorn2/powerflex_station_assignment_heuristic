import json
from typing import Optional, Dict

from src.asset_simulator.depot.asset_depot import AssetDepot

from src.asset_simulator.station.station import Station
from src.heuristic.vehicle.algovehicle import AlgoVehicle


class AlgoDepot(AssetDepot):
    walk_in_pool: Optional[Dict[int, AlgoVehicle]] = {}
    minimum_ready_vehicle_pool: Dict

    # Msg Broker Functions
    def poll_queues(self):
        self.subscribe_to_vehicle_queue()

    def subscribe_to_vehicle_queue(self):
        for vehicle_json in self.queue.vehicles:
            vehicle_dict = json.loads(vehicle_json)
            vehicle = AlgoVehicle.parse_obj(vehicle_dict)
            # if vehicle exists overwrite else add entry
            self.vehicles[vehicle.id] = vehicle


    def run_interval(self):

        # collect any instructions from the queue
        self.poll_queues()

        # update assets based on those instructions
        # many of these actions will come from the heuristic algorithm
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

    def get_walk_in_ready_vehicles(self, vehicle_class: str = None):
        pass

    def walk_in_available(self, vehicle_class: str = None):
        pass

    def can_free_up_dcfc(self, incoming_vehicle_id: int):
        pass

    def get_free_up_dcfc_instructions(self, incoming_vehicle_id: int):
        pass