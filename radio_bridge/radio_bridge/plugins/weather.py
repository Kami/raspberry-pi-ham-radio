import datetime

from wx_server.io import get_weather_observation_for_date

from radio_bridge.plugins.base import BaseDTMFPlugin
from radio_bridge.utils import weather as weather_utils

__all__ = ["WeatherObservationPlugin"]


class WeatherObservationPlugin(BaseDTMFPlugin):
    NAME = "Current weather"
    DESCRIPTION = "Current weather information."
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
