from datetime import datetime, timedelta
import json

from pydantic import BaseModel

from src.asset_simulator.depot_config.depot_config import DepotConfig
from src.mock_queue.mock_queue import MockQueue
from src.asset_simulator.depot.depot import Depot
from src.demand_simulator.demand_simulator.demand_simulator import DemandSimulator
from src.demand_simulator.demand_simulator_config.demand_simulator_config import DemandSimulatorConfig


class RuntimeEnvironment(BaseModel):
    mock_queue: MockQueue
    demand_simulator: DemandSimulator
    asset_simulator: Depot

    def run(self):
        interval_seconds = self.demand_simulator.config.interval_seconds
        horizon_length_hours = self.demand_simulator.config.horizon_length_hours

        n_intervals = int((horizon_length_hours * 3600) / interval_seconds)
        for interval in range(0, n_intervals):

            self.demand_simulator.run_interval()
            self.asset_simulator.run_interval()

            # increment clock
            self.demand_simulator.increment_interval()
            self.asset_simulator.increment_interval()


# setup mock queue
mock_queue = MockQueue(
    scan_events=[],
    reservation_events=[],
    walk_in_events=[]
)

# setup demand_simulator
with open('demand_simulator/demand_simulator_config/configs/2days_15min_40res_per_day.json') as f:
    config = json.load(f)

demand_simulator_config = DemandSimulatorConfig(**config)
demand_simulator = DemandSimulator(config=demand_simulator_config, queue=mock_queue)

# setup asset_simulator
with open('asset_simulator/depot_config/configs/150_vehicles_10_L2_2_DCFC.json') as f:
    config = json.load(f)
depot_config = DepotConfig(**config)
depot = Depot.build_depot(config=depot_config,queue=mock_queue)
depot.initialize_plugins()

# setup heuristic
# with open('heuristic/depot_config/configs/150_vehicles_10_L2_2_DCFC.json') as f:
#     config = json.load(f)
# depot_config = DepotConfig(**config)
# depot = Depot.build_depot(depot_config)




runtime = RuntimeEnvironment(
    mock_queue=mock_queue,
    demand_simulator=demand_simulator,
    asset_simulator=depot
)

runtime.run()

print('simulation complete')
