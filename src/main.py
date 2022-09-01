from datetime import datetime, timedelta
import json

from pydantic import BaseModel

from src.supply_simulator.depot_config.depot_config import DepotConfig
from src.mock_queue.mock_queue import MockQueue
from src.supply_simulator.depot.depot import Depot
from src.demand_simulator.demand_simulator.demand_simulator import DemandSimulator
from src.demand_simulator.demand_simulator_config.demand_simulator_config import DemandSimulatorConfig


class RuntimeEnvironment(BaseModel):
    current_datetime: datetime
    mock_queue: MockQueue
    demand_simulator: DemandSimulator
    depot: Depot

    def run(self):
        interval_seconds = self.demand_simulator.config.interval_seconds
        horizon_length_hours = self.demand_simulator.config.horizon_length_hours


        n_intervals = int((horizon_length_hours * 3600) / interval_seconds)
        for interval in range(0, n_intervals):

            self.demand_simulator.get_demand_signal(self.current_datetime)

            # increment clock
            self.current_datetime = self.current_datetime + timedelta(seconds=interval_seconds)


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

# setup supply_simulator
with open('supply_simulator/depot_config/configs/150_vehicles_10_L2_2_DCFC.json') as f:
    config = json.load(f)
depot_config = DepotConfig(**config)
depot = Depot.build_depot(depot_config)

runtime = RuntimeEnvironment(
    current_datetime=datetime(year=2022, month=1, day=1, hour=0),
    mock_queue=mock_queue,
    demand_simulator=demand_simulator,
    depot=depot
)

runtime.run()

print('simulation complete')
