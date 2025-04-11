import sys

from loguru import logger

from .configs import settings

# set level based on environment (production: info)
if not settings.is_dev():
    logger.remove()
    logger.add(sys.stderr, level="INFO")
