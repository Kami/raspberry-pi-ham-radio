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

from typing import List

import os

from radio_bridge.configuration import get_plugin_config_option
from radio_bridge.configuration import set_plugin_config_option
from radio_bridge.plugins.base import BasePlugin
from radio_bridge.plugins import get_plugins_with_dtmf_sequence

from tests.unit.base import BaseTestCase

# TODO: Use debug log level for tests
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../../conf/logging.tests.conf"))

__all__ = ["BasePluginTestCase", "BaseAdminPluginTestCase", "MockBasePlugin"]


class MockBasePlugin(BasePlugin):
    mock_said_text: List[str]

    def __init__(self, *args, **kwargs):
        super(MockBasePlugin, self).__init__(*args, **kwargs)
        self.mock_said_text = []

    def say(self, text: str):
        """
        Mock say function which records said text on the class instance variable.
        """
        self.mock_said_text.append(text)

    def reset_mock_values(self):
        self.mock_said_text = []


class BasePluginTestCase(BaseTestCase):
    """
    Base class for plugin test cases.
    """

    pass


class BaseAdminPluginTestCase(BasePluginTestCase):
    """
    Base class for admin plugin test cases.
    """

    def assertAllPluginsAreDisabled(self, include_admin=False):
        plugins = get_plugins_with_dtmf_sequence(include_admin=include_admin)

        for plugin_instance in plugins.values():
            value = get_plugin_config_option(plugin_instance.ID, "enable", "bool")
            self.assertFalse(
                value, "Plugin %s is enabled, but it should be disabled" % (plugin_instance.ID)
            )

    def assertAllPluginsAreEnabled(self, include_admin=False):
        plugins = get_plugins_with_dtmf_sequence(include_admin=include_admin)

        for plugin_instance in plugins.values():
            value = get_plugin_config_option(plugin_instance.ID, "enable", "bool")
            self.assertTrue(
                value, "Plugin %s is disabled, but it should be enabled" % (plugin_instance.ID)
            )

    def _disable_all_plugins(self, include_admin=False):
        plugins = get_plugins_with_dtmf_sequence(include_admin=include_admin)

        for plugin_instance in plugins.values():
            set_plugin_config_option(plugin_instance.ID, "enable", "False", write_to_disk=False)

    def _enable_all_plugins(self, include_admin=False):
        plugins = get_plugins_with_dtmf_sequence(include_admin=include_admin)

        for plugin_instance in plugins.values():
            set_plugin_config_option(plugin_instance.ID, "enable", "True", write_to_disk=False)
