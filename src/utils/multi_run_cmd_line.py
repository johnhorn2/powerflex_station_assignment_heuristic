import os
from collections import namedtuple
import click
import pickle

import numpy as np

from src.utils.single_run import single_run

# we use tuples (ev_cnt, station_cnt) as the key
Result = namedtuple('Result', ('vehicle_cnt', 'station_cnt', 'random_sort', 'n_dcfc'))

@click.command()
@click.option('--random_sort', default=False, help='disable the heuristic for random charging station assignment')
@click.option('--n_days', default=14, help='number of days in the simulation')
@click.option('--n_repeats', default=3, help='number of repeats at every coordinate of # evs and # L2 EVSE')
@click.option('--l2_station_min', default=1, help='min number of L2 EVSEs simulated')
@click.option('--l2_station_max', default=40, help='max number of L2 EVSEs simulated')
@click.option('--l2_steps', default=2, help='increment # L2 stations by this interval')
@click.option('--veh_min', default=5, help='min number of vehs simulated')
@click.option('--veh_max', default=100, help='max number of vehs simulated')
@click.option('--veh_steps', default=10, help='increment number of vehs simulated by step size')
@click.option('--n_dcfc', default=1, help='number of dcfc stations')
@click.option('--output_file_name', default='default_result', help='name of output pickle file')
def run(random_sort, n_days, n_repeats, l2_station_min, l2_station_max, l2_steps, veh_min, veh_max, veh_steps, n_dcfc, output_file_name):

    L2_STATIONS = np.arange(l2_station_min, l2_station_max, l2_steps)
    VEHICLES = np.arange(veh_min, veh_max, veh_steps)

    config_settings = \
    'random_sort_' + str(random_sort) + \
    '_n_days_' + str(n_days) + \
    '_n_repeats_' + str(n_repeats) + \
    '_n_veh_min_' + str(veh_min) + \
    '_n_veh_max_' + str(veh_max) + \
    '_n_l2_min_' + str(l2_station_min) + \
    '_n_l2_max_' + str(l2_station_max) + \
    '_n_dcfc_' + str(n_dcfc)
    click.echo('Running on: ' + config_settings)

    if output_file_name == 'default_result':
        output_file_name = config_settings


    veh_runs = len(VEHICLES)
    station_runs = len(L2_STATIONS)

    total_combos = veh_runs * station_runs * n_repeats

    output_list = []
    with click.progressbar(length=total_combos) as bar:
        for repeat in range(0,n_repeats):
            print('Repeat #: ' + str(repeat))
            for veh in VEHICLES:
                for station_count in L2_STATIONS:
                    bar.update(1)

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


    result_dict = {}


    for result_dict in output_list:
        key = Result(result_dict['vehicles'], result_dict['l2_stations'], result_dict['random_sort'], result_dict['n_dcfc'])
        try:
            # list instantiated already
            result_dict[key].append(result_dict['departure_deltas'])
        except KeyError:
            # need to initiate list for this new index
            result_dict[key] = []
            result_dict[key].append(result_dict['departure_deltas'])

    cwd = os.getcwd()
    target = 'src/plotter/data_from_prior_runs/old/' + output_file_name + '.pickle'
    path = os.path.join(cwd,target)
    with open(path, 'wb') as handle:
        pickle.dump(result_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':
    run()

