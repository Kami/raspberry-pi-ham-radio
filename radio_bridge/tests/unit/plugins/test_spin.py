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

from radio_bridge.plugins.spin_events import DEFAULT_URL
from radio_bridge.plugins.spin_events import SPINEventsPlugin
import radio_bridge.plugins.spin_events

from tests.unit.plugins.base import BasePluginTestCase
from tests.unit.plugins.base import MockBasePlugin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../fixtures/plugins/spin"))


with open(os.path.join(FIXTURES_DIR, "response.xml"), "r") as fp:
    MOCK_DATA = fp.read()


class SPINEventsPluginForTest(SPINEventsPlugin, MockBasePlugin):
    pass


class SPINEventsPluginTrafficEventsTestCase(BasePluginTestCase):
    maxDiff = None

    def setUp(self):
        super(SPINEventsPluginTrafficEventsTestCase, self).setUp()

        radio_bridge.plugins.spin_events.URL_RESPONSE_CACHE = {}

    def test_run_success(self):
        plugin = SPINEventsPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})

        with requests_mock.Mocker() as m:
            m.get(DEFAULT_URL, text=MOCK_DATA)
            plugin.run()

        expected_text = """
Ob 20.00 si je na Vodiški planini, občina Radovljica, pohodnica zlomila golen. Reševalci GRS Radovljica so poškodovanko na kraju oskrbeli, na klasični način prenesli v dolino, kjer so jo predali v nadaljnjo oskrbo reševalcem NMP Radovljica in Bled.
Ob 18.57 je na Ulici Malči Beličeve v Ljubljani gorel zabojnik za odpadni papir. Požar so pogasili gasilci GB Ljubljana.
Ob 18.37 je v naselju Drganja sela, občina Straža, na parkirišču občana osebno vozilo stisnilo ob kamniti zid. Gasilci PGD Vavta vas in GRC Novo mesto so osebi nudili prvo pomoč do prihoda reševalcev NMP Novo mesto. O nesreči so bile obveščene pristojen službe.
Ob 18.22 je na obalni kolesarski poti med Koprom in Izolo zagorelo razkužilo v plastičnem stranišču. Posredovali so gasilci JZ GB Koper, ki so požar pogasili.
Ob 17.40 sta se na poti z Jerebikovca, občina Kranjska Gora, izgubila dva planinca, ki nista imela luči. Gorski reševalci GRS Mojstrana so planinca našli nepoškodovana in ju pospremili v dolino.
""".strip()  # NOQA

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)
