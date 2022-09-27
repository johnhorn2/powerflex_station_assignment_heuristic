from collections import namedtuple
import click
import pickle
import sqlite3

import numpy as np

from src.utils.single_run import single_run


N_REPEATS = 3

L2_STATION_MIN = 1
L2_STATION_MAX = 10
L2_STEPS = 1
L2_STATIONS = np.arange(L2_STATION_MIN, L2_STATION_MAX, L2_STEPS)

VEH_MIN = 5
VEH_MAX = 100
VEH_STEPS = 10
VEHICLES = np.arange(VEH_MIN, VEH_MAX, VEH_STEPS)

DCFC_STATION_MIN = 0
DCFC_STEPS = 1
DCFC_STATION_MAX = 6
DCFC_STATIONS = np.arange(DCFC_STATION_MIN, DCFC_STATION_MAX, DCFC_STEPS)

random_sort_list=[True,False]

for repeat in range(0,N_REPEATS):
    print('Repeat #: ' + str(repeat))
    for random_sort in random_sort_list:
        for veh in VEHICLES:
        # for dcfc_station_count in DCFC_STATIONS:
            for station_count in L2_STATIONS:
                single_run(
                    n_days=14,
                    sedan_count=veh,
                    suv_count=0,
                    crossover_count=0,
                    l2_station_count=station_count,
                    random_sort=random_sort,
                    dcfc_station_count=0,
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

with open('plotter/data_from_prior_runs/old/heuristic_result.pickle', 'wb') as handle:
    pickle.dump(heur_result_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

with open('plotter/data_from_prior_runs/old/bau_result.pickle', 'wb') as handle:
    pickle.dump(bau_result_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
