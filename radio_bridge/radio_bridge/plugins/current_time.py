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

from radio_bridge.plugins.base import BaseDTMFPlugin

__all__ = ["CurrentTimePlugin"]

TEXT = """
Current time is {hour_local} {minute_local} local. {hour_utc}, {minute_utc} U T C.
""".strip()


class CurrentTimePlugin(BaseDTMFPlugin):
    """
    Plugin which says current time.
    """

    ID = "current_time"
    NAME = "Current time"
    DESCRIPTION = "Current date and time."
    DTMF_SEQUENCE = "23"

    def run(self):
        now_local = datetime.datetime.now()
        now_utc = datetime.datetime.utcnow()

        text = TEXT.format(
            hour_local=now_local.hour,
            minute_local=now_local.minute,
            hour_utc=now_utc.hour,
            minute_utc=now_utc.minute,
        )
        self.say(text=text)
