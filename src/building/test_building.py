import unittest
from src.building.building import Building
from src.building.building_utils import BuildingUtils


class TestBuilding(unittest.TestCase):

    def test_get_bldg_load_max(self):
        county = 'San Diego'
        type = 'smalloffice'
        sqft = 4000
        df_bldg_load = BuildingUtils.get_bldg_load(county, type, sqft)
        df_bldg_load_max = BuildingUtils.get_bldg_load_max_hourly_kwh(df_bldg_load)
        assert len(df_bldg_load_max) == 24

    def test_zip_geocoder_san_diego_climate_zone(self):
        lat, lon = BuildingUtils.geocode_zip_code_to_lat_lon(91945)

        assert lat == 32.733147
        assert lon == -117.034068

    def test_get_climate_zone_from_san_diego_county(self):
        cz, county_fips = BuildingUtils.get_climate_zone_county_fips_from_county(county='San Diego')
        assert cz == '3B'
        assert county_fips == '06073'

    def test_get_timezone_from_county_fips(self):
        fips_dict = {
            'Los_Angeles': '06037',
            'Anchorage': '02020',
            'Denver': '08031',
            'Queens': '36081'
            # 'Honolulu': '15003'
        }

        for county, fips in fips_dict.items():
            tz = BuildingUtils.get_timezone_from_county_fips(fips)
            if county == 'Los_Angeles':
                assert tz == 'US/Pacific'
            if county == 'Anchorage':
                assert tz == 'US/Alaska'
            if county == 'Denver':
                assert tz == 'US/Mountain'
            if county == 'Queens':
                assert tz == 'US/Eastern'
            # if county == 'Honolulu':
            #     assert tz == 'US/Aleutian'

    def test_get_bldg_load_profile(self):
        county = 'San Diego'
        type = 'smalloffice'
        sqft = 4000
        df_bldg_load = BuildingUtils.get_bldg_load(county, type, sqft)
        assert len(df_bldg_load) > 0

    # def test_bldg_load_profile_from_san_diego(self):
    #     df_load_profile_sd_small_office = BuildingUtils.get_bldg_load_profile_from_climate_zone(
    #         climate_zone='3B',
    #         type = 'smalloffice',
    #         sqft = 10000
    #     )