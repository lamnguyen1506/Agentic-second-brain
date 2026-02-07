"""Observability: structured logging with Loguru."""

import sys
from pathlib import Path

from loguru import logger

from src.config import get_settings

_logging_initialized = False


def setup_logging(log_level: str | None = None) -> None:
    """Initialize structured logging with loguru."""
    global _logging_initialized

    if _logging_initialized:
        return

    settings = get_settings()
    log_level = log_level or settings.log_level

    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.remove()

    logger.add(
        settings.log_file,
        format="{message}",
        level=log_level,
        rotation="10 MB",
        retention="7 days",
        serialize=True,
    )

    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    _logging_initialized = True


log = logger
