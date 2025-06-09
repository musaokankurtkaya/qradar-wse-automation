from os import path as os_path, makedirs as os_makedirs
from datetime import datetime
import logging

from pythonjsonlogger.json import JsonFormatter

from .constants import LOG_FOLDER_PATH, ENV, IS_PROD, REDMINE_PROJECT


class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to the console log messages.

    Attributes
    ----------
    ANSI_COLORS : dict[str, str]
        ANSI colors for the log messages.
    LOG_COLORS : dict[str, str]
        Log level colors for the log messages.

    Methods
    -------
    - format(record: logging.LogRecord) -> str
    """

    ANSI_COLORS: dict[str, str] = {
        "red": "\033[1;31;40m",
        "green": "\033[1;32;40m",
        "yellow": "\033[1;33;40m",
        "purple": "\033[1;35;40m",
        "reset": "\033[0m",
    }

    LOG_COLORS: dict[str, str] = {
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "purple",
    }

    def __init__(self, fmt: str) -> None:
        super().__init__(fmt=fmt)

    def format(self, record: logging.LogRecord) -> str:
        log_level: str = record.levelname
        log_color: str = self.LOG_COLORS.get(log_level, "reset")

        record.levelname = (
            f"{self.ANSI_COLORS[log_color]}[{log_level}]{self.ANSI_COLORS['reset']}"
        )
        return super().format(record=record)


def setup_console_handler() -> logging.Handler:
    """Create and return the console handler for colored log output."""

    console_handler: logging.StreamHandler = logging.StreamHandler()

    console_formatter: logging.Formatter = logging.Formatter(
        fmt="%(levelname)s %(message)s"
    )
    console_handler.setFormatter(fmt=ColoredFormatter(fmt=console_formatter._fmt))
    return console_handler


def setup_file_handler() -> logging.Handler:
    """Create and return the file handler for JSON formatted logs."""

    # create log folder if not exists
    now: datetime = datetime.now()
    log_folder_path: str = os_path.join(LOG_FOLDER_PATH, str(now.year))
    os_makedirs(name=log_folder_path, exist_ok=True)

    # create log file path based on the current month
    log_file_name: str = f"log_{now.month:02d}.log"
    log_file_path: str = os_path.join(log_folder_path, log_file_name)

    file_handler: logging.FileHandler = logging.FileHandler(
        filename=log_file_path, mode="a", encoding="utf-8"
    )
    file_formatter: JsonFormatter = JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        json_ensure_ascii=False,
        rename_fields={"levelname": "level", "asctime": "timestamp"},
        static_fields={
            "environment": ENV,
            "redmine_project": {**REDMINE_PROJECT.__dict__},
        },
    )
    file_handler.setFormatter(fmt=file_formatter)
    file_handler.setLevel(level=logging.WARNING)
    return file_handler


def setup_logger(name: str | None = None, level: int = logging.INFO) -> None:
    """Setup logger for the app.

    Parameters
    ----------
    name : str, optional
        Logger name, by default None.
    level : int, optional
        Log level for the logger, by default logging.INFO (20)

    - Log level: **INFO** for console, **WARNING** for file
    - Log format: **'%(levelname)s %(message)s'** (console), **formatted with JSON** (file)
    - Log date format: **'%Y-%m-%d %H:%M:%S'**
    - Log file name: **log_01.log**, **log_02.log**, ...
    - Log file path: **/path/to/logs/2025/log_01.log**
    """

    # create logger
    logger: logging.Logger = logging.getLogger(name=name)
    # set minimum log level
    logger.setLevel(level=level)
    # add console and file handlers based on the environment
    if IS_PROD:
        logger.addHandler(hdlr=setup_file_handler())

    logger.addHandler(hdlr=setup_console_handler())


def log_message(mode: str, msg: str, **log_kwargs) -> None:
    """Log a message with the given mode & message.

    Parameters
    ----------
    mode : str
        Log level mode (notset, debug, info, warning, error, critical)
    msg : str
        Log message to log.
    **log_kwargs
        Additional log keyword arguments to pass to the logger (e.g. extra, stack_info, exc_info etc.)
    """

    levels: dict[str, int] = {
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    level: int = levels.get(mode, logging.INFO)
    logging.log(level=level, msg=msg, **log_kwargs)
