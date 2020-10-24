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

from typing import Any

__all__ = ["InvalidPluginConfigurationValue", "PluginExecutionTimeoutException"]


class InvalidPluginConfigurationValue(ValueError):
    def __init__(self, plugin_id: str, option_name: str, option_value: Any, error: str):
        message = 'Invalid value "%s" for plugin "%s" and config option "%s": %s' % (
            option_value,
            plugin_id,
            option_name,
            error,
        )
        super(InvalidPluginConfigurationValue, self).__init__(message)

        self.plugin_id = plugin_id
        self.option_name = option_name
        self.option_value = option_value


class PluginExecutionTimeoutException(Exception):
    pass
