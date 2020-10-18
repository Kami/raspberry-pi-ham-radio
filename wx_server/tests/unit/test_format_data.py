import os
import unittest
import datetime

import urllib.parse

from wx_server.formatters import format_ecowitt_weather_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../fixtures"))

ECOWITT_FORM_DATA_FIXTURE_PATH = os.path.join(FIXTURES_DIR, "example_requests/ecowitt")

with open(ECOWITT_FORM_DATA_FIXTURE_PATH, "r") as fp:
    ECOWITT_FORM_DATA = fp.read()

ECOWITT_FORM_DATA_DICT = dict(urllib.parse.parse_qsl(ECOWITT_FORM_DATA))


class FormatDataTestCase(unittest.TestCase):
    maxDiff = None

    def test_format_ecowitt_weather_data(self):
        expected_result = {
            "date": "2020-10-18 20:23:31",
            "datetime": datetime.datetime(2020, 10, 18, 20, 23, 31),
            "timestamp": 1603045411,
            "temperature": 6.61,
            "humidity": 96,
            "dewpoint": 5.81,
            "pressure_abs": 996.31,
            "pressure_rel": 1022.72,
            "wind_direction": 245,
            "wind_speed": 1.61,
            "wind_gust": 8.05,
            "wind_gust_max_daily": 5.47,
            "rain_event": 0.0,
            "rain_rate": 2.54,
            "rain_hourly": 5.08,
            "rain_daily": 0.0,
            "rain_weekly": 0.0,
            "rain_monthly": 167.59,
            "rain_total": 234.39,
            "uv": 3,
            "solar_radiation": 1.50,
        }
        result = format_ecowitt_weather_data(ECOWITT_FORM_DATA_DICT)
        self.assertEqual(result, expected_result)

    def test_format_weatherunderground_weather_data(self):
        # TODO
        pass
