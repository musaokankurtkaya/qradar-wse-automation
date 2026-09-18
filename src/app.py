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
    SMTPConfig,
    WindowsSecurityEvent,
)
from src.utils.constants import (
    CONFIG,
    DEFAULT_QRADAR_SEARCH_QUERY_INTERVAL,
    DEFAULT_QRADAR_SEARCH_QUERY_LIMIT,
    QRADAR_MAX_SEARCH_QUERY_INTERVAL,
    QRADAR_SEARCH_QUERY_COMPLETED_REQUEST_ATTEMPTS,
    QRADAR_SEARCH_QUERY_COMPLETED_REQUEST_DELAY,
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

    search_query: str = qradar_config["QRADAR_SEARCH_QUERY"]

    # get all wse ids from the wse_json_data and join them with a comma to use in the search_query
    wse_ids: str = ", ".join([wse["id"] for wse in wse_json_data])
    # get search_query_interval from qradar_config to use in the search_query
    search_query_interval_key: str = "QRADAR_SEARCH_QUERY_INTERVAL"
    search_query_interval: int = int(
        qradar_config.get(search_query_interval_key)
        or DEFAULT_QRADAR_SEARCH_QUERY_INTERVAL
    )
    # get search_query_limit from qradar_config to use in the search_query
    search_query_limit_key: str = "QRADAR_SEARCH_QUERY_LIMIT"
    search_query_limit: int = int(
        qradar_config.get(search_query_limit_key) or DEFAULT_QRADAR_SEARCH_QUERY_LIMIT
    )

    search_query = search_query.format(
        wse_ids=wse_ids, interval=search_query_interval, limit=search_query_limit
    )

    # create post search to get search id by search_query
    search_id: str = qradar.post_create_search_id_by_search_query(
        search_query=search_query
    )
    if search_id == "-":
        log_message(mode="error", msg="search id not found")
        return

    # check if the search id is completed to get the results
    is_search_completed: bool = qradar.check_search_is_completed_by_search_id(
        search_id=search_id,
        max_request_attempts=QRADAR_SEARCH_QUERY_COMPLETED_REQUEST_ATTEMPTS,
        request_delay_seconds=QRADAR_SEARCH_QUERY_COMPLETED_REQUEST_DELAY,
    )
    if not is_search_completed:
        log_message(
            mode="error",
            msg=f"search is not completed after {QRADAR_SEARCH_QUERY_COMPLETED_REQUEST_ATTEMPTS} attempts with {QRADAR_SEARCH_QUERY_COMPLETED_REQUEST_DELAY} seconds delay between each attempt",
        )
        return

    # get the search results by search id to parse
    search_results: list[PostArielSearchResultItem] = (
        qradar.get_search_results_by_search_id(search_id=search_id)
    )
    if not search_results:
        # no any search results found, add 15 minutes to the search_query_interval to search in the next run
        search_query_interval += DEFAULT_QRADAR_SEARCH_QUERY_INTERVAL
        # check if the search_query_interval is less than QRADAR_MAX_SEARCH_QUERY_INTERVAL, if not, set it to DEFAULT_QRADAR_SEARCH_QUERY_INTERVAL
        if search_query_interval < QRADAR_MAX_SEARCH_QUERY_INTERVAL:
            update_config_key(
                key=search_query_interval_key, value=str(search_query_interval)
            )
            log_message(
                mode="warning",
                msg=f"no any search results found in the last {search_query_interval - DEFAULT_QRADAR_SEARCH_QUERY_INTERVAL} minutes",
            )
        else:
            update_config_key(
                key=search_query_interval_key,
                value=str(DEFAULT_QRADAR_SEARCH_QUERY_INTERVAL),
            )
            log_message(
                mode="warning",
                msg=f"no any search results found for {QRADAR_MAX_SEARCH_QUERY_INTERVAL} minutes, query_interval is set to {DEFAULT_QRADAR_SEARCH_QUERY_INTERVAL} minutes",
            )
        return

    # search results found, reset the search_query_interval to the DEFAULT_QRADAR_SEARCH_QUERY_INTERVAL
    update_config_key(
        key=search_query_interval_key, value=str(DEFAULT_QRADAR_SEARCH_QUERY_INTERVAL)
    )

    # get the parsed wse after matching with the wse_json_data
    parsed_wse: list[ParsedWindowsSecurityEvent] = qradar.parse_search_results(
        search_results=search_results, windows_security_events=wse_json_data
    )
    if not parsed_wse:
        return

    # load smtp config from CONFIG to use in the smtp instance
    smtp_config: SMTPConfig = load_smtp_conf(conf=CONFIG)

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
