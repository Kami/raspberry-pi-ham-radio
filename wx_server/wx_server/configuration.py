import os

import configparser

import structlog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../"))

DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../conf/wx_server.conf'))
CONFIG_PATH = os.environ.get("WX_SERVER_CONFIG_PATH", DEFAULT_CONFIG_PATH)

DEFAULT_VALUES = {
    "main": {
        "data_dir": "{rootdir}/data/",
        "logging_config": "{rootdir}/conf/logging.conf",
    }
}

CONFIG = None

LOG = structlog.get_logger()


def load_and_parse_config(config_path: str, validate=True):
    global CONFIG

    log = LOG.bind(config_path=config_path)

    LOG.debug("Loading config from %s" % (config_path))

    if not os.path.isfile(config_path):
        raise ValueError("Config file %s doesn't exist" % (config_path))

    config = configparser.ConfigParser()
    config.read_dict(DEFAULT_VALUES)
    config.read(config_path)

    if validate:
        log.debug("Validating config")
        config = validate_config(config)
        log.debug("Config validated")

    CONFIG = config


def validate_config(config):
    data_dir = config["main"]["data_dir"]
    config["main"]["data_dir"] = config["main"]["data_dir"].replace("{rootdir}", ROOT_DIR)

    if not os.path.isdir(config["main"]["data_dir"]):
        raise ValueError("Data dir %s doesn't exist or it's not a directory" %
                         (config["main"]["data_dir"]))


    logging_config = config["main"]["logging_config"]
    config["main"]["logging_config"] = config["main"]["logging_config"].replace("{rootdir}", ROOT_DIR)

    if not os.path.isfile(config["main"]["logging_config"]):
        raise ValueError("Logging config %s doesn't exist or it's not a file" %
                         (config["main"]["logging_config"]))

    return config


def get_config():
    """
    Retrieved loaded and parsed config instance.

    If config hasn't be loaded yet, it will be loaded and parsed by this method.
    """
    global CONFIG

    if not CONFIG:
        load_and_parse_config(CONFIG_PATH)

    return CONFIG
