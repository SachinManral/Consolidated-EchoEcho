# This file is responsible for shared logging setup ko handle karne ke liye.
# Yahan se application logs ka format, level aur logger reuse manage kiya jata hai.

import logging

from .config import config


def get_logger(name: str = "copyright_agent") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, config.log_level, logging.INFO))
    logger.propagate = False
    return logger
