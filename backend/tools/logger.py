import logging
import sys


def get_logger(name: str):

    """
    Returns a logger with the given name, configured with a console and file handler.

    The logger is created with the logging.INFO level and a custom formatter that
    includes the timestamp, log level, logger name, and message.

    If a logger with the given name already exists, it is returned immediately.

    :param name: The name of the logger to create.
    :return: The created logger.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("system.log")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger