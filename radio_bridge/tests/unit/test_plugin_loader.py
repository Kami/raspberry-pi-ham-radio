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

import radio_bridge.plugins

from radio_bridge.plugins import _validate_dtmf_sequence

__all__ = ["PluginLoaderTestCase"]


class PluginLoaderTestCase(unittest.TestCase):
    def setUp(self):
        super(PluginLoaderTestCase, self).setUp()

        radio_bridge.plugins.DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP = {}

    def tearDown(self):
        super(PluginLoaderTestCase, self).tearDown()

        radio_bridge.plugins.DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP = {}

    def test_verify_dtmf_sequence(self):
        # Repeated DTMF sequences
        invalid_sequences = [
            "00",
            "11",
            "1233",
            "54899",
            "7777",
        ]

        for invalid_sequence in invalid_sequences:
            plugin_class = mock.Mock()
            plugin_class.NAME = "MOCK"
            plugin_class.DTMF_SEQUENCE = invalid_sequence

            expected_msg = r'Plugin "MOCK" contains repeated DTMF sequence numbers \(%s\).' % (
                invalid_sequence
            )

            self.assertRaisesRegex(
                ValueError, expected_msg, _validate_dtmf_sequence, plugin_class=plugin_class
            )

        # This sequence is already registered
        plugin_class = mock.Mock()
        plugin_class.NAME = "MOCK1"
        plugin_class.DTMF_SEQUENCE = "21"

        radio_bridge.plugins.DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP["21"] = plugin_class

        expected_msg = r'DTMF sequence "21" is already registered for another plugin \(MOCK1\)'
        self.assertRaisesRegex(
            ValueError, expected_msg, _validate_dtmf_sequence, plugin_class=plugin_class
        )
