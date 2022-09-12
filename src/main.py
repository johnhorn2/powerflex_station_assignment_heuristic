from datetime import datetime, timedelta
import json
import os

import pandas as pd
from pydantic import BaseModel

from src.asset_simulator.depot_config.depot_config import AssetDepotConfig
from src.asset_simulator.depot.asset_depot import AssetDepot
from src.demand_simulator.demand_simulator.demand_simulator import DemandSimulator
from src.demand_simulator.demand_simulator_config.demand_simulator_config import DemandSimulatorConfig
from src.heuristic.depot.algo_depot import AlgoDepot
from src.mock_queue.mock_queue import MockQueue
from src.plotter.plotter import Plotter


class RuntimeEnvironment(BaseModel):
    demand_simulator: DemandSimulator
    asset_simulator: AssetDepot
    heuristic: AlgoDepot
    queue: MockQueue

    def run(self):
        interval_seconds = self.demand_simulator.config.interval_seconds
        horizon_length_hours = self.demand_simulator.config.horizon_length_hours

        n_intervals = int((horizon_length_hours * 3600) / interval_seconds)
        for interval in range(0, n_intervals):

            pct_complete = 100.0*interval/n_intervals
            print(str(pct_complete) + ': % complete')

            self.demand_simulator.run_interval()
            self.asset_simulator.run_interval()
            self.heuristic.run_interval()

            # increment clock
            self.demand_simulator.increment_interval()
            self.asset_simulator.increment_interval()
            self.heuristic.increment_interval()


        # load meta data into dataframe for plotting
        df_soc = pd.DataFrame.from_dict(self.asset_simulator.vehicle_soc_snapshot)
        df_status = pd.DataFrame.from_dict(self.asset_simulator.vehicle_status_snapshot)

        plot = Plotter()
        soc_chart = plot.get_soc_timeseries(df_soc, df_status, self.asset_simulator.reservation_assignment_snapshot)
        return (soc_chart, None)


# setup mock queue
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
demand_sim_config = 'demand_simulator/demand_simulator_config/configs/2days_15min_40res_per_day.json'
demand_sim_path = os.path.join(script_dir, demand_sim_config)

# setup demand_simulator
with open(demand_sim_path) as f:
    config = json.load(f)

demand_simulator_config = DemandSimulatorConfig(**config)
demand_simulator = DemandSimulator(config=demand_simulator_config, queue=mock_queue)




# setup asset_simulator
asset_sim_config = 'asset_simulator/depot_config/configs/150_vehicles_10_L2_2_DCFC.json'
asset_sim_path = os.path.join(script_dir, asset_sim_config)

with open(asset_sim_path) as f:
    config = json.load(f)
asset_depot_config = AssetDepotConfig(**config)
asset_depot = AssetDepot.build_depot(config=asset_depot_config, queue=mock_queue)
asset_depot.initialize_plugins()

# setup heuristic
# add a few more algo specific configs
config['minimum_ready_vehicle_pool'] = {
    'sedan': 2,
    'crossover': 2,
    'suv': 2
}
algo_depot_config = AssetDepotConfig(**config)

algo_depot = AlgoDepot.build_depot(config=asset_depot_config, queue=mock_queue)


runtime = RuntimeEnvironment(
    mock_queue=mock_queue,
    demand_simulator=demand_simulator,
    asset_simulator=asset_depot,
    heuristic=algo_depot,
    queue=mock_queue
)

runtime.run()

print('simulation complete')
