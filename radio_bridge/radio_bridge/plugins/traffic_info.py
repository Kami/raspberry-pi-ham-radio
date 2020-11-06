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

from typing import Optional
from typing import Tuple

import json
import urllib.parse

import structlog
import requests
from expiringdict import ExpiringDict

from radio_bridge.plugins.base import BaseDTMFWithDataPlugin
from radio_bridge.configuration import get_plugin_config_option

LOG = structlog.getLogger(__name__)

BASE_URL = "https://www.promet.si/dc/"

TEXT_NO_EVENTS = {
    "en_US": "No recent events.",
    "sl_SI": "Ni dogodkov.",
}

TEXT_NO_BORDER_CROSSING_DATA = {
    "en_US": "No reported delays.",
    "sl_SI": "Ni cakalnih dob.",
}

# Dictionary where we stored cached HTTP responses to avoid re-fetching the data when it's not
# necessary.
URL_RESPONSE_CACHE = ExpiringDict(max_len=20, max_age_seconds=(5 * 60))

__all__ = ["TrafficInfoPlugin"]


class TrafficInfoPlugin(BaseDTMFWithDataPlugin):
    ID = "traffic_info"
    NAME = "Traffic Events and Border Crossings info"
    DESCRIPTION = "Traffic events and border crossings delays information"
    REQUIRES_INTERNET_CONNECTION = True
    DEFAULT_LANGUAGE = "en_US"
    SUPPORTED_LANGUAGES = ["en_US", "sl_SI"]
    # 1 for traffic events
    # 2 for border crossing times
    DTMF_SEQUENCE = get_plugin_config_option(ID, "dtmf_sequence", fallback="25?")

    _skipload_ = get_plugin_config_option(ID, "enable", "bool", fallback=True) is False

    def run(self, sequence: str):
        # TODO: Query params based on language
        if sequence not in ["1", "2"]:
            self.say(text="Invalid sequence.")
            return

        username = self._config.get("username", None)
        password = self._config.get("password", None)

        if not password or not username:
            LOG.warning(
                "plugin:traffic_info.username and plugin:traffic_info.password config "
                "option is not set so traffic report and border crossing delays can't "
                "be retrieved"
            )
            self.say(text="Plugin has not been configured correctly by the admin.")
            return

        auth = (username, password)

        # TODO: Normalize and clean up text to make it more suitable for tts
        language = self._config.get("language", "en_US")

        if sequence == "1":
            text_to_say = self._get_traffic_events_text_to_say(auth=auth, language=language)
        elif sequence == "2":
            # Border crossings wait times API only supports English
            text_to_say = self._get_border_delays_text_to_say(auth=auth, language=language)

        self.say(text=text_to_say, language=language)

    def _get_traffic_events_text_to_say(
        self, auth: Optional[Tuple[str, str]] = None, language: str = "en_US"
    ) -> str:
        """
        Return text which should be read for the traffic events.
        """
        method = "b2b.dogodki.json"
        query_params = {"language": language}

        query_params["eventtype"] = get_plugin_config_option(
            self.ID, "event_types", "str", fallback="all"
        )
        query_params["roadtype"] = get_plugin_config_option(
            self.ID, "road_types", "str", fallback="all"
        )

        success, data = self._retrieve_and_parse_data_for_method(
            method=method, query_params=query_params, auth=auth
        )

        if not success:
            return "Failed to retrieve traffic events data."

        items = []

        items_count = get_plugin_config_option(self.ID, "items_count", "int", fallback=5)

        for entry in data.get("features", [])[:items_count]:
            item = "%s" % entry.get("properties", {}).get("opis", None)

            if not item:
                continue

            items.append(item)

        result = "\n".join(items)

        if not result:
            result = TEXT_NO_EVENTS[language]

        return result

    def _get_border_delays_text_to_say(
        self, auth: Optional[Tuple[str, str]] = None, language: str = "en_US"
    ) -> str:
        method = "b2b.borderdelays.geojson"
        success, data = self._retrieve_and_parse_data_for_method(method=method, auth=auth)

        if not success:
            return "Failed to retrieve border crossings delays data."

        items = []

        items_count = get_plugin_config_option(self.ID, "items_count", "int", fallback=5)

        for entry in data.get("features", [])[:items_count]:
            item = "%s" % entry.get("properties", {}).get("Description_i18n", {}).get(
                language, None
            )

            if not item:
                continue

            items.append(item)

        result = "\n".join(items)

        if not result:
            result = TEXT_NO_BORDER_CROSSING_DATA[language]

        return result

    def _get_full_url(self, method: str, query_params: Optional[dict] = None) -> str:
        url = BASE_URL + method

        if query_params:
            url += "?" + urllib.parse.urlencode(query_params)

        return url

    def _retrieve_and_parse_data_for_method(
        self,
        method: str,
        query_params: Optional[dict] = None,
        auth: Optional[Tuple[str, str]] = None,
    ) -> Tuple[bool, dict]:
        """
        Retrieve data for the provided API method and parse it.
        """
        url = self._get_full_url(method=method, query_params=query_params)

        if url not in URL_RESPONSE_CACHE or URL_RESPONSE_CACHE[url].status_code != 200:
            LOG.debug("Retrieving data from %s" % (url))
            URL_RESPONSE_CACHE[url] = requests.get(url, auth=auth)
        else:
            LOG.debug("Using existing cached data")

        response = URL_RESPONSE_CACHE[url]

        if response.status_code != 200:
            LOG.warning(
                "Received non-200 response",
                url=url,
                status_code=response.status_code,
                body=response.text[:200] + "...",
            )
            return False, {}

        try:
            result = json.loads(response.content)
        except Exception as e:
            LOG.warning("Failed to parse response data: %s" % (str(e)), url=url)
            return False, {}

        return True, result
