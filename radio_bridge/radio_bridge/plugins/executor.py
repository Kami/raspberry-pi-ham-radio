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
from typing import Type
from typing import Dict

import abc
import time
import sys
import traceback
import functools
import multiprocessing
from collections import defaultdict

import structlog

from radio_bridge.configuration import get_config
from radio_bridge.configuration import get_plugin_config_option
from radio_bridge.plugins.base import BasePlugin
from radio_bridge.plugins.errors import PluginExecutionTimeoutException

__all__ = ["PluginExecutor"]

LOG = structlog.getLogger(__name__)


class BasePluginExecutor(object):
    """
    Class responsible for execution / running a plugin.
    """

    def __init__(self):
        self._max_run_time = get_config().getint("plugins", "max_run_time", fallback=None)

    @abc.abstractmethod
    def run(self, plugin: Type[BasePlugin], *args: Any, **kwargs: Any) -> None:
        """
        Run the plugin and pass args kwargs to the plugin run method.
        """
        pass


class NativePluginExecutor(BasePluginExecutor):
    """
    Plugin executor which runs the plugin directly in the current / main server thread.
    """

    def run(self, plugin: Type[BasePlugin], *args: Any, **kwargs: Any) -> None:
        """
        Run the plugin and pass args kwargs to the plugin run method.
        """
        return plugin.run(*args, **kwargs)


class ProccessPluginExecutor(BasePluginExecutor):
    """
    Plugin executor which runs a plugin inside a subprocess.

    This provides for a better isolation and allows us to implement safe guards which kill the
    plugin and disable TX if the run time has been longer than the max run time defined in the
    config.
    """

    def run(self, plugin: Type[BasePlugin], *args: Any, **kwargs: Any) -> None:
        """
        Run the plugin and pass args kwargs to the plugin run method.
        """
        queue = multiprocessing.Queue()
        args = (queue,) + args

        # Plguin max run time (if set) has precedence over global max run time
        max_run_time = get_plugin_config_option(
            plugin.ID, "max_run_time", fallback=self._max_run_time, get_method="getint"
        )

        process = multiprocessing.Process(target=plugin.run_in_subprocess, args=args, kwargs=kwargs)
        process.daemon = True
        process.start()
        process.join(max_run_time)

        timed_out = False

        if process.is_alive():
            timed_out = True
            LOG.info("Plugin execution didn't finish in %s seconds, killing it..." % (max_run_time))
            process.terminate()
            plugin.disable_tx()

        if timed_out:
            raise PluginExecutionTimeoutException("Plugin execution timed out")
        else:
            result = queue.get()

        return result


class PluginExecutor(object):
    implementations = {"native": NativePluginExecutor, "process": ProccessPluginExecutor}

    def __init__(self, implementation: str) -> None:
        self._executor = self.implementations[implementation]()
        self._logger = LOG.bind(executor=implementation)

        # Maps plugin name to the last run timestamp. This allows us to implement various
        # safe-guards and abuse prevention
        self._plugin_run_times: Dict[str, int] = {}

        # Maps plugin name to execution stats
        self._plugin_execution_stats = defaultdict(
            functools.partial(defaultdict, success=0, failure=0, timeout=0, refuse_to_run=0)
        )

    def run(self, plugin: Type[BasePlugin], *args: Any, **kwargs: Any) -> None:
        plugin_id = plugin.ID

        self._logger.debug("Running plugin %s" % (str(plugin)))

        start_time = int(time.time())

        can_run = self._can_run(plugin=plugin)

        if not can_run:
            self._plugin_execution_stats[plugin_id]["refuse_to_run"] += 1
            return None

        self._plugin_run_times[plugin.ID] = start_time

        try:
            result = self._executor.run(plugin=plugin, *args, **kwargs)
        except PluginExecutionTimeoutException:
            self._plugin_execution_stats[plugin_id]["timeout"] += 1
            status = "timeout"
            result = None
            error = None
        except Exception as e:
            self._plugin_execution_stats[plugin_id]["failure"] += 1
            status = "failure"
            result = None
            _, _, exc_traceback = sys.exc_info()
            error = str(e) + "\n" + str("\n".join(traceback.format_tb(exc_traceback)))
        else:
            status = "success"
            error = None
            self._plugin_execution_stats[plugin_id]["success"] += 1

        end_time = int(time.time())
        duration = end_time - start_time

        self._logger.debug(
            "Plugin run() execution finished", duration=duration, status=status, error=error
        )

        return result

    def _can_run(self, plugin: Type[BasePlugin]) -> bool:
        """
        Check if currect plugin meets varios abuse prevention and other criteria and can run at the
        current time.
        """
        now = int(time.time())
        minimum_run_interval = get_plugin_config_option(
            plugin.ID, "minimum_run_interval", fallback=None, get_method="getint"
        )

        if not minimum_run_interval:
            # Minimum run interval not specified for this plugin
            return True

        previous_run_time = self._plugin_run_times.get(plugin.ID, None)

        if previous_run_time and previous_run_time + minimum_run_interval > now:
            grace_time_seconds = abs(now - (previous_run_time + minimum_run_interval))
            LOG.info(
                "Plugin was executed less than %s seconds ago, refusing execution. Plugin can run "
                "again in %s seconds." % (minimum_run_interval, grace_time_seconds)
            )
            return False

        return True
