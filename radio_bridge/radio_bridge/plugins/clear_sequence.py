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

from radio_bridge.plugins.base import BaseDTMFWithDataPlugin
from radio_bridge.configuration import get_plugin_config_option

"""
Plugin which resets / clears currently accumulated sequence.
"""

__all__ = ["ClearSequencePlugin"]


class ClearSequencePlugin(BaseDTMFWithDataPlugin):
    """
    Special plugin which can be triggered any time and causes currently accumulated DTMF sequence
    to be cleared (this comes handy in case of a typo or similar).
    """

    ID = "clear_sequence"
    NAME = "Clear sequence"
    DESCRIPTION = "Clear currently accumulated DTMF sequence."
    REQUIRES_INTERNET_CONNECTION = False
    DTMF_SEQUENCE = get_plugin_config_option(ID, "dtmf_sequence", fallback="*D*")

    _skipload_ = get_plugin_config_option(ID, "enable", "bool", fallback=True) is False

    def run(self, sequence: str):
        pass
