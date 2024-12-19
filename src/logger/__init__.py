from sys import stderr

from loguru import logger

from config import settings

from core.enums import Environments, LogLevels

logger.remove()

logger.add(stderr, level=LogLevels.DEBUG if settings.ENVIRONMENT == Environments.LOCAL else LogLevels.INFO)

logger: 'logger' = logger.opt(colors=True)
