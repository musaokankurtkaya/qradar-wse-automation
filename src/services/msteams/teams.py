from ..http_client import HttpClient, Response, log_message
from src.utils.constants import IS_PROD, TEAMS_WORKFLOW_CONFIG


class MsTeams:
    """Microsoft Teams class to interact with Teams' workflows, such as sending messages.

    Attributes
    ----------
    workflow_url: str | None
        URL of the Microsoft Teams workflow to send messages to.
    http_client : HttpClient
        HTTP client to make requests.

    Static Methods
    --------------
    - send_message(msg: str, title=TEAMS_WORKFLOW_CONFIG["title"]) -> None
    """

    workflow_url: str | None = TEAMS_WORKFLOW_CONFIG["url"]
    http_client: HttpClient = HttpClient(url=workflow_url, verify=True)

    @classmethod
    def send_message(
        cls,
        msg: str,
        title: str = TEAMS_WORKFLOW_CONFIG["title"],
        send_on_prod: bool = True,
    ) -> None:
        """Send a message to Microsoft Teams with the given message and title using the workflow URL.

        Parameters
        ----------
        msg : str
            Message to send.
        title : str, optional
            Title of the message, by default TEAMS_WORKFLOW_CONFIG["title"]
        send_on_prod : bool, optional
            Flag to send the message on production, by default True.
        """

        if not IS_PROD and not send_on_prod:
            return

        if not cls.workflow_url:
            log_message(
                mode="error",
                msg="TEAMS_WORKFLOW_URL not found in the .env file, message will not be sent to teams",
            )
            return

        json_body = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "msTeams": {"width": "full"},
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": title,
                                "size": "large",
                                "weight": "bolder",
                            },
                            {
                                "type": "TextBlock",
                                "text": msg,
                                "wrap": True,
                            },
                        ],
                    },
                }
            ],
        }

        res: Response | None = cls.http_client.request(method="post", json=json_body)

        is_error: bool = not res or res.status_code > 299
        if is_error:
            log_message(
                mode="error",
                msg="error occurred while sending message to teams",
            )
