from collections import namedtuple
import os
import re


import pandas as pd
import streamlit as st
import pickle

import numpy as np
import plotly.graph_objects as go

st.set_page_config(layout="wide")

with st.echo(code_location='below'):

    """
    # Station Recommender

    Given your:
    - Fleet
    - Driving Schedule
    - KPI Thresholds

    We show you what charging station strategies are optimal
    """


    #--------- Load Data ------

    Result = namedtuple('Result', ('vehicle_cnt', 'station_cnt', 'random_sort', 'n_dcfc'))

    n_dcfc = st.slider('# DC Fast Chargers', 0, 5, value=0)

    # Load everything in memory before hand
    file_list = [
        'random_sort_False_n_days_14_n_repeats_3_n_veh_min_5_n_veh_max_100_n_l2_min_1_n_l2_max_40_n_dcfc_0',
        'random_sort_False_n_days_14_n_repeats_3_n_veh_min_5_n_veh_max_100_n_l2_min_1_n_l2_max_40_n_dcfc_1',
        'random_sort_False_n_days_14_n_repeats_3_n_veh_min_5_n_veh_max_100_n_l2_min_1_n_l2_max_40_n_dcfc_2',
        'random_sort_False_n_days_14_n_repeats_3_n_veh_min_5_n_veh_max_100_n_l2_min_1_n_l2_max_40_n_dcfc_3',
        'random_sort_False_n_days_14_n_repeats_3_n_veh_min_5_n_veh_max_100_n_l2_min_1_n_l2_max_40_n_dcfc_4',
        'random_sort_False_n_days_14_n_repeats_3_n_veh_min_5_n_veh_max_100_n_l2_min_1_n_l2_max_40_n_dcfc_5'
    ]

    def read_file(file_path):

        base = os.getcwd()
        path = os.path.join(base, 'src/plotter/data_from_prior_runs/old/archive/' + file_path + '.pickle')

        with open(path, 'rb') as handle:
            results = pickle.load(handle)

        return results

    # def add_results_to_existing_dict(global_result_dict, results):
        # for key, val in results.items():
        #     try:
        #         assumes key is initialized
                # global_result_dict[key].append(val)

    # def extract_params_from_file_name(file_name):
    #     random_sort = re.search('random_sort_(.+?)_n_days', file_name).group(1)
    #     n_days = re.search('_n_days_(.+?)_n_repeats', file_name).group(1)
    #     n_repeats = re.search('_n_repeats_(.+?)_n_veh', file_name).group(1)
    #     n_dcfc = re.search('n_dcfc_(.+?)', file_name).group(1)
    #
    #     return random_sort, n_days, n_repeats, n_dcfc

    # def process_files(file_list):
        # global_result_dict = {}
        # for file in file_list:
        #     random_sort, n_days, n_repeats, n_dcfc = extract_params_from_file_name(file)
        #     results = read_file(file)

    # result_list = []
    # for file in file_list:
    #     result_list.append(read_file(file))
    #
    # global_dict = {}
    # for d in result_list:
    #     global_dict.update(d)


    # uniq_keys = list(str([key for key in global_dict.keys()]))
    # keys = [key for key in global_dict.keys()]

    d = read_file(file_list[0])


    # ----------------  create a figure
    def filter_results(results, random_sort=False, n_days=14, n_repeats=3, n_dcfc=0):
        filtered_results = {key:val for key, val in results.items() if (
            key.random_sort == random_sort and
            key.n_days == n_days and
            key.n_repeats == n_repeats and
            key.n_dcfc == n_dcfc
        )
                            }

        return filtered_results

    def prep_figure(results):

        # Prep Z for Heuristic
        heuristic_flat_dict = {}


        for keys, values in results.items():
        #     print(values)
            heuristic_flat_dict[keys] =  [item for sublist in values['departure_deltas'] for item in sublist]


        heuristic_kpi_dict = {}
        for keys, values in heuristic_flat_dict.items():
            list_of_1_hour_tardy = [dept for dept in values if dept >= 60]
            pct_tardy = 100.0*len(list_of_1_hour_tardy) / len(values)
            heuristic_kpi_dict[keys] = pct_tardy

        ev_cnt_ordered_list = []
        evse_cnt_ordered_list = []
        for keys in heuristic_kpi_dict.keys():
            ev_cnt_ordered_list.append(keys.vehicle_cnt)
            evse_cnt_ordered_list.append(keys.station_cnt)

        ev_cnt_ordered_list = sorted(list(set(ev_cnt_ordered_list)))
        evse_cnt_ordered_list = sorted(list(set(evse_cnt_ordered_list)))

        # assume evse_cnt is x and ev_cnt is y, z will be the KPI
        # so shape would be len(evse_cnt_ordered_list) x len(ev_cnt_ordered_list)
        evse_dim = len(evse_cnt_ordered_list)
        ev_dim = len(ev_cnt_ordered_list)
        new_shape = (evse_dim, ev_dim)

        # ---------------------------------------

        z = np.ones(new_shape)

        for evse_idx in range(0,evse_dim):
            for ev_idx in range(0, ev_dim):
                evse_key = evse_cnt_ordered_list[evse_idx]
                ev_key = ev_cnt_ordered_list[ev_idx]
                heur_key = Result(vehicle_cnt=ev_key, station_cnt=evse_key, random_sort=False)
                bau_key = Result(vehicle_cnt=ev_key, station_cnt=evse_key, random_sort=True)
                z[evse_idx,ev_idx]= heuristic_kpi_dict[heur_key]


        x = sorted(evse_cnt_ordered_list, reverse=True)
        y = sorted(ev_cnt_ordered_list, reverse=True)

        fig = go.Figure(data=[
            go.Surface(z=z, x=x, y=y, opacity=1.0,
            hovertemplate = "EVSE cnt: %{x}" + "<br>EV cnt: %{y}" + "<br>%{z:.2f}% Late Departures"),
            ],

        )
        fig.update_layout(title='Percent Hour Late',autosize=True,
                          width=500, height=500,
                          margin=dict(l=65, r=50, b=65, t=90),
                          )
        fig.update_layout(scene = dict(
                            xaxis_title='# EVSE',
                            yaxis_title='# EV',
                            zaxis_title='Pct Hour Late'),
                            width=700,
                            margin=dict(r=20, b=10, l=10, t=10))

        # fig.show()
        return fig


    # filtered_results = filter_results(global_dict, n_dcfc=2)
    # fig = prep_figure(filtered_results)

    # ---------------  Make UI
    # n = len(d)
    vals = d.values()

    run = st.button(
      label='run'
    )

    if run:
        with st.container():
            vals
            # n
            # n_dcfc
            # global_dict
            # uniq_keys
            # keys
            # list_of_dicts
            # results = vis_n_dcfc(n_dcfc)
            # results
            # st.plotly_chart(fig, use_container_width=True)






