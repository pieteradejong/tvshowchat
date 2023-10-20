import os
import logging


class Config:
    LOGGING_LEVEL = logging.getLevelName(os.getenv("LOGGING_LEVEL", "INFO"))
    LOGGING_FORMAT = os.getenv(
        "LOGGING_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


config = Config()

