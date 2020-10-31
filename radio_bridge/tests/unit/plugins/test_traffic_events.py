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

from radio_bridge.plugins.traffic_events import BASE_URL
from radio_bridge.plugins.traffic_events import TrafficEventsPlugin
import radio_bridge.plugins.traffic_events

from tests.unit.plugins.base import BasePluginTestCase
from tests.unit.plugins.base import MockBasePlugin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../fixtures/plugins/traffic_events"))

QUERY_PARAMS = {
    "language": "en_US",
    "event_type": "all",
    "roadtype": "all",
}

with open(os.path.join(FIXTURES_DIR, "b2b.dogodki.rss"), "r") as fp:
    MOCK_DATA = fp.read()


class TrafficEventsPluginForTest(TrafficEventsPlugin, MockBasePlugin):
    pass


class TrafficEventsPluginTestCase(BasePluginTestCase):
    def setUp(self):
        super(TrafficEventsPluginTestCase, self).setUp()

        radio_bridge.plugins.traffic_events.URL_RESPONSE_CACHE = {}

    def test_run_success(self):
        plugin = TrafficEventsPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})

        with requests_mock.Mocker() as m:
            m.get(BASE_URL, text=MOCK_DATA)
            plugin.run()

        expected_text = """
R2-452, Radovljica - Lesce, traffic accident, road closed.
A2, border crossing Obrežje, Bregana, delays info: cars 1 h at entrance.
A5, motorway, near Maribor in the direction of Hungary, roadworks, traffic is diverted through rest area.
A2-E70, motorway, near Krško in the direction of Croatia, congestion, length: 500 m.
A2, border crossing Obrežje, Bregana, delays info: cars 1 h at exit.
""".strip()  # NOQA

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_non_200_response(self):
        plugin = TrafficEventsPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})

        with requests_mock.Mocker() as m:
            m.get(BASE_URL, text=MOCK_DATA, status_code=500)
            plugin.run()

        expected_text = "Failed to retrieve traffic events data."
        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_failed_to_parse_data(self):
        plugin = TrafficEventsPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})

        with requests_mock.Mocker() as m:
            m.get(BASE_URL, text="<invalid")
            plugin.run()

        expected_text = "Failed to retrieve traffic events data."
        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)
