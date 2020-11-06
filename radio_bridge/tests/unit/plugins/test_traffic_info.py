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

from radio_bridge.plugins.traffic_info import BASE_URL
from radio_bridge.plugins.traffic_info import TrafficInfoPlugin
import radio_bridge.plugins.traffic_info

from tests.unit.plugins.base import BasePluginTestCase
from tests.unit.plugins.base import MockBasePlugin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../fixtures/plugins/traffic_info"))

QUERY_PARAMS = {
    "language": "en_US",
    "event_type": "all",
    "roadtype": "all",
}

MOCK_CONFIG = {
    "username": "foo",
    "password": "bar",
}

MOCK_CONFIG_SL = {
    "username": "foo",
    "password": "bar",
    "language": "sl_SI",
}


MOCK_URL_TRAFFIC_EVENTS = BASE_URL + "b2b.dogodki.json"
MOCK_URL_BORDER_DATA = BASE_URL + "b2b.borderdelays.geojson"

with open(os.path.join(FIXTURES_DIR, "b2b.dogodki.json"), "r") as fp:
    MOCK_DATA_EVENTS = fp.read()

with open(os.path.join(FIXTURES_DIR, "b2b.dogodki.slo.json"), "r") as fp:
    MOCK_DATA_EVENTS_SL = fp.read()


with open(os.path.join(FIXTURES_DIR, "b2b.borderdelays.geojson"), "r") as fp:
    MOCK_DATA_BORDERS = fp.read()


class TrafficInfoPluginForTest(TrafficInfoPlugin, MockBasePlugin):
    pass


class TrafficInfoPluginTrafficEventsTestCase(BasePluginTestCase):
    def setUp(self):
        super(TrafficInfoPluginTrafficEventsTestCase, self).setUp()

        radio_bridge.plugins.traffic_info.URL_RESPONSE_CACHE = {}

    def test_run_success_en_US(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config=MOCK_CONFIG)

        with requests_mock.Mocker() as m:
            m.get(MOCK_URL_TRAFFIC_EVENTS, text=MOCK_DATA_EVENTS)
            plugin.run(sequence="1")

        expected_text = """
R3-688, Žiče - Poljčane, at Lušečka vas, roadworks, single alternate lane traffic, until 3. 11. 2020, between 8 am to 5 pm.
G2-103, Nova Gorica - Tolmin, at Plave, roadworks, single alternate lane traffic, until 4. 11. 2020.
R3-646, Grosuplje - Šmarje Sap, roadworks, single alternate lane traffic, until 31. 3. 2021.
R3-687, Dole - Ponikva - Loče, in Hotunje, roadworks, single alternate lane traffic, until 7. 11. 2020.
R1-219, Bizeljsko - Čatež, at Župelevec, roadworks, single alternate lane traffic, until 4. 11. 2020.
""".strip()  # NOQA

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_success_si_SL(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config=MOCK_CONFIG_SL)

        with requests_mock.Mocker() as m:
            m.get(MOCK_URL_TRAFFIC_EVENTS, text=MOCK_DATA_EVENTS_SL)
            plugin.run(sequence="1")

        expected_text = """
R3-643, Cerknica - Rakitna - Podpeč, na Rakitni, dela, izmenično enosmerni promet, do 9. 11. 2020, od 7. do 17. ure.
G1-1, Miklavž - Maribor, v Mariboru, na Ptujski cesti, med Tržaško cesto in Poljsko ulico, zaprt en prometni pas, popravilo jaška, do 9. 11. 2020, od 7. do 15. ure.
R2-430, Maribor - Slovenska Bistrica - Slovenske Konjice, v Slovenski Bistrici, na Mariborski cesti, dela, izmenično enosmerni promet, pomična zapora, do 7. 11. 2020, od 7. do 17. ure.
G1-1, Maribor - Ptuj, v Mariboru na Ptujski cesti, med avtocesto in Tržaško cesto, oviran promet, obnova talnih obeležb, do 8. 11. 2020, od 7. do 17. ure.
H4, Nova Gorica - Razdrto, počivališče Šempas v smeri Razdrtega, dela, zaprt izvoz na počivališče, do 30. 11. 2020.
""".strip()  # NOQA

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_invalid_sequence(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config=MOCK_CONFIG)
        plugin.run(sequence="3")

        expected_text = "Invalid sequence."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_plugin_not_configured(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})
        plugin.run(sequence="1")

        expected_text = "Plugin has not been configured correctly by the admin."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_non_200_response(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config=MOCK_CONFIG)

        with requests_mock.Mocker() as m:
            m.get(MOCK_URL_TRAFFIC_EVENTS, text="", status_code=500)
            plugin.run(sequence="1")

        expected_text = "Failed to retrieve traffic events data."
        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_failed_to_parse_data(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config=MOCK_CONFIG)

        with requests_mock.Mocker() as m:
            m.get(MOCK_URL_TRAFFIC_EVENTS, text="<invalid")
            plugin.run(sequence="1")

        expected_text = "Failed to retrieve traffic events data."
        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)


class TrafficInfoPluginBorderCrossingsDelaysTestCase(BasePluginTestCase):
    def setUp(self):
        super(TrafficInfoPluginBorderCrossingsDelaysTestCase, self).setUp()

        radio_bridge.plugins.traffic_info.URL_RESPONSE_CACHE = {}

    def test_run_success_en_US(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config=MOCK_CONFIG_SL)

        with requests_mock.Mocker() as m:
            m.get(MOCK_URL_BORDER_DATA, text=MOCK_DATA_BORDERS)
            plugin.run(sequence="2")

        expected_text = """
Mejni prehod Gruškovje, Macelj, tovorna vozila 6 h pri vstopu
Mejni prehod Obrežje, Bregana, tovorna vozila 2 h pri vstopu
""".strip()  # NOQA

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_success_si_SL(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config=MOCK_CONFIG)

        with requests_mock.Mocker() as m:
            m.get(MOCK_URL_BORDER_DATA, text=MOCK_DATA_BORDERS)
            plugin.run(sequence="2")

        expected_text = """
Border crossing Gruškovje, Macelj, heavy vehicles 6 h at entrance
Border crossing Obrežje, Bregana, heavy vehicles 2 h at entrance
""".strip()  # NOQA

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_invalid_sequence(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config=MOCK_CONFIG)
        plugin.run(sequence="4")

        expected_text = "Invalid sequence."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_plugin_not_configured(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})
        plugin.run(sequence="2")

        expected_text = "Plugin has not been configured correctly by the admin."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_non_200_response(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config=MOCK_CONFIG)

        with requests_mock.Mocker() as m:
            m.get(MOCK_URL_BORDER_DATA, text="", status_code=500)
            plugin.run(sequence="2")

        expected_text = "Failed to retrieve border crossings delays data."
        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_failed_to_parse_data(self):
        plugin = TrafficInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config=MOCK_CONFIG)

        with requests_mock.Mocker() as m:
            m.get(MOCK_URL_BORDER_DATA, text="<invalid")
            plugin.run(sequence="2")

        expected_text = "Failed to retrieve border crossings delays data."
        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)
