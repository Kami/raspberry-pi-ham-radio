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

from wx_server.io import get_weather_observation_for_date

from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.configuration import get_config
from radio_bridge.utils import weather as weather_utils

__all__ = ["LocalWeatherPlugin"]


class LocalWeatherPlugin(BaseDTMFPlugin):
    """
    Plugin which says weather information for the weather station which is running local and sending
    data to Weather Server connected to this Raspberry Pi instance.
    """

    ID = "local_weather"
    NAME = "Current weather"
    DESCRIPTION = "Current weather information for local weather station."
    REQUIRES_INTERNET_CONNECTION = False
    DTMF_SEQUENCE = get_config().get("plugin:local_weather", "dtmf_sequence", fallback="31")

    _skipload_ = get_config().getboolean("plugin:local_weather", "enable", fallback=True) == False

    def run(self):
        # 1. Retrieve local weather data from disk
        date = datetime.datetime.utcnow()

        station_id = self._config.get("weather_station_id", "default")

        observation_pb = get_weather_observation_for_date(station_id=station_id, date=date)
        if not observation_pb:
            self.say("No recent weather observation found.")
            return

        # 2. Convert it to text and say it
        text = weather_utils.observation_pb_to_text(observation_pb)
        self.say(text)
