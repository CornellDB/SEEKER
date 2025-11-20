# File: utils/logger.py
import logging

def setup_logging(level: str = 'INFO') -> None:
    """
    Configure the root logger with a standard format and the given log level.
    Call this once at program start.
    """
    level_name = level.upper()
    log_level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        filename='app.log',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=log_level
    )

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a named logger (or the root logger if name is None).
    Usage:
        logger = get_logger(__name__)
        logger.info("Hello, world!")
    """
    return logging.getLogger(name)
