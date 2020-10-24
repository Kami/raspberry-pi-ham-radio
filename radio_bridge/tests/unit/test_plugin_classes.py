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

import unittest

import mock

from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.plugins.base import BaseDTMFWithDataPlugin
from radio_bridge.plugins.base import BaseAdminDTMFPlugin
from radio_bridge.plugins.base import BaseAdminDTMFWithDataPlugin

__all__ = [
    "BaseDTMFPluginTestCase",
    "BaseDTMFWithDataPluginTestCase",
    "BaseAdminDTMFPluginTestCase",
    "BaseAdminDTMFWithDataPluginTestCase",
]


class MockDTMFPlugin(BaseDTMFPlugin):
    ID = "mock"
    NAME = "mock"
    DTMF_SEQUENCE = "12"

    def run(self):
        return "success"


class MockDTMFWithDataPlugin(BaseDTMFWithDataPlugin):
    ID = "mock_with_data"
    NAME = "mock"
    DTMF_SEQUENCE = "32??"

    def run(self, sequence: str):
        return sequence


class MockAdminDTMFPlugin(BaseAdminDTMFPlugin):
    ID = "mock_admin"
    NAME = "mock admin"
    DTMF_SEQUENCE = "45"

    def run(self):
        return "success"


class MockAdminDTMFWithDataPlugin(BaseAdminDTMFWithDataPlugin):
    ID = "mock_admin_with_data"
    NAME = "mock admin"
    DTMF_SEQUENCE = "65?"

    def run(self):
        return "success"


class BaseDTMFPluginTestCase(unittest.TestCase):
    def test_matches_dtmf_sequence(self):
        plugin = MockDTMFPlugin()

        self.assertEqual(plugin.matches_dtmf_sequence("12"), (True, (), {}))

        self.assertEqual(plugin.matches_dtmf_sequence("123"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("1"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("2"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("023"), (False, (), {}))


class BaseDTMFWithDataPluginTestCase(unittest.TestCase):
    def test_matches_dtmf_sequence(self):
        plugin = MockDTMFWithDataPlugin()

        self.assertEqual(plugin.matches_dtmf_sequence("3201"), (True, (), {"sequence": "01"}))
        self.assertEqual(plugin.matches_dtmf_sequence("3221"), (True, (), {"sequence": "21"}))
        self.assertEqual(plugin.matches_dtmf_sequence("3295"), (True, (), {"sequence": "95"}))

        self.assertEqual(plugin.matches_dtmf_sequence("32"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("320"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("32567"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("123"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("1"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("2"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("023"), (False, (), {}))


class BaseAdminDTMFPluginTestCase(unittest.TestCase):
    @mock.patch(
        "radio_bridge.plugins.base.validate_otp",
        mock.Mock(side_effect=lambda sequence: sequence == "1234"),
    )
    def test_matches_dtmf_sequence(self):
        plugin = MockAdminDTMFPlugin()

        self.assertEqual(plugin.matches_dtmf_sequence("451234"), (True, (), {}))

        self.assertEqual(plugin.matches_dtmf_sequence("451235"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("45123"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("4512345"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("451"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("45"), (False, (), {}))


class BaseAdminDTMFWithDataPluginTestCase(unittest.TestCase):
    @mock.patch(
        "radio_bridge.plugins.base.validate_otp",
        mock.Mock(side_effect=lambda sequence: sequence == "1234"),
    )
    def test_matches_dtmf_sequence(self):
        plugin = MockAdminDTMFWithDataPlugin()

        self.assertEqual(plugin.matches_dtmf_sequence("6512346"), (True, (), {"sequence": "6"}))
        self.assertEqual(plugin.matches_dtmf_sequence("6512341"), (True, (), {"sequence": "1"}))
        self.assertEqual(plugin.matches_dtmf_sequence("6512343"), (True, (), {"sequence": "3"}))

        self.assertEqual(plugin.matches_dtmf_sequence("65123467"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("651234"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("6512"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("65"), (False, (), {}))
        self.assertEqual(plugin.matches_dtmf_sequence("651"), (False, (), {}))
