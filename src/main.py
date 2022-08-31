import json

from src.scenario.scenario import Scenario
from src.scenario.scenario_config import ScenarioConfig

with open('configs/10_vehicles_10_L2_2_DCFC.json') as f:
    config = json.load(f)

scenario_config = ScenarioConfig(**config)
scenario = Scenario(config=scenario_config)
scenario.intialize()
print('fin init')