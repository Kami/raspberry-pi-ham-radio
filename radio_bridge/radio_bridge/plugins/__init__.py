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
from radio_bridge.plugins.base import BaseAdminDTMFPlugin
from radio_bridge.plugins.base import BaseAdminDTMFWithDataPlugin
from radio_bridge.configuration import get_plugin_config

import structlog
import pluginlib

# Maps DTMF sequence to a plugin class instance (singleton)
DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP: Dict[str, Type[BasePlugin]] = {}

REGISTERED_PLUGINS: Dict[str, Type[BasePlugin]] = {}

LOG = structlog.getLogger(__name__)

INITIALIZED = False


def get_plugin_class_for_dtmf_sequence(sequence: str) -> Optional[Type[BasePlugin]]:
    return DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP.get(sequence, None)


def get_available_plugins() -> Dict[str, Type[BasePlugin]]:
    """
    Return a list of all the available and registered plugins.
    """
    return REGISTERED_PLUGINS


def get_plugins_with_dtmf_sequence(include_admin: bool = True) -> Dict[str, Type[BasePlugin]]:
    """
    Return a list of all the available plugins which are triggered via DTMF sequence.
    """
    if include_admin:
        return DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP

    result = {}

    for key, plugin_instance in DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP.items():
        if not isinstance(plugin_instance, BaseAdminDTMFPlugin) and not isinstance(
            plugin_instance, BaseAdminDTMFWithDataPlugin
        ):
            result[key] = plugin_instance

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
        LOG.debug("Found plugin: %s" % (plugin_name))

        # Initialize and validate plugin config
        plugin_config = get_plugin_config(plugin_class.ID)
        plugin_instance = plugin_class()
        plugin_instance.initialize(config=plugin_config)

        REGISTERED_PLUGINS[plugin_name] = plugin_instance

        dtmf_sequence = plugin_class.DTMF_SEQUENCE

        if dtmf_sequence in DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP:
            raise ValueError(
                "DTMF sequence #%s is already registered for another plugin (%s)"
                % (dtmf_sequence, DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP[dtmf_sequence])
            )

        DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP[dtmf_sequence] = plugin_instance
        LOG.debug("Registered plugin %s with DTMF sequence #%s" % (plugin_name, dtmf_sequence))

    for plugin_name, plugin_class in plugins["NonDTMFPlugin"].items():
        LOG.debug("Found plugin: %s" % (plugin_name))

        # Initialize and validate plugin config
        plugin_config = get_plugin_config(plugin_class.ID)
        plugin_instance = plugin_class()
        plugin_instance.initialize(config=plugin_config)

        REGISTERED_PLUGINS[plugin_name] = plugin_instance
        LOG.debug("Registered plugin %s" % (plugin_name))

    INITIALIZED = True


if not INITIALIZED:
    _load_and_register_plugins()
