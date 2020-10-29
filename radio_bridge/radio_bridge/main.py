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

from typing import Tuple
from typing import Dict
from typing import List
from typing import Any
from typing import Optional

import os
import tty
import sys
import threading
import atexit
import select
import termios

import structlog

from apscheduler.schedulers.background import BackgroundScheduler

from wx_server.configuration import load_and_parse_config as wx_server_load_and_parse_config

from radio_bridge.configuration import get_config_option
from radio_bridge.configuration import set_config_option
from radio_bridge.log import configure_logging
from radio_bridge.otp import generate_and_write_otps
from radio_bridge.rx import RX
from radio_bridge.dtmf import DTMFDecoder
from radio_bridge.dtmf import DTMF_TABLE_HIGH_LOW
from radio_bridge.plugins import get_available_plugins
from radio_bridge.plugins import get_plugins_with_dtmf_sequence
from radio_bridge.plugins.base import BasePlugin
from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.plugins.executor import PluginExecutor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "../conf/logging.conf"))
DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "../conf/radio_bridge.conf"))

DEFAULT_WX_SERVER_CONFIG_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "../../wx_server/conf/wx_server.conf")
)
WX_SERVER_CONFIG_PATH = os.environ.get("WX_SERVER_CONFIG_PATH", DEFAULT_WX_SERVER_CONFIG_PATH)

LOG = structlog.getLogger(__name__)

# Maximum transmit time in seconds. This acts as a safe guard and ensures TX functionality on the
# radio is automatically disabled if it has been enabled for more than this amount of seconds.
MAX_TRANSMIT_TIME = 120

# Maximum length for DTMF sequences
MAX_SEQUENCE_LENGTH = 7

# Each loop iteration lasts around 0.4-0.5 seconds since we record 0.4 seconds long audio
MAX_LOOP_ITERATIONS_RX_MODE = 15

# select.select timeout when running in emulator mode and DTMF sequences are read from keyboard
SELECT_TIMEOUT = 0.5

# In regular RX mode, each recording is 0.4 seconds long, which means, we use the same number of
# iterations in emulator mode
MAX_LOOP_ITERATIONS_EMULATOR_MODE = (MAX_LOOP_ITERATIONS_RX_MODE * 0.4) / SELECT_TIMEOUT

VALID_DTMF_CHARACTERS = DTMF_TABLE_HIGH_LOW.keys()


