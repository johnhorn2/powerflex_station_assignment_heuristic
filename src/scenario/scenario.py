from datetime import datetime
import random
from typing import Dict

from pydantic import BaseModel

from src.depot.depot import Depot

class Scenario(BaseModel):
    current_timestamp: datetime
    config: Dict
    depot: Depot = None


    def build_depot(self):
        pass