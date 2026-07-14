import logging
import os


def get_logger(name: str, log_level: str = 'INFO', log_path: str = 'logs/opticrop.log') -> logging.Logger:
    """
    Creates and returns a structured logger.

    Parameters
    ----------
    name      : Module ``__name__`` passed by the caller.
    log_level : Log level string (e.g. 'DEBUG', 'INFO'). Defaults to 'INFO'.
    log_path  : Filesystem path for the rotating log file.  Falls back to
                stdout if the path is inaccessible.

    WARNING: Raw IP addresses must NEVER be written to this logger.
    Always use sha256_ip() (app/utils/hashing.py) for privacy/GDPR compliance.
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # Attempt to create a file handler; fall back to stdout on failure.
    try:
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.warning(
            "Log file '%s' is inaccessible; falling back to stdout.", log_path
        )

    return logger
