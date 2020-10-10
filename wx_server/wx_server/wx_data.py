import hashlib
import datetime

import structlog

from flask import Blueprint
from flask import Response
from flask import request
from flask import current_app as app

from wx_server.formatters import format_ecowitt_weather_data
from wx_server.formatters import dict_to_protobuf
from wx_server.configuration import get_config
from wx_server.io import persist_weather_observation
from wx_server.io import get_weather_observation_for_date

from generated.protobuf import messages_pb2

__all__ = ["wx_data_app"]

wx_data_app = Blueprint('wxz_data', __name__, url_prefix='/v1/wx/data')

LOG = structlog.get_logger(__name__)


@wx_data_app.route('/<string:station_id>/<string:secret>', methods=['POST'])
def handle_wx_data(station_id: str, secret: str) -> Response:
    config_secret = get_config()["secrets"].get(station_id, "")
    secret_hash = hashlib.sha256(b"%s:%s" % (station_id.encode("utf-8"), secret.encode("utf-8"))).hexdigest()

    if secret_hash != config_secret:
        LOG.info("Received invalid or missing secret, aborting request")
        return 'Invalid or missing secret', 403, {}

    log = LOG.bind(station_id=station_id)

    form_data = dict(request.form)

    log.debug("Received request", path="/".join(request.path.split("/")[:-1]))
    log.debug("Raw request payload / form data", payload=form_data)

    res = format_ecowitt_weather_data(form_data)
    observation_pb = dict_to_protobuf(res)

    persist_weather_observation(observation_pb)
    log.debug("Weather observation persisted", observation_pb=observation_pb)

    return '', 200, {}
