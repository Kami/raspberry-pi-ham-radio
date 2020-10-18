import os
import unittest

import requests_mock

from radio_bridge.plugins.repeater_info import REPEATERS_URL_2M
from radio_bridge.plugins.repeater_info import REPEATERS_URL_70CM
from radio_bridge.plugins.repeater_info import RepeaterInfoPlugin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../fixtures/plugins/repeater_info"))

with open(os.path.join(FIXTURES_DIR, "repeaters_2m.html"), "r") as fp:
    MOCK_DATA_2M = fp.read()

with open(os.path.join(FIXTURES_DIR, "repeaters_70cm.html"), "r") as fp:
    MOCK_DATA_70CM = fp.read()


class RepeaterInfoPluginTestCase(unittest.TestCase):
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
