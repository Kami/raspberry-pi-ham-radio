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

import os

import configparser

import structlog

__all__ = ["get_config", "get_plugin_config", "get_plugin_config_option"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../"))

DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "../conf/radio_bridge.conf"))
CONFIG_PATH = os.environ.get("RADIO_BRIDGE_CONFIG_PATH", DEFAULT_CONFIG_PATH)

VALID_TTS_IMPLEMENTATIONS = []

VALID_DTMF_DECODER_IMPLEMENTATION = []

DEFAULT_VALUES = {
    "main": {
        "logging_config": "{rootdir}/conf/logging.conf",
        "dev_mode": False,
        "emulator_mode": False,
    },
    "tx": {
        "mode": "vox",
        "max_tx_time": 120,
        "gpio_pin": 10,
        "callsign": "TEST",
    },
    "audio": {
        "input_device_index": 0,
        "sample_rate": 48000,
    },
    "tts": {
        "implementation": "gtts",
        "enable_cache": True,
        "cache_directory": "/tmp/tts-audio-cache",
    },
    "dtmf": {
        "implementation": "fft_2",
    },
    "plugins": {
        "executor": "native",
        "max_tx_time": 120,
    },
}

CONFIG = None

LOG = structlog.get_logger()


def load_and_parse_config(config_path: str, validate: bool = True):
    global CONFIG

    log = LOG.bind(config_path=config_path)

    LOG.debug("Loading config from %s" % (config_path))

    if not os.path.isfile(config_path):
        raise ValueError("Config file %s doesn't exist" % (config_path))

    config = configparser.ConfigParser()
    config.read_dict(DEFAULT_VALUES)
    config.read(config_path)

    if validate:
        log.debug("Validating config")
        config = validate_config(config)
        log.debug("Config validated")

    CONFIG = config


def validate_config(config):
    config["main"]["logging_config"] = config["main"]["logging_config"].replace(
        "{rootdir}", ROOT_DIR
    )

    if not os.path.isfile(config["main"]["logging_config"]):
        raise ValueError(
            "Logging config %s doesn't exist or it's not a file"
            % (config["main"]["logging_config"])
        )

    callsign = config["tx"]["callsign"]
    callsign_ext = os.path.splitext(callsign)[1]

    if callsign_ext:
        if callsign_ext not in [".mp3", ".mp3"]:
            raise ValueError("Supported audio file extensions are: .mp3,.wav")

        if not os.path.isfile(callsign):
            raise ValueError("File %s doesn't exist" % (callsign))

    if config["tx"]["mode"] not in ["vox", "gpio"]:
        raise ValueError(
            "Invalid tx.mode value: %s. Valid values: vox, gpio" % (config["tx"]["mode"])
        )

    if config["tts"]["implementation"] not in ["gtts", "espeak"]:
        raise ValueError(
            "Invalid tts.library value: %s. Valid values: gtts, espeak"
            % (config["tts"]["implementation"])
        )

    if config["plugins"]["executor"] not in ["native", "process"]:
        raise ValueError(
            "Invalid plugins.executor value: %s. Valid values: native, processs"
            % (config["plugins"]["exeecution_model"])
        )

    return config


def get_config() -> configparser.ConfigParser:
    """
    Retrieved loaded and parsed config instance.

    If config hasn't be loaded yet, it will be loaded and parsed by this method.
    """
    global CONFIG

    if not CONFIG:
        load_and_parse_config(CONFIG_PATH)

    assert CONFIG is not None
    return CONFIG


def get_plugin_config(plugin_id: str) -> dict:
    """
    Return plugin config for the provided plugin.
    """
    try:
        plugin_config = dict(get_config()["plugin:%s" % (plugin_id)])
        LOG.debug("Found config for plugin %s" % (plugin_id), config=plugin_config)
    except KeyError:
        plugin_config = {}

    return plugin_config


def get_plugin_config_option(
    plugin_id: str, option: str, fallback: Any = None, get_method: str = "get"
) -> Any:
    """
    Return configuration option for the provided plugin and option name.
    """
    config = get_config()
    result = getattr(config, get_method)("plugin:%s" % (plugin_id), option, fallback=fallback)
    return result
    return value
