from src.config.config import ROOT_FOLDER_PATH, Path, load_config

LOG_FOLDER_PATH: Path = ROOT_FOLDER_PATH / "logs"

CONFIG: dict[str, str | None] = load_config()

DEFAULT_ENV: str = "dev"

ENV: str = CONFIG.get("ENV") or DEFAULT_ENV

IS_PROD: bool = ENV == "prod"

TEAMS_WORKFLOW_CONFIG: dict[str, str | None] = {
    "url": CONFIG.get("TEAMS_WORKFLOW_URL"),
    "title": ROOT_FOLDER_PATH.name,
}

DEFAULT_QUERY_INTERVAL_IN_MINUTES: int = 15

MAX_QUERY_INTERVAL_IN_MINUTES: int = 1440

SEARCH_QUERY_COMPLETED_REQUEST_ATTEMPTS_IN_MINUTES: int = 15
SEARCH_QUERY_COMPLETED_REQUEST_DELAY_IN_SECONDS: int = 1
