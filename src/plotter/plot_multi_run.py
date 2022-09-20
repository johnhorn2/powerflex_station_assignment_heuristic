from collections import namedtuple
import pickle

import numpy as np
import plotly.graph_objects as go

Result = namedtuple('Result', ('dcfc_station_cnt', 'station_cnt'))

with open('data_from_prior_runs/heuristic_result.pickle', 'rb') as handle:
    heuristic_raw_results = pickle.load(handle)

with open('data_from_prior_runs/bau_result.pickle', 'rb') as handle:
    bau_raw_results = pickle.load(handle)

# process the output for 3d plotting
heuristic = {}
heuristic['dcfc_station_cnt'] = []
heuristic['station_cnt'] = []
heuristic['mean_tardiness'] = []

bau = {}
bau['dcfc_station_cnt'] = []
bau['station_cnt'] = []
bau['mean_tardiness'] = []


# need to find the average of all the entries in the values and assign to a list
for keys, values in heuristic_raw_results.items():
    heuristic['dcfc_station_cnt'].append(keys.dcfc_station_cnt)
    heuristic['station_cnt'].append(keys.station_cnt)
    flat_list = [item for sublist in values for item in sublist]
    heuristic['mean_tardiness'].append(np.mean(flat_list))

for keys, values in heuristic_raw_results.items():
    bau['dcfc_station_cnt'].append(keys.dcfc_station_cnt)
    bau['station_cnt'].append(keys.station_cnt)
    flat_list = [item for sublist in values for item in sublist]
    bau['mean_tardiness'].append(np.mean(flat_list))

L2_STATION_MIN = 1
L2_STATION_MAX = 15
L2_STEPS = 1
L2_STATIONS = np.arange(L2_STATION_MIN, L2_STATION_MAX, L2_STEPS)


DCFC_STATION_MIN = 0
DCFC_STEPS = 1
DCFC_STATION_MAX = 6
DCFC_STATIONS = np.arange(DCFC_STATION_MIN, DCFC_STATION_MAX, DCFC_STEPS)

new_shape = (len(L2_STATIONS), len(DCFC_STATIONS))
heuristic_result = np.reshape(heuristic['mean_tardiness'], newshape=(new_shape))
bau_result = np.reshape(bau['mean_tardiness'], newshape=new_shape)


fig = go.Figure(data=[go.Surface(z=heuristic_result, x=L2_STATIONS, y=DCFC_STATIONS)])
fig.update_layout(title='Mean Departure Tardiness (minutes)',autosize=True,
                  width=500, height=500,
                  margin=dict(l=65, r=50, b=65, t=90),
                  )
fig.update_layout(scene = dict(
                    xaxis_title='# L2 Stations',
                    yaxis_title='# DCFC Stations',
                    zaxis_title='Avg Minutes Late for Deptarture'),
                    width=700,
                    margin=dict(r=20, b=10, l=10, t=10))

fig.show()