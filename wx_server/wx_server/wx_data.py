import datetime

import structlog

from flask import Blueprint
from flask import Response
from flask import request
from flask import current_app as app

from wx_server.formatters import format_ecowitt_weather_data
from wx_server.formatters import dict_to_protobuf
from wx_server.io import persist_weather_observation
from wx_server.io import get_weather_observation_for_date

from generated.protobuf import messages_pb2

__all__ = ["wx_data_app"]

wx_data_app = Blueprint('wxz_data', __name__, url_prefix='/v1/wx/data')

LOG = structlog.get_logger(__name__)

# Maps station id to a secret
VALID_SECRETS = {
    "home": "foobar"
}


@wx_data_app.route('/<string:station_id>/<string:secret>', methods=['POST'])
def handle_wx_data(station_id: str, secret: str) -> Response:
    if secret != VALID_SECRETS.get(station_id, None):
        LOG.info("Received invalid or missing secret, aborting request")
        return 'Invalid or missing secret', 403, {}

    log = LOG.bind(station_id=station_id)

    form_data = dict(request.form)

    log.debug("Received request", path="/".join(request.path.split("/")[:-1]))
    log.debug("Raw request payload / form data", payload=form_data)

    res = format_ecowitt_weather_data(form_data)
    observation_pb = dict_to_protobuf(res)

    persist_weather_observation(observation_pb)
    date = datetime.datetime.fromtimestamp(observation_pb.timestamp)
    print(get_weather_observation_for_date(date))

    return '', 200, {}
