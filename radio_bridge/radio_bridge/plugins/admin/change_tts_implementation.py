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

__all__ = ["ChangeTTSImplementationPlugin"]


class ChangeTTSImplementationPlugin(BaseAdminDTMFWithDataPlugin):
    ID = "change_tts_implementation"
    NAME = "Change TTS implementation"
    DESCRIPTION = "Change TTS implementation to online / offline"

    # 92???1 - To change it to online one (gtts)
    # 92???2 - To change it to offline one (espeak)
    DTMF_SEQUENCE = "92?"

    def run(self, sequence: str):
        # TODO: Actually change TTS mode
        if sequence == "1":
            self.say("TTS mode changed to online")
        elif sequence == "2":
            self.say("TTS mode changes to offline")
        else:
            self.say("Invalid TTS mode value")
