from typing import Dict
from typing import Type
from typing import Optional

from radio_bridge.plugins.base import BasePlugin

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


def get_plugins_with_dtmf_sequence() -> Dict[str, Type[BasePlugin]]:
    """
    Return a list of all the available plugins which are triggered via DTMF sequence.
    """
    return DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP


def _load_and_register_plugins() -> None:
    global INITIALIZED, REGISTERED_PLUGINS

    if INITIALIZED:
        return

    loader = pluginlib.PluginLoader(modules=["radio_bridge.plugins"])
    plugins = loader.plugins

    for plugin_name, plugin_class in plugins["DTMFPlugin"].items():
        LOG.debug("Found plugin: %s" % (plugin_name))

        REGISTERED_PLUGINS[plugin_name] = plugin_class()

        dtmf_sequence = plugin_class.DTMF_SEQUENCE

        if dtmf_sequence:
            if dtmf_sequence in DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP:
                raise ValueError("DTMF sequence #%s is already registered for another plugin" % (dtmf_sequence))

            DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP[dtmf_sequence] = plugin_class()
            LOG.debug("Registered plugin %s with DTMF sequence #%s" % (plugin_name, dtmf_sequence))
        else:
            LOG.debug("Registered plugin %s" % (plugin_name))

    INITIALIZED = True


if not INITIALIZED:
    _load_and_register_plugins()
