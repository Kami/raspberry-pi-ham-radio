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
from radio_bridge.configuration import get_config
from radio_bridge.configuration import set_config_option
from radio_bridge.plugins import get_plugins_with_dtmf_sequence

__all__ = ["DisableDTMFCommandsAdminPlugin"]


class DisableDTMFCommandsAdminPlugin(BaseAdminDTMFPlugin):
    ID = "disable_dtmf_commands"
    NAME = "Disable DTMF commands"
    DESCRIPTION = "Disable all the non-admin DTMF commands."
    DTMF_SEQUENCE = "93"

    _skipload_ = (
        get_config().getboolean("plugin:disable_dtmf_commands", "enable", fallback=True) is False
    )

    def run(self):
        config = get_config()
        plugins = get_plugins_with_dtmf_sequence(include_admin=False)

        for dtmf_sequence, plugin_instance in plugins.items():
            section_name = "plugin:%s" % (plugin_instance.ID)

            if config.has_section(section_name):
                set_config_option(section_name, "enable", "False")

        self.say("All non-admin DTMF plugins disabled.")