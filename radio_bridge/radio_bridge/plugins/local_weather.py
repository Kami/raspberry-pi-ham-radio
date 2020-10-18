import datetime

from wx_server.io import get_weather_observation_for_date

from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.utils import weather as weather_utils

__all__ = ["LocalWeatherPlugin"]


class LocalWeatherPlugin(BaseDTMFPlugin):
    """
    Plugin which says weather information for the weather station which is running local and sending
    data to Weather Server connected to this Raspberry Pi instance.
    """

    ID = "local_weather"
    NAME = "Current weather"
    DESCRIPTION = "Current weather information for local weather station."
    DTMF_SEQUENCE = "34"

    def run(self):
        # 1. Retrieve local weather data from disk
        date = datetime.datetime.utcnow()

        observation_pb = get_weather_observation_for_date(date=date)
        if not observation_pb:
            self.say("No recent weather observation found.")
            return

        # 2. Convert it to text and say it
        text = weather_utils.observation_pb_to_text(observation_pb)
        self.say(text)
