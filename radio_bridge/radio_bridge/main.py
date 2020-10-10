import os

import structlog

from wx_server.configuration import load_and_parse_config

from radio_bridge.log import configure_logging
from radio_bridge.dtmf import DTMFSequenceReader
from radio_bridge.plugins import get_available_plugins

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../conf/logging.conf'))

DEFAULT_WX_SERVER_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../../wx_server/conf/wx_server.conf'))
WX_SERVER_CONFIG_PATH = os.environ.get("WX_SERVER_CONFIG_PATH", DEFAULT_WX_SERVER_CONFIG_PATH)

LOG = structlog.getLogger(__name__)


class RadioBridgeServer(object):
    def __init__(self):
        self._started = False

        self._plugins = get_available_plugins()
        self._dtmf_sequence_reader = DTMFSequenceReader(sequence_to_plugin_map=self._plugins)

    def start(self):
        self._started = True

        load_and_parse_config(WX_SERVER_CONFIG_PATH)

        LOG.info("Active plugins: %s" % (self._plugins))

        configure_logging(LOGGING_CONFIG_PATH)

        LOG.info("Radio Bridge Server Started")

        while self._started:
            # Read sequence and invoke any plugin callback
            self._dtmf_sequence_reader.start()

    def stop(self):
        self._started = False


if __name__ == "__main__":
    server = RadioBridgeServer()
    server.start()
