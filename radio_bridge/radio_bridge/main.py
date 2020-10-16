from typing import Tuple
from typing import Callable

import os
import fnmatch
import functools
import threading

import structlog

from apscheduler.schedulers.background import BackgroundScheduler

from wx_server.configuration import load_and_parse_config as wx_server_load_and_parse_config

from radio_bridge.configuration import get_config
from radio_bridge.log import configure_logging
from radio_bridge.rx import RX
from radio_bridge.dtmf import DTMFDecoder
from radio_bridge.plugins import get_available_plugins
from radio_bridge.plugins import get_plugins_with_dtmf_sequence
from radio_bridge.plugins.base import BasePlugin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../conf/logging.conf'))
DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../conf/radio_bridge.conf'))

DEFAULT_WX_SERVER_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../../wx_server/conf/wx_server.conf'))
WX_SERVER_CONFIG_PATH = os.environ.get("WX_SERVER_CONFIG_PATH", DEFAULT_WX_SERVER_CONFIG_PATH)

LOG = structlog.getLogger(__name__)

# Maximum transmit time in seconds. This acts as a safe guard and ensures TX functionality on the
# radio is automatically disabled if it has been enabled for more than this amount of seconds.
MAX_TRANSMIT_TIME = 120

# Maximum length for DTMF sequences
MAX_SEQUENCE_LENGTH = 6


class RadioBridgeServer(object):
    def __init__(self):
        self._started = False

        self._all_plugins = get_available_plugins()
        self._dtmf_plugins = get_plugins_with_dtmf_sequence()
        self._sequence_to_plugin_map = self._dtmf_plugins
        print(self._dtmf_plugins)

        config = get_config()

        self._dtmf_decoder = DTMFDecoder()
        self._rx = RX(input_device_index=int(config["audio"]["input_device_index"]),
                      rate=int(config["audio"]["sample_rate"]))

        self._scheduler = BackgroundScheduler()

        # Holds a list of ids for cron jobs which should run during the next iteration of the main loop
        self._cron_jobs_to_run_lock = threading.Lock()
        self._cron_jobs_to_run = []

    def start(self):
        self._started = True

        config = get_config()
        configure_logging(config["main"]["logging_config"])
        wx_server_load_and_parse_config(WX_SERVER_CONFIG_PATH)

        LOG.info("Active plugins: %s" % (self._all_plugins))

        # Start the scheduler
        self._scheduler.start()

        # Add any configured jobs to the scheduler
        cron_plugin = self._all_plugins["CronSayPlugin"]
        jobs = cron_plugin.get_scheduler_jobs()

        def add_job_to_jobs_to_run(job_id):
            def add_job_to_jobs_to_run_inner():
                self._cron_jobs_to_run_lock.acquire()

                try:
                    self._cron_jobs_to_run.append(job_id)
                finally:
                    self._cron_jobs_to_run_lock.release()

            return add_job_to_jobs_to_run_inner

        for job_id, job_trigger in jobs:
            self._scheduler.add_job(add_job_to_jobs_to_run(job_id),
                                    trigger=job_trigger,
                                    id=job_id)

        LOG.info("Radio Bridge Server Started")

        # Run main read on input loop and invoke corresponding plugin callbacks
        self._main_loop()

    def _main_loop(self) -> None:
        # Read sequence and invoke any matching plugins
        last_char = None
        read_sequence = ""
        iteration_counter = 0

        # How many loop iterations before we reset the read_sequence array
        max_loop_iterations = 15

        while self._started:
            self._run_scheduled_jobs()

            # TODO: Check if there are any cron jobs scheduled to run now and run them
            if iteration_counter >= max_loop_iterations:
                # Max iterations reached, reset read_sequence and start from scratch
                LOG.info("Max iterations reached, reseting read_sequence and iteration counter")

                read_sequence = ""
                iteration_counter = 0

            self._rx.record_audio()
            char = self._dtmf_decoder.decode()

            if char != last_char:
                if not char:
                    iteration_counter += 1
                    continue

                iteration_counter = 0
                read_sequence += char

                LOG.info("Got char %s, current sequence: %s" % (char, read_sequence))

                # If sequence is valid
                plugin, callback = self._get_plugin_for_dtmf_sequence(sequence=read_sequence)

                if plugin or len(read_sequence) > MAX_SEQUENCE_LENGTH:
                    if plugin:
                        LOG.info("Found valid sequence \"%s\", invoking plugin \"%s\"" % (read_sequence,
                                                                                          plugin.NAME))
                        callback()
                    else:
                        LOG.info("Max sequence length limit reached, resetting sequence")

                    read_sequence = ""
            else:
                iteration_counter += 1
                continue

            last_char = char

    def _get_plugin_for_dtmf_sequence(self, sequence: str) -> Tuple[BasePlugin, Callable]:
        """
        Retrieve reference to the Plugin class instance and pre-applied plugin.run() method for the
        provided DTMF sequence (if any is found registered for that sequence).
        """
        for plugin_sequence, plugin_instance in self._sequence_to_plugin_map.items():
            if fnmatch.fnmatch(sequence, plugin_sequence):
                if "?" in plugin_sequence:
                    data_sequence = sequence.replace(plugin_sequence.split("?", 1)[0], "")
                    callback = functools.partial(plugin_instance.run, sequence=data_sequence)
                else:
                    callback = plugin_instance_run

                return plugin_instance, callback

        return None, None

    def _run_scheduled_jobs(self) -> None:
        """
        Function which runs as part of every loop iteration and checks if there are any scheduled
        jobs which should run.

        If they are, it runs them sequentially in order and removes them from jobs to run at the end.
        """
        jobs_to_run = self._cron_jobs_to_run[:]

        LOG.trace("Jobs scheduled to run: %s" % (jobs_to_run))

        cron_plugin = self._all_plugins["CronSayPlugin"]
        # TODO: If there is a "pile up", auto drop old jobs to make sure we don't end up stick in
        # infinite job execution loop

        for job_id in jobs_to_run:
            LOG.debug("Running scheduled job: %s" % (job_id))

            try:
                cron_plugin.run(job_id=job_id)
            finally:
                self._cron_jobs_to_run_lock.acquire()
                self._cron_jobs_to_run.remove(job_id)
                self._cron_jobs_to_run_lock.release()

    def stop(self):
        self._started = False


if __name__ == "__main__":
    server = RadioBridgeServer()
    server.start()
