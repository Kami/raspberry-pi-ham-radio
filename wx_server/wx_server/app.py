from gevent import monkey

monkey.patch_all()

import os
import logging

import structlog
from flask import Flask

from wx_server.wx_data import wx_data_app
from wx_server.logging import configure_logging
from wx_server.configuration import load_and_parse_config
from wx_server.configuration import get_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "../conf/logging.conf"))
DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "../conf/wx_server.conf"))

CONFIG_PATH = os.environ.get("WX_SERVER_CONFIG_PATH", DEFAULT_CONFIG_PATH)

LOG = structlog.get_logger()


def create_app() -> Flask:
    load_and_parse_config(CONFIG_PATH)
    config = get_config()
    configure_logging(config["main"]["logging_config"])

    LOG.info("Using logging config %s" % (config["main"]["logging_config"]))
    LOG.info("Data will be stored to %s" % (config["main"]["data_dir"]))

    app = Flask(__name__)

    with app.app_context():
        app.register_blueprint(wx_data_app)

    return app
