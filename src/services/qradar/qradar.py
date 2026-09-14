from time import sleep

from src.types import (
    ParsedWindowsSecurityEvent,
    PostArielSearchResponse,
    PostArielSearchResultItem,
    PostArielSearchResultsResponse,
    WindowsSecurityEvent,
)

from ..http_client import HttpClient, Response


class QRadar:
    """QRadar class to interact with IBM QRadar's API.

    For more details, see [IBM QRadar API Documentation](https://ibmsecuritydocs.github.io/qradar_api_16.0)

    Instance Attributes
    -------------------
    http_client : HttpClient
        HTTP client to make requests.
    """

    def __init__(self, url: str, username: str, password: str) -> None:
        self.http_client: HttpClient = HttpClient(url=url, auth=(username, password))

    def post_create_search_id_by_aql_query(self, aql_query: str) -> str:
        """Create a new search id based on the given AQL query.

        For more details, see [POST /ariel/searches](https://ibmsecuritydocs.github.io/qradar_api_16.0/16.0--ariel-searches-POST.html)

        Parameters
        ----------
        aql_query : str
            The AQL query to create search id.

        Returns
        -------
        str
            The search_id if the search id is created, "-" otherwise.
        """

        res: Response | None = self.http_client.request(
            method="post",
            endpoint="/api/ariel/searches",
            params={"query_expression": aql_query},
        )
        if res is None:
            return "-"

        data: PostArielSearchResponse = res.json()
        return data.get("search_id") or "-"

    def check_search_is_completed_by_search_id(
        self,
        search_id: str,
        max_request_attempts: int = 15,
        request_delay_seconds: int = 1,
    ) -> bool:
        """Check if the search completed by the search id.

        For more details, see [GET /ariel/searches/{search_id}](https://ibmsecuritydocs.github.io/qradar_api_16.0/16.0--ariel-searches-search_id-GET.html)

        Parameters
        ----------
        search_id : str
            The search_id to check.
        max_request_attempts : int, optional
            The maximum number of request attempts. Default is 15.
        request_delay_seconds : int, optional
            Delay in seconds between each request attempt. Default is 1.

        Returns
        -------
        bool
            True if the search status is "COMPLETED", False otherwise.
        """

        prefer_wait: int = max(1, request_delay_seconds)
        for _ in range(max_request_attempts):
            res: Response | None = self.http_client.request(
                method="get",
                endpoint=f"/api/ariel/searches/{search_id}",
                headers={"Prefer": f"wait={prefer_wait}"},
            )
            if res is None:
                sleep(request_delay_seconds)
                continue

            data: PostArielSearchResponse = res.json()
            status: str = str(data.get("status")).strip().upper()

            if status == "COMPLETED":
                return True

            sleep(request_delay_seconds)

        return False

    def get_search_results_by_search_id(
        self, search_id: str
    ) -> list[PostArielSearchResultItem]:
        """Get the searched results by search_id.

        For more details, see [GET /ariel/searches/{search_id}/results](https://ibmsecuritydocs.github.io/qradar_api_16.0/16.0--ariel-searches-search_id-results-GET.html)

        Parameters
        ----------
        search_id : str
            The search_id to get the results.

        Returns
        -------
        list[PostArielSearchResultItem]
            The searched results.
        """

        res: Response | None = self.http_client.request(
            method="get", endpoint=f"/api/ariel/searches/{search_id}/results"
        )
        if res is None:
            return []

        data: PostArielSearchResultsResponse = res.json()
        events: list[PostArielSearchResultItem] = data.get("events", [])
        return events

    @staticmethod
    def parse_searched_results(
        searched_results: list[PostArielSearchResultItem],
        windows_security_events: list[WindowsSecurityEvent],
    ) -> list[ParsedWindowsSecurityEvent]:
        """Parse the search results to match with the windows security events.

        Parameters
        ----------
        searched_results : list[PostArielSearchResultItem]
            The search results to parse.
        windows_security_events : list[WindowsSecurityEvent]
            The windows security events list to match with the search results.

        Returns
        -------
        list[ParsedWindowsSecurityEvent]
            The filtered windows security events that contain parsed events.
        """

        def _is_event_matched(
            wse: WindowsSecurityEvent,
            event_id: str | None,
            src_user: str,
            dst_user: str,
            group_name: str,
        ) -> bool:
            """Check if a specific windows security event matches the filters."""

            if wse.get("id") != event_id:
                return False

            if src_user == "-" and dst_user == "-" and group_name == "-":
                return False

            # get filters from wse
            filters = wse.get("filters", {})

            excluded = filters.get("excluded", {})
            excluded_src_users = excluded.get("src_users", [])
            excluded_dst_users = excluded.get("dst_users", [])
            excluded_groups = excluded.get("groups", [])

            included = filters.get("included", {})
            included_src_users = included.get("src_users", [])
            included_dst_users = included.get("dst_users", [])
            included_groups = included.get("groups", [])

            # excluded conditions
            if src_user in excluded_src_users:
                return False
            if dst_user in excluded_dst_users:
                return False
            if group_name in excluded_groups:
                return False

            # included conditions
            if included_src_users and src_user not in included_src_users:
                return False
            if included_dst_users and dst_user not in included_dst_users:
                return False
            if included_groups and group_name not in included_groups:  # noqa: SIM103
                return False

            return True

        for s_result in searched_results:
            # get windows security event expected fields from the searched result
            event_id: str | None = s_result.get("event_id")
            src_user: str = s_result.get("src_user") or "-"
            dst_user: str = s_result.get("dst_user") or "-"
            group_name: str = s_result.get("group_name") or "-"
            log: str = s_result.get("log") or "-"

            # match the search result with the windows security event
            matched_wse: WindowsSecurityEvent | None = next(
                (
                    wse
                    for wse in windows_security_events
                    if _is_event_matched(
                        wse=wse,
                        event_id=event_id,
                        src_user=src_user,
                        dst_user=dst_user,
                        group_name=group_name,
                    )
                ),
                None,
            )
            if matched_wse is None:
                continue

            # cast the matched_wse to ParsedWindowsSecurityEvent to access the events and log fields
            parsed_matched_wse: ParsedWindowsSecurityEvent = matched_wse  # type: ignore

            # format the parsed_matched_wse_text with the event text from the windows_security_events list
            parsed_matched_wse_text: str = parsed_matched_wse["text"].format(
                src_user=src_user, dst_user=dst_user, group_name=group_name
            )

            # add the parsed_matched_wse_text to the parsed_matched_wse events list to avoid duplicates
            parsed_matched_wse_list: set[str] = set(
                parsed_matched_wse.get("events", [])
            )
            parsed_matched_wse_list.add(parsed_matched_wse_text)
            parsed_matched_wse["events"] = list(parsed_matched_wse_list)
            # update the parsed_matched_wse log field with the last parsed windows security event's log field
            parsed_matched_wse["log"] = log

        # get the parsed wse from the windows_security_events list that has events
        return [wse for wse in windows_security_events if wse.get("events")]  # type: ignore
