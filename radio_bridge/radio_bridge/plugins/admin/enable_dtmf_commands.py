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
from radio_bridge.configuration import set_config_option
from radio_bridge.plugins import get_plugins_with_dtmf_sequence

__all__ = ["EnableDTMFCommandsAdminPlugin"]


class EnableDTMFCommandsAdminPlugin(BaseAdminDTMFPlugin):
    ID = "enable_dtmf_commands"
    NAME = "Enable DTMF commands"
    DESCRIPTION = "Enable all the non-admin DTMF commands."
    DTMF_SEQUENCE = get_plugin_config_option(ID, "dtmf_sequence", fallback="94")

    _skipload_ = get_plugin_config_option(ID, "enable", "bool", fallback=True) is False

    def run(self):
        plugins = get_plugins_with_dtmf_sequence(include_admin=False)

        for dtmf_sequence, plugin_instance in plugins.items():
            section_name = "plugin:%s" % (plugin_instance.ID)
            set_config_option(section_name, "enable", "True", write_to_disk=True)

        self.say("All non-admin DTMF plugins enabled.")
