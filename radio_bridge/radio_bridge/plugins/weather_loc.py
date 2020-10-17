import time

import structlog
import requests
import xmltodict

from generated.protobuf import messages_pb2

from radio_bridge.plugins.base import BaseDTMFWithDataPlugin
from radio_bridge.utils import weather as weather_utils

LOCATION_CODE_TO_CITY_MAP = {
    "01": "Ljubljana",
    "02": "Maribor",
    "03": "Celje",
    "04": "Brnik",
    "05": "Portoroz",
    "07": "Novo Mesto",
}

CITY_TO_XML_LOCATION_MAP = {
    "Ljubljana": "http://meteo.arso.gov.si/uploads/probase/www/observ/surface/text/en/observation_LJUBL-ANA_BEZIGRAD_latest.xml",
    "Maribor": "http://meteo.arso.gov.si/uploads/probase/www/observ/surface/text/en/observation_MARIBOR_SLIVNICA_latest.xml",
    "Celje": "http://meteo.arso.gov.si/uploads/probase/www/observ/surface/text/en/observation_CELJE_latest.xml",
    "Brnik": "",
    "Koper": "http://meteo.arso.gov.si/uploads/probase/www/observ/surface/text/en/observation_PORTOROZ_SECOVLJE_latest.xml",
    "Novo Mesto": "http://meteo.arso.gov.si/uploads/probase/www/observ/surface/text/en/observation_NOVO-MES_latest.xml",
}

LOG = structlog.getLogger(__name__)

__all__ = ["WeatherForLocationPlugin"]


class WeatherForLocationPlugin(BaseDTMFWithDataPlugin):
    NAME = "Location weather info"
    DESCRIPTION = "Current weather for location"
    # Second two characters and city code - e.g. 01 - Ljubljana, 02 - Maribor, etc.
    DTMF_SEQUENCE = "35??"

    def run(self, sequence: str):
        if sequence not in LOCATION_CODE_TO_CITY_MAP:
            self.say("Invalid weather location sequence.")
            return

        city = LOCATION_CODE_TO_CITY_MAP[sequence]

        observation_pb = get_weather_observation(city=city)
        if not observation_pb:
            self.say("Unable to retrieve weather observation data")

        text = weather_utils.observation_pb_to_text(observation_pb)
        self.say("Weather information for %s. %s" % (city, text))


def get_weather_observation(city: str) -> messages_pb2.WeatherObservation:
    """
    Retrieve weather data from arso XML endpoint, parse it and convert it to WeatherObservation
    object.
    """
    # TODO: Cache data for 60 seconds
    url = CITY_TO_XML_LOCATION_MAP[city]

    LOG.debug("Retrieving weather data for city %s from %s" % (city, url))
    response = requests.get(url)
    result = xmltodict.parse(response.content)

    LOG.trace("Retrieved weather data: %s" % (str(result)))

    observation_pb = weather_data_dict_to_weather_observation_pb(result["data"]["metData"])
    LOG.debug("Observation data", observation_pb=observation_pb)
    return observation_pb


def weather_data_dict_to_weather_observation_pb(data: dict) -> messages_pb2.WeatherObservation:
    observation_pb = messages_pb2.WeatherObservation()

    # TODO: Parse actual timestamp
    observation_pb.timestamp = int(time.time())
    # TODO: parse float
    observation_pb.temperature = int(data["t_degreesC"])
    observation_pb.dewpoint = int(data["td_degreesC"])
    observation_pb.humidity = int(data["rh"])
    observation_pb.pressure_rel = int(data["msl_mb"])
    observation_pb.pressure_abs = int(data["p_mb"])
    observation_pb.wind_direction = int(data["dd_val"])
    observation_pb.wind_speed = int(data["ff_value_kmh"])

    if data["ffmax_val_kmh"]:
        observation_pb.wind_gust = int(data["ffmax_val_kmh"])

    # TODO: Include rain data
    return observation_pb
