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

__all__ = ["AdminTestPlugin"]


class AdminTestPlugin(BaseAdminDTMFPlugin):
    ID = "admin_test"
    NAME = "Test Plugin"
    DESCRIPTION = "Test Admin Plugin"
    DTMF_SEQUENCE = "91"

    def run(self):
        self.say("Admin Test Plugin")
