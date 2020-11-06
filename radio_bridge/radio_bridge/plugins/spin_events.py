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

import structlog
import requests
import xmltodict
from expiringdict import ExpiringDict

from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.configuration import get_plugin_config_option

LOG = structlog.getLogger(__name__)

DEFAULT_URL = "https://spin3.sos112.si/api/javno/ODRSS/false"

URL_RESPONSE_CACHE = ExpiringDict(max_len=20, max_age_seconds=(3 * 60))

__all__ = ["SPINEventsPlugin"]


class SPINEventsPlugin(BaseDTMFPlugin):
    ID = "spin_events"
    NAME = "SPIN Events"
    DESCRIPTION = "Events from SPIN SOS Portal"
    REQUIRES_INTERNET_CONNECTION = True
    DEFAULT_LANGUAGE = "sl_SI"
    SUPPORTED_LANGUAGES = ["sl_SI"]

    DTMF_SEQUENCE = get_plugin_config_option(ID, "dtmf_sequence", fallback="26")

    _skipload_ = get_plugin_config_option(ID, "enable", "bool", fallback=True) is False

    def run(self):
        url = self._config.get("url", DEFAULT_URL)

        response = requests.get(url)

        with open("1.xml", "w") as fp:
            fp.write(response.text)
        data = xmltodict.parse(response.text)

        result = []

        for item in data["rss"]["channel"]["item"][:5]:
            result.append(item["description"])

        text_to_say = "\n".join(result)
        self.say(text=text_to_say, language=self._language)
