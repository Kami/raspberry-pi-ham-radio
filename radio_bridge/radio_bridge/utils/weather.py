from generated.protobuf import messages_pb2

WEATHER_OBSERVATION_SHORT = """
Temperature {temperature} degrees celsius.
Dew point {dewpoint}.
Pressure {pressure} hPa.
{wind}
{rain}
UV index: {uv_index}
""".strip()

WIND_DATA_WIND = "Wind {wind_speed} kilometers per hour from the {wind_direction}."
WIND_DATA_NO_WIND = "No wind."

RAIN_RAIN = "Rain {rain_rate} mm per hour"
RAIN_NO_RAIN = ""

__all__ = ["observation_pb_to_text", "get_wind_direction_text"]


def observation_pb_to_text(observation_pb: messages_pb2.WeatherObservation) -> str:
    temperature = round(observation_pb.temperature, 1)
    dewpoint = round(observation_pb.dewpoint, 1)
    humidity = observation_pb.humidity
    pressure = round(observation_pb.pressure_rel, 1)
    wind_speed = round(observation_pb.wind_speed, 1)
    wind_direction = get_wind_direction_text(observation_pb.wind_direction)
    rain_rate = round(observation_pb.rain_rate, 1)
    uv_index = observation_pb.uv

    if wind_speed >= 3:
        wind = WIND_DATA_WIND.format(wind_speed=wind_speed, wind_direction=wind_direction)
    else:
        wind = WIND_DATA_NO_WIND

    if rain_rate > 0:
        # TODO: Friendly string (light showers of rain, etc.)
        rain = RAIN_RAIN.format(rain_rate=rain_rate)
    else:
        rain = RAIN_NO_RAIN

    text = WEATHER_OBSERVATION_SHORT.format(
        temperature=temperature,
        dewpoint=dewpoint,
        humidity=humidity,
        pressure=pressure,
        wind=wind,
        rain=rain,
        uv_index=uv_index,
    )

    return text


def get_wind_direction_text(wind_direction: int) -> str:
    """
    :param wind_direction: Win direction in degrees.
    """
    if wind_direction in [0, 360]:
        return "north"
    elif wind_direction >= 1 and wind_direction < 90:
        return "north east"
    elif wind_direction == 90:
        return "east"
    elif wind_direction >= 91 and wind_direction < 180:
        return "south east"
    elif wind_direction == 180:
        return "south"
    elif wind_direction >= 181 and wind_direction < 260:
        return "south west"
    elif wind_direction >= 261 and wind_direction < 360:
        return "north west"
    else:
        raise ValueError("Invalid wind direction, value must be >=0 and <= 360")
