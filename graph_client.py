"""
Microsoft Graph API client for reading emails and sending HTML summaries.
Uses OAuth2 client_credentials flow (application permissions).
"""

import base64
import logging
import tempfile
from pathlib import Path

import requests

from config import Config

logger = logging.getLogger(__name__)

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
AUTH_URL_TEMPLATE = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


class GraphClient:
    """Microsoft Graph API client for mail operations."""

    def __init__(self, config: Config):
        self.config = config
        self._access_token: str | None = None

    def _get_access_token(self) -> str:
        """Authenticate using client credentials and return an access token."""
        if self._access_token:
            return self._access_token

        url = AUTH_URL_TEMPLATE.format(tenant_id=self.config.azure_tenant_id)
        payload = {
            "client_id": self.config.azure_client_id,
            "client_secret": self.config.azure_client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }

        logger.info("Authenticating with Microsoft Graph API...")
        response = requests.post(url, data=payload, timeout=30)
        response.raise_for_status()

        self._access_token = response.json()["access_token"]
        logger.info("Successfully authenticated with Microsoft Graph API.")
        return self._access_token

    @property
    def _headers(self) -> dict:
        """Authorization headers for Graph API requests."""
        return {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
        }

    def find_latest_report_email(self) -> dict | None:
        """
        Search the mailbox for the most recent Power BI report email.
        Returns the email message dict, or None if not found.
        """
        user = self.config.mailbox_user
        subject_filter = self.config.email_subject_filter
        sender_filter = self.config.email_sender_filter

        # Build OData filter
        filters = [f"contains(subject, '{subject_filter}')"]
        if sender_filter:
            filters.append(
                f"from/emailAddress/address eq '{sender_filter}'"
            )
        filter_query = " and ".join(filters)

        url = (
            f"{GRAPH_BASE_URL}/users/{user}/messages"
            f"?$filter={filter_query}"
            f"&$orderby=receivedDateTime desc"
            f"&$top=1"
            f"&$select=id,subject,receivedDateTime,from,hasAttachments"
        )

        logger.info(f"Searching for Power BI report email (filter: {subject_filter})...")
        response = requests.get(url, headers=self._headers, timeout=30)
        response.raise_for_status()

        messages = response.json().get("value", [])
        if not messages:
            logger.warning("No Power BI report email found matching the filter.")
            return None

        msg = messages[0]
        logger.info(
            f"Found email: '{msg['subject']}' "
            f"received at {msg['receivedDateTime']}"
        )
        return msg

    def download_pdf_attachment(self, message_id: str) -> Path | None:
        """
        Download the first PDF attachment from a message.
        Returns the path to the downloaded temp file, or None.
        """
        user = self.config.mailbox_user
        url = (
            f"{GRAPH_BASE_URL}/users/{user}/messages/{message_id}/attachments"
            f"?$filter=contentType eq 'application/pdf'"
        )

        logger.info("Fetching PDF attachment...")
        response = requests.get(url, headers=self._headers, timeout=60)
        response.raise_for_status()

        attachments = response.json().get("value", [])
        if not attachments:
            # Fallback: get all attachments and look for PDF by name
            url_all = (
                f"{GRAPH_BASE_URL}/users/{user}/messages/{message_id}/attachments"
            )
            response = requests.get(url_all, headers=self._headers, timeout=60)
            response.raise_for_status()
            attachments = [
                a for a in response.json().get("value", [])
                if a.get("name", "").lower().endswith(".pdf")
            ]

        if not attachments:
            logger.warning("No PDF attachment found in the email.")
            return None

        attachment = attachments[0]
        file_name = attachment.get("name", "report.pdf")
        content_bytes = base64.b64decode(attachment["contentBytes"])

        # Save to temp file
        temp_dir = Path(tempfile.mkdtemp())
        pdf_path = temp_dir / file_name
        pdf_path.write_bytes(content_bytes)

        logger.info(f"Downloaded PDF: {file_name} ({len(content_bytes):,} bytes)")
        return pdf_path

    def send_html_email(
        self,
        subject: str,
        html_body: str,
        recipients: list[str],
    ) -> None:
        """Send an HTML email via Microsoft Graph API."""
        user = self.config.mailbox_user

        to_recipients = [
            {"emailAddress": {"address": email}} for email in recipients
        ]

        email_payload = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": html_body,
                },
                "toRecipients": to_recipients,
            },
            "saveToSentItems": "true",
        }

        url = f"{GRAPH_BASE_URL}/users/{user}/sendMail"

        logger.info(f"Sending summary email to {len(recipients)} recipient(s)...")
        response = requests.post(
            url, headers=self._headers, json=email_payload, timeout=30
        )
        response.raise_for_status()
        logger.info("Summary email sent successfully!")
