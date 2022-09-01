from datetime import datetime, timedelta
import json

from pydantic import BaseModel

from src.supply_simulator.depot_config.depot_config import DepotConfig
from src.mock_queue.mock_queue import MockQueue
from src.supply_simulator.depot.depot import Depot
from src.demand_simulator.demand_simulator.demand_simulator import Simulator
from src.demand_simulator.demand_simulator_config.demand_simulator_config import SimulatorConfig


class RuntimeEnvironment(BaseModel):
    current_datetime: datetime = datetime
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

# setup demand_simulator
with open('demand_simulator/demand_simulator_config/configs/2days_15min_40res_per_day.json') as f:
    config = json.load(f)

simulator_config = SimulatorConfig(**config)
simulator = Simulator(config=simulator_config, queue=mock_queue, current_datetime=datetime(year=2022, month=1, day=1, hour=0))

# setup depot
with open('supply_simulator/depot_config/configs/150_vehicles_10_L2_2_DCFC.json') as f:
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
