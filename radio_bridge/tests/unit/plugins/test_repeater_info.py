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

from radio_bridge.plugins.repeater_info import REPEATERS_URL_2M
from radio_bridge.plugins.repeater_info import REPEATERS_URL_70CM
from radio_bridge.plugins.repeater_info import RepeaterInfoPlugin

from tests.unit.plugins.base import BasePluginTestCase
from tests.unit.plugins.base import MockBasePlugin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../fixtures/plugins/repeater_info"))

with open(os.path.join(FIXTURES_DIR, "repeaters_2m.html"), "r") as fp:
    MOCK_DATA_2M = fp.read()

with open(os.path.join(FIXTURES_DIR, "repeaters_70cm.html"), "r") as fp:
    MOCK_DATA_70CM = fp.read()


class RepeaterInfoPluginForTest(RepeaterInfoPlugin, MockBasePlugin):
    pass


class RepeaterInfoPluginTestCase(BasePluginTestCase):
    def test_run_success(self):
        plugin = RepeaterInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})

        with requests_mock.Mocker() as m:
            m.get(REPEATERS_URL_2M, text=MOCK_DATA_2M)
            plugin.run(sequence="201")

        expected_text = "Invalid repeater type."

        expected_text = """
Repeater S55VLM.
Location: LJUBLJANA CENTER.
Input frequency: 1 4 4 decimal 9 7 5 MHz.
Output frequency: 1 4 5 decimal 5 7 5.
CTCSS: 1 2 3 decimal 0 MHz
""".strip()

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_invalid_repeater_type(self):
        plugin = RepeaterInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})
        plugin.run(sequence="901")

        expected_text = "Invalid repeater type."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_unable_to_retrieve_details(self):
        plugin = RepeaterInfoPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})
        plugin.run(sequence="255")

        expected_text = "Unable to retrieve details for repeater with id 55"

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_parse_repeater_id_and_type_from_sequence(self):
        plugin = RepeaterInfoPlugin()

        # 1. Invalid sequence
        repeater_id, repeater_type = plugin._parse_repeater_id_url_from_sequence("0000")
        self.assertEqual(repeater_id, None)
        self.assertEqual(repeater_type, None)

        repeater_id, repeater_type = plugin._parse_repeater_id_url_from_sequence("000")
        self.assertEqual(repeater_id, None)
        self.assertEqual(repeater_type, None)

        # 2. VHF RPT
        repeater_id, repeater_type = plugin._parse_repeater_id_url_from_sequence("201")
        self.assertEqual(repeater_id, "1")
        self.assertEqual(repeater_type, "vhf")

        repeater_id, repeater_type = plugin._parse_repeater_id_url_from_sequence("211")
        self.assertEqual(repeater_id, "11")
        self.assertEqual(repeater_type, "vhf")

        # 3. UHF RPT
        repeater_id, repeater_type = plugin._parse_repeater_id_url_from_sequence("701")
        self.assertEqual(repeater_id, "1")
        self.assertEqual(repeater_type, "uhf")

        repeater_id, repeater_type = plugin._parse_repeater_id_url_from_sequence("721")
        self.assertEqual(repeater_id, "21")
        self.assertEqual(repeater_type, "uhf")

    def test_get_2m_repeater_info(self):
        plugin = RepeaterInfoPlugin()

        with requests_mock.Mocker() as m:
            m.get(REPEATERS_URL_2M, text=MOCK_DATA_2M)
            repeater = plugin._get_repeater_info(1, "vhf")

            self.assertEqual(repeater.numeric_id, "RV46")
            self.assertEqual(repeater.name, "S55VLM")
            self.assertEqual(repeater.input_freq, "144.975")
            self.assertEqual(repeater.output_freq, "145.575")
            self.assertEqual(repeater.ctcss, "123.0")
            self.assertEqual(repeater.location, "LJUBLJANA CENTER")

        with requests_mock.Mocker() as m:
            m.get(REPEATERS_URL_2M, text=MOCK_DATA_2M)
            repeater = plugin._get_repeater_info(100, "vhf")
            self.assertIsNone(repeater)

    def test_get_70m_repeater_info(self):
        plugin = RepeaterInfoPlugin()

        with requests_mock.Mocker() as m:
            m.get(REPEATERS_URL_70CM, text=MOCK_DATA_70CM)
            repeater = plugin._get_repeater_info(1, "uhf")

            self.assertEqual(repeater.numeric_id, "RU688")
            self.assertEqual(repeater.name, "S55UBK")
            self.assertEqual(repeater.input_freq, "431.000")
            self.assertEqual(repeater.output_freq, "438.600")
            self.assertEqual(repeater.ctcss, None)
            self.assertEqual(repeater.location, "MIRNA GORA")

        with requests_mock.Mocker() as m:
            m.get(REPEATERS_URL_70CM, text=MOCK_DATA_70CM)
            repeater = plugin._get_repeater_info(100, "uhf")
            self.assertIsNone(repeater)
