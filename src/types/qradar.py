from typing import Any, NotRequired, TypedDict


class QRadarConfig(TypedDict):
    """QRadar config type"""

    QRADAR_URL: str
    QRADAR_USERNAME: str
    QRADAR_PASSWORD: str
    QRADAR_AQL_SEARCH_QUERY: str
    QRADAR_QUERY_INTERVAL: NotRequired[str]
    QRADAR_QUERY_LIMIT: NotRequired[str]


class PostArielSearchResponse(TypedDict, total=False):
    """QRadar post ariel search response type"""

    cursor_id: str
    compressed_data_file_count: int
    compressed_data_total_size: int
    data_file_count: int
    data_total_size: int
    index_file_count: int
    index_total_size: int
    processed_record_count: int
    error_messages: list[dict[str, Any]]
    desired_retention_time_msec: int
    progress: int
    progress_details: list[Any]
    query_execution_time: int
    query_string: str
    record_count: int
    save_results: bool
    status: str
    snapshot: dict[str, list[dict[str, Any]]]
    subsearch_ids: list[str]
    search_id: str


class PostArielSearchResultItem(TypedDict, total=False):
    """QRadar post ariel search result item type"""

    event_id: str
    src_user: str
    dst_user: str
    group_name: str
    log: str


class PostArielSearchResultsResponse(TypedDict, total=False):
    """QRadar post ariel search results response type"""

    events: list[PostArielSearchResultItem]
