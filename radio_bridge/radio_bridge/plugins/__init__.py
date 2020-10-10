from typing import Dict
from typing import Type
from typing import Optional

from radio_bridge.plugins.base import BasePlugin

import structlog
import pluginlib

# Maps DTMF sequence to a plugin class instance (singleton)
DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP: Dict[str, Type[BasePlugin]] = {}

LOG = structlog.getLogger(__name__)

INITIALIZED = False

def get_plugin_class_for_dtmf_sequence(sequence: str) -> Optional[Type[BasePlugin]]:
    return DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP.get(sequence, None)


def get_available_plugins() -> Dict[str, Type[BasePlugin]]:
    return DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP

def _load_and_register_plugins() -> None:
    global INITIALIZED

    if INITIALIZED:
        return

    loader = pluginlib.PluginLoader(modules=["radio_bridge.plugins"])
    plugins = loader.plugins

    for plugin_name, plugin_class in plugins["DTMFPlugin"].items():
        LOG.debug("Found plugin: %s" % (plugin_name))

        dtmf_sequence = plugin_class.DTMF_SEQUENCE

        if dtmf_sequence in DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP:
            raise ValueError("DTMF sequence #%s is already registered for another plugin" % (dtmf_sequence))

        DTMF_SEQUENCE_TO_PLUGIN_CLASS_INSTANCE_MAP[dtmf_sequence] = plugin_class()
        LOG.debug("Registered plugin %s with DTMF sequence #%s" % (plugin_name, dtmf_sequence))

    INITIALIZED = True


if not INITIALIZED:
    _load_and_register_plugins()
