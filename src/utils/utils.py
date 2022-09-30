import pandas as pd
from pydantic import BaseModel
import sqlite3

from src.asset_simulator.depot.asset_depot import AssetDepot
from src.demand_simulator.demand_simulator.demand_simulator import DemandSimulator
from src.heuristic.depot.algo_depot import AlgoDepot
from src.mock_queue.mock_queue import MockQueue
from src.plotter.plotter import Plotter


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
        df_actual_departures['departure_delta_minutes'] = df_actual_departures['actual_departure_datetime'] - df_actual_departures['scheduled_departure_datetime']
        df_actual_departures['departure_delta_minutes'] = pd.to_timedelta(df_actual_departures['departure_delta_minutes'])/pd.Timedelta('60s')

        flat_list_results = []
        for veh_key, veh_res_list in self.asset_simulator.reservation_assignment_snapshot.items():
            # we need to exclude non-vehicle assignments
            if veh_key != None:
                for res in veh_res_list:
                    # find the corresponding item in the dataframe
                    delta_minutes = df_actual_departures.loc[(df_actual_departures['vehicle_id'] == veh_key) & (df_actual_departures['reservation_id'] == res.id)]['departure_delta_minutes'].values

                    if len(delta_minutes) > 0:
                        delta_minutes = delta_minutes[0]
                    elif len(delta_minutes) == 0:
                        # if the departure never occured we default to a large delta minutes departure for tracking
                        # NOTE: use delta from current_timestamp and prior
                        delta_minutes = self.asset_simulator.current_datetime - res.departure_timestamp_utc
                        delta_minutes = delta_minutes.total_seconds()/60

                    flat_list_results.append(delta_minutes)


        if plot_output:
            plot = Plotter()
            soc_chart = plot.get_soc_timeseries(
                df_soc,
                df_status,
                self.asset_simulator.reservation_assignment_snapshot,
                self.asset_simulator.move_charge_snapshot,
                self.asset_simulator.fleet_manager.station_fleet
            )
            # departure_delta_minutes = (pd.to_timedelta(df_actual_departures['departure_delta_minutes'])/pd.Timedelta('60s')).tolist()
            # return (soc_chart, departure_delta_minutes)
            return (soc_chart, df_actual_departures, self.asset_simulator.reservation_assignment_snapshot, flat_list_results)

        if plot_output == False:
            # departure_delta_minutes = df_actual_departures['departure_delta_minutes'].tolist()
            # return departure_delta_minutes
            return flat_list_results