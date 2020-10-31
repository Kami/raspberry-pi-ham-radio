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

from typing import Dict
from typing import List

import urllib.parse

import structlog
import requests
import xmltodict
from expiringdict import ExpiringDict

from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.configuration import get_plugin_config_option

LOG = structlog.getLogger(__name__)

BASE_URL = "https://www.promet.si/dc/b2b.dogodki.rss"

# Dictionary where we stored cached HTTP responses to avoid re-fetching the data when it's not
# necessary.
URL_RESPONSE_CACHE = ExpiringDict(max_len=20, max_age_seconds=(5 * 60))


class TrafficEventsPlugin(BaseDTMFPlugin):
    ID = "traffic_events"
    NAME = "Traffic Events"
    DESCRIPTION = "Traffic events and incidents"
    REQUIRES_INTERNET_CONNECTION = True
    DTMF_SEQUENCE = get_plugin_config_option(ID, "dtmf_sequence", fallback="23")

    _skipload_ = get_plugin_config_option(ID, "enable", "bool", fallback=True) is False

    def run(self):
        query_params = {"language": "en_US"}

        query_params["eventtype"] = get_plugin_config_option(
            self.ID, "event_types", "str", fallback="all"
        )
        query_params["roadtype"] = get_plugin_config_option(
            self.ID, "road_types", "str", fallback="all"
        )

        url = self._get_full_url(query_params=query_params)
        response = self._retrieve_data_for_url(url=url)

        if response.status_code != 200:
            LOG.warning(
                "Received non-200 response",
                status_code=response.status_code,
                body=response.text[:200] + "...",
            )
            self.say(text="Failed to retrieve traffic events data.")
            return

        try:
            result = xmltodict.parse(response.content)
            text_to_say = self._entries_to_text_string(entries=result["feed"]["entry"])
        except Exception as e:
            LOG.warning("Failed to parse response data: %s" % (str(e)))
            self.say(text="Failed to retrieve traffic events data.")
            return

        self.say(text=text_to_say)

    def _get_full_url(self, query_params: dict) -> str:
        url = BASE_URL + "?" + urllib.parse.urlencode(query_params)
        return url

    def _retrieve_data_for_url(self, url: str) -> requests.Response:
        if url not in URL_RESPONSE_CACHE:
            LOG.debug("Retrieving traffic events data from %s" % (url))
            URL_RESPONSE_CACHE[url] = requests.get(url)
        else:
            LOG.debug("Using existing cached data")

        response = URL_RESPONSE_CACHE[url]
        return response

    def _entries_to_text_string(self, entries: List[Dict[str, str]], count=5) -> str:
        result = ""

        items = []

        for entry in entries[:count]:
            item = "%s" % entry["summary"]
            items.append(item)

        result = "\n".join(items)
        return result
