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
import unittest

from radio_bridge.log import configure_logging
from radio_bridge.plugins.base import BasePlugin

# TODO: Use debug log level for tests
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../../conf/logging.tests.conf"))

__all__ = ["BasePluginTestCase", "MockBasePlugin"]


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


class BasePluginTestCase(unittest.TestCase):
    """
    Base class for plugin test cases.
    """

    @classmethod
    def setUpClass(cls):
        configure_logging(LOGGING_CONFIG_PATH)
