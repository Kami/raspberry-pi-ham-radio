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

from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.configuration import get_config
from radio_bridge.plugins import get_plugins_with_dtmf_sequence

__all__ = ["HelpPlugin"]


class HelpPlugin(BaseDTMFPlugin):
    """
    Plugin which says all the available commands.
    """

    ID = "help"
    NAME = "Help Plugin"
    DESCRIPTION = "List available commands."
    REQUIRES_INTERNET_CONNECTION = False
    DTMF_SEQUENCE = get_config().get("plugin:help", "dtmf_sequence", fallback="12")

    _skipload_ = get_config().getboolean("plugin:help", "enable", fallback=True) is False

    def run(self):
        plugins = get_plugins_with_dtmf_sequence(include_admin=False)

        text_to_say = "Available commands:"

        for index, plugin_class in enumerate(plugins.values()):
            # Skip admin plugins
            sequence_text = ""
            for char in plugin_class.DTMF_SEQUENCE:
                sequence_text += char + " "

            text_to_say += "\n%s. Sequence %s. %s" % (
                index + 1,
                sequence_text,
                plugin_class.DESCRIPTION,
            )

        self.say(text_to_say)
