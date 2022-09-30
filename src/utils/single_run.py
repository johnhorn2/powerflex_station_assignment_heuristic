import json
import os
import sqlite3

from src.asset_simulator.depot_config.depot_config import AssetDepotConfig
from src.asset_simulator.depot.asset_depot import AssetDepot
from src.demand_simulator.demand_simulator.demand_simulator import DemandSimulator
from src.demand_simulator.demand_simulator_config.demand_simulator_config import DemandSimulatorConfig
from src.heuristic.depot.algo_depot import AlgoDepot
from src.mock_queue.mock_queue import MockQueue

from src.utils.utils import RuntimeEnvironment

def single_run(n_days, sedan_count, suv_count, crossover_count, l2_station_count, dcfc_station_count, random_sort, asset_config, write_results=True):

    print('running with veh_count: ' + str(sedan_count) + ' and l2_station_count: ' + str(l2_station_count))
    # setup mock queue
    mock_queue = MockQueue()

    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    demand_sim_config = '../demand_simulator/demand_simulator_config/configs/5days_15min_40res_per_day.json'
    demand_sim_path = os.path.join(script_dir, demand_sim_config)

    # setup demand_simulator
    with open(demand_sim_path) as f:
        demand_sim_config = json.load(f)

        demand_sim_config['horizontal_length_hours'] = n_days * 24

        demand_simulator_config = DemandSimulatorConfig(**demand_sim_config)
        demand_simulator = DemandSimulator(config=demand_simulator_config, queue=mock_queue)

        # setup asset_simulator
        asset_sim_config = '../asset_simulator/depot_config/configs/' + asset_config
        asset_sim_path = os.path.join(script_dir, asset_sim_config)

        with open(asset_sim_path) as f:
            asset_sim_config = json.load(f)

        # override params
        asset_sim_config['vehicles']['sedan']['n'] = sedan_count
        asset_sim_config['vehicles']['suv']['n'] = suv_count
        asset_sim_config['vehicles']['crossover']['n'] = crossover_count
        asset_sim_config['n_l2_stations'] = l2_station_count
        asset_sim_config['n_dcfc_stations'] = dcfc_station_count

        asset_depot_config = AssetDepotConfig(**asset_sim_config)
        asset_depot = AssetDepot.build_depot(config=asset_depot_config, queue=mock_queue)
        # asset_depot.initialize_plugins()

        # setup heuristic
        # add a few more algo specific configs
        asset_sim_config['minimum_ready_vehicle_pool'] = {
            'sedan': 2,
            'crossover': 2,
            'suv': 2
        }
        algo_depot_config = AssetDepotConfig(**asset_sim_config)

        algo_depot = AlgoDepot.build_depot(config=algo_depot_config, queue=mock_queue)


        runtime = RuntimeEnvironment(
            mock_queue=mock_queue,
            demand_simulator=demand_simulator,
            asset_simulator=asset_depot,
            heuristic=algo_depot,
            queue=mock_queue
        )

        # departure deltas in minutes
        results = runtime.run(plot_output=False, random_sort=random_sort)

        if write_results:

            con = sqlite3.connect('test.db')
            cur = con.cursor()
            cur.execute("""
            CREATE TABLE IF NOT EXISTS late_departures(
                departure_id INTEGER PRIMARY KEY,
                random_sort INTEGER NOT NULL,
                vehicles INTEGER,
                l2_station INTEGER,
                departure_deltas REAL,
                n_dcfc INTEGER
            )
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS power_stats(
                sim_id INTEGER PRIMARY KEY,
                random_sort INTEGER NOT NULL,
                n_dcfc INTEGER,
                l2_station INTEGER,
                vehicles INTEGER,
                max_power REAL,
                min_power REAL,
                avg_power REAL 
            )
            """)


            cur.execute("""
            CREATE TABLE IF NOT EXISTS hourly_power_stats(
                sim_id INTEGER PRIMARY KEY,
                random_sort INTEGER NOT NULL,
                n_dcfc INTEGER,
                l2_station INTEGER,
                vehicles INTEGER,
                meter_power_kw REAL,
                datetime DATETIME
            )
            """)




            sql_template = """INSERT INTO late_departures(random_sort, vehicles, l2_station, departure_deltas, n_dcfc) VALUES({random_sort}, {vehicles}, {l2_stations}, {departure_delta}, {n_dcfc});"""

            # cycle through each delta
            for departure_delta in results:
                sql_formatted = sql_template.format(
                    random_sort=random_sort,
                    vehicles=sedan_count,
                    l2_stations=l2_station_count,
                    departure_delta=departure_delta,
                    n_dcfc=dcfc_station_count
                )

                cur.execute(sql_formatted)

            # mark the max power draw at a given point in time
            list_of_power_measures = [kw for kw in asset_depot.power_snapshot.values()]
            max_instant_power = max(list_of_power_measures)
            min_instant_power = min(list_of_power_measures)
            avg_instant_power = sum(list_of_power_measures)/len(list_of_power_measures)

            sql_template = """INSERT INTO power_stats(random_sort, n_dcfc, l2_station, vehicles, max_power, min_power, avg_power) VALUES({random_sort}, {n_dcfc}, {l2_stations}, {vehicles}, {max_power}, {min_power}, {avg_power});"""
            sql_formatted = sql_template.format(
                random_sort=random_sort,
                n_dcfc=dcfc_station_count,
                l2_stations=l2_station_count,
                vehicles=sedan_count,
                max_power=max_instant_power,
                min_power=min_instant_power,
                avg_power=avg_instant_power
            )
            cur.execute(sql_formatted)


            sql_template = """INSERT INTO hourly_power_stats(random_sort, n_dcfc, l2_station, vehicles, meter_power_kw, datetime) VALUES({random_sort}, {n_dcfc}, {l2_stations}, {vehicles}, {meter_power_kw}, '{datetime}');"""
            for datetime, meter_power_kw in asset_depot.power_snapshot.items():
                sql_formatted = sql_template.format(
                    random_sort=random_sort,
                    n_dcfc=dcfc_station_count,
                    l2_stations=l2_station_count,
                    vehicles=sedan_count,
                    meter_power_kw=meter_power_kw,
                    datetime=datetime
                )
                cur.execute(sql_formatted)

            con.commit()


        print('simulation complete')


if __name__ == '__main__':
    n_days = 14
    sedan_count = 85
    suv_count = 0
    crossover_count = 0
    l2_station_count = 33
    dcfc_station_count = 5
    random_sort = 0
    asset_config = 'hiker_9_to_5.json'
    single_run(n_days, sedan_count, suv_count, crossover_count, l2_station_count, dcfc_station_count, random_sort, asset_config, write_results=True)
