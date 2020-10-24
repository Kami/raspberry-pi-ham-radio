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

import time
import unittest

from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.plugins.executor import PluginExecutor

from tests.unit.utils import use_mock_config
from tests.unit.utils import reset_config


class MockDTMFPlugin(BaseDTMFPlugin):
    ID = "mock"
    NAME = "mock"
    DTMF_SEQUENCE = "01"

    def run(self):
        return "success"


class MockDTMFWithDataPlugin(BaseDTMFPlugin):
    ID = "mock_with_data"
    NAME = "mock"
    DTMF_SEQUENCE = "02??"

    def run(self):
        time.sleep(10)
        return "failure"


class NativePluginExecutorTestCase(unittest.TestCase):
    def setUp(self):
        super(NativePluginExecutorTestCase, self).setUp()
        self._executor = PluginExecutor(implementation="native")

    def tearDown(self):
        super(NativePluginExecutorTestCase, self).tearDown()
        reset_config()

    def test_run_success(self):
        self.assertEqual(self._executor._plugin_execution_stats["mock"]["success"], 0)

        result = self._executor.run(plugin=MockDTMFPlugin())
        self.assertEqual(result, "success")
        self.assertEqual(self._executor._plugin_execution_stats["mock"]["success"], 1)

    def test_minimum_run_time(self):
        mock_config = {
            "tx": {
                "callsign": "T",
            },
            "plugin:mock": {
                "minimum_run_interval": 10,
            },
        }
        use_mock_config(mock_config)

        executor = PluginExecutor(implementation="native")
        self.assertEqual(executor._plugin_execution_stats["mock"]["success"], 0)
        self.assertEqual(executor._plugin_execution_stats["mock"]["refuse_to_run"], 0)

        result = executor.run(plugin=MockDTMFPlugin())
        self.assertEqual(result, "success")
        self.assertEqual(executor._plugin_execution_stats["mock"]["success"], 1)
        self.assertEqual(executor._plugin_execution_stats["mock"]["refuse_to_run"], 0)

        result = executor.run(plugin=MockDTMFPlugin())
        self.assertEqual(result, None)
        self.assertEqual(executor._plugin_execution_stats["mock"]["success"], 1)
        self.assertEqual(executor._plugin_execution_stats["mock"]["refuse_to_run"], 1)

        executor._plugin_run_times["mock"] = 0

        result = executor.run(plugin=MockDTMFPlugin())
        self.assertEqual(result, "success")
        self.assertEqual(executor._plugin_execution_stats["mock"]["success"], 2)
        self.assertEqual(executor._plugin_execution_stats["mock"]["refuse_to_run"], 1)


class ProcessPluginExecutorTestCase(unittest.TestCase):
    def setUp(self):
        super(ProcessPluginExecutorTestCase, self).setUp()

        mock_config = {
            "tx": {
                "callsign": "T",
            },
            "plugins": {
                "max_run_time": 1,
            },
        }
        use_mock_config(mock_config)

        self._executor = PluginExecutor(implementation="process")

    def tearDown(self):
        super(ProcessPluginExecutorTestCase, self).tearDown()
        reset_config()

    def test_run_success(self):
        self.assertEqual(self._executor._plugin_execution_stats["mock"]["success"], 0)

        result = self._executor.run(plugin=MockDTMFPlugin())
        self.assertEqual(result, "success")
        self.assertEqual(self._executor._plugin_execution_stats["mock"]["success"], 1)

    def test_run_timeout_reached_plugin_process_killed(self):
        self.assertEqual(self._executor._plugin_execution_stats["mock_with_data"]["timeout"], 0)

        result = self._executor.run(plugin=MockDTMFWithDataPlugin())
        self.assertEqual(result, None)
        self.assertEqual(self._executor._plugin_execution_stats["mock_with_data"]["timeout"], 1)
