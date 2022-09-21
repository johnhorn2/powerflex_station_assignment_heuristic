from collections import namedtuple
import os
import pickle

import numpy as np
import plotly.graph_objects as go

Result = namedtuple('Result', ('vehicle_cnt', 'station_cnt', 'random_sort'))

base = os.getcwd()
heur_path = 'heuristic_result.pickle'
full_path_heur = os.path.join(base, heur_path)
random_path = 'heuristic_result.pickle'
full_path_random = os.path.join(base, random_path)

with open(full_path_heur, 'rb') as handle:
    heuristic_raw_results = pickle.load(handle)

with open(full_path_random, 'rb') as handle:
    bau_raw_results = pickle.load(handle)

for keys in heuristic_raw_results.keys():
    x = keys._fields[0]
    y = keys._fields[1]

# process the output for 3d plotting
heuristic = {}
heuristic[x] = []
heuristic[y] = []
heuristic['mean_tardiness'] = []

bau = {}
bau[x] = []
bau[y] = []
bau['mean_tardiness'] = []


# need to find the average of all the entries in the values and assign to a list
for keys, values in heuristic_raw_results.items():
    heuristic[x].append(getattr(keys,x))
    heuristic[y].append(getattr(keys,y))
    flat_list = [item for sublist in values for item in sublist]
    heuristic['mean_tardiness'].append(np.mean(flat_list))

for keys, values in bau_raw_results.items():
    bau[x].append(getattr(keys,x))
    bau[y].append(getattr(keys,y))
    flat_list = [item for sublist in values for item in sublist]
    bau['mean_tardiness'].append(np.mean(flat_list))

x_dims = list(set(bau[x]))
y_dims = list(set(bau[y]))

new_shape = (len(x_dims), len(y_dims))
heuristic_result = np.reshape(heuristic['mean_tardiness'], newshape=(new_shape))
bau_result = np.reshape(bau['mean_tardiness'], newshape=new_shape)


fig = go.Figure(data=[go.Surface(z=heuristic_result, x=x_dims, y=y_dims)])
fig.update_layout(title='Mean Departure Tardiness (minutes)',autosize=True,
                  width=500, height=500,
                  margin=dict(l=65, r=50, b=65, t=90),
                  )
fig.update_layout(scene = dict(
                    xaxis_title=x,
                    yaxis_title=y,
                    zaxis_title='Avg Minutes Late for Deptarture'),
                    width=700,
                    margin=dict(r=20, b=10, l=10, t=10))

fig.show()
