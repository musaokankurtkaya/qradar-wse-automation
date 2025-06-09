from src.config.config import (
    load_windows_security_events,
    load_qradar_config,
    load_redmine_config,
    update_config_key,
)
from src.services.qradar.qradar import QRadar, PostArielSearchResultItem, Any
from src.services.redmine.redmine import Redmine, User, log_message
from src.utils.constants import CONFIG, MAX_QUERY_INTERVAL


def main() -> None:
    # read windows_security_events.json from data/ folder to match with the qradar's wse events
    windows_security_events: list[dict[str, Any]] | None = (
        load_windows_security_events()
    )
    if not windows_security_events:
        return

    # load qradar's config from CONFIG to use in qradar's instance
    qradar_config: dict[str, str] | None = load_qradar_config(config=CONFIG)
    if not qradar_config:
        return

    # create qradar's instance to search & parse events
    qradar: QRadar = QRadar(
        url=qradar_config["QRADAR_URL"],
        username=qradar_config["QRADAR_USERNAME"],
        password=qradar_config["QRADAR_PASSWORD"],
    )

    # get query_interval & limit from qradar_config to use in the post ariel search
    default_interval: int = 15
    query_interval: int = int(
        qradar_config.get("QRADAR_QUERY_INTERVAL", default_interval)
    )
    default_limit: str = "9999"
    limit: str = qradar_config.get("QRADAR_QUERY_LIMIT", default_limit)

    # get all event ids from the windows_security_events and join them with OR operator to use in the query
    event_ids: str = " OR ".join(
        [f"\"Event ID\"={wse['event_id']}" for wse in windows_security_events]
    )

    # create sql query based on the windows_security_events to search
    sql_query: tuple[str, ...] = (
        "select \"Event ID\" AS 'event_id', username as 'src_user', \"Target Username\" as 'dst_user', ",
        "\"Group Name\" as 'group_name', utf8(payload) as 'log'",
        "from events",
        f"where LOGSOURCETYPENAME(devicetype)='Microsoft Windows Security Event Log' and ({event_ids}) LIMIT {limit} LAST {query_interval} MINUTES",
    )
    # join the sql query to use in the post ariel search
    str_sql_query: str = " ".join(sql_query)

    # create post search to get results
    search_id: str | None = qradar.post_create_search_by_sql_query(
        sql_query=str_sql_query
    )
    if not search_id:
        log_message(mode="error", msg="search id not found")
        return

    # check if the search is completed to get the results
    is_search_completed: bool = qradar.check_search_is_completed_by_search_id(
        search_id=search_id, request_delay=0.8
    )
    if not is_search_completed:
        return

    # get the searched events and parse them to match with the windows security events
    searched_events: list[PostArielSearchResultItem] = (
        qradar.get_search_results_by_search_id(search_id=search_id)
    )

    # process on the searched events to match with the windows security events and update the events list
    for searched_event in searched_events:
        qradar.parse_searched_events(
            searched_event=searched_event,
            windows_security_events=windows_security_events,
        )

    # get the parsed events from the windows_security_events list that has events
    parsed_events: list[dict[str, Any]] = [
        wse for wse in windows_security_events if wse.get("events", [])
    ]
    if not parsed_events:
        # no wse events found, add 15 minutes to the query_interval to search in the next run
        query_interval += default_interval
        # check if the query_interval is less than 1 day (1440 minutes), if not, set it to default_interval
        if query_interval < MAX_QUERY_INTERVAL:
            update_config_key(key="QRADAR_QUERY_INTERVAL", value=str(query_interval))
            log_message(
                mode="warning",
                msg=f"no any windows security events found in the last ⊱ {query_interval} ⊰ minutes",
            )
        else:
            update_config_key(key="QRADAR_QUERY_INTERVAL", value=str(default_interval))
            log_message(
                mode="warning",
                msg=f"no windows security events were found for 1 day, query_interval is set to {default_interval} minutes",
            )
        return

    # wse events found, reset the QRADAR_QUERY_INTERVAL to the default_interval
    update_config_key(key="QRADAR_QUERY_INTERVAL", value=str(default_interval))

    # load redmine config from CONFIG to use in the redmine instance
    redmine_config: dict[str, str] | None = load_redmine_config(config=CONFIG)
    if not redmine_config:
        return

    # create redmine instance to upsert wse issues for the parsed events
    redmine: Redmine = Redmine(
        url=redmine_config["REDMINE_URL"], key=redmine_config["REDMINE_KEY"]
    )

    # check if the redmine user is logged in with the given credentials
    redmine_user: User | None = redmine.auth()
    if not redmine_user:
        log_message(mode="error", msg="redmine authentication failed")
        return

    # process on the parsed events to create or update the wse issues
    for parsed_event in parsed_events:
        redmine.upsert_wse_event(
            redmine_user=redmine_user, event_to_upsert=parsed_event
        )