class RadioBridgeServer(object):
    def __init__(self):
        self._started = False

        self._all_plugins: Dict[str, BasePlugin] = {}
        self._dtmf_plugins: Dict[str, BaseDTMFPlugin] = {}
        self._sequence_to_plugin_map: Dict[str, BaseDTMFPlugin] = {}

        self._emulator_mode = False

        self._dtmf_decoder = DTMFDecoder()
        self._rx = RX(
            input_device_index=get_config_option("audio", "input_device_index", "int"),
            rate=get_config_option("audio", "sample_rate", "int"),
        )
        self._plugin_executor = PluginExecutor(
            implementation=get_config_option("plugins", "executor")
        )

        self._scheduler = BackgroundScheduler()

        self._cron_jobs_to_run_lock = threading.Lock()
        # Holds a list of ids for cron jobs which should run during the next iteration of the main
        # loop
        self._cron_jobs_to_run: List[str] = []

    def initialize(self, dev_mode: bool = False, emulator_mode: bool = False, debug: bool = False):
        # 1. Configure logging
        configure_logging(get_config_option("main", "logging_config"), debug=debug)
        wx_server_load_and_parse_config(WX_SERVER_CONFIG_PATH)

        if dev_mode:
            LOG.info("Development mode is active")
            set_config_option("main", "dev_mode", "True")

        if emulator_mode:
            LOG.info("Running in emulator mode")
            set_config_option("main", "emulator_mode", "True")

        self._emulator_mode = get_config_option("main", "emulator_mode", "bool", fallback=False)

        # 2. Load and register plugins
        self._all_plugins = get_available_plugins()
        self._dtmf_plugins = get_plugins_with_dtmf_sequence()
        self._sequence_to_plugin_map = self._dtmf_plugins

        # 3. Generate OTPs
        all_otps, _ = generate_and_write_otps()
        LOG.info("Generated and unused OTPs for admin commands", otps=all_otps)

    def start(self):
        self._started = True

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
            self._scheduler.add_job(add_job_to_jobs_to_run(job_id), trigger=job_trigger, id=job_id)

        LOG.info("Radio Bridge Server Started")

        # Run main read on input loop and invoke corresponding plugin callbacks
        self._main_loop()

    def _main_loop(self) -> None:
        # Read sequence and invoke any matching plugins
        last_char = None
        read_sequence = ""
        iteration_counter = 0

        # How many loop iterations before we reset the read_sequence array
        if self._emulator_mode:
            # In regular RX mode, each recording is 0.4 seconds long, which means, we use the same
            # number of iterations in emulator mode
            max_loop_iterations = MAX_LOOP_ITERATIONS_EMULATOR_MODE
        else:
            max_loop_iterations = MAX_LOOP_ITERATIONS_RX_MODE

        if self._emulator_mode:
            old_settings = termios.tcgetattr(sys.stdin)

            # Make sure we reset tty back to the original settigs on exit
            def reset_tty():
                LOG.debug("Resetting TTY")
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

            atexit.register(reset_tty)

            # Enable non blocking mode for stdin tty so we can read characters without enter
            tty.setcbreak(sys.stdin.fileno())

        while self._started:
            self._run_scheduled_jobs()

            if iteration_counter >= max_loop_iterations:
                # Max iterations reached, reset read_sequence and start from scratch
                LOG.info("Max iterations reached, reseting read_sequence and iteration counter")

                read_sequence = ""
                iteration_counter = 0

            if self._emulator_mode:
                if sys.stdin in select.select([sys.stdin], [], [], SELECT_TIMEOUT)[0]:
                    char = sys.stdin.read(1).upper()
                    if char not in VALID_DTMF_CHARACTERS:
                        LOG.error(
                            "Invalid DTMF character: %s. Valid characters are: %s"
                            % (char, ", ".join(VALID_DTMF_CHARACTERS))
                        )
                        continue
                    LOG.info("Read DTMF character %s from the keyboard" % (char))
                else:
                    char = ""
            else:
                self._rx.record_audio()
                char = self._dtmf_decoder.decode()

            if char != last_char:
                if not char:
                    iteration_counter += 1
                    continue

                iteration_counter = 0
                read_sequence += char

                LOG.info("Got char %s, current sequence: %s" % (char, read_sequence))

                # If sequence is valid, invoke plugin run() method via the executor
                plugin, args, kwargs = self._get_plugin_for_dtmf_sequence(sequence=read_sequence)

                if plugin or len(read_sequence) > MAX_SEQUENCE_LENGTH:
                    if plugin:
                        LOG.info(
                            'Found valid sequence "%s", invoking plugin "%s"'
                            % (read_sequence, plugin.NAME)
                        )
                        self._plugin_executor.run(plugin=plugin, *args, **kwargs)
                    else:
                        LOG.info("Max sequence length limit reached, resetting sequence")

                    read_sequence = ""
            else:
                iteration_counter += 1
                continue

            last_char = char

    def _get_plugin_for_dtmf_sequence(
        self, sequence: str
    ) -> Tuple[Optional[BasePlugin], Optional[Tuple], Optional[Dict[str, Any]]]:
        """
        Retrieve reference to the Plugin class instance and any args and kwargs which should be
        passed to the plugin run() method.
        """
        for plugin_instance in self._dtmf_plugins.values():
            matches, args, kwargs = plugin_instance.matches_dtmf_sequence(sequence=sequence)

            if matches:
                return plugin_instance, args, kwargs

        return None, None, None

    def _run_scheduled_jobs(self) -> None:
        """
        Function which runs as part of every loop iteration and checks if there are any scheduled
        jobs which should run.

        If they are, it runs them sequentially in order and removes them from jobs to run at the
        end.
        """
        jobs_to_run = self._cron_jobs_to_run[:]

        LOG.trace("Jobs scheduled to run: %s" % (jobs_to_run))

        cron_plugin = self._all_plugins["CronSayPlugin"]
        # TODO: If there is a "pile up", auto drop old jobs to make sure we don't end up stick in
        # infinite job execution loop

        for job_id in jobs_to_run:
            LOG.debug("Running scheduled job: %s" % (job_id))

            try:
                cron_plugin.run(job_id=job_id)  # type: ignore
            finally:
                self._cron_jobs_to_run_lock.acquire()
                self._cron_jobs_to_run.remove(job_id)
                self._cron_jobs_to_run_lock.release()

    def stop(self):
        self._started = False


if __name__ == "__main__":
    server = RadioBridgeServer()
    server.start()
