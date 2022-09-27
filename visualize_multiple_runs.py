from collections import namedtuple
import os
import re


import pandas as pd
import streamlit as st
import sqlite3
import pickle

import numpy as np
import pandas as pd
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

    n_dcfc = st.slider('# DC Fast Chargers', 0, 5, value=0)
    late_minute_threshold_slider = 60*st.number_input(label='# Hours = Late', min_value=0.25, max_value=24.0, value=0.5, step=0.15)

    def get_data(late_minute_threshold):
        con = sqlite3.connect('test.db')
        cur = con.cursor()
        sql = """
        with aggs as
        (
            select
                random_sort,
                n_dcfc,
                vehicles,
                l2_station,
                CAST(count(1) AS REAL) as total_cnt,
                CAST(
                    sum(
                        case when departure_deltas >= {late_minute_threshold}
                        then 1
                        else 0
                        end
                    ) AS REAL)
                     as late_cnt
                    
        from
            results
        group by
            1, 2, 3, 4
        ) 
        select 
            random_sort,
            n_dcfc,
            vehicles,
            l2_station,
            100.0*(late_cnt / total_cnt) as pct_late
        from aggs;
        """
        sql_formatted = sql.format(late_minute_threshold=late_minute_threshold)
        df = pd.read_sql_query(sql_formatted, con)

        return df


    def prep_figure(df_results):

        # Prep Z for Heuristic
        ev_cnt_ordered_list = sorted(df_results.vehicles.unique())
        evse_cnt_ordered_list = sorted(df_results.l2_station.unique())


        evse_dim = len(evse_cnt_ordered_list)
        ev_dim = len(ev_cnt_ordered_list)
        new_shape = (evse_dim, ev_dim)

        # ---------------------------------------

        z = np.ones(new_shape)

        for evse_idx in range(0,evse_dim):
            for ev_idx in range(0, ev_dim):
                evse_val = evse_cnt_ordered_list[evse_idx]
                ev_val = ev_cnt_ordered_list[ev_idx]

                z_val = df_results[(df_results['l2_station'] == evse_val) & (df_results['vehicles'] == ev_val)].pct_late.values
                z[evse_idx,ev_idx]= z_val

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
                            margin=dict(r=20, b=10, l=10, t=10),
        )

        fig.update_layout(scene = dict (
                            zaxis = dict(range=[0,100],))

        )

        return fig


    target_dcfc = 0
    late_minute_threshold = 60

    if n_dcfc:
        target_dcfc = n_dcfc

    if late_minute_threshold_slider:
        late_minute_threshold= late_minute_threshold_slider

        df_result = get_data(late_minute_threshold=late_minute_threshold)
        random_sort = 0
        df_filtered = df_result[(df_result['n_dcfc'] == target_dcfc) & (df_result['random_sort'] == random_sort)]
        fig = prep_figure(df_filtered)

        with st.container():
            fig

    df_result = get_data(late_minute_threshold=late_minute_threshold)
    random_sort = 0


    df_filtered = df_result[(df_result['n_dcfc'] == target_dcfc) & (df_result['random_sort'] == random_sort)]
    fig = prep_figure(df_filtered)

