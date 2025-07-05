from src.config.config import (
    Path,
    load_config,
    ROOT_FOLDER_PATH,
    PROJECT_FOLDER_PATH,
    ENV_FOLDER_PATH,
    DATA_FOLDER_PATH,
)
from src.services.redmine.types import CustomProject

LOG_FOLDER_PATH: Path = ROOT_FOLDER_PATH / "logs"

CONFIG: dict[str, str | None] = load_config()

DEFAULT_ENV: str = "dev"

ENV: str = CONFIG.get("ENV", DEFAULT_ENV)

IS_PROD: bool = ENV == "prod"

MAX_QUERY_INTERVAL: int = 1440  # 1 day in minutes

TEAMS_WORKFLOW_CONFIG: dict[str, str | None] = {
    "url": CONFIG.get("TEAMS_WORKFLOW_URL"),
    "title": f"{ROOT_FOLDER_PATH.name}-wse-automation",
}

REDMINE_PROJECT: CustomProject = (
    CustomProject(
        id=int(CONFIG.get("REDMINE_PROD_PROJECT_ID", 0)),
        name=CONFIG.get("REDMINE_PROD_PROJECT_NAME"),
    )
    if IS_PROD
    else CustomProject(
        id=int(CONFIG.get("REDMINE_DEV_PROJECT_ID", 0)),
        name=CONFIG.get("REDMINE_DEV_PROJECT_NAME"),
    )
)

REDMINE_WINDOWS_SECURITY_EVENT_TRACKER_ID: int = int(
    CONFIG.get("REDMINE_WINDOWS_SECURITY_EVENT_TRACKER_ID", 0)
)

REDMINE_ISSUE_DESC_TEMPLATE_MODE: str = CONFIG.get(
    "REDMINE_ISSUE_DESC_TEMPLATE_MODE", "light"
)
