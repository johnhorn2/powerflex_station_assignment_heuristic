import json

from pydantic import BaseModel
from typing import Dict, List

from src.mock_queue.mock_queue import MockQueue
from src.asset_simulator.reservation.reservation import Reservation
from src.asset_simulator.station.station import Station
from src.asset_simulator.vehicle.vehicle import Vehicle


class MsgBroker(BaseModel):
    queue: MockQueue
    reservation_assignment_snapshot: Dict[str, List] = {}

    def publish_object_to_queue(self, object, route):
        object_json = json.dumps(object.dict(), default=str)
        getattr(self.queue, route).append(object_json)

    def publish_to_queue(self, attribute_name, route):
        for object in getattr(self, attribute_name).values():
            # this would be telematics data that the heuristic depends on
            object_json = json.dumps(object.dict(), default=str)
            getattr(self.queue, route).append(object_json)

    def subscribe_to_queue(self, attribute_name, object_type, route, delete_on_read=True):

        for object_json in getattr(self.queue, route):
            object_dict = json.loads(object_json)

            # We need to capture the stream of reservation assignments to evaluate how verbose and accurate they are
            if object_type == 'reservation':
                object = Reservation.parse_obj(object_dict)

                if route == 'reservation_assignments':
                    # assumes we sent an assignment for this vehicle before
                    try:
                        self.reservation_assignment_snapshot[object.assigned_vehicle_id].append(object)
                    except KeyError:
                        # first time sending vehicle reservation assignment
                        self.reservation_assignment_snapshot[object.assigned_vehicle_id] = [object]



            elif object_type == 'station':
                object = Station.parse_obj(object_dict)
            elif object_type == 'vehicle':
                object = Vehicle.parse_obj(object_dict)

            # if object exists overwrite else add entry, since this is a dictionary attribute
            getattr(self, attribute_name)[object.id] = object

        # once we have read each item from our mock route then clear messages
        if delete_on_read:
            setattr(self.queue, route, [])