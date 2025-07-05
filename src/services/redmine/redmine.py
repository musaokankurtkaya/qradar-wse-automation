from datetime import datetime
from os import path as os_path
from html import escape as html_escape

from jinja2 import (
    Environment,
    FileSystemLoader,
    Template,
    TemplateNotFound,
    select_autoescape,
)
import redminelib
from redminelib.resources import Issue, User
from redminelib.exceptions import BaseRedmineError

from src.utils.constants import (
    REDMINE_PROJECT,
    REDMINE_ISSUE_DESC_TEMPLATE_MODE,
    REDMINE_WINDOWS_SECURITY_EVENT_TRACKER_ID,
)
from ..msteams.teams import MsTeams, log_message


class Redmine(redminelib.Redmine):
    CUSTOM_DEFAULT_PRIORITY: dict[str, str | int] = {"id": 2, "name": "Medium"}
    CUSTOM_DEFAULT_STATUS: dict[str, str | int] = {"id": 1, "name": "New"}

    def __init__(self, url: str, **redmine_kwargs) -> None:
        super().__init__(url=url, **redmine_kwargs)

    def is_wse_issue_exists(self, issue_subject: str) -> list[Issue]:
        """Check with the given **issue_subject** if there is any issue exists in the **Windows Security Events** category which is tracker id **6**.

        Parameters
        ----------
        issue_subject : str
            Issue subject to check if exists.

        Returns
        -------
        list[Issue]
            Today list of **Windows Security Events** issues with notes if exists else empty list.
        """

        return list(
            self.issue.filter(
                project_id=REDMINE_PROJECT.id,
                tracker_id=REDMINE_WINDOWS_SECURITY_EVENT_TRACKER_ID,
                status_id="*",
                subject=issue_subject,
                created_on=datetime.now().strftime("%Y-%m-%d"),
                include=["journals"],
            )
        )

    def create_wse_issue(
        self,
        user: User,
        priority_id: int,
        issue_subject: str,
        event_id: str,
        event_desc: str,
        events: list[str],
        event_log: str,
    ) -> Issue:
        """Create an issue in the **Windows Security Events** category which is tracker id **6**.

        Parameters
        ----------
        user : User
            User to assign the issue.
        priority_id : int
            Issue priority id.
        issue_subject : str
        event_id : str
            Windows Security Event ID.
        event_desc : str
            Windows Security Event Description.
        events : list[str]
            List of Windows Security Events to add to the issue's description.
        event_log : str

        Returns
        -------
        Issue
            Created issue.
        """

        # get last issue id to pass to the issue template
        last_issue_id: int = self.get_last_issue_id()

        # format issue description via the issue template
        description: str | None = self.load_issue_template(
            subject=issue_subject,
            user=user,
            priority_id=priority_id,
            event_id=event_id,
            event_desc=event_desc,
            events=events,
            event_log=event_log,
            issue_id=last_issue_id + 1,
        )

        return self.issue.create(
            project_id=REDMINE_PROJECT.id,
            subject=issue_subject,
            tracker_id=REDMINE_WINDOWS_SECURITY_EVENT_TRACKER_ID,
            description=description,
            status_id=self.CUSTOM_DEFAULT_STATUS["id"],
            priority_id=priority_id,
            assigned_to_id=user.id,
            custom_fields=[
                {
                    "id": 10,
                    "value": f"Windows\t{event_id}" if event_id.isdigit() else event_id,
                }
            ],
        )

    def update_wse_issue(
        self,
        subject: str,
        user: User,
        priority_id: int,
        event_id: str,
        event_desc: str,
        new_events: list[str],
        event_log: str,
        to_update_issue_id: int,
    ) -> None:
        """Update the issue in the **Windows Security Events** category which is tracker id **6**.

        Parameters
        ----------
        subject : str
            Issue subject
        user : User
            User to assign the issue
        priority_id : int
            Issue priority id
        event_id : str
            Windows Security Event ID
        event_desc : str
            Windows Security Event Description
        new_events : list[str]
            List of Windows Security Events to add to the issue's journal
        event_log : str
        to_update_issue_id : int
        """

        # format issue description via the issue template
        description: str | None = self.load_issue_template(
            subject=subject,
            user=user,
            priority_id=priority_id,
            event_id=event_id,
            event_desc=event_desc,
            events=new_events,
            event_log=event_log,
            issue_id=to_update_issue_id,
        )

        self.issue.update(
            resource_id=to_update_issue_id,
            status_id=1,
            priority_id=priority_id,
            notes=description,
        )

    def get_last_issue_id(self) -> int:
        """Get the last issue id to use in the issue template.

        Returns
        -------
        int
            Last issue id if exists else 0
        """
        issues: list[Issue] = list(self.issue.all(sort="created_on:desc", limit=1))
        return issues[0].id if issues else 0

    def upsert_wse_event(self, redmine_user: User, event_to_upsert: dict[str,]) -> None:
        """Update or create the wse issue on redmine for the given event."

        Parameters
        ----------
        event_to_upsert : dict[str, Any]
            The event to update or create the wse issue
        """

        pe_priority_id: int = int(
            event_to_upsert.get(
                "redmine_issue_priority_id", self.CUSTOM_DEFAULT_PRIORITY["id"]
            )
        )
        pe_event_id: str = event_to_upsert.get("event_id")
        pe_issue_subject: str = event_to_upsert.get("redmine_issue_subject")
        pe_issue_description: str = event_to_upsert.get("redmine_issue_description")
        pe_events: list[str] = event_to_upsert.get("events", [])
        pe_log: str = event_to_upsert.get("event_log")

        log_message(
            mode="info",
            msg=f"upserting ⊱ {len(pe_events)} ⊰ events for event id ⊱ {pe_event_id} ⊰",
        )

        try:
            # check if there is any wse issue exists that given the issue subject
            is_wse_issue_exists: list[Issue] = self.is_wse_issue_exists(
                issue_subject=pe_issue_subject
            )
            if not is_wse_issue_exists:
                created_issue: Issue = self.create_wse_issue(
                    user=redmine_user,
                    priority_id=pe_priority_id,
                    issue_subject=pe_issue_subject,
                    event_id=pe_event_id,
                    event_desc=pe_issue_description,
                    events=pe_events,
                    event_log=pe_log,
                )
                log_message(
                    mode="info",
                    msg=f"⊱ {self.url}/issues/{created_issue.id} ⊰ issue created for event id ⊱ {pe_event_id} ⊰",
                )
                return

            wse_issue: Issue = is_wse_issue_exists[0]

            # check if the new events are in the description
            is_pe_in_desc = [
                pe
                for pe in pe_events
                if pe not in wse_issue.description.replace("\r", "")
            ]
            if not is_pe_in_desc:
                log_message(
                    mode="warning",
                    msg=f"⊱ {self.url}/issues/{wse_issue.id} ⊰ event already exists in description for event id ⊱ {pe_event_id} ⊰",
                )
                return

            # check if the new events are in the journal notes
            is_pe_in_notes = [
                pe
                for pe in pe_events
                if pe
                not in "".join(
                    [
                        journal.notes if journal.notes else ""
                        for journal in wse_issue.journals
                    ]
                )
            ]
            if not is_pe_in_notes:
                log_message(
                    mode="warning",
                    msg=f"⊱ {self.url}/issues/{wse_issue.id} ⊰ event already exists in journal for event ⊱ {pe_event_id} ⊰",
                )
                return

            # if the event is not in the description or journal, update the wse_issue
            self.update_wse_issue(
                subject=pe_issue_subject,
                user=redmine_user,
                priority_id=pe_priority_id,
                event_id=pe_event_id,
                event_desc=pe_issue_description,
                new_events=is_pe_in_notes,
                event_log=pe_log,
                to_update_issue_id=wse_issue.id,
            )
            log_message(
                mode="info",
                msg=f"⊱ {self.url}/issues/{wse_issue.id} ⊰ issue updated for event id ⊱ {pe_event_id} ⊰",
            )
        except BaseRedmineError as e:
            log_message(
                mode="error",
                msg=f"redmine error occured ⊱ {e} ⊰ while upserting for event id ⊱ {pe_event_id} ⊰",
            )
            MsTeams.send_message(
                msg=f"redmine error occured ⊱ {e} ⊰ while upserting for event id ⊱ {pe_event_id} ⊰"
            )

    def get_priority_name_by_id(self, priority_id: int) -> str:
        """Get the priority name by the given priority id.

        Parameters
        ----------
        priority_id : int
            Priority id to get the priority name

        Returns
        -------
        str
            Priority name
        """

        issue_priorities: list[dict] = list(
            self.enumeration.filter(resource="issue_priorities")
        )
        return next(
            (p.name for p in issue_priorities if p.id == priority_id),
            self.CUSTOM_DEFAULT_PRIORITY["name"],
        )

    def load_issue_template(
        self,
        subject: str,
        user: User | str,
        priority_id: int,
        event_id: str,
        event_desc: str,
        events: list[str],
        event_log: str,
        issue_id: int,
    ) -> str | None:
        """Load the issue description template to format the issue description with the given parameters.

        Parameters
        ----------
        subject : str
            Issue subject.
        user : User | str
            User to assign the issue.
        priority_id : int
            Issue priority id.
        event_id : str
            Windows Security Event ID.
        event_desc : str
            Windows Security Event Description.
        events : list[str]
            List of Windows Security Events.
        event_log : str
            Windows Security Event Log.
        issue_id : int
            Issue id to pass to the issue template.

        Returns
        -------
        str | None
            Formatted issue description template or None if the issue template file not found.

        Raises
        ------
        BaseRedmineError
            If the issue template file not found in the redmine/templates directory.
        """

        template_path: str = os_path.join(os_path.dirname(__file__), "templates")
        env: Environment = Environment(
            loader=FileSystemLoader(searchpath=template_path),
            autoescape=select_autoescape(
                enabled_extensions=(), disabled_extensions=("html", "htm", "xml")
            ),
        )

        # set the issue template file name based on the issue description template mode
        issue_template_file_name: str = (
            f"{REDMINE_ISSUE_DESC_TEMPLATE_MODE}_issue_description_template.html"
        )
        try:
            template: Template = env.get_template(name=issue_template_file_name)
            template_content: str = template.render(
                date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                created_by=str(user),
                subject=subject,
                status=self.CUSTOM_DEFAULT_STATUS["name"],
                priority=self.get_priority_name_by_id(priority_id=priority_id),
                event_id=event_id,
                event_description=event_desc,
                events="".join(events),
                event_log=html_escape(s=event_log),
                issue_id=issue_id,
            )

            return "{{html\n" + template_content + "\n}}"
        except TemplateNotFound:
            raise BaseRedmineError(
                f"{issue_template_file_name} not found in redmine/templates directory"
            )
