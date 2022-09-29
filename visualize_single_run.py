from collections import namedtuple
import os


import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

from src.utils.utils import RuntimeEnvironment


import json


from src.asset_simulator.depot_config.depot_config import AssetDepotConfig
from src.asset_simulator.depot.asset_depot import AssetDepot
from src.demand_simulator.demand_simulator.demand_simulator import DemandSimulator
from src.demand_simulator.demand_simulator_config.demand_simulator_config import DemandSimulatorConfig
from src.heuristic.depot.algo_depot import AlgoDepot
from src.mock_queue.mock_queue import MockQueue
from src.tests.test_reservation_overlap import TestReservationOverlap

"""
# Heuristic Simulator

Choose your parameters for the simulation and hit run!
"""


with st.echo(code_location='below'):
   # run algo

   # setup mock queue
   mock_queue = MockQueue()

   # setup demand_simulator
   script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
   demand_sim_config = 'src/demand_simulator/demand_simulator_config/configs/5days_15min_40res_per_day.json'
   demand_sim_path = os.path.join(script_dir, demand_sim_config)

   with open(demand_sim_path) as f:
      config = json.load(f)


   st.subheader('Simulation Parameters')

   n_days_simulation = st.number_input('# days', 3, 30, value=14)

   if n_days_simulation:
      config['horizon_length_hours'] = n_days_simulation*24

   mean_reservations_per_day = st.number_input("# Reservation Attempts Per Day", 0, 200, value=60)
   mean_walk_ins_per_day = st.number_input("# Walk-Ins Per Day", 0, 200, value=60)

   config['mean_reservations_per_day'] = mean_reservations_per_day
   config['mean_walk_ins_per_day'] = mean_walk_ins_per_day

   demand_simulator_config = DemandSimulatorConfig(**config)
   demand_simulator = DemandSimulator(config=demand_simulator_config, queue=mock_queue)

   # setup asset_simulator
   # asset_sim_config = 'src/asset_simulator/depot_config/configs/150_vehicles_10_L2_2_DCFC.json'
   asset_sim_config = 'src/asset_simulator/depot_config/configs/hiker_9_to_5.json'
   asset_sim_path = os.path.join(script_dir, asset_sim_config)

   with open(asset_sim_path) as f:
      config = json.load(f)


   st.subheader('Vehicles at Depot')

   # allow user to override config with GUI selection
   n_sedans = st.number_input("# sedans", 0, 100, value=20)
   n_suvs = st.number_input("# suvs", 0, 100, value=0)
   n_crossovers = st.number_input("# crossovers", 0, 100, value=0)

   print('before')
   print(config)


   # default the suv and crossover values to 0 for now
   config['vehicles']['suv']['n'] = 0
   config['vehicles']['crossover']['n'] = 0

   if n_sedans:
      config['vehicles']['sedan']['n'] = n_sedans

   if n_suvs:
      config['vehicles']['suv']['n'] = n_suvs

   if n_crossovers:
      config['vehicles']['crossover']['n'] = n_crossovers



   print('after')
   print(config)

   st.subheader('Charging Stations at Depot')

   n_l2_stations = st.number_input("# L2 Stations", 0, 100, value=3)
   l2_max_power = st.number_input("L2 Max Power (kW)", 0, 20, value=7)
   n_dcfc_stations = st.number_input("# DCFC Stations", 0, 100, value=0)
   dcfc_max_power = st.number_input("DCFC Max Power (kw)", 0, 100, value=50)

   if n_l2_stations:
      config['n_l2_stations'] = n_l2_stations

   if n_dcfc_stations:
      config['n_dcfc_stations'] = n_dcfc_stations

   if l2_max_power:
      config['l2_max_power_kw'] = l2_max_power

   if dcfc_max_power:
      config['dcfc_max_power_kw'] = dcfc_max_power



   asset_depot_config = AssetDepotConfig(**config)

   print('config details')
   print(asset_depot_config)

   asset_depot = AssetDepot.build_depot(config=asset_depot_config, queue=mock_queue)
   # asset_depot.initialize_plugins()

   print('num vehicles test 123')
   print(len(asset_depot.vehicles))

   # setup heuristic
   # add a few more algo specific configs
   config['minimum_ready_vehicle_pool'] = {
      'sedan': 2,
      'crossover': 2,
      'suv': 2
   }
   algo_depot_config = AssetDepotConfig(**config)

   algo_depot = AlgoDepot.build_depot(config=asset_depot_config, queue=mock_queue)

   runtime = RuntimeEnvironment(
      mock_queue=mock_queue,
      demand_simulator=demand_simulator,
      asset_simulator=asset_depot,
      heuristic=algo_depot,
      queue=mock_queue
   )

   heuristic = st.checkbox('heuristic (smart charging assignment)', value=True)
   if heuristic:
      random_sort=False
   else:
      random_sort=True

   run = st.button(
      label='run'
   )

   if run:
      chart, df_deltas, reservation_snapshot, veh_res_tracker = runtime.run(random_sort=random_sort)

      denom = len(veh_res_tracker)
      num = len([val for val in veh_res_tracker if val >= 60])


      with st.container():
         'number of late departures: ' + str(num)
         'number of departures: ' + str(denom)
         '% of departures late: ' + str(round(100.0*(num/denom), 2))
         st.plotly_chart(chart, use_container_width=True)
         snapshot = runtime.asset_simulator.reservation_assignment_snapshot
         overlaps, res1, res2 = TestReservationOverlap.assigned_overlaps_exist(snapshot)
         overlaps
         res1
         res2
         snapshot


   print('simulation complete')


