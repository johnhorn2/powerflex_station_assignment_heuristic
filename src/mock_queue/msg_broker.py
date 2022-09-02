import json

from pydantic import BaseModel

from src.mock_queue.mock_queue import MockQueue
from src.asset_simulator.reservation.reservation import Reservation
from src.asset_simulator.station.station import Station
from src.asset_simulator.vehicle.vehicle import Vehicle


class MsgBroker(BaseModel):
    queue: MockQueue

    def publish_to_queue(self, object_type):
        for object in getattr(self, object_type).values():
            # this would be telematics data that the heuristic depends on
            object_json = json.dumps(object.dict(), default=str)
            getattr(self.queue, object_type).append(object_json)

    def subscribe_to_queue(self, object_type):
        # object_type = 'reservations' | 'stations' | 'vehicles'
        for object_json in getattr(self.queue, object_type):
            object_dict = json.loads(object_json)

            if object_type == 'reservations':
                object = Reservation.parse_obj(object_dict)
            elif object_type == 'stations':
                object = Station.parse_obj(object_dict)
            elif object_type == 'vehicles':
                object = Vehicle.parse_obj(object_dict)

            # if object exists overwrite else add entry
            getattr(self, object_type)[object.id] = object