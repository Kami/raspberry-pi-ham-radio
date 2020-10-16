import os

import configparser

import structlog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../"))

DEFAULT_CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, '../conf/radio_bridge.conf'))
CONFIG_PATH = os.environ.get("RADIO_BRIDGE_CONFIG_PATH", DEFAULT_CONFIG_PATH)

DEFAULT_VALUES = {
    "main": {
        "logging_config": "{rootdir}/conf/logging.conf",
        "dev_mode": False,
        "tx_mode": "vox",
    },
    "audio": {
        "input_device_index": 0,
        "sample_rate": 48000,
    },
    "tts": {
        "library": "gtts",
        "enable_cache": True,
        "cache_directory": "/tmp/tts-audio-cache"
    },
    "dtmf": {
        "implementation": "fft_2"
    }
}

CONFIG = None

LOG = structlog.get_logger()


def load_and_parse_config(config_path: str, validate: bool = True):
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
    logging_config = config["main"]["logging_config"]
    config["main"]["logging_config"] = config["main"]["logging_config"].replace("{rootdir}", ROOT_DIR)

    if not os.path.isfile(config["main"]["logging_config"]):
        raise ValueError("Logging config %s doesn't exist or it's not a file" %
                         (config["main"]["logging_config"]))

    # TODO validate dtms implementation, tts library
    if config["main"]["tx_mode"] not in ["vox", "gpio"]:
        raise ValueError("Invalid tx_mode value: %s. valid values: vox, gpio" %
                         (config["main"]["tx_mode"]))

    return config


def get_config() -> configparser.ConfigParser:
    """
    Retrieved loaded and parsed config instance.

    If config hasn't be loaded yet, it will be loaded and parsed by this method.
    """
    global CONFIG

    if not CONFIG:
        load_and_parse_config(CONFIG_PATH)

    assert CONFIG is not None
    return CONFIG
