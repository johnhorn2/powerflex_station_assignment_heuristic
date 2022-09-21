import pandas as pd
from pydantic import BaseModel

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