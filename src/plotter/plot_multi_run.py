import pickle

import numpy as np
import plotly.graph_objects as go

with open('../multi_run.pickle', 'rb') as handle:
    multi_run_list = pickle.load(handle)

# process the output for 3d plotting
heur_ev_cnt = []
heur_station_cnt = []
heur_mean_late = []


bau_ev_cnt = []
bau_station_cnt = []
bau_mean_late = []

print(multi_run_list)

for result_dict in multi_run_list:
    if result_dict['business_as_usual']:
        bau_ev_cnt.append(result_dict['num_vehicles'])
        bau_station_cnt.append(result_dict['l2_stations'])
        bau_mean_late.append(np.mean(result_dict['departure_deltas']))
    else:
        heur_ev_cnt.append(result_dict['num_vehicles'])
        heur_station_cnt.append(result_dict['l2_stations'])
        heur_mean_late.append(np.mean(result_dict['departure_deltas']))

print(heur_ev_cnt)
print(heur_station_cnt)
print(heur_mean_late)


# x, y = np.linspace(0, 1, sh_0), np.linspace(0, 1, sh_1)
fig = go.Figure(data=[go.Surface(z=heur_mean_late, x=heur_station_cnt, y=heur_station_cnt)])
fig.update_layout(title='Mean Departure Tardiness (minutes)', autosize=False,
                  width=500, height=500,
                  margin=dict(l=65, r=50, b=65, t=90))
fig.show()