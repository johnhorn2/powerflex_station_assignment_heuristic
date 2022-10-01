import streamlit as st

import src.building.building
from src.plotter.plotter import Plotter

from src.plotter.plotter_data import get_departure_kpis, get_power_stats, get_hourly_power_stats
from src.building.building import BuildingUtils

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

    n_dcfc = st.slider('# DC Fast Chargers', 0, 5, value=0)
    late_minute_threshold_slider = 60*st.number_input(label='# Hours = Late', min_value=0.25, max_value=24.0, value=0.5, step=0.15)
    heuristic = True

    heuristic = st.checkbox('Heuristic', value=True)

    if heuristic:
        random_sort = False
    else:
        random_sort = True

    target_dcfc = 0
    late_minute_threshold = 60

    if n_dcfc:
        target_dcfc = n_dcfc

    if late_minute_threshold_slider:
        # KPI Plot
        late_minute_threshold= late_minute_threshold_slider

        df_kpis = get_departure_kpis(late_minute_threshold=late_minute_threshold)
        df_kpis_filtered = df_kpis[(df_kpis['n_dcfc'] == target_dcfc) & (df_kpis['random_sort'] == random_sort)]
        fig_kpi = Plotter.get_kpi_3d_surface_figure(df_kpis_filtered)

        # Power Plot
        df_power_stats = get_power_stats()
        df_power_stats_filtered = df_power_stats[(df_power_stats['n_dcfc'] == target_dcfc) & (df_power_stats['random_sort'] == random_sort)]
        df_power_max = df_power_stats_filtered.groupby(['vehicles', 'l2_station'])['max_power'].max().reset_index()
        fig_power, x, y, z = Plotter.get_power_3d_surface_figure(df_power_max)




        with st.container():
            st.plotly_chart(fig_kpi)
            st.plotly_chart(fig_power)

        with st.container():
            n_l2_stations = st.select_slider(label='# L2 Stations', options=x, value=15)
            n_vehicles = st.select_slider(label='# EVs', options=y, value=15)

            county = st.text_input(label='County Name', value='San Diego')
            building_types = {
                'Full Service Restaurant': 'fullservicerestaurant',
                'Hospital': 'hospital',
                'Large Hotel': 'largehotel',
                'Large Office': 'largeoffice',
                'Medium Office': 'mediumoffice',
                'Out Patient': 'outpatient',
                'Primary School': 'primaryschool',
                'Quick Service Restaurant': 'quickservicerestaurant',
                'Retail Stand Alone': 'retailstandalone',
                'Retail Strip Mall': 'retailstripmall',
                'Secondary School': 'secondaryschool',
                'Small Hotel': 'smallhotel',
                'Small Office': 'smalloffice',
                'Warehouse': 'warehouse'
            }
            display_bldg_type = st.selectbox(label='Building Type', options=list(building_types.keys()))
            bldg_type_value = building_types[display_bldg_type]

            sqft = st.number_input(label='Building SQFT', value=8000)

            df_bldg_profile = BuildingUtils.get_bldg_load(county, bldg_type_value, sqft)

            # Hourly Plot
            n_dcfc = target_dcfc
            df_hourly_power = get_hourly_power_stats()
            fig_hourly_power = Plotter.get_hourly_power_bar_chart(df_hourly_power, random_sort, n_dcfc, n_l2_stations, n_vehicles)

            st.plotly_chart(fig_hourly_power)
