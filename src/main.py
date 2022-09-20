import pickle
import json
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pydantic import BaseModel

from src.asset_simulator.depot_config.depot_config import AssetDepotConfig
from src.asset_simulator.depot.asset_depot import AssetDepot
from src.demand_simulator.demand_simulator.demand_simulator import DemandSimulator
from src.demand_simulator.demand_simulator_config.demand_simulator_config import DemandSimulatorConfig
from src.heuristic.depot.algo_depot import AlgoDepot
from src.mock_queue.mock_queue import MockQueue
from src.plotter.plotter import Plotter


L2_STATION_MIN = 1
L2_STATION_MAX = 30
L2_STEPS = 5
STATIONS = np.linspace(L2_STATION_MIN, L2_STATION_MAX, L2_STEPS, dtype=int)

VEH_MIN = 5
VEH_MAX = 30
VEH_STEPS = 5
VEHS = np.linspace(VEH_MIN, VEH_MAX, VEH_STEPS, dtype=int)

random_sort_list=[True,False]

class RuntimeEnvironment(BaseModel):
    demand_simulator: DemandSimulator
    asset_simulator: AssetDepot
    heuristic: AlgoDepot
    queue: MockQueue

    def run(self, plot_output=True, random_sort=False):
        interval_seconds = self.demand_simulator.config.interval_seconds
        horizon_length_hours = self.demand_simulator.config.horizon_length_hours

        n_intervals = int((horizon_length_hours * 3600) / interval_seconds)
        for interval in range(0, n_intervals):

            pct_complete = 100.0*interval/n_intervals
            # print(str(pct_complete) + ': % complete')

            self.demand_simulator.run_interval()
            self.asset_simulator.run_interval()
            self.heuristic.run_interval(random_sort=True)

            # increment clock
            self.demand_simulator.increment_interval()
            self.asset_simulator.increment_interval()
            self.heuristic.increment_interval()


        # load meta data into dataframe for plotting
        df_soc = pd.DataFrame.from_dict(self.asset_simulator.vehicle_soc_snapshot)
        df_status = pd.DataFrame.from_dict(self.asset_simulator.vehicle_status_snapshot)
        df_actual_departures = pd.DataFrame.from_dict(self.asset_simulator.departure_snapshot)
        df_actual_departures['departure_delta_minutes'] = (df_actual_departures['actual_departure_datetime'] - df_actual_departures['scheduled_departure_datetime'])

        if plot_output:
            plot = Plotter()
            soc_chart = plot.get_soc_timeseries(
                df_soc,
                df_status,
                self.asset_simulator.reservation_assignment_snapshot,
                self.asset_simulator.move_charge_snapshot,
                self.asset_simulator.fleet_manager.station_fleet
            )
            return (soc_chart, None)

        if plot_output == False:
            departure_delta_minutes = (pd.to_timedelta(df_actual_departures['departure_delta_minutes'])/pd.Timedelta('60s')).tolist()
            return departure_delta_minutes

output_list = []
for random_sort in random_sort_list:
    for veh_count in VEHS:
        for station_count in STATIONS:
            print('running with veh_count: ' + str(veh_count) + ' and station_count: ' + str(station_count))
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
            demand_sim_config = 'demand_simulator/demand_simulator_config/configs/5days_15min_40res_per_day.json'
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

                # override params
                config['vehicles']['sedan']['n'] = veh_count
                config['n_l2_stations'] = station_count

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

                # departure deltas in minutes
                results = runtime.run(plot_output=False, random_sort=random_sort)

                output_list.append(
                    {
                        'business_as_usual': random_sort,
                        'num_vehicles': veh_count,
                        'l2_stations': station_count,
                        'departure_deltas': results
                    }
                )


                # create dictionary for vis dataframe where key: vehicle_id, value: cnt
                vis_tracker = {}
                for veh_id, val in runtime.asset_simulator.reservation_assignment_snapshot.items():
                    vis_tracker[veh_id] = len(val)

                # create dictionary for self.reservation dataframe where key: vehicle_id, value: cnt
                # res_tracker = {}
                # for res in runtime.asset_simulator.reservations.values():
                #     try:
                #         res_tracker[res.assigned_vehicle_id] += 1
                #     except KeyError:
                #         res_tracker[res.assigned_vehicle_id] = 1
                #
                # print('resrevations tracker')
                # for veh_id, cnt in res_tracker.items():
                #     print('veh:' + str(veh_id) + ', cnt: ' + str(cnt))

                # departure_tracker = {}
                # for veh_id in runtime.asset_simulator.departure_snapshot['vehicle_id']:
                #     try:
                #         departure_tracker[veh_id] += 1
                #     except KeyError:
                #         departure_tracker[veh_id] = 1

                # print('departure tracker')
                # for veh_id, cnt in departure_tracker.items():
                #     print('veh:' + str(veh_id) + ', cnt: ' + str(cnt))

                # runtime.asset_simulator.departure_snapshot

                print('simulation complete')

with open('multi_run.pickle', 'wb') as handle:
    pickle.dump(output_list, handle, protocol=pickle.HIGHEST_PROTOCOL)

with open('multi_run.pickle', 'rb') as handle:
    multi_run_list = pickle.load(handle)

# process the output for 3d plotting
heur_ev_cnt = []
heur_station_cnt = []
heur_mean_late = []


bau_ev_cnt = []
bau_station_cnt = []
bau_mean_late = []

for result_dict in multi_run_list:
    if result_dict['business_as_usual']:
        bau_ev_cnt.append(result_dict['num_vehicles'])
        bau_station_cnt.append(result_dict['l2_stations'])
        bau_mean_late.append(np.mean(result_dict['departure_deltas']))
    else:
        heur_ev_cnt.append(result_dict['num_vehicles'])
        heur_station_cnt.append(result_dict['l2_stations'])
        heur_mean_late.append(np.mean(result_dict['departure_deltas']))


# x, y = np.linspace(0, 1, sh_0), np.linspace(0, 1, sh_1)
fig = go.Figure(data=[go.Surface(z=heur_mean_late, x=heur_station_cnt, y=heur_station_cnt)])
fig.update_layout(title='Mean Departure Tardiness (minutes)', autosize=False,
                  width=500, height=500,
                  margin=dict(l=65, r=50, b=65, t=90))
fig.show()