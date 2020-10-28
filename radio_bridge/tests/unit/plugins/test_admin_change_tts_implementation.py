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

from radio_bridge.plugins.admin.change_tts_implementation import ChangeTTSImplementationAdminPlugin
from radio_bridge.configuration import get_config_option
from radio_bridge.configuration import set_config_option

from tests.unit.plugins.base import BasePluginTestCase
from tests.unit.plugins.base import MockBasePlugin

__all__ = ["ChangeTTSImplementationAdminPluginTestCase"]


class ChangeTTSImplementationAdminPluginForTest(ChangeTTSImplementationAdminPlugin, MockBasePlugin):
    pass


class ChangeTTSImplementationAdminPluginTestCase(BasePluginTestCase):
    def test_run_success_sequence_1(self):
        set_config_option("tts", "implementation", "invalid", write_to_disk=True)
        self.assertEqual(get_config_option("tts", "implementation", "str"), "invalid")
        self.assertConfigFileContainsValue(self._config_path, "tts", "implementation", "invalid")

        plugin = ChangeTTSImplementationAdminPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})
        plugin.run(sequence="1")

        self.assertEqual(get_config_option("tts", "implementation", "str"), "gtts")
        self.assertConfigFileContainsValue(self._config_path, "tts", "implementation", "gtts")

        expected_text = "TTS mode changed to online."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)

    def test_run_success_sequence_2(self):
        set_config_option("tts", "implementation", "invalid", write_to_disk=True)
        self.assertEqual(get_config_option("tts", "implementation", "str"), "invalid")

        plugin = ChangeTTSImplementationAdminPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})
        plugin.run(sequence="2")

        self.assertEqual(get_config_option("tts", "implementation", "str"), "espeak")
        self.assertConfigFileContainsValue(self._config_path, "tts", "implementation", "espeak")

        expected_text = "TTS mode changed to offline."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)
