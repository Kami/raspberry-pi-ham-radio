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

from radio_bridge.plugins.help import HelpPlugin

from tests.unit.plugins.base import BasePluginTestCase
from tests.unit.plugins.base import MockBasePlugin

__all__ = ["HelpPluginTestCase"]


class HelpPluginForTest(HelpPlugin, MockBasePlugin):
    pass


class HelpPluginTestCase(BasePluginTestCase):
    maxDiff = None

    def test_run_success(self):
        plugin = HelpPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})
        plugin.run()

        expected_text = """
Available commands:
1. Sequence * D * . Clear currently accumulated DTMF sequence.
2. Sequence 1 2 . List available commands.
3. Sequence 2 1 . Current date and time.
4. Sequence 2 5 ? . Traffic events and border crossings delays information
5. Sequence 3 4 . Current weather information for local weather station.
6. Sequence 3 5 ? ? . Current weather for location.
7. Sequence 3 8 ? ? ? . Display information for a specific repeater.
""".strip()

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)
