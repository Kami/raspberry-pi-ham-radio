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

from radio_bridge.plugins.current_time import CurrentTimePlugin

from tests.unit.plugins.base import BasePluginTestCase
from tests.unit.plugins.base import MockBasePlugin

__all__ = ["CurrentTimePluginTestCase"]


class CurrentTimePluginForTest(CurrentTimePlugin, MockBasePlugin):
    pass


class CurrentTimePluginTestCase(BasePluginTestCase):
    @mock.patch("radio_bridge.plugins.current_time.datetime")
    def test_run_success_en_US(self, mock_datetime):
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2020, 10, 26, 19, 57)
        plugin = CurrentTimePluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={"local_timezone": "CET"})
        plugin.run()

        expected_text = "Current time is 20 57 local. 19 57 U T C."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    @mock.patch("radio_bridge.plugins.current_time.datetime")
    def test_run_success_si_SL(self, mock_datetime):
        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2020, 10, 26, 19, 57)
        plugin = CurrentTimePluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={"local_timezone": "CET", "language": "sl_SI"})
        plugin.run()

        expected_text = "Trenuten cas je 20 57 lokalno. 19 57 U T C."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)
