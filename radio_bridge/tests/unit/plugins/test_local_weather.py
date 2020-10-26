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

import mock
import datetime

from wx_server.formatters import dict_to_protobuf
from wx_server.io import persist_weather_observation

from radio_bridge.plugins.local_weather import LocalWeatherPlugin

from tests.unit.plugins.base import BasePluginTestCase
from tests.unit.plugins.base import MockBasePlugin

__all__ = ["LocalWeatherPluginTestCase"]

MOCK_DATETIME = datetime.datetime(2020, 10, 26, 19, 57, tzinfo=datetime.timezone.utc)

MOCK_OBSERVATION_DATA = {
    "date": "2020-10-26 26:19:57",
    "datetime": MOCK_DATETIME,
    "timestamp": int(MOCK_DATETIME.timestamp()),
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


class LocalWeatherPluginForTest(LocalWeatherPlugin, MockBasePlugin):
    pass


class LocalWeatherPluginTestCase(BasePluginTestCase):
    @classmethod
    def setUpClass(cls):
        super(LocalWeatherPluginTestCase, cls).setUpClass()
        cls._insert_mock_observations()

    @classmethod
    def _insert_mock_observations(cls):
        observation_pb = dict_to_protobuf(MOCK_OBSERVATION_DATA)
        persist_weather_observation(station_id="home", observation_pb=observation_pb)

    @mock.patch("radio_bridge.plugins.local_weather.datetime")
    def test_run(self, mock_datetime):
        # 1. No observation found for this date
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2020, 10, 25, 19, 57)

        plugin = LocalWeatherPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={"weather_station_id": "home"})
        plugin.run()

        expected_text = "No recent weather observation found."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

        # 2. Weather observation found.
        mock_datetime.datetime.utcnow.return_value = MOCK_DATETIME

        plugin.reset_mock_values()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={"weather_station_id": "home"})
        plugin.run()

        expected_text = """
Temperature 6.6 degrees celsius.
Dew point 5.8.
Pressure 1022.7 hPa.
No wind.
Rain 2.5 mm per hour
UV index: 3
""".strip()

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)
        mock_datetime.datetime.utcnow.return_value = MOCK_DATETIME

        # 3. Weather observation not found (different station id)
        mock_datetime.datetime.utcnow.return_value = MOCK_DATETIME

        plugin.reset_mock_values()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={"weather_station_id": "other_station"})
        plugin.run()

        expected_text = "No recent weather observation found."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)
