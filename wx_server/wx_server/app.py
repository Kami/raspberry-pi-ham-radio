from gevent import monkey
monkey.patch_all()

import os
import logging

import structlog
from flask import Flask

from wx_server.wx_data import wx_data_app
from wx_server.logging import configure_logging


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGGING_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../conf/logging.conf'))

LOG = structlog.get_logger()


def create_app() -> Flask:
    configure_logging(LOGGING_CONFIG_PATH)

    app = Flask(__name__)

    with app.app_context():
        app.register_blueprint(wx_data_app)

    return app
