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

from radio_bridge.plugins.base import BaseAdminDTMFPlugin
from radio_bridge.configuration import get_plugin_config_option
from radio_bridge.configuration import set_plugin_config_option
from radio_bridge.plugins import get_plugins_with_dtmf_sequence

__all__ = ["DisableDTMFCommandsAdminPlugin"]


class DisableDTMFCommandsAdminPlugin(BaseAdminDTMFPlugin):
    ID = "disable_dtmf_commands"
    NAME = "Disable DTMF commands"
    DESCRIPTION = "Disable all the non-admin DTMF commands."
    DTMF_SEQUENCE = get_plugin_config_option(ID, "dtmf_sequence", fallback="93")
    REQUIRES_INTERNET_CONNECTION = False

    _skipload_ = get_plugin_config_option(ID, "enable", "bool", fallback=True) is False

    def run(self):
        plugins = get_plugins_with_dtmf_sequence(include_admin=False)

        for dtmf_sequence, plugin_instance in plugins.items():
            set_plugin_config_option(plugin_instance.ID, "enable", "False", write_to_disk=True)

        self.say("All non-admin DTMF plugins disabled.")
