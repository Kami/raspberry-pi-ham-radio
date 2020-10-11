from radio_bridge.plugins.base import BasePlugin

"""
Plugin which allows schedueling of say task to run at specific intervals.
"""

class CronSayPlugin(BasePlugin):
    # TODO: Add support for adding time, wx data, etc to the context which is available inside text.
    NAME = "Cron Plugin"

    def run(self):
        pass
