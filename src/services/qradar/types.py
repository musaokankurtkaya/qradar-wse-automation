from typing import TypedDict, Any


class PostArielSearchResponse(TypedDict, total=False):
    """QRadar post ariel search response type.

    Attributes
    ----------
    cursor_id: str

    status: str

    compressed_data_file_count: int

    compressed_data_total_size: int

    data_file_count: int

    data_total_size: int

    index_file_count: int

    index_total_size: int

    processed_record_count: int

    desired_retention_time_msec: int

    progress: int

    progress_details: list[Any]

    query_execution_time: int

    query_string: str

    record_count: int

    size_on_disk: int

    save_results: bool

    completed: bool

    subsearch_ids: list[Any]

    snapshot: None

    search_id: str
    """

    cursor_id: str
    status: str
    compressed_data_file_count: int
    compressed_data_total_size: int
    data_file_count: int
    data_total_size: int
    index_file_count: int
    index_total_size: int
    processed_record_count: int
    desired_retention_time_msec: int
    progress: int
    progress_details: list[Any]
    query_execution_time: int
    query_string: str
    record_count: int
    size_on_disk: int
    save_results: bool
    completed: bool
    subsearch_ids: list[str]
    snapshot: None
    search_id: str


class PostArielSearchResultItem(TypedDict, total=False):
    """QRadar post ariel search result item type.

    Attributes
    ----------
    event_id: str
    src_user: str
    dst_user: str
    group_name: str
    log: str
    """

    event_id: str
    src_user: str
    dst_user: str
    group_name: str
    log: str


class PostArielSearchResultsResponse(TypedDict, total=False):
    """QRadar post ariel search results response type.

    Attributes
    ----------
    events: list[PostArielSearchResultItem]
    """

    events: list[PostArielSearchResultItem]
