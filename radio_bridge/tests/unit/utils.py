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

import configparser

import radio_bridge.configuration

__all__ = ["use_mock_config", "reset_config"]


def use_mock_config(mock_config: dict) -> configparser.ConfigParser:
    """
    Use mock configuration values from the provided dictionary.
    """
    config = configparser.ConfigParser()
    config.read_dict(radio_bridge.configuration.DEFAULT_VALUES)
    config.read_dict(mock_config)

    radio_bridge.configuration.CONFIG = config

    return radio_bridge.configuration.CONFIG


def reset_config() -> configparser.ConfigParser:
    """
    Reset config to the default values.
    """
    config = configparser.ConfigParser()
    config.read_dict(radio_bridge.configuration.DEFAULT_VALUES)

    radio_bridge.configuration.CONFIG = config

    return radio_bridge.configuration.CONFIG
