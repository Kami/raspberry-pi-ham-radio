from typing import Optional

import os
import datetime
import pathlib

import structlog

from generated.protobuf import messages_pb2

from wx_server.configuration import get_config

LOG = structlog.get_logger(__name__)


def persist_weather_observation(observation_pb: messages_pb2.WeatherObservation):
    """
    Persistent weather observation as Protobuf serialized by string on file on disk.

    We use the following directory structure / file layout:

    <station id>/<YYYY>/<MM>/<DD>/observation_<hhmm>.pb

    For example:

    station_1/2020/10/01/observation_2015.pb

    Observations are organized into 1 minute buckets and we simply assume we will receive a single
    observation per minute.
    """
    date = datetime.datetime.fromtimestamp(observation_pb.timestamp)
    target_directory = get_directory_path_for_date(date=date)

    os.makedirs(target_directory, exist_ok=True)

    file_path = get_file_path_for_date(date=date, target_directory=target_directory)

    if os.path.exists(file_path):
        LOG.info("Observation for timestamp %s already exists, skipping write" % (date))
        return

    with open(file_path, "wb") as fp:
        fp.write(observation_pb.SerializeToString())

    LOG.info("Observation written to %s" % (file_path))


def get_bucket_name_for_date(date: datetime.datetime) -> str:
    """
    Return bucket name for the provided date time.
    """
    hour = zero_pad_value(date.hour)
    minute = zero_pad_value(date.minute)
    bucket_name = '%s%s' % (hour, minute)
    return bucket_name


def get_weather_observation_for_date(date: datetime.datetime, return_closest=True) -> Optional[messages_pb2.WeatherObservation]:
    """
    Return wethaer observation for the provided date.

    If value for the provided timestamp doesn't exist, we try to find one for the last 5 minutes. If
    no matching observation is found, None is returned.
    """
    # We only care about minute resolution so we ignore other components
    date = date.replace(second=0, microsecond=0)

    dates = [
        date,
    ]

    if return_closest:
        for index in range(1, 5):
            date_prev = date - datetime.timedelta(minutes=index)
            dates.append(date_prev)

    target_directory = get_directory_path_for_date(date=date)

    for date in dates:
        file_path = get_file_path_for_date(date=date, target_directory=target_directory)

        if os.path.isfile(file_path):
            break

    if not os.path.isfile(file_path):
        LOG.debug("Unable to find observation for %s" % (date))
        return None

    with open(file_path, "rb") as fp:
        content = fp.read()

    LOG.debug("Found observation for %s" % (date))
    observation_pb = messages_pb2.WeatherObservation.FromString(content)
    return observation_pb


def get_directory_path_for_date(date: datetime.datetime) -> str:
    year = zero_pad_value(date.year)
    month = zero_pad_value(date.month)
    day = zero_pad_value(date.day)

    target_directory = os.path.join(get_config()["main"]["data_dir"], year, month, day)
    return target_directory


def get_file_path_for_date(date: datetime.datetime, target_directory: str) -> str:
    bucket_name = get_bucket_name_for_date(date=date)
    file_name = 'observation_%s.pb' % (bucket_name)
    file_path = os.path.join(target_directory, file_name)
    return file_path


def zero_pad_value(value: int) -> str:
    """
    Zero pad the provided value and return string.
    """
    return "0" + str(value) if value < 10 else str(value)
