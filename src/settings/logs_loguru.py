import inspect
import logging
import sys
import os
import re
import json
from loguru._better_exceptions import ExceptionFormatter
import loguru
from loguru import logger


# -----------------------------------------------------------------------------
# This file will allow us to replace the Django default logger with loguru
# -----------------------------------------------------------------------------
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

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


# Helps colorize json logs
def colorize_run_args(json_str):
    """
    Apply colorization to a run_args in compute workers and celery
    """
    # Define color codes
    reset = "\033[0m"
    green = "\033[32m"
    cyan = "\033[36m"
    yellow = "\033[33m"
    magenta = "\033[35m"

    lineskip = "\n"
    # Colorize json
    # Yellow by default
    # Magenta for numbers
    # Cyan for docker images
    # Green for True/False
    json_str = re.sub(
        r'("detailed_results_url": ")(.*?)(",)',
        rf"\1{yellow}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("docker_image": ")(.*?)(",)', rf"\1{cyan}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("execution_time_limit":)(.*?)(,)',
        rf"\1{magenta}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("id":)(.*?)(,)', rf"\1{magenta}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("ingestion_only_during_scoring": )(.*?)(,)',
        rf"\1{green}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("is_scoring": )(.*?)(,)', rf"\1{green}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("prediction_result": ")(.*?)(",)',
        rf"\1{yellow}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("program_data": ")(.*?)(",)', rf"\1{yellow}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("reference_data": ")(.*?)(",)', rf"\1{yellow}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("scoring_ingestion_stderr": ")(.*?)(")',
        rf"\1{yellow}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("scoring_ingestion_stdout": ")(.*?)(",)',
        rf"\1{yellow}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("scoring_result": ")(.*?)(",)', rf"\1{yellow}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("scoring_stderr": ")(.*?)(",)', rf"\1{yellow}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("scoring_stdout": ")(.*?)(",)', rf"\1{yellow}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("secret": ")(.*?)(",)', rf"\1{yellow}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("submissions_api_url": ")(.*?)(",)',
        rf"\1{yellow}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("user_pk":)(.*?)(,)', rf"\1{magenta}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("ingestion_only_during_scoring": ")(.*?)(,)',
        rf"\1{green}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("prediction_ingestion_stderr": ")(.*?)(")',
        rf"\1{yellow}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("ingestion_program": ")(.*?)(",)',
        rf"\1{yellow}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("input_data": ")(.*?)(",)', rf"\1{yellow}\2{reset}\3{lineskip}", json_str
    )
    json_str = re.sub(
        r'("prediction_stdout": ")(.*?)(",)',
        rf"\1{yellow}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("prediction_stderr": ")(.*?)(",)',
        rf"\1{yellow}\2{reset}\3{lineskip}",
        json_str,
    )
    json_str = re.sub(
        r'("prediction_ingestion_stdout": ")(.*?)(",)',
        rf"\1{yellow}\2{reset}\3{lineskip}",
        json_str,
    )

    return json_str


def colorize_json_string(json_str):
    """
    Apply colorization to a JSON string after it's been serialized.
    Colorize message based on the color of the level.
    """
    # Define color codes
    reset = "\033[0m"
    green = "\033[32m"  # For timestamp and success level
    cyan = "\033[34m"  # For DEBUG level and paths
    white = "\033[0m"  # For INFO level
    yellow = "\033[33m"  # For WARNING level
    red = "\033[31m"  # For ERROR level
    white_on_red = "\033[37;41m"  # For CRITICAL level

    # Find and colorize the timestamp
    json_str = re.sub(r'("time": ")([^"]+)(")', rf"\1{green}\2{reset}\3", json_str)

    # Extract the level before colorizing to determine message color
    level_match = re.search(r'"level": "([^"]+)"', json_str)
    level_color = white  # Default color

    if level_match:
        level = level_match.group(1)
        if level == "DEBUG":
            level_color = cyan
        elif level == "INFO":
            level_color = white
        elif level == "WARNING":
            level_color = yellow
        elif level == "ERROR":
            level_color = red
        elif level == "SUCCESS":
            level_color = green
        elif level == "CRITICAL":
            level_color = white_on_red

    # Find and colorize the log level
    json_str = re.sub(r'("level": ")DEBUG(")', rf"\1{cyan}DEBUG{reset}\2", json_str)
    json_str = re.sub(r'("level": ")INFO(")', rf"\1{white}INFO{reset}\2", json_str)
    json_str = re.sub(
        r'("level": ")WARNING(")', rf"\1{yellow}WARNING{reset}\2", json_str
    )
    json_str = re.sub(r'("level": ")ERROR(")', rf"\1{red}ERROR{reset}\2", json_str)
    json_str = re.sub(
        r'("level": ")SUCCESS(")', rf"\1{green}SUCCESS{reset}\2", json_str
    )
    json_str = re.sub(
        r'("level": ")CRITICAL(")', rf"\1{white_on_red}CRITICAL{reset}\2", json_str
    )

    # Find and colorize the message using the level color
    json_str = re.sub(
        r'("message": ")(.*?)(")', rf"\1{level_color}\2{reset}\3", json_str
    )

    # Find and colorize the path
    json_str = re.sub(r'("path": ")(.*?)(")', rf"\1{cyan}\2{reset}\3", json_str)

    # Find and colorize exceptions
    json_str = re.sub(r'("type": ")(.*?)(")', rf"\1{red}\2{reset}\3", json_str)
    json_str = re.sub(r'("value": ")(.*?)(")', rf"\1{red}\2{reset}\3", json_str)

    return json_str


def serialize(record):
    """Serialize with datetime, path info, and apply colorization to the JSON string."""
    # Extract datetime
    timestamp = record["time"].isoformat(" ", "seconds")

    # Extract file path, module, function and line info
    module_name = record["name"]
    function_name = record["function"]
    line_number = record["line"]

    path_info = f"{module_name}:{function_name}:{line_number}"

    # Get log level
    level = record["level"].name

    # Extract other info
    error: loguru.RecordException = record["exception"]
    error_by_default = sys.exc_info()  # logger.error
    show_exception_value: bool = record["extra"].get("show_exception_value", True)
    extra = record["extra"].copy()

    # Process exception info
    if error:  # only set when exception.
        exc_type, exc_value, exc_tb = error.type, error.value, error.traceback

        # Use ExceptionFormatter directly with the specific error components
        formatter = ExceptionFormatter(backtrace=True, diagnose=True, colorize=True)
        formatted_traceback = formatter.format_exception(exc_type, exc_value, exc_tb)

        exception = {
            "type": exc_type.__name__,
            "value": str(exc_value).strip("'") if show_exception_value else None,
            "traceback": "".join(formatted_traceback),
        }
    elif error_by_default[0]:  # whenever error occurs
        _type, _value, _ = sys.exc_info()
        exception = {
            "type": _type.__name__,
            "value": str(_value).strip("'") if show_exception_value else None,
            "traceback": None,
        }
    else:
        exception = None

    # Prepare data for serialization
    to_serialize = {
        "time": timestamp,
        "level": level,
        "path": path_info,
        "message": record["message"],
        "exception": exception,
    }

    # Add other extra fields
    for key, value in extra.items():
        if key not in ("serialized", "show_exception_value"):
            to_serialize[key] = value

    # Convert to JSON string
    json_str = json.dumps(to_serialize)
    record["extra"]["serialized"] = colorize_json_string(json_str)
    # Colorize the JSON string
    return "{extra[serialized]}\n"


def configure_logging(
    log_level=os.environ.get("LOG_LEVEL", "INFO"),
    serialized=os.environ.get("SERIALIZED", "false"),
):
    # We can change the level per module here. uvicorn.protolcs is set to warning, otherwise we would get logs that Caddy is already getting
    # You can get the name of modules you want to add from the logs
    if log_level.upper() == "INFO":
        moduleLogLevel = "WARNING"
    else:
        moduleLogLevel = log_level

    level_per_module = {
        "": log_level.upper(),
        "uvicorn.protocols.http": moduleLogLevel.upper(),
    }

    # Remove default logger configuration then configure logger
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    if serialized.lower() == "true":
        logger.remove()
        # logger.add(sys.stderr, format="{time:MMMM D, YYYY > HH:mm:ss!UTC} | {level} | {message}", serialize=True, filter=level_per_module)
        logger.add(
            sys.stderr,
            colorize=True,
            serialize=False,
            backtrace=True,
            diagnose=True,
            level=log_level.upper(),
            format=serialize,
            filter=level_per_module,
        )
    else:
        logger.remove()
        logger.add(sys.stderr, colorize=True, filter=level_per_module)
