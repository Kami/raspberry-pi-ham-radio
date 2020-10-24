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

import urllib
import hashlib

import structlog

from flask import Blueprint
from flask import request

from wx_server.formatters import format_ecowitt_weather_data
from wx_server.formatters import format_wu_weather_data
from wx_server.formatters import dict_to_protobuf
from wx_server.configuration import get_config
from wx_server.io import persist_weather_observation

__all__ = ["wx_data_app"]

wx_data_app = Blueprint("wx_data", __name__, url_prefix="/v1/wx/observation")

LOG = structlog.get_logger(__name__)


@wx_data_app.route("/ew/<string:station_id>/<string:secret>", methods=["POST"])
def handle_observation_ecowitt_format(station_id: str, secret: str):
    config_secret = get_config()["secrets"].get(station_id, "")
    secret_hash = hashlib.sha256(
        b"%s:%s" % (station_id.encode("utf-8"), secret.encode("utf-8"))
    ).hexdigest()

    if secret_hash != config_secret:
        LOG.info("Received invalid or missing secret, aborting request")
        return "Invalid or missing secret", 403, {}

    log = LOG.bind(station_id=station_id)

    form_data = dict(request.form)

    log.debug("Received request", path="/".join(request.path.split("/")[:-1]))
    log.debug("Raw request payload / form data", payload=form_data)

    res = format_ecowitt_weather_data(form_data)
    observation_pb = dict_to_protobuf(res)

    persist_weather_observation(station_id=station_id, observation_pb=observation_pb)
    log.debug("Weather observation persisted", observation_pb=observation_pb)

    return "", 200, {}


@wx_data_app.route("/wu/<string:data>", methods=["GET"])
def handle_observation_wunderground_format(data: str):
    data = dict(urllib.parse.parse_qsl(data))

    station_id = data["ID"]
    secret = data["PASSWORD"]

    config_secret = get_config()["secrets"].get(station_id, "")
    secret_hash = hashlib.sha256(
        b"%s:%s" % (station_id.encode("utf-8"), secret.encode("utf-8"))
    ).hexdigest()

    if secret_hash != config_secret:
        LOG.info("Received invalid or missing secret, aborting request")
        return "Invalid or missing secret", 403, {}

    log = LOG.bind(station_id=station_id)

    log.debug("Received request", path="/".join(request.path.split("/")[:-1]))
    log.debug("Raw request data", data=data)

    res = format_wu_weather_data(data)
    observation_pb = dict_to_protobuf(res)

    persist_weather_observation(station_id=station_id, observation_pb=observation_pb)
    log.debug("Weather observation persisted", observation_pb=observation_pb)

    return "", 200, {}
