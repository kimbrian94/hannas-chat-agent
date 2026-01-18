import logging
import sys
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(levelname)s:%(name)s:%(message)s"

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(LOG_LEVEL)

    # ---- STDOUT handler (INFO, WARNING) ----
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # ---- STDERR handler (ERROR, CRITICAL) ----
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    logger.propagate = False

    return logger