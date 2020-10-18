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

from wx_server.formatters import dict_to_protobuf
from wx_server.formatters import format_ecowitt_weather_data
from wx_server.io import persist_weather_observation

from tests.unit.test_format_data import ECOWITT_FORM_DATA_DICT


class PersistAndRetrieveDataTestCase(unittest.TestCase):
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
