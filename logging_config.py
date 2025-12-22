"""Shared logging configuration for Energenie scripts."""

import logging
from pathlib import Path


LOG_PATH = Path(__file__).with_name('outdoor_lights.log')


def configure_logging(level=logging.INFO):
    """Configure logging to append to the shared outdoor lights log file."""
    logging.basicConfig(
        filename=str(LOG_PATH),
        level=level,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
    )
