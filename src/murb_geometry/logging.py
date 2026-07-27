"""Structured logging for murb-geometry."""

import logging
import sys

from rich.logging import RichHandler


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure structured logging with rich output.

    Parameters
    ----------
    level
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns
    -------
    logging.Logger
        Configured root logger for murb_geometry.
    """
    logger = logging.getLogger("murb_geometry")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = RichHandler(
            show_time=True,
            show_path=True,
            rich_tracebacks=True,
            markup=True,
        )
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        fmt = logging.Formatter("%(message)s", datefmt="[%X]")
        handler.setFormatter(fmt)
        logger.addHandler(handler)

        # Also log to stderr for non-interactive use
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(logging.WARNING)
        logger.addHandler(stream_handler)

    return logger
