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

import datetime

import pytz

from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.plugins.errors import InvalidPluginConfigurationValue
from radio_bridge.configuration import get_plugin_config_option

__all__ = ["CurrentTimePlugin"]

TEXT = {
    "en_US": """
Current time is {hour_local} {minute_local} local. {hour_utc} {minute_utc} U T C.
""".strip(),
    "sl_SI": """
Trenuten cas je {hour_local} {minute_local} lokalno. {hour_utc} {minute_utc} U T C.
""".strip(),
}


class CurrentTimePlugin(BaseDTMFPlugin):
    """
    Plugin which says current time.
    """

    ID = "current_time"
    NAME = "Current time"
    DESCRIPTION = "Current date and time."
    REQUIRES_INTERNET_CONNECTION = False
    DEFAULT_LANGUAGE = "en_US"
    SUPPORTED_LANGUAGES = ["en_US", "sl_SI"]
    DTMF_SEQUENCE = get_plugin_config_option(ID, "dtmf_sequence", fallback="21")

    _skipload_ = get_plugin_config_option(ID, "enable", "bool", fallback=True) is False

    def __init__(self):
        super(CurrentTimePlugin, self).__init__()

    def initialize(self, config: dict) -> None:
        """
        Validate plugin specific configuration.
        """
        super(CurrentTimePlugin, self).initialize(config=config)

        # Validate that the specified timezone is correct
        assert config is not None
        local_timezone = config.get("local_timezone")

        if not local_timezone:
            msg = "local_timezone config option is mandatory"
            raise InvalidPluginConfigurationValue(self.ID, "local_timezone", local_timezone, msg)

        try:
            pytz.timezone(local_timezone)
        except Exception as e:
            raise InvalidPluginConfigurationValue(self.ID, "local_timezone", local_timezone, str(e))

    def run(self):
        local_tz = pytz.timezone(self._config["local_timezone"])
        now_utc = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
        now_local = now_utc.astimezone(local_tz)

        text = TEXT[self._language]

        text = text.format(
            hour_local=now_local.hour,
            minute_local=now_local.minute,
            hour_utc=now_utc.hour,
            minute_utc=now_utc.minute,
        )
        self.say(text=text, language=self._language)
