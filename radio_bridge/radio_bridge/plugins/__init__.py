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
from typing import Type
from typing import Optional

import itertools

from radio_bridge.plugins.base import BasePlugin
from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.plugins.base import BaseAdminDTMFPlugin
from radio_bridge.plugins.base import BaseAdminDTMFWithDataPlugin
from radio_bridge.configuration import get_plugin_config

import structlog
import pluginlib

# Maps plugin name to plugin class instance (singleton) for all the available plugins
REGISTERED_PLUGINS: Dict[str, BasePlugin] = {}

# Maps DTMF sequence to a plugin class instance (singleton)
DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP: Dict[str, BaseDTMFPlugin] = {}

LOG = structlog.getLogger(__name__)

INITIALIZED = False


def get_plugin_class_for_dtmf_sequence(sequence: str) -> Optional[BasePlugin]:
    if not INITIALIZED:
        _load_and_register_plugins()

    return DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP.get(sequence, None)


def get_available_plugins() -> Dict[str, BasePlugin]:
    """
    Return a list of all the available and registered plugins.
    """
    if not INITIALIZED:
        _load_and_register_plugins()

    return REGISTERED_PLUGINS


def get_plugins_with_dtmf_sequence(include_admin: bool = True) -> Dict[str, BaseDTMFPlugin]:
    """
    Return a list of all the available plugins which are triggered via DTMF sequence.
    """
    if not INITIALIZED:
        _load_and_register_plugins()

    if include_admin:
        return DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP

    result = {}

    for key, plugin_instance in DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP.items():
        if not isinstance(plugin_instance, BaseAdminDTMFPlugin) and not isinstance(
            plugin_instance, BaseAdminDTMFWithDataPlugin
        ):
            result[key] = plugin_instance

    result = dict(sorted(result.items(), key=lambda x: x[1].DTMF_SEQUENCE))
    return result


def _load_and_register_plugins() -> None:
    global INITIALIZED, REGISTERED_PLUGINS

    if INITIALIZED:
        return

    loader = pluginlib.PluginLoader(modules=["radio_bridge.plugins", "radio_bridge.plugins.admin"])
    plugins = loader.plugins

    for plugin_name, plugin_class in itertools.chain(
        plugins["DTMFPlugin"].items(),
        plugins["DTMFWithDataPlugin"].items(),
        plugins["AdminDTMFPlugin"].items(),
        plugins["AdminDTMFWithDataPlugin"].items(),
    ):
        if "ForTest" in plugin_name or "Mock" in plugin_name:
            continue

        LOG.debug("Found plugin: %s" % (plugin_name))

        # Initialize and validate plugin config
        plugin_config = get_plugin_config(plugin_class.ID)
        plugin_instance = plugin_class()
        plugin_instance.initialize(config=plugin_config)

        REGISTERED_PLUGINS[plugin_name] = plugin_instance

        dtmf_sequence = _validate_dtmf_sequence(plugin_class=plugin_class)

        DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP[dtmf_sequence] = plugin_instance
        LOG.debug("Registered plugin %s with DTMF sequence #%s" % (plugin_name, dtmf_sequence))

    for plugin_name, plugin_class in plugins["NonDTMFPlugin"].items():
        if "ForTest" in plugin_name or "Mock" in plugin_name:
            continue

        LOG.debug("Found plugin: %s" % (plugin_name))

        # Initialize and validate plugin config
        plugin_config = get_plugin_config(plugin_class.ID)
        plugin_instance = plugin_class()
        plugin_instance.initialize(config=plugin_config)

        REGISTERED_PLUGINS[plugin_name] = plugin_instance
        LOG.debug("Registered plugin %s" % (plugin_name))

    INITIALIZED = True


def _validate_dtmf_sequence(plugin_class: Type[BaseDTMFPlugin]) -> str:
    """
    Verify that the provided plugin contains a valid DTMF sequence.
    """
    dtmf_sequence = plugin_class.DTMF_SEQUENCE

    # Validate sequence is unique
    if dtmf_sequence in DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP:
        raise ValueError(
            'DTMF sequence "%s" is already registered for another plugin (%s)'
            % (dtmf_sequence, DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP[dtmf_sequence].NAME)
        )

    # Validate sequence contains no repeted numbers
    for index in range(1, len(dtmf_sequence)):
        char = dtmf_sequence[index]

        if char == dtmf_sequence[index - 1] and char not in ["?", "*"]:
            raise ValueError(
                'Plugin "%s" contains repeated DTMF sequence numbers (%s). For '
                "better DTMF decoding accuracy, plugins should contain no repeated "
                "sequences" % (plugin_class.NAME, dtmf_sequence)
            )

    return dtmf_sequence
