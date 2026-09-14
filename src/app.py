from html import escape as html_escape

from src.config import (
    load_json_file,
    load_qradar_conf,
    load_smtp_conf,
    update_config_key,
)
from src.services.qradar import QRadar
from src.services.smtp import SMTP, Template
from src.types import (
    ParsedWindowsSecurityEvent,
    PostArielSearchResultItem,
    QRadarConfig,
    SMTP_Config,
    WindowsSecurityEvent,
)
from src.utils.constants import (
    CONFIG,
    DEFAULT_QUERY_INTERVAL_IN_MINUTES,
    MAX_QUERY_INTERVAL_IN_MINUTES,
    SEARCH_QUERY_COMPLETED_REQUEST_ATTEMPTS_IN_MINUTES,
    SEARCH_QUERY_COMPLETED_REQUEST_DELAY_IN_SECONDS,
)
from src.utils.logger import datetime, log_message


def main() -> None:
    # read windows_security_events.json from data/ folder to match with the qradar's windows security events
    wse_json_data: list[WindowsSecurityEvent] = load_json_file(
        f_name="windows_security_events.json"
    )

    # load qradar's config from CONFIG to use in qradar's instance
    qradar_config: QRadarConfig = load_qradar_conf(conf=CONFIG)

    # create qradar's instance to search & parse windows security events
    qradar: QRadar = QRadar(
        url=qradar_config["QRADAR_URL"],
        username=qradar_config["QRADAR_USERNAME"],
        password=qradar_config["QRADAR_PASSWORD"],
    )

    # get query_interval from qradar_config to use in the AQL query
    query_interval_key: str = "QRADAR_QUERY_INTERVAL"
    query_interval: int = int(
        qradar_config.get(query_interval_key) or DEFAULT_QUERY_INTERVAL_IN_MINUTES
    )

    # get all wse ids from the wse_json_data and join them with a comma to use in the AQL query
    wse_ids: str = ", ".join([wse["id"] for wse in wse_json_data])
    aql_query: str = qradar_config["QRADAR_AQL_SEARCH_QUERY"]
    aql_query = aql_query.replace("{wse_ids}", wse_ids)

    # create post search to get search id by aql query
    search_id: str = qradar.post_create_search_id_by_aql_query(aql_query=aql_query)
    if search_id == "-":
        log_message(mode="error", msg="search id not found")
        return

    # check if the search id is completed to get the results
    is_search_completed: bool = qradar.check_search_is_completed_by_search_id(
        search_id=search_id,
        max_request_attempts=SEARCH_QUERY_COMPLETED_REQUEST_ATTEMPTS_IN_MINUTES,
        request_delay_seconds=SEARCH_QUERY_COMPLETED_REQUEST_DELAY_IN_SECONDS,
    )
    if not is_search_completed:
        log_message(
            mode="error",
            msg=f"search is not completed after {SEARCH_QUERY_COMPLETED_REQUEST_ATTEMPTS_IN_MINUTES} attempts with {SEARCH_QUERY_COMPLETED_REQUEST_DELAY_IN_SECONDS} seconds delay between each attempt",
        )
        return

    # get the searched results by search id to parse
    searched_results: list[PostArielSearchResultItem] = (
        qradar.get_search_results_by_search_id(search_id=search_id)
    )
    if not searched_results:
        # no any search results found, add 15 minutes to the query_interval to search in the next run
        query_interval += DEFAULT_QUERY_INTERVAL_IN_MINUTES
        # check if the query_interval is less than 1 day, if not, set it to default_interval
        if query_interval < MAX_QUERY_INTERVAL_IN_MINUTES:
            update_config_key(key=query_interval_key, value=str(query_interval))
            log_message(
                mode="warning",
                msg=f"no any search results found in the last {query_interval - DEFAULT_QUERY_INTERVAL_IN_MINUTES} minutes",
            )
        else:
            update_config_key(
                key=query_interval_key, value=str(DEFAULT_QUERY_INTERVAL_IN_MINUTES)
            )
            log_message(
                mode="warning",
                msg=f"no any search results found for 1 day, query_interval is set to {DEFAULT_QUERY_INTERVAL_IN_MINUTES} minutes",
            )
        return

    # search results found, reset the QRADAR_QUERY_INTERVAL to the DEFAULT_QUERY_INTERVAL_IN_MINUTES
    update_config_key(
        key=query_interval_key, value=str(DEFAULT_QUERY_INTERVAL_IN_MINUTES)
    )

    # get the parsed wse after matching with the wse_json_data
    parsed_wse: list[ParsedWindowsSecurityEvent] = qradar.parse_searched_results(
        searched_results=searched_results, windows_security_events=wse_json_data
    )
    if not parsed_wse:
        return

    # load smtp config from CONFIG to use in the smtp instance
    smtp_config: SMTP_Config = load_smtp_conf(conf=CONFIG)

    # create smtp instance to send parsed wse via email
    smtp: SMTP = SMTP(
        host=smtp_config["SMTP_HOST"], port=int(smtp_config.get("SMTP_PORT") or 587)
    )

    # check if the smtp user is logged in with the given credentials
    is_logged_in: bool = smtp._login(
        user=smtp_config["SMTP_FROM_EMAIL"],
        password=smtp_config["SMTP_FROM_EMAIL_APP_PASSWORD"],
    )
    if not is_logged_in:
        return

    # process on the parsed wse to send email via smtp
    for p_wse in parsed_wse:
        # load the mail template for the each p_wse
        p_wse_mail_template: Template | None = smtp.load_mail_template()
        if p_wse_mail_template is None:
            continue

        # render the mail template with the p_wse data
        p_wse_rendered_mail_template: str = p_wse_mail_template.render(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            wse_id=p_wse["id"],
            wse_name=p_wse["name"],
            wse_desc=p_wse["description"],
            wses="".join(p_wse["events"]),
            wse_log=html_escape(s=p_wse["log"]),
        )
        # send the rendered mail template via smtp
        smtp._sendmail(
            subject=f"[QRADAR_WSE] {p_wse['name']}",
            message=p_wse_rendered_mail_template,
            to_email=smtp_config["SMTP_TO_EMAILS"],
            cc=smtp_config["SMTP_CC_EMAILS"],
        )

    smtp._quit()
