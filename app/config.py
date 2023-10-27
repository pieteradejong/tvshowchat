import logging.config
import json


def load_logging_config():
    try:
        with open("logging_config.json", "r") as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    except Exception as e:
        raise Exception(f"Failed to load logging configuration: {e}")


def get_logger(name: str = "my_app"):
    load_logging_config()
    return logging.getLogger(name)


logger = get_logger()
