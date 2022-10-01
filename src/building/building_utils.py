from datetime import datetime
import os


import pandas as pd


class BuildingUtils:

    @classmethod
    def get_bldg_load_max_hourly_kwh(cls, df_bldg_load) -> pd.DataFrame:
        df_bldg_load['hour'] = df_bldg_load['timestamp'].dt.hour
        df_bldg_load['dayofyear'] = df_bldg_load['timestamp'].dt.dayofyear
        df_sum_power_by_hour = df_bldg_load.groupby(['hour', 'dayofyear'])['total_kwh'].sum().reset_index()
        df_max_power_by_hour = df_sum_power_by_hour.groupby('hour')['total_kwh'].max().reset_index()
        return df_max_power_by_hour

    @classmethod
    def get_bldg_load(cls, county, type, sqft) -> pd.DataFrame:
        climate_zone, county_fips = cls.get_climate_zone_county_fips_from_county(county)
        df_bldg_load_profile = cls.get_bldg_load_profile_from_climate_zone(climate_zone, county_fips, type, sqft)
        return df_bldg_load_profile

    @classmethod
    def get_climate_zone_county_fips_from_county(cls, county) -> str: # return ashrae climate zone e.g. '3B'
        cwd = os.getcwd()
        path = 'data/climate_zones.csv'
        if 'src' not in cwd:
            full_path = os.path.join(cwd, 'src/building/', path)
        # run from test
        elif 'src' in cwd:
            full_path = os.path.join(cwd, path)
        dtype = {
            'State': str,
            'State FIPS': str,
            'County FIPS': str,
            'IECC Climate Zone': str,
            'IECC Moisure Regime': str,
            'BA Climate Zone': str,
            'County Name': str
        }
        df_cz = pd.read_csv(filepath_or_buffer=full_path, dtype=dtype)
        climate_zone = df_cz[df_cz['County Name'] == county]['IECC Climate Zone'].values[0]
        moisture_region = df_cz[df_cz['County Name'] == county]['IECC Moisture Regime'].values[0]
        combined_climate_zone = climate_zone + moisture_region
        state_fips = df_cz[df_cz['County Name'] == county]['State FIPS'].values[0]
        county_fips = df_cz[df_cz['County Name'] == county]['County FIPS'].values[0]
        state_county_fips = state_fips + county_fips

        return combined_climate_zone, state_county_fips

    @classmethod
    def get_timezone_from_county_fips(cls, fips_code):
        dtype = {
            'STATEFP': str,
            'COUNTYFP': str,
            'GEOID': str,
            'NAME': str,
            'NAMELSAD': str,
            'TIMEZONE': str,
            'GMT_OFFSET': str
        }
        cwd = os.getcwd()
        path = 'data/county_fips_to_cz.csv'

        if 'src' not in cwd:
            full_path = os.path.join(cwd, 'src/building/', path)
        # run from test
        elif 'src' in cwd:
            full_path = os.path.join(cwd, path)

        df_fips_to_cz = pd.read_csv(filepath_or_buffer=full_path, dtype=dtype)
        tz = df_fips_to_cz[df_fips_to_cz['GEOID'] == fips_code]['TIMEZONE'].values[0]

        convert_tz_name = {
            "Alaska": 'US/Alaska',
            "Pacific": "US/Pacific",
            "Mountain": "US/Mountain",
            "Eastern": "US/Eastern",
            "Central": "US/Central",
            "Hawaii - Aleutian": "US/Aleutian",
            "Atlantic": "AST"
        }

        pytz_tz = convert_tz_name[tz]

        return pytz_tz


    @classmethod
    def get_bldg_load_profile_from_climate_zone(cls, climate_zone, county_fips, type, sqft) -> pd.DataFrame:
        file_name = climate_zone.lower() + '-' + type + '.csv'
        path = os.path.join('data', 'load_by_climate_zone', climate_zone, file_name)
        cwd = os.getcwd()

        # run from streamlit
        if 'src' not in cwd:
            full_path = os.path.join(cwd, 'src/building/', path)
        # run from test
        elif 'src' in cwd:
            full_path = os.path.join(cwd, path)
        usecols = ['timestamp', 'floor_area_represented', 'out.electricity.total.energy_consumption']
        dtype = {
            'floor_area_represented': float,
            'out.electricity.total.energy_consumption': float
        }
        df = pd.read_csv(filepath_or_buffer=full_path, dtype=dtype, usecols=usecols)
        df = df.rename(columns={'out.electricity.total.energy_consumption': 'total_kwh'})
        df['total_kwh'] = df['total_kwh'] / df['floor_area_represented']
        df['total_kwh'] = df['total_kwh'] * sqft
        df = df.loc[:, df.columns != 'floor_area_represented']
        # convert time timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        # DOE data comes in EST for all data so need to localize data
        tz_target = cls.get_timezone_from_county_fips(county_fips)
        df['timestamp'] = df['timestamp'].dt.tz_localize('EST')

        # convert to the local timezone of the county fips code
        df['timestamp'] = df['timestamp'].dt.tz_convert(tz_target)
        return df

    # @classmethod
    # def get_bldg_load(cls, zip_code, bldg_type) -> pd.DataFrame:
    #     climate_zone = cls.get_building_america_climate_zone(zip_code)
    #     df_bldg_load = cls.query_building_load(bldg_type, climate_zone)
    #     return df_bldg_load

    # @classmethod
    # def get_building_america_climate_zone(cls, zip_code) -> str:
    #     lat, lon = cls.geocode_zip_to_lat_lon(zip_code)
    #     climate_zone = cls.query_climate_zone_intersect(lat, lon)
    #     return climate_zone

    # @classmethod
    # def query_building_load(cls, bldg_type, bldg_america_climate_zone) -> pd.DataFrame:
    #     pass

    @classmethod
    def geocode_zip_code_to_lat_lon(cls, zip_code: str) -> (float, float):  # (Lat, Lon)
        file_path = 'data/zip_code_to_lat_lon.csv'
        dtype = {'zip': str, 'lat': float, 'lon': float}
        df = pd.read_csv(filepath_or_buffer=file_path, dtype=dtype)
        lat = df[df['zip'] == str(zip_code)]['lat'].values[0]
        lon = df[df['zip'] == str(zip_code)]['lon'].values[0]
        return lat, lon

    # @classmethod
    # def query_climate_zone_intersect(cls, lat, lon) -> str:
    #     pass