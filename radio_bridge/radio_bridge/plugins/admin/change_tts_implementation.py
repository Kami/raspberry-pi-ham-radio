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

from radio_bridge.plugins.base import BaseAdminDTMFWithDataPlugin
from radio_bridge.configuration import get_plugin_config_option
from radio_bridge.configuration import set_config_option

__all__ = ["ChangeTTSImplementationAdminPlugin"]


class ChangeTTSImplementationAdminPlugin(BaseAdminDTMFWithDataPlugin):
    ID = "change_tts_mode"
    NAME = "Change TTS mode"
    DESCRIPTION = "Change TTS mode to online / offline"
    REQUIRES_INTERNET_CONNECTION = False
    DEFAULT_LANGUAGE = "en_US"
    SUPPORTED_LANGUAGES = ["en_US"]
    # 92???1 - To change it to online one (gtts)
    # 92???2 - To change it to offline one (espeak)
    DTMF_SEQUENCE = get_plugin_config_option(ID, "dtmf_sequence", fallback="92?")

    _skipload_ = get_plugin_config_option(ID, "enable", "bool", fallback=True) is False

    def run(self, sequence: str):
        if sequence == "1":
            set_config_option("tts", "implementation", "gtts", write_to_disk=True)
            self.say("TTS mode changed to online.")
        elif sequence == "2":
            set_config_option("tts", "implementation", "espeak", write_to_disk=True)
            self.say("TTS mode changed to offline.")
        else:
            self.say("Invalid TTS mode value.")
