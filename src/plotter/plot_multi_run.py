from collections import namedtuple
import pickle

import numpy as np
import plotly.graph_objects as go

Result = namedtuple('Result', ('vehicle_cnt', 'station_cnt', 'random_sort'))

with open('data_from_prior_runs/old/14day_3runs/heuristic_result.pickle', 'rb') as handle:
    heuristic_raw_results = pickle.load(handle)

with open('data_from_prior_runs/old/14day_3runs/bau_result.pickle', 'rb') as handle:
    bau_raw_results = pickle.load(handle)

for keys in heuristic_raw_results.keys():
    x = keys._fields[0]
    y = keys._fields[1]

# process the output for 3d plotting
heuristic = {}
heuristic[x] = []
heuristic[y] = []
heuristic['pct_hour_late'] = []

bau = {}
bau[x] = []
bau[y] = []
bau['pct_hour_late'] = []


# need to find the average of all the entries in the values and assign to a list
for keys, values in heuristic_raw_results.items():
    heuristic[x].append(getattr(keys,x))
    heuristic[y].append(getattr(keys,y))
    flat_list = [item for sublist in values for item in sublist]

    list_of_1_hour_tardy = [dept for dept in flat_list if dept >= 60]
    pct_tardy = 100.0*len(list_of_1_hour_tardy) / len(flat_list)
    heuristic['pct_hour_late'].append(pct_tardy)

    # heuristic['pct_hour_late'].append(np.max(flat_list))

for keys, values in bau_raw_results.items():
    bau[x].append(getattr(keys,x))
    bau[y].append(getattr(keys,y))
    flat_list = [item for sublist in values for item in sublist]

    list_of_1_hour_tardy = [dept for dept in flat_list if dept >= 60]
    pct_tardy = 100.0*len(list_of_1_hour_tardy) / len(flat_list)
    bau['pct_hour_late'].append(pct_tardy)
    # bau['pct_hour_late'].append(np.max(flat_list))

# L2_STATION_MIN = 1
# L2_STATION_MAX = 15
# L2_STEPS = 1
# L2_STATIONS = np.arange(L2_STATION_MIN, L2_STATION_MAX, L2_STEPS)

# VEH_MIN = 5
# VEH_MAX = 30
# VEH_STEPS = 5
# VEHICLES = np.linspace(VEH_MIN, VEH_MAX, VEH_STEPS, dtype=int)

L2_STATION_MIN = 1
L2_STATION_MAX = 10
L2_STEPS = 1
# L2_STATIONS = np.linspace(L2_STATION_MIN, L2_STATION_MAX, L2_STEPS, dtype=int)
L2_STATIONS = np.arange(L2_STATION_MIN, L2_STATION_MAX, L2_STEPS)

VEH_MIN = 5
VEH_MAX = 100
VEH_STEPS = 5
VEHICLES = np.linspace(VEH_MIN, VEH_MAX, VEH_STEPS, dtype=int)




# new_shape = (len(L2_STATIONS), len(VEHICLES))
new_shape = ( len(VEHICLES), len(L2_STATIONS))
heuristic_result = np.reshape(heuristic['pct_hour_late'], newshape=(new_shape))
bau_result = np.reshape(bau['pct_hour_late'], newshape=new_shape)


# fig = go.Figure(data=[go.Surface(z=heuristic_result, x=L2_STATIONS, y=VEHICLES)])
fig = go.Figure(data=[

    go.Surface(z=bau_result, x=L2_STATIONS, y=VEHICLES, opacity=0.3),
    go.Surface(z=heuristic_result, x=L2_STATIONS, y=VEHICLES, opacity=0.3)],


)
fig.update_layout(title='Percent Hour Late',autosize=True,
                  width=500, height=500,
                  margin=dict(l=65, r=50, b=65, t=90),
                  )
fig.update_layout(scene = dict(
                    xaxis_title='# L2 Stations',
                    yaxis_title='# vehicles',
                    zaxis_title='Pct Hour Late'),
                    width=700,
                    margin=dict(r=20, b=10, l=10, t=10))

fig.show()