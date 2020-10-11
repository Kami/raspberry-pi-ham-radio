import os

import structlog

from apscheduler.schedulers.background import BackgroundScheduler

from wx_server.configuration import load_and_parse_config

from radio_bridge.log import configure_logging
from radio_bridge.dtmf import DTMFSequenceReader
from radio_bridge.plugins import get_available_plugins

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../conf/logging.conf'))
DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../conf/radio_bridge.conf'))

DEFAULT_WX_SERVER_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../../wx_server/conf/wx_server.conf'))
WX_SERVER_CONFIG_PATH = os.environ.get("WX_SERVER_CONFIG_PATH", DEFAULT_WX_SERVER_CONFIG_PATH)

CONFIG_PATH = os.environ.get("RADIO_BRIDGE_CONFIG_PATH", DEFAULT_CONFIG_PATH)

LOG = structlog.getLogger(__name__)

# Maximum transmit time in seconds. This acts as a safe guard and ensures TX functionality on the
# radio is automatically disabled if it has been enabled for more than this amount of seconds.
MAX_TRANSMIT_TIME = 120


class RadioBridgeServer(object):
    def __init__(self):
        self._started = False

        self._plugins = get_available_plugins()
        self._dtmf_sequence_reader = DTMFSequenceReader(server=self, sequence_to_plugin_map=self._plugins)

        self._scheduler = BackgroundScheduler()

        self._cron_jobs_to_run = []

    def start(self):
        self._started = True

        self._scheduler.add_job(lambda: self._cron_jobs_to_run.append("a"), "interval", seconds=5)

        load_and_parse_config(WX_SERVER_CONFIG_PATH)

        LOG.info("Active plugins: %s" % (self._plugins))

        configure_logging(LOGGING_CONFIG_PATH)

        # Start the scheduler
        self._scheduler.start()

        LOG.info("Radio Bridge Server Started")

        while self._started:
            # Read sequence and invoke any plugin callback
            self._dtmf_sequence_reader.start()

    def stop(self):
        self._started = False


if __name__ == "__main__":
    server = RadioBridgeServer()
    server.start()
