from collections import namedtuple
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

from src.single_run import single_run

N_REPEATS = 3

L2_STATION_MIN = 1
L2_STATION_MAX = 10
L2_STEPS = 1
# L2_STATIONS = np.linspace(L2_STATION_MIN, L2_STATION_MAX, L2_STEPS, dtype=int)
L2_STATIONS = np.arange(L2_STATION_MIN, L2_STATION_MAX, L2_STEPS)

VEH_MIN = 5
VEH_MAX = 100
VEH_STEPS = 5
VEHICLES = np.linspace(VEH_MIN, VEH_MAX, VEH_STEPS, dtype=int)

DCFC_STATION_MIN = 0
DCFC_STEPS = 1
DCFC_STATION_MAX = 6
# DCFC_STATIONS = np.linspace(DCFC_STATION_MIN, DCFC_STATION_MAX, DCFC_STEPS, dtype=int)
DCFC_STATIONS = np.arange(DCFC_STATION_MIN, DCFC_STATION_MAX, DCFC_STEPS)

# VEHS = np.linspace(VEH_MIN, VEH_MAX, VEH_STEPS, dtype=int)

random_sort_list=[True,False]

output_list = []
for repeat in range(0,N_REPEATS):
    print('Repeat #: ' + str(repeat))
    for random_sort in random_sort_list:
        for veh in VEHICLES:
        # for dcfc_station_count in DCFC_STATIONS:
            for station_count in L2_STATIONS:
                output_list.append(
                    single_run(
                        n_days=14,
                        sedan_count=veh,
                        suv_count=0,
                        crossover_count=0,
                        l2_station_count=station_count,
                        random_sort=random_sort,
                        dcfc_station_count=0
                    )
                )


# we use tuples (ev_cnt, station_cnt) as the key
# Result = namedtuple('Result', ('dcfc_station_cnt', 'station_cnt'))
Result = namedtuple('Result', ('vehicle_cnt', 'station_cnt', 'random_sort'))
bau_result_dict = {}
heur_result_dict = {}


for result_dict in output_list:
    if result_dict['random_sort']:
        # key = Result(result_dict['dcfc_stations'], result_dict['l2_stations'])
        key = Result(result_dict['vehicles'], result_dict['l2_stations'], result_dict['random_sort'])
        try:
            # list instantiated already
            bau_result_dict[key].append(result_dict['departure_deltas'])
        except KeyError:
            # need to initiate list for this new index
            bau_result_dict[key] = []
            bau_result_dict[key].append(result_dict['departure_deltas'])
    else:
        # key = Result(result_dict['dcfc_stations'], result_dict['l2_stations'])
        key = Result(result_dict['vehicles'], result_dict['l2_stations'], result_dict['random_sort'])
        try:
            # list instantiated already
            heur_result_dict[key].append(result_dict['departure_deltas'])
        except KeyError:
            # need to initiate list for this new index
            heur_result_dict[key] = []
            heur_result_dict[key].append(result_dict['departure_deltas'])

with open('plotter/data_from_prior_runs/old/14day_3runs/heuristic_result.pickle', 'wb') as handle:
    pickle.dump(heur_result_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

with open('plotter/data_from_prior_runs/old/14day_3runs/bau_result.pickle', 'wb') as handle:
    pickle.dump(bau_result_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)