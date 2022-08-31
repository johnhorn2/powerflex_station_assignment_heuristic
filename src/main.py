import json

from src.simulator.simulator.simulator import Simulator
from src.simulator.simulator_config.simulator_config import SimulatorConfig

with open('simulator/simulator_config/configs/2days_15min_40res_per_day.json') as f:
    config = json.load(f)

scenario_config = SimulatorConfig(**config)
scenario = Simulator(config=scenario_config)
scenario.run()
print('simulation complete')

