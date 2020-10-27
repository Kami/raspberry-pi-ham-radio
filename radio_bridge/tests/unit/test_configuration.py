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
import time
import unittest
import tempfile
import shutil

import radio_bridge.configuration
from radio_bridge.configuration import _get_config
from radio_bridge.configuration import get_config_option
from radio_bridge.configuration import get_plugin_config
from radio_bridge.configuration import get_plugin_config_option
from radio_bridge.configuration import set_config_option

__all__ = ["ConfigurationTestCase"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../"))

CONFIG_PATH_1 = os.path.abspath(os.path.join(BASE_DIR, "../fixtures/configs/config1.ini"))


class ConfigurationTestCase(unittest.TestCase):
    def setUp(self):
        super(ConfigurationTestCase, self).setUp()
        self._reset_environ()

        radio_bridge.configuration.CONFIG = None

        _, self._temp_path = tempfile.mkstemp()
        shutil.copy(CONFIG_PATH_1, self._temp_path)

    def tearDown(self):
        super(ConfigurationTestCase, self).tearDown()
        self._reset_environ()

    def _reset_environ(self):
        if "RADIO_BRIDGE_CONFIG_PATH" in os.environ:
            del os.environ["RADIO_BRIDGE_CONFIG_PATH"]

    def test_get_config_success(self):
        # 1. No config specified, only default values should be used
        config = _get_config()
        self.assertEqual(config["main"]["dev_mode"], "False")
        self.assertEqual(config["main"]["emulator_mode"], "False")

        # 2. Custom config specified, should override default values
        os.environ["RADIO_BRIDGE_CONFIG_PATH"] = CONFIG_PATH_1

        config = _get_config(force_load=True)
        self.assertEqual(config["main"]["dev_mode"], "True")
        self.assertEqual(config["main"]["emulator_mode"], "True")
        self.assertEqual(config["tx"]["callsign"], "ABCD")

    def test_get_config_success_reload_on_new_config(self):
        # Verify _get_config() re-loads the config from disk if the version on disk has been
        # modified
        os.environ["RADIO_BRIDGE_CONFIG_PATH"] = self._temp_path

        config = _get_config()
        self.assertEqual(config["main"]["dev_mode"], "True")
        self.assertEqual(config["main"]["emulator_mode"], "True")
        self.assertEqual(config["tx"]["callsign"], "ABCD")

        # Modify config on disk, verify changes are reflected on _get_config()
        with open(self._temp_path, "r") as fp:
            original_content = fp.read()

        time.sleep(1)

        modified_content = original_content.replace("ABCD", "MODIFIED")
        with open(self._temp_path, "w") as fp:
            fp.write(modified_content)

        os.environ["RADIO_BRIDGE_CONFIG_PATH"] = self._temp_path

        config = _get_config()
        self.assertEqual(config["main"]["dev_mode"], "True")
        self.assertEqual(config["main"]["emulator_mode"], "True")
        self.assertEqual(config["tx"]["callsign"], "MODIFIED")

    def test_get_config_option(self):
        os.environ["RADIO_BRIDGE_CONFIG_PATH"] = CONFIG_PATH_1

        value = get_config_option("tx", "callsign", "str")
        self.assertEqual(value, "ABCD")

        value = get_config_option("tx", "invalid", "str", fallback="default")
        self.assertEqual(value, "default")

        value = get_config_option("invalid_section", "callsign", "str", fallback="default1")
        self.assertEqual(value, "default1")

    def test_get_plugin_config_success(self):
        os.environ["RADIO_BRIDGE_CONFIG_PATH"] = CONFIG_PATH_1

        config = get_plugin_config("current_time")
        self.assertEqual(config["dtmf_sequence"], "54")

        config = get_plugin_config("invalid")
        self.assertEqual(config, {})

    def test_get_plugin_config_option(self):
        os.environ["RADIO_BRIDGE_CONFIG_PATH"] = CONFIG_PATH_1

        value = get_plugin_config_option("current_time", "dtmf_sequence", "str")
        self.assertEqual(value, "54")

        value = get_plugin_config_option("current_time", "invalid", "str", fallback="fallback")
        self.assertEqual(value, "fallback")

        value = get_plugin_config_option(
            "current_time_invalid", "invalid", "str", fallback="fallback2"
        )
        self.assertEqual(value, "fallback2")

    def test_set_config_option(self):
        os.environ["RADIO_BRIDGE_CONFIG_PATH"] = self._temp_path

        config = _get_config()
        self.assertEqual(config["tx"]["callsign"], "ABCD")

        set_config_option("tx", "callsign", "UPDATED", write_to_disk=False)

        config = _get_config()
        self.assertEqual(config["tx"]["callsign"], "UPDATED")

        config = _get_config(force_load=True)
        self.assertEqual(config["tx"]["callsign"], "ABCD")

        # Now verify write_to_disk=True
        set_config_option("tx", "callsign", "UPDATED", write_to_disk=True)

        config = _get_config(force_load=True)
        self.assertEqual(config["tx"]["callsign"], "UPDATED")
