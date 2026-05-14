"""
Configuration module for Power BI PDF Summarizer.
All settings are loaded from environment variables.
"""

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    # Microsoft Graph API (Azure AD App Registration)
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""

    # Email settings
    mailbox_user: str = ""  # The mailbox to read from (e.g., reports@company.com)
    email_subject_filter: str = "Power BI"  # Subject line filter to find the report
    email_sender_filter: str = ""  # Optional: filter by sender address

    # Recipients (comma-separated email addresses)
    recipient_emails: str = ""

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Summary settings
    company_name: str = "Our Company"
    report_name: str = "Daily Performance Report"
    full_report_url: str = ""  # Link to the full Power BI report online

    # Logging
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            azure_tenant_id=os.environ.get("AZURE_TENANT_ID", ""),
            azure_client_id=os.environ.get("AZURE_CLIENT_ID", ""),
            azure_client_secret=os.environ.get("AZURE_CLIENT_SECRET", ""),
            mailbox_user=os.environ.get("MAILBOX_USER", ""),
            email_subject_filter=os.environ.get("EMAIL_SUBJECT_FILTER", "Power BI"),
            email_sender_filter=os.environ.get("EMAIL_SENDER_FILTER", ""),
            recipient_emails=os.environ.get("RECIPIENT_EMAILS", ""),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
            company_name=os.environ.get("COMPANY_NAME", "Our Company"),
            report_name=os.environ.get("REPORT_NAME", "Daily Performance Report"),
            full_report_url=os.environ.get("FULL_REPORT_URL", ""),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )

    def validate(self) -> list[str]:
        """Validate that all required config values are set. Returns list of errors."""
        errors = []
        required_fields = {
            "AZURE_TENANT_ID": self.azure_tenant_id,
            "AZURE_CLIENT_ID": self.azure_client_id,
            "AZURE_CLIENT_SECRET": self.azure_client_secret,
            "MAILBOX_USER": self.mailbox_user,
            "RECIPIENT_EMAILS": self.recipient_emails,
            "OPENAI_API_KEY": self.openai_api_key,
        }
        for name, value in required_fields.items():
            if not value:
                errors.append(f"Missing required environment variable: {name}")
        return errors

    @property
    def recipients_list(self) -> list[str]:
        """Parse comma-separated recipient emails into a list."""
        return [e.strip() for e in self.recipient_emails.split(",") if e.strip()]
