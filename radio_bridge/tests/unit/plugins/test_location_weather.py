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

import requests_mock

from radio_bridge.plugins.location_weather import LocationWeatherPlugin
from radio_bridge.plugins.location_weather import CITY_TO_XML_URL_MAP

from tests.unit.plugins.base import BasePluginTestCase
from tests.unit.plugins.base import MockBasePlugin

__all__ = ["LocationWeatherPluginTestCase"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../fixtures/plugins/location_weather"))

with open(os.path.join(FIXTURES_DIR, "01_ljubljana.xml"), "r") as fp:
    MOCK_DATA_LJUBLJANA = fp.read()


class LocationWeatherPluginForTest(LocationWeatherPlugin, MockBasePlugin):
    pass


class LocationWeatherPluginTestCase(BasePluginTestCase):
    def test_run_invalid_location_sequence(self):
        plugin = LocationWeatherPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})
        plugin.run(sequence="99")

        expected_text = "Invalid weather location sequence."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_valid_sequence_ljubljana(self):
        plugin = LocationWeatherPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})

        with requests_mock.Mocker() as m:
            m.get(CITY_TO_XML_URL_MAP["Ljubljana"], text=MOCK_DATA_LJUBLJANA)
            plugin.run(sequence="01")

        expected_text = """
Weather information for Ljubljana.
Temperature 14.0 degrees celsius.
Dew point 10.0.
Pressure 1008.0 hPa.
Wind 11.0 kilometers per hour from the south east.
No rain.
UV index: 0
""".strip()

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)
