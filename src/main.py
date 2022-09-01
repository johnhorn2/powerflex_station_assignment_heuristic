from datetime import datetime, timedelta
import json

from pydantic import BaseModel

from src.api.depot_config.depot_config import DepotConfig
from src.mock_queue.mock_queue import MockQueue
from src.api.depot.depot import Depot
from src.simulator.simulator.simulator import Simulator
from src.simulator.simulator_config.simulator_config import SimulatorConfig


class RuntimeEnvironment(BaseModel):
    mock_queue: MockQueue
    simulator: Simulator
    depot: Depot

    def run(self):
        simulator.run()


# setup mock queue
mock_queue = MockQueue(
    scan_events=[],
    reservation_events=[],
    walk_in_events=[]
)

# setup simulator
with open('simulator/simulator_config/configs/2days_15min_40res_per_day.json') as f:
    config = json.load(f)

simulator_config = SimulatorConfig(**config)
simulator = Simulator(config=simulator_config, queue=mock_queue)

# setup depot
with open('api/depot_config/configs/150_vehicles_10_L2_2_DCFC.json') as f:
    config = json.load(f)
depot_config = DepotConfig(**config)
depot = Depot.build_depot(depot_config)

runtime= RuntimeEnvironment(
    mock_queue=mock_queue,
    simulator=simulator,
    depot=depot
)

runtime.run()

print('simulation complete')
