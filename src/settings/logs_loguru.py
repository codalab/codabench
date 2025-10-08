import inspect
import logging
import sys
import os

from loguru import logger

# This file will allow us to replace the Django default logger with loguru

class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def configure_logging(log_level=os.environ.get("LOG_LEVEL", "INFO"),serialized=os.environ.get("SERIALIZED", "false")):
    # We can change the level per module here. uvicorn.protolcs is set to warning, otherwise we would get logs that Caddy is already getting
    # You can get the name of modules you want to add from the logs
    if log_level.upper() == "INFO":
        moduleLogLevel = "WARNING"
    else :
        moduleLogLevel = log_level

    level_per_module = {
        "": log_level.upper(),
        "uvicorn.protocols.http": moduleLogLevel.upper()
    }

    # Remove default logger configuration then configure logger
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    if serialized.lower() == 'true':
        logger.remove()
        logger.add(sys.stderr, format="{time:MMMM D, YYYY > HH:mm:ss!UTC} | {level} | {message}", serialize=True, filter=level_per_module)
    else:
        logger.remove()
        logger.add(sys.stderr, colorize=True, filter=level_per_module)
