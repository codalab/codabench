import os
import logging

from gunicorn.app.base import BaseApplication
from gunicorn.glogging import Logger
import settings.logs_loguru as logs_loguru

import asgi

app = asgi.application

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
WORKERS = int(os.environ.get("GUNICORN_WORKERS", "2"))


class StubbedGunicornLogger(Logger):
    def setup(self, cfg):
        handler = logging.NullHandler()
        self.error_logger = logging.getLogger("gunicorn.error")
        self.error_logger.addHandler(handler)
        self.access_logger = logging.getLogger("gunicorn.access")
        self.access_logger.addHandler(handler)
        self.error_logger.setLevel(LOG_LEVEL.upper())
        self.access_logger.setLevel(LOG_LEVEL.upper())


class StandaloneApplication(BaseApplication):
    """Our Gunicorn application."""

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


if __name__ == "__main__":
    intercept_handler = logs_loguru.InterceptHandler()
    logging.root.setLevel(LOG_LEVEL.upper())

    seen = set()
    for name in [
        *logging.root.manager.loggerDict.keys(),
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            logging.getLogger(name).handlers = [intercept_handler]

    logs_loguru.configure_logging(LOG_LEVEL.upper(), os.environ.get("SERIALIZED", "false"))

    options = {
        "bind": [':8000', ':80'],
        "workers": WORKERS,
        "accesslog": "-",
        "errorlog": "-",
        "worker_class": "uvicorn.workers.UvicornWorker",
        "logger_class": StubbedGunicornLogger,
        "capture_output": 'true'
    }

    StandaloneApplication(app, options).run()
