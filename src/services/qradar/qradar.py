from time import sleep

from ..http_client import HttpClient, Response
from .types import (
    PostArielSearchResponse,
    PostArielSearchResultItem,
    PostArielSearchResultsResponse,
    Any,
)


class QRadar:
    """QRadar class to interact with QRadar's API.

    For more details, see [QRadar API Documentation](https://ibmsecuritydocs.github.io/qradar_api_16.0)

    Attributes
    ----------
    http_client : HttpClient
        HTTP client to make requests.

    Methods
    -------
    - post_create_search_by_aql_query(aql_query: str) -> str
    - check_search_is_completed_by_search_id(search_id: str, max_request_attempt: int = 5, request_delay: float | int = 1) -> bool
    - get_search_results_by_search_id(search_id: str) -> list[PostArielSearchResultItem]
    - parse_searched_events(searched_event: PostArielSearchResultItem, windows_security_events: list[dict[str, Any]]) -> None

    Static Methods
    --------------
    - is_field_value_empty(field: Any) -> str
    """

    def __init__(self, url: str, username: str, password: str) -> None:
        self.http_client: HttpClient = HttpClient(url=url, auth=(username, password))

    def post_create_search_by_aql_query(self, aql_query: str) -> str | None:
        """Create a new search based on the given AQL query.

        For more details, see [POST /ariel/searches](https://ibmsecuritydocs.github.io/qradar_api_16.0/16.0--ariel-searches-POST.html)

        Parameters
        ----------
        aql_query : str
            The AQL query to create search.

        Returns
        -------
        str | None
            The search_id if the search is created, None otherwise.
        """

        res: Response | None = self.http_client.request(
            method="post",
            endpoint="/api/ariel/searches",
            params={"query_expression": aql_query},
        )
        if not res:
            return

        data: PostArielSearchResponse = res.json()
        search_id: str | None = data.get("search_id")
        return search_id

    def check_search_is_completed_by_search_id(
        self,
        search_id: str,
        request_delay: float | int = 1,
    ) -> bool:
        """Check if the search is completed.

        For more details, see [GET /ariel/searches/{search_id}](https://ibmsecuritydocs.github.io/qradar_api_16.0/16.0--ariel-searches-search_id-GET.html)

        Parameters
        ----------
        search_id : str
            The search_id to check.
        request_delay : float | int, optional
            Delay in seconds between each request. Default is 1.

        Returns
        -------
        bool
            True if the search is completed, False otherwise.
        """

        is_searching: bool = False
        while not is_searching:
            res: Response | None = self.http_client.request(
                method="get", endpoint=f"/api/ariel/searches/{search_id}"
            )
            if not res:
                return False

            data: PostArielSearchResponse = res.json()
            is_searching = data.get("completed", True)

            sleep(request_delay)

        return is_searching

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
            method="get", endpoint=f"api/ariel/searches/{search_id}/results"
        )
        if not res:
            return []

        data: PostArielSearchResultsResponse = res.json()
        events: list[PostArielSearchResultItem] = data.get("events", [])
        return events

    def parse_searched_events(
        self,
        searched_event: PostArielSearchResultItem,
        windows_security_events: list[dict[str, Any]],
    ) -> None:
        """Parse the searched event to match with the windows security events and update the events list.

        Parameters
        ----------
        searched_event : dict[str, dict[str, Any]]
            The searched event to parse.
        windows_security_events : list[dict[str, Any]]
            The windows security events list to match with the searched event.
        """

        # get windows security event expected fields from the searched event
        event_id: str | None = searched_event.get("event_id")
        src_user: str = self.is_field_value_empty(field=searched_event.get("src_user"))
        dst_user: str = self.is_field_value_empty(field=searched_event.get("dst_user"))
        group_name: str = self.is_field_value_empty(
            field=searched_event.get("group_name")
        )
        event_log: str = self.is_field_value_empty(field=searched_event.get("log"))

        # does the searched event match with the windows security events list by the event_id
        # and the src_user, dst_user, group_name fields are not in the excluded fields
        matched_searched_event: dict[str, Any] = next(
            (
                wse
                for wse in windows_security_events
                if wse.get("event_id") == event_id
                and src_user not in wse.get("excluded_src_users", [])
                and dst_user not in wse.get("excluded_dst_users", [])
                and group_name not in wse.get("excluded_groups", [])
                and (
                    not wse.get("included_src_users", [])
                    or src_user in wse.get("included_src_users", [])
                )
                and (
                    not wse.get("included_dst_users", [])
                    or dst_user in wse.get("included_dst_users", [])
                )
                and (
                    not wse.get("included_groups", [])
                    or group_name in wse.get("included_groups", [])
                )
            ),
            {},
        )
        if not matched_searched_event:
            return

        # update the event_text with the came fields from the searched event
        matched_searched_event_text: str = matched_searched_event["event_text"]
        matched_searched_event_text = matched_searched_event_text.format(**locals())

        # if the matched_searched_event_text is not in the events list
        # add the matched_searched_event_text to the matched_searched_event events list
        matched_searched_event_events: set[str] = set(
            matched_searched_event.get("events", [])
        )
        matched_searched_event_events.add(matched_searched_event_text)
        matched_searched_event["events"] = list(matched_searched_event_events)
        # update the event_log with the searched event log
        matched_searched_event["event_log"] = event_log

    @staticmethod
    def is_field_value_empty(field: Any) -> str:
        """Check if the value of field is empty or not.

        Parameters
        ----------
        field : Any
            The field to check if it is empty or not.

        Returns
        -------
        str
            The value of field if it is not empty, else "( not exist )".
        """

        is_valid: bool = field in ("", " ", "N/A", "n/a", "-", " - ", "None", None)
        is_str = isinstance(field, str)

        return "( not exists )" if is_valid and not is_str else field
