import pandas as pd
from pydantic import BaseModel

from src.building.building_utils import BuildingUtils


class Building(BaseModel):
    load_profile: pd.DataFrame = None
    type: str = None
    zip_code: int = None


    def __init__(self, type, zip_code):

        self.zip_code = zip_code
        self.type = type
        self.load_profile = BuildingUtils.get_bldg_load(zip_code, type)

    # so that pandas dataframe can be returned in pydantic
    class Config:
        arbitrary_types_allowed = True





