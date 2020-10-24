# -*- coding: utf-8 -*-
# Copyright 2020 Tomaz Muraus
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import unittest
import datetime

import urllib.parse

from wx_server.formatters import format_ecowitt_weather_data
from wx_server.formatters import format_wu_weather_data

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../fixtures"))

ECOWITT_FORM_DATA_FIXTURE_PATH = os.path.join(FIXTURES_DIR, "example_requests/ecowitt")

with open(ECOWITT_FORM_DATA_FIXTURE_PATH, "r") as fp:
    ECOWITT_FORM_DATA = fp.read()

ECOWITT_FORM_DATA_DICT = dict(urllib.parse.parse_qsl(ECOWITT_FORM_DATA))


WU_PATH_DATA_FIXTURE_PATH = os.path.join(FIXTURES_DIR, "example_requests/wunderground")

with open(WU_PATH_DATA_FIXTURE_PATH, "r") as fp:
    WU_PATH_DATA = fp.read()

WU_PATH_DATA_DICT = dict(urllib.parse.parse_qsl(WU_PATH_DATA))


class FormatDataTestCase(unittest.TestCase):
    maxDiff = None

    def test_format_ecowitt_weather_data(self):
        expected_result = {
            "date": "2020-10-18 20:23:31",
            "datetime": datetime.datetime(2020, 10, 18, 20, 23, 31, tzinfo=datetime.timezone.utc),
            "timestamp": 1603052611,
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
        expected_result = {
            "date": "2020-10-24 11:10:12",
            "datetime": datetime.datetime(2020, 10, 24, 11, 10, 12, tzinfo=datetime.timezone.utc),
            "timestamp": 1603537812,
            "temperature": 14.5,
            "humidity": 98,
            "dewpoint": 14.44,
            "pressure_abs": 989.13,
            "pressure_rel": 1015.51,
            "wind_direction": 267,
            "wind_speed": 0.0,
            "wind_gust": 0.0,
            "rain_event": 1.8,
            "rain_rate": 1.8,
            "rain_daily": 3.91,
            "rain_weekly": 3.91,
            "rain_monthly": 171.5,
            "uv": 0,
            "solar_radiation": 36.33,
        }
        result = format_wu_weather_data(WU_PATH_DATA_DICT)
        self.assertEqual(result, expected_result)
