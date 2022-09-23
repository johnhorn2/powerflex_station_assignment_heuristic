from collections import namedtuple
import click
import pickle

import numpy as np

from src.utils.single_run import single_run

@click.command()
@click.option('--random_sort', default=False, help='disable the heuristic for random charging station assignment')
@click.option('--n_days', default=14, help='number of days in the simulation')
@click.option('--n_repeats', default=3, help='number of repeats at every coordinate of # evs and # L2 EVSE')
@click.option('--l2_station_min', default=1, help='min number of L2 EVSEs simulated')
@click.option('--l2_station_max', default=40, help='max number of L2 EVSEs simulated')
@click.option('--l2_steps', default = 2, help='increment # L2 stations by this interval')
@click.option('--veh_min', default = 5, help='min number of vehs simulated')
@click.option('--veh_max', default = 100, help='max number of vehs simulated')
@click.option('--veh_steps', default = 10, help='increment number of vehs simulated by step size')
@click.option('--n_dcfc', default = 0, help='number of dcfc stations')
@click.option('--output_file_name', help='name of output pickle file')
def run(random_sort, n_days, n_repeats, l2_station_min, l2_station_max, l2_steps, veh_min, veh_max, veh_steps, n_dcfc):

    L2_STATIONS = np.arange(l2_station_min, l2_station_max, l2_steps)
    VEHICLES = np.arange(veh_min, veh_max, veh_steps)

    output_list = []
    for repeat in range(0,n_repeats):
        print('Repeat #: ' + str(repeat))
        for veh in VEHICLES:
            for station_count in L2_STATIONS:
                output_list.append(
                    single_run(
                        n_days=n_days,
                        sedan_count=veh,
                        suv_count=0,
                        crossover_count=0,
                        l2_station_count=station_count,
                        random_sort=random_sort,
                        dcfc_station_count=n_dcfc,
                        asset_config='hiker_9_to_5.json'
                    )
                )


    # we use tuples (ev_cnt, station_cnt) as the key
    # Result = namedtuple('Result', ('dcfc_station_cnt', 'station_cnt'))
    Result = namedtuple('Result', ('vehicle_cnt', 'station_cnt', 'random_sort', 'n_dcfc'))
    result_dict = {}


    for result_dict in output_list:
        if result_dict['random_sort']:
            key = Result(result_dict['vehicles'], result_dict['l2_stations'], result_dict['random_sort'], result_dict['n_dcfc'])
            try:
                # list instantiated already
                result_dict[key].append(result_dict['departure_deltas'])
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

if __name__ == '__main__':
    run()

