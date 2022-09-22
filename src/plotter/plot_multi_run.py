from collections import namedtuple
import pickle

import numpy as np
import plotly.graph_objects as go

Result = namedtuple('Result', ('vehicle_cnt', 'station_cnt', 'random_sort'))

# with open('data_from_prior_runs/old/14day_3runs_business_hours_move_at_100pct/heuristic_result.pickle', 'rb') as handle:
# with open('data_from_prior_runs/old/14day_3runs_all_hours_move_at_100pct/heuristic_result.pickle', 'rb') as handle:
with open('data_from_prior_runs/old/14day_3runs_all_hours_move_at_80pct/heuristic_result.pickle', 'rb') as handle:
# with open('data_from_prior_runs/old/14day_3runs/heuristic_result.pickle', 'rb') as handle:
    heuristic_raw_results = pickle.load(handle)

# with open('data_from_prior_runs/old/14day_3runs_business_hours_move_at_100pct/bau_result.pickle', 'rb') as handle:
# with open('data_from_prior_runs/old/14day_3runs_all_hours_move_at_100pct/bau_result.pickle', 'rb') as handle:
with open('data_from_prior_runs/old/14day_3runs_all_hours_move_at_80pct/bau_result.pickle', 'rb') as handle:
# with open('data_from_prior_runs/old/14day_3runs/bau_result.pickle', 'rb') as handle:
    bau_raw_results = pickle.load(handle)


heuristic_flat_dict = {}

for keys, values in heuristic_raw_results.items():
    heuristic_flat_dict[keys] =  [item for sublist in values for item in sublist]

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

z = np.ones(new_shape)

for evse_idx in range(0,evse_dim):
    for ev_idx in range(0, ev_dim):
        evse_key = evse_cnt_ordered_list[evse_idx]
        ev_key = ev_cnt_ordered_list[ev_idx]
        key = Result(vehicle_cnt=ev_key, station_cnt=evse_key, random_sort=False)
        z[evse_idx,ev_idx]= heuristic_kpi_dict[key]

x = evse_cnt_ordered_list
y = ev_cnt_ordered_list

fig = go.Figure(data=[

    go.Surface(z=z, x=x, y=y, opacity=1.0)],

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

fig.show()