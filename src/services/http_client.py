from urllib.parse import urljoin
from requests import Session, Response, RequestException

from src.utils.logger import log_message


class HttpClient:
    """HTTP client to make requests.

    Attributes
    ----------
    url : str
        Base URL to make requests.
    session : Session
        Session object to make requests.

    Methods
    -------
    - request(method: str, url: str = None, endpoint: str = None, **request_kwargs) -> Response
    - get_full_url(url: str, endpoint: str = None) -> str
    """

    def __init__(self, url: str, **session_kwargs) -> None:
        """Initialize the HTTP client.

        Parameters
        ----------
        url : str
            Base URL to make requests.
        **session_kwargs
            Request keyword arguments to pass to the session object.
        """

        self.url: str = url

        with Session() as session:
            self.session = session
            self.session.headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            } | session_kwargs.get("headers", {})
            self.session.auth = session_kwargs.get("auth", None)
            self.session.verify = session_kwargs.get("verify", False)

    def request(
        self, method: str, url: str = None, endpoint: str = None, **request_kwargs
    ) -> Response | None:
        """Make an HTTP request.

        Parameters
        ----------
        method : str
            HTTP method to use (get, post, put, delete, etc.)
        url : str, optional
            URL to make the request. If not provided, it will use the base URL. Default is None.
        endpoint : str, optional
            Endpoint to append to the base URL. If not provided, it will use the base URL. Default is None.
        **request_kwargs
            Request keyword arguments to pass to the request method.

        Returns
        -------
        Response | None
            HTTP response object if the request is successful, otherwise None.
        """

        try:
            full_url: str = self.get_full_url(
                url=url if url else self.url, endpoint=endpoint
            )
            return self.session.request(
                method=method,
                url=full_url,
                timeout=120,
                **request_kwargs,
            )
        except RequestException as e:
            log_message(
                mode="error",
                msg=f"request error occured ⊱ {e} ⊰ while requesting to {full_url}",
            )
        except Exception as e:
            log_message(
                mode="error",
                msg=f"unexpected error occured ⊱ {e} ⊰ while requesting to {full_url}",
            )

    def get_full_url(self, url: str, endpoint: str = None) -> str:
        """Join the base URL with the endpoint.

        Parameters
        ----------
        url : str
            Base URL to join.
        endpoint : str, optional
            Endpoint to append to the url. Default is None.

        Returns
        -------
        str
            Full URL.

        Examples
        --------
        >>> http_client.get_full_url(url="http://example.com/home", endpoint="/api/v1")
        ... "http://example.com/api/v1"
        """

        return urljoin(base=url, url=endpoint) if endpoint else url
