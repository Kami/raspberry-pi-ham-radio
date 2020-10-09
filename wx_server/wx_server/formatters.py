from typing import Dict

import copy
import datetime

from generated.protobuf import messages_pb2

__all__ = ["format_ecowitt_weather_data"]


def format_ecowitt_weather_data(data: Dict[str, str]) -> dict:
    """
    Format and normalize weather data in Ecowitt format.
    """
    result = {}

    result["date"] = data["dateutc"]
    result["datetime"] = datetime.datetime.strptime(data["dateutc"], "%Y-%m-%d %H:%M:%S")
    result["timestamp"] = int(result["datetime"].timestamp())

    # Temperature, dewpoint and humidity
    result["temperature"] = fahrenheit_to_celsius(float(data["tempinf"]))  # celsius
    result["dewpoint"] = fahrenheit_to_celsius(float(data["humidityin"]))  # celsius
    result["humidity"] = int(data["humidity"])  # %

    # Pressure data
    result["pressure_abs"] = inches_of_mercury_to_hpa(float(data["baromabsin"]))  # hpa
    result["pressure_rel"] = inches_of_mercury_to_hpa(float(data["baromrelin"]))  # hpa

    # Wind data
    result["wind_direction"] = int(data["winddir"])  # degrees, 0-360
    result["wind_speed"] = mph_to_kmph(float(data["windspeedmph"]))  # km/h
    result["wind_gust"] = mph_to_kmph(float(data["windgustmph"]))  # km/h
    result["wind_gust_max_daily"] = mph_to_kmph(float(data["maxdailygust"]))  # km/h

    # Rain data
    result["rain_event"] = inches_to_mm(float(data["eventrainin"]))  # mm
    result["rain_rate"] = inches_to_mm(float(data["rainratein"]))  # mm/hr
    result["rain_hourly"] = inches_to_mm(float(data["hourlyrainin"]))  # mm
    result["rain_daily"] = inches_to_mm(float(data["dailyrainin"]))  # mm
    result["rain_weekly"] = inches_to_mm(float(data["weeklyrainin"]))  # mm
    result["rain_monthly"] = inches_to_mm(float(data["monthlyrainin"]))  # mm
    result["rain_total"] = inches_to_mm(float(data["totalrainin"]))  # mm

    # Light data
    result["uv"] = int(data["uv"])
    result["solar_radiation"] = round(float(data["solarradiation"]), 2)

    return result


def dict_to_protobuf(data: dict) -> messages_pb2.WeatherObservation:
    """
    Convert dictionary as returned by format_ecowitt_weather_data() method to Protobuf object.
    """
    values = copy.copy(data)

    del values["date"]
    del values["datetime"]

    observation_pb = messages_pb2.WeatherObservation(**values)
    return observation_pb


def inches_of_mercury_to_hpa(value: float) -> float:
    return round(float(value) * 3386.389 / 100, 2)


def fahrenheit_to_celsius(value: float):
    return round(((float(value) - 32) * 5 / 9), 2)


def mph_to_kmph(value: float):
    return round(value * 1.60934, 2)


def inches_to_mm(value: float):
    return round(value * 25.4, 2)
