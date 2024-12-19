from enum import StrEnum


class Environments(StrEnum):
    LOCAL: str = 'local'
    DEVELOPMENT: str = 'development'
    PRODUCTION: str = 'production'


class LogLevels(StrEnum):
    DEBUG: str = 'DEBUG'
    INFO: str = 'INFO'
    WARNING: str = 'WARNING'
    ERROR: str = 'ERROR'
    CRITICAL: str = 'CRITICAL'
