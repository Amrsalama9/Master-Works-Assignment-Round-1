import logging
from datetime import datetime

from config.settings import LOGS_DIR


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger that writes to both the console and a run-specific
    log file under logs/. Safe to call multiple times for the same name -
    handlers are only attached once.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
