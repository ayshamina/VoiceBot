"""
Telephony debug logging utility.
Provides structured logging for Exotel/Twilio webhook interactions.
"""
import logging
import sys
from app.core.config import settings

# Create a dedicated telephony logger
logger = logging.getLogger("telephony")

# Configure handler if not already set
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [TELEPHONY] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(handler)

if settings.TELEPHONY_DEBUG:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


def debug(message: str, **kwargs):
    """Log a debug-level telephony message."""
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    logger.debug(f"{message} {extra}".strip())


def info(message: str, **kwargs):
    """Log an info-level telephony message."""
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    logger.info(f"{message} {extra}".strip())


def error(message: str, **kwargs):
    """Log an error-level telephony message."""
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    logger.error(f"{message} {extra}".strip())


def warn(message: str, **kwargs):
    """Log a warning-level telephony message."""
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    logger.warning(f"{message} {extra}".strip())
