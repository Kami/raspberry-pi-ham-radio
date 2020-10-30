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
from typing import Optional
from typing import List

import os
import time

import configparser
from configobj import ConfigObj
import structlog

__all__ = [
    "get_config_option",
    "get_plugin_config",
    "get_plugin_config_option",
    "set_config_option",
    "set_plugin_config_option",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../"))

DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "conf/radio_bridge.conf"))

DEFAULT_VALUES_CONFIG_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "conf/radio_bridge.defaults.conf")
)

VALID_TTS_IMPLEMENTATIONS: List[str] = []
VALID_DTMF_DECODER_IMPLEMENTATION: List[str] = []

# Stores parsed config file reference
CONFIG = None

# Stores unix timestamp of when the config has been loaded and parsed
CONFIG_LOAD_TIME: int = 0

# Special value used so we can differentiate between fallback not being provided and fallback
# being Nont
FALLBACK_NOT_SET_VALUE = "|~*~notset*~|"

LOG = structlog.get_logger()


class ConfigParserConfigObj(ConfigObj):
    """
    Wrapper class around ConfigObj which provides "getboolean" and other methods as provided by the
    upstream ConfigParser class.
    """

    _original_get = ConfigObj.get

    def get(self, section, option=None, fallback=None):
        return get_config_option(section, option, "str", fallback=fallback)

    def getint(self, section: str, option: str, fallback: Any = None):
        return get_config_option(section, option, "int", fallback=fallback)

    def getfloat(self, section: str, option: str, fallback: Any = None):
        return get_config_option(section, option, "float", fallback=fallback)

    def getboolean(self, section: str, option: str, fallback: Any = None):
        return get_config_option(section, option, "bool", fallback=fallback)


def _load_and_parse_config(config_path: Optional[str] = None, validate: bool = True):
    global CONFIG, CONFIG_LOAD_TIME

    log = LOG.bind(config_path=config_path)

    LOG.debug("Loading config from %s" % (config_path))

    if config_path and not os.path.isfile(config_path):
        raise ValueError("Config file %s doesn't exist" % (config_path))

    config = ConfigParserConfigObj(
        DEFAULT_VALUES_CONFIG_PATH, default_encoding="utf-8", write_empty_values=True
    )

    if config_path:
        user_config = ConfigParserConfigObj(
            config_path, default_encoding="utf-8", write_empty_values=True
        )
        config.merge(user_config)

    if validate:
        log.debug("Validating config")
        config = _validate_config(config)
        log.debug("Config validated")

    CONFIG = config
    CONFIG_LOAD_TIME = int(time.time())


def _validate_config(config):
    config["main"]["logging_config"] = config["main"]["logging_config"].replace(
        "{rootdir}", ROOT_DIR
    )

    if not os.path.isfile(config["main"]["logging_config"]):
        raise ValueError(
            "Logging config with path \"%s\" doesn't exist or it's not a file"
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


def _get_config(validate: bool = True, force_load: bool = False) -> configparser.ConfigParser:
    """
    Retrieved loaded and parsed config instance.

    If config hasn't be loaded yet, it will be loaded and parsed by this method.
    """
    global CONFIG

    config_path = os.environ.get("RADIO_BRIDGE_CONFIG_PATH", None)

    if not CONFIG or force_load:
        _load_and_parse_config(config_path=config_path, validate=validate)

    if config_path and CONFIG_LOAD_TIME < int(os.path.getmtime(config_path)):
        LOG.debug("Config file on disk has been updated since we parsed it, re-loading...")
        _load_and_parse_config(config_path=config_path, validate=validate)

    assert CONFIG is not None
    return CONFIG


def get_config_option(
    section: str, option: str, option_type: str = "str", fallback: Any = FALLBACK_NOT_SET_VALUE
) -> Any:
    """
    Return value for the provided config section and option.
    """
    config = _get_config()

    if option_type == "str":
        get_method = "get"
    elif option_type == "int":
        get_method = "as_int"
    elif option_type == "float":
        get_method = "as_loat"
    elif option_type == "bool":
        get_method = "as_bool"
    else:
        raise ValueError("Unsupported option_type: %s" % (option_type))

    section_value = ConfigParserConfigObj._original_get(config, section)

    if section_value is None:
        if fallback != FALLBACK_NOT_SET_VALUE:
            return fallback

        raise ValueError("Section %s is empty or missing" % (section))

    try:
        value = getattr(section_value, get_method)(option)
    except KeyError as e:
        if fallback != FALLBACK_NOT_SET_VALUE:
            return fallback

        raise e

    if value is None and fallback != FALLBACK_NOT_SET_VALUE:
        return fallback

    return value


def get_plugin_config(plugin_id: str) -> dict:
    """
    Return plugin config for the provided plugin.
    """
    try:
        plugin_config = dict(_get_config()["plugin:%s" % (plugin_id)])
        LOG.debug("Found config for plugin %s" % (plugin_id), config=plugin_config)
    except KeyError as e:
        LOG.debug('Missing config entry for plugin "%s": %s' % (plugin_id, str(e)))
        plugin_config = {}

    return plugin_config


def get_plugin_config_option(
    plugin_id: str, option: str, option_type: str = "str", fallback: Any = FALLBACK_NOT_SET_VALUE
) -> Any:
    """
    Return configuration option for the provided plugin and option name.
    """
    section = "plugin:%s" % (plugin_id)
    result = get_config_option(section, option, option_type=option_type, fallback=fallback)

    if result is None and fallback != FALLBACK_NOT_SET_VALUE:
        return fallback

    return result


def set_config_option(section: str, option: str, value: Any, write_to_disk: bool = False) -> bool:
    """
    Function which updates configuration option value.

    By default if "write_to_disk" is False, value will only be updated in memory and not on disk.

    This means it won't be reflected in Plugin processes when using process plugin execution where
    each plugin is executed in a new sub process.
    """
    config = _get_config()
    config_path = os.environ.get("RADIO_BRIDGE_CONFIG_PATH", None)

    try:
        config[section][option] = value
    except KeyError:
        config[section] = {}
        config[section][option] = value

    if write_to_disk and config_path:
        LOG.debug("Writing updated config file to disk", file_path=config_path)
        with open(config_path, "wb") as fp:
            config.write(fp)  # type: ignore

    return True


def set_plugin_config_option(
    plugin_id: str, option: str, value: Any, write_to_disk: bool = False
) -> bool:
    """
    Function which updates config value for a particular plugin.
    """
    section = "plugin:%s" % (plugin_id)
    return set_config_option(
        section=section, option=option, value=value, write_to_disk=write_to_disk
    )
