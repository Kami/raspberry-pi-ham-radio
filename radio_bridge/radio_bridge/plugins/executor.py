from typing import Any
from typing import Type

import abc
import time
import multiprocessing

import structlog

from radio_bridge.configuration import get_config
from radio_bridge.plugins.base import BasePlugin

__all__ = ["PluginExecutor"]

LOG = structlog.getLogger(__name__)


class BasePluginExecutor(object):
    """
    Class responsible for execution / running a plugin.
    """

    def __init__(self):
        self._max_run_time = get_config()["plugins"].getint("max_run_time")

        self._start_time = None
        self._end_time = None

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
        process = multiprocessing.Process(target=plugin.run, args=args, kwargs=kwargs)
        process.daemon = True
        process.start()
        process.join(self._max_run_time)

        if process.is_alive():
            LOG.info(
                "Plugin execution didn't finish in %s seconds, killing it..." % (self._max_run_time)
            )
            process.terminate()
            # TODO: if tx mode is gpio, disable TX

        return None


class PluginExecutor(object):
    implementations = {"native": NativePluginExecutor, "process": ProccessPluginExecutor}

    def __init__(self, implementation: str) -> None:
        self._executor = self.implementations[implementation]()
        self._logger = LOG.bind(executor=implementation)

        # Maps plugin name to the last run timestamp. This allows us to implement various
        # safe-guards and abuse prevention
        self._plugin_run_times = {}

    def run(self, plugin: Type[BasePlugin], *args: Any, **kwargs: Any) -> None:
        self._logger.debug("Running plugin %s" % (str(plugin)))

        start_time = int(time.time())

        can_run = self._can_run(plugin=plugin)

        if not can_run:
            return

        self._plugin_run_times[plugin.ID] = start_time

        result = self._executor.run(plugin=plugin, *args, **kwargs)
        end_time = int(time.time())
        duration = end_time - start_time

        self._logger.debug("Plugin run() execution finished", duration=duration)

        return result

    def _can_run(self, plugin: Type[BasePlugin]) -> bool:
        """
        Check if currect plugin meets varios abuse prevention and other criteria and can run at the
        current time.
        """
        now = int(time.time())
        minimum_run_interval = get_config()["plugin:%s" % (plugin.ID)].getint(
            "minimum_run_interval", None
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
