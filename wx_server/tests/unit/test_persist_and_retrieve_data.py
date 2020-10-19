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

import unittest
import datetime
import tempfile

import wx_server.configuration

from wx_server.formatters import dict_to_protobuf
from wx_server.formatters import format_ecowitt_weather_data
from wx_server.io import persist_weather_observation
from wx_server.io import get_weather_observation_for_date

from tests.unit.test_format_data import ECOWITT_FORM_DATA_DICT


class PersistAndRetrieveDataTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(PersistAndRetrieveDataTestCase, cls).setUpClass()

        # Use temporary directory for tests data path
        temp_dir = tempfile.mkdtemp()
        wx_server.configuration.CONFIG = {"main": {"data_dir": temp_dir}}
        cls._insert_mock_observations()

    @classmethod
    def _insert_mock_observations(cls):
        data = format_ecowitt_weather_data(ECOWITT_FORM_DATA_DICT)

        observation_pb = dict_to_protobuf(data)
        observation_pb.temperature = 1.0
        observation_pb.timestamp = int(
            datetime.datetime(2020, 10, 10, 13, 10).replace(tzinfo=None).timestamp()
        )
        persist_weather_observation(station_id="home", observation_pb=observation_pb)

        observation_pb = dict_to_protobuf(data)
        observation_pb.temperature = 2.0
        observation_pb.timestamp = int(
            datetime.datetime(2020, 10, 10, 15, 00).replace(tzinfo=None).timestamp()
        )
        persist_weather_observation(station_id="home", observation_pb=observation_pb)

        observation_pb = dict_to_protobuf(data)
        observation_pb.temperature = 3.0
        observation_pb.timestamp = int(
            datetime.datetime(2020, 10, 10, 16, 00).replace(tzinfo=None).timestamp()
        )
        persist_weather_observation(station_id="home", observation_pb=observation_pb)

        observation_pb = dict_to_protobuf(data)
        observation_pb.temperature = 4.0
        observation_pb.timestamp = int(
            datetime.datetime(2020, 10, 10, 16, 2).replace(tzinfo=None).timestamp()
        )
        persist_weather_observation(station_id="home", observation_pb=observation_pb)

    def test_observation_dict_to_pb(self):
        data = format_ecowitt_weather_data(ECOWITT_FORM_DATA_DICT)
        observation_pb = dict_to_protobuf(data)

        self.assertEqual(round(observation_pb.temperature, 2), 6.61)
        self.assertEqual(round(observation_pb.dewpoint, 2), 5.81)
        self.assertEqual(observation_pb.humidity, 96)
        self.assertEqual(round(observation_pb.pressure_rel, 2), 1022.72)
        self.assertEqual(observation_pb.wind_direction, 245)
        self.assertEqual(round(observation_pb.wind_speed, 2), 1.61)
        self.assertEqual(round(observation_pb.wind_gust, 2), 8.05)
        self.assertEqual(round(observation_pb.wind_gust_max_daily, 2), 5.47)
        self.assertEqual(round(observation_pb.rain_event, 2), 0.0)
        self.assertEqual(round(observation_pb.rain_rate, 2), 2.54)
        self.assertEqual(round(observation_pb.rain_hourly, 2), 5.08)
        self.assertEqual(round(observation_pb.rain_total, 2), 234.39)
        self.assertEqual(observation_pb.uv, 3)
        self.assertEqual(round(observation_pb.solar_radiation, 2), 1.50)

    def test_get_weather_observation_for_date(self):
        # 1. Invalid / unrecognized station id (no observations available)
        date = datetime.datetime(2020, 10, 10, 15, 00)
        station_id = "invalid"

        result = get_weather_observation_for_date(station_id=station_id, date=date)
        self.assertEqual(result, None)

        # 2. Observation exists for this timestamp
        date = datetime.datetime(2020, 10, 10, 15, 00)
        station_id = "home"

        result = get_weather_observation_for_date(station_id=station_id, date=date)
        self.assertTrue(result is not None)
        self.assertEqual(result.temperature, 2)

        # 3. Observation doesn't exist for this minute, but exists for 5 minutes ago (non strict
        # mode)
        date = datetime.datetime(2020, 10, 10, 16, 7)
        station_id = "home"

        result = get_weather_observation_for_date(station_id=station_id, date=date)
        self.assertTrue(result is not None)
        self.assertEqual(
            result.timestamp,
            int(datetime.datetime(2020, 10, 10, 16, 2).replace(tzinfo=None).timestamp()),
        )
        self.assertEqual(result.temperature, 4)

        # 4. Observation doesn't exist for this minute, but exists for 5 minutes ago (strict mode)

        date = datetime.datetime(2020, 10, 10, 16, 7)
        station_id = "home"

        result = get_weather_observation_for_date(
            station_id=station_id, date=date, return_closest=False
        )
        self.assertEqual(result, None)
