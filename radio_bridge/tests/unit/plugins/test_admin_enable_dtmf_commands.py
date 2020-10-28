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

from radio_bridge.plugins.admin.enable_dtmf_commands import EnableDTMFCommandsAdminPlugin

from tests.unit.plugins.base import BaseAdminPluginTestCase
from tests.unit.plugins.base import MockBasePlugin

__all__ = ["EnableDTMFCommandsAdminPluginTestCase"]


class EnableDTMFCommandsAdminPluginForTest(EnableDTMFCommandsAdminPlugin, MockBasePlugin):
    pass


class EnableDTMFCommandsAdminPluginTestCase(BaseAdminPluginTestCase):
    def test_run_success_sequence_1(self):
        self._disable_all_plugins(write_to_disk=True)

        # Verify all plugins are disabled
        self.assertAllPluginsAreDisabled(include_admin=False)
        self.assertConfigFileContainsValue(
            self._config_path, "plugin:current_time", "enable", "False"
        )

        # Run plugin
        plugin = EnableDTMFCommandsAdminPluginForTest()
        self.assertEqual(len(plugin.mock_said_text), 0)

        plugin.initialize(config={})
        plugin.run()

        self.assertAllPluginsAreEnabled(include_admin=False)
        self.assertConfigFileContainsValue(
            self._config_path, "plugin:current_time", "enable", "True"
        )

        expected_text = "All non-admin DTMF plugins enabled."

        self.assertEqual(len(plugin.mock_said_text), 1)
        self.assertEqual(plugin.mock_said_text[0], expected_text)
