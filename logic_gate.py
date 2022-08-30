from datetime import datetime

import random

import numpy as np

n_vehicles = 20
# example requests
vehicle_ids = range(0, n_vehicles)

# Init Code
vehicles_out_driving = vehicle_ids[16:]
vehicles_in_depot = vehicle_ids[0:16]
n_hours_horizon = 24
n_secs_per_timestep = 60*15 # 15 min time steps

schedule = np.zeros(n_vehicles, (n_hours_horizon*3600) / n_secs_per_timestep ) # 1 = available to charge, 0 = unavailable to charge
assigned_station = np.zeros(n_vehicles, (n_hours_horizon*3600) / n_secs_per_timestep ) # 0 = no station assigned



request = {
   "type": "vehicle_scan",
   "timestamp": str(datetime.now()),
   "vehicle_id": str(random.sample(vehicles_out_driving)[0])
   "soc": round(random.uniform(0,0.8), 1)
}


def get_payload(request):
   if request.type == 'vehicle_scan':
      vehicle_scan(request)
   elif request.type == 'walk_in':
      pass
   elif request.type == 'reservation':
      pass



def vehicle_scan():
