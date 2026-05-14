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
        Uses a two-step approach:
          1. Fetch recent emails filtered by subject (using $search)
          2. Filter by sender in Python (Graph API doesn't support combining these)
        Returns the email message dict, or None if not found.
        """
        user = self.config.mailbox_user
        subject_filter = self.config.email_subject_filter
        sender_filter = self.config.email_sender_filter

        # Use $search for subject (KQL syntax) — this is the most reliable
        # approach for Graph API. $search requires ConsistencyLevel: eventual.
        # NOTE: $orderby cannot be combined with $search, so we sort in Python.
        search_query = f'"subject:{subject_filter}"'

        url = (
            f"{GRAPH_BASE_URL}/users/{user}/messages"
            f"?$search={search_query}"
            f"&$top=10"
            f"&$select=id,subject,receivedDateTime,from,hasAttachments"
        )

        headers = {
            **self._headers,
            "ConsistencyLevel": "eventual",
        }

        logger.info(f"Searching for Power BI report email (subject: {subject_filter})...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        messages = response.json().get("value", [])

        # Filter by sender in Python if configured
        if sender_filter and messages:
            sender_lower = sender_filter.lower()
            messages = [
                m for m in messages
                if m.get("from", {}).get("emailAddress", {}).get("address", "").lower() == sender_lower
            ]

        if not messages:
            logger.warning("No Power BI report email found matching the filter.")
            return None

        # Sort by receivedDateTime descending (can't use $orderby with $search)
        messages.sort(key=lambda m: m.get("receivedDateTime", ""), reverse=True)
        msg = messages[0]
        logger.info(
            f"Found email: '{msg['subject']}' "
            f"received at {msg['receivedDateTime']}"
        )
        return msg

    def download_pdf_attachment(self, message_id: str) -> Path | None:
        """
        Download the first PDF attachment from a message.
        Handles both inline (#microsoft.graph.fileAttachment) and
        large attachments. Returns the path to a temp file, or None.
        """
        user = self.config.mailbox_user

        # Fetch all attachments (no contentType filter — not always reliable)
        url = (
            f"{GRAPH_BASE_URL}/users/{user}/messages/{message_id}/attachments"
        )

        logger.info("Fetching attachments...")
        response = requests.get(url, headers=self._headers, timeout=60)
        response.raise_for_status()

        all_attachments = response.json().get("value", [])
        logger.info(f"Found {len(all_attachments)} attachment(s)")

        # Log details for debugging
        for att in all_attachments:
            logger.info(
                f"  - name='{att.get('name')}' "
                f"type={att.get('@odata.type')} "
                f"contentType={att.get('contentType')} "
                f"size={att.get('size', 'N/A')}"
            )

        # Find PDF attachment by name or contentType
        pdf_attachment = None
        for att in all_attachments:
            name = (att.get("name") or "").lower()
            content_type = (att.get("contentType") or "").lower()
            if name.endswith(".pdf") or "pdf" in content_type:
                pdf_attachment = att
                break

        if not pdf_attachment:
            logger.warning("No PDF attachment found in the email.")
            return None

        att_name = pdf_attachment.get("name", "report.pdf")
        att_type = pdf_attachment.get("@odata.type", "")
        att_id = pdf_attachment.get("id", "")

        # Ensure filename has .pdf extension
        if not att_name.lower().endswith(".pdf"):
            att_name += ".pdf"

        logger.info(f"Selected attachment: '{att_name}' (type: {att_type})")

        # Handle file attachment with contentBytes present
        if pdf_attachment.get("contentBytes"):
            content_bytes = base64.b64decode(pdf_attachment["contentBytes"])
        else:
            # contentBytes may be missing for large attachments.
            # Fetch the raw content using $value endpoint.
            logger.info("No contentBytes — fetching raw content via $value endpoint...")
            value_url = (
                f"{GRAPH_BASE_URL}/users/{user}/messages/{message_id}"
                f"/attachments/{att_id}/$value"
            )
            value_response = requests.get(
                value_url, headers=self._headers, timeout=120
            )
            value_response.raise_for_status()
            content_bytes = value_response.content

        # Save to temp file
        temp_dir = Path(tempfile.mkdtemp())
        pdf_path = temp_dir / att_name
        pdf_path.write_bytes(content_bytes)

        # Verify it looks like a PDF
        with open(pdf_path, "rb") as f:
            header = f.read(5)
        if header != b"%PDF-":
            logger.error(
                f"Downloaded file does not appear to be a valid PDF. "
                f"Header bytes: {header!r}"
            )
            logger.error(
                f"First 200 chars: {content_bytes[:200]!r}"
            )
            return None

        logger.info(f"Downloaded PDF: {att_name} ({len(content_bytes):,} bytes) ✅")
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
