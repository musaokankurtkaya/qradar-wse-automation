from json import load as json_load, JSONDecodeError
from pathlib import Path
from typing import Any

from dotenv import dotenv_values, set_key


ROOT_FOLDER_PATH: Path = Path(__file__).parent.parent.parent

PROJECT_FOLDER_PATH: Path = ROOT_FOLDER_PATH / "src"

CONFIG_FOLDER_PATH: Path = PROJECT_FOLDER_PATH / "config"

ENV_FOLDER_PATH: Path = CONFIG_FOLDER_PATH / ".env"

DATA_FOLDER_PATH: Path = PROJECT_FOLDER_PATH / "data"


def load_config() -> dict[str, str | None]:
    """Reads the .env file and returns the settings as a dictionary.

    Returns
    -------
    dict[str, str | None]
        Configuration settings, if the .env file exists and is not empty. Otherwise, empty dictionary.
    """

    return dict(dotenv_values(dotenv_path=ENV_FOLDER_PATH))


def update_config_key(key: str, value: str) -> None:
    """Update the value of a key in the .env file.

    Parameters
    ----------
    key : str
        Key to set.
    value : str
        Value to set for the key.
    """

    set_key(
        dotenv_path=ENV_FOLDER_PATH,
        key_to_set=key,
        value_to_set=value,
        quote_mode="never",
    )


def load_qradar_config(config: dict[str, str | None]) -> dict[str, str | None]:
    """Load qradar configuration with the given config parameter.

    Parameters
    ----------
    config : dict[str, str | None]
        The configuration settings as a dictionary from the .env file.

    Returns
    -------
    dict[str, str | None]
        qradar configuration settings, if all the expected parameters are found. Otherwise, raises ValueError.

    Raises
    ------
    ValueError
        - If QRADAR_URL, QRADAR_USERNAME, QRADAR_PASSWORD, QRADAR_EVENT_IDS_QUERY not found in .env file.
    """

    qradar_config: dict[str, str | None] = {
        k: v for k, v in config.items() if k.startswith("QRADAR_")
    }

    required_config_keys: list[str] = [
        "QRADAR_URL",
        "QRADAR_USERNAME",
        "QRADAR_PASSWORD",
        "QRADAR_EVENT_IDS_QUERY",
    ]
    missing_config_keys: list[str] = [
        k for k in required_config_keys if not config.get(k)
    ]
    if missing_config_keys:
        error_msg: str = f"{', '.join(missing_config_keys)} not found in .env file"
        raise ValueError(error_msg)

    return qradar_config


def load_redmine_config(config: dict[str, str | None]) -> dict[str, str | None]:
    """Load redmine configuration with the given config parameter.

    Parameters
    ----------
    config : dict[str, str | None]
        The configuration settings as a dictionary from the .env file.

    Returns
    -------
    dict[str, str | None]
        Redmine configuration settings, if all the expected parameters are found. Otherwise, raises ValueError.

    Raises
    ------
    ValueError
        - If REDMINE_URL, REDMINE_KEY not found in .env file.
    """

    redmine_config: dict[str, str | None] = {
        k: v for k, v in config.items() if k.startswith("REDMINE_")
    }

    required_config_keys: list[str] = ["REDMINE_URL", "REDMINE_KEY"]
    missing_config_keys: list[str] = [
        k for k in required_config_keys if not redmine_config.get(k)
    ]
    if missing_config_keys:
        error_msg: str = f"{', '.join(missing_config_keys)} not found in .env file"
        raise ValueError(error_msg)

    return redmine_config


def load_windows_security_events(
    file_name: str = "windows_security_events.json",
) -> list[dict[str, Any]]:
    """Load windows security events from data/ folder.

    Parameters
    ----------
    file_name : str, optional
        The name of the file to load. Default is "windows_security_events.json".

    Returns
    -------
    list[dict[str, Any]]
        List of windows security events, if the file exists and not empty. Otherwise, raises exception.

    Raises
    ------
    FileNotFoundError
        If the file is not found in data/ folder.
    ValueError
        If the file is empty.
    JSONDecodeError
        If the file is not a valid JSON file.
    """

    file_path: Path = DATA_FOLDER_PATH / file_name
    if not file_path.exists():
        raise FileNotFoundError(f"{file_name} not found in data/ folder")

    with open(file=file_path, encoding="utf-8") as f:
        try:
            file_content: list[dict[str, Any]] = json_load(fp=f)
            if not file_content:
                raise ValueError(f"{file_name} not contains any data")
            return file_content
        except JSONDecodeError as e:
            raise JSONDecodeError(
                msg=f"{file_name} not a valid JSON file", doc=e.doc, pos=e.pos
            )
