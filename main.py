"""
Power BI PDF Summarizer — Main Entry Point

Orchestrates the complete pipeline:
1. Fetch the latest Power BI report email from Microsoft 365
2. Download and parse the PDF attachment
3. Generate an AI-powered executive summary via OpenAI
4. Send a polished HTML email to the leadership team
"""

import logging
import sys
import tempfile
from pathlib import Path

from config import Config
from graph_client import GraphClient
from pdf_extractor import extract_pdf_content
from summarizer import generate_summary
from email_template import render_email, build_email_subject


def setup_logging(level: str) -> None:
    """Configure structured logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def main() -> None:
    """Run the complete Power BI summarization pipeline."""
    # Load configuration
    config = Config.from_env()
    setup_logging(config.log_level)
    logger = logging.getLogger("main")

    logger.info("=" * 60)
    logger.info("🚀 Power BI PDF Summarizer — Starting")
    logger.info("=" * 60)

    # Validate config
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(error)
        logger.error("❌ Configuration invalid. Please set all required environment variables.")
        sys.exit(1)

    logger.info(f"Report: {config.report_name}")
    logger.info(f"Mailbox: {config.mailbox_user}")
    logger.info(f"Recipients: {', '.join(config.recipients_list)}")
    logger.info(f"AI Model: {config.openai_model}")

    # Step 1: Find the latest Power BI report email
    logger.info("")
    logger.info("📧 STEP 1: Finding latest Power BI report email...")
    graph = GraphClient(config)

    email_msg = graph.find_latest_report_email()
    if not email_msg:
        logger.error("❌ No Power BI report email found. Exiting.")
        sys.exit(1)

    if not email_msg.get("hasAttachments"):
        logger.error("❌ Email found but has no attachments. Exiting.")
        sys.exit(1)

    # Step 2: Download the PDF attachment
    logger.info("")
    logger.info("📥 STEP 2: Downloading PDF attachment...")
    pdf_path = graph.download_pdf_attachment(email_msg["id"])
    if not pdf_path:
        logger.error("❌ Could not download PDF attachment. Exiting.")
        sys.exit(1)

    # Step 3: Extract content from PDF
    logger.info("")
    logger.info("📄 STEP 3: Extracting tables and data from PDF...")
    try:
        report_content = extract_pdf_content(pdf_path)
    except Exception as e:
        logger.error(f"❌ Failed to extract PDF content: {e}")
        sys.exit(1)

    if not report_content.strip():
        logger.error("❌ No content extracted from PDF. The file may be image-based.")
        sys.exit(1)

    logger.info(f"✅ Extracted {len(report_content):,} characters from PDF")

    # Step 4: Generate AI summary
    logger.info("")
    logger.info("🤖 STEP 4: Generating executive summary via OpenAI...")
    try:
        summary = generate_summary(report_content, config)
    except Exception as e:
        logger.error(f"❌ Failed to generate summary: {e}")
        sys.exit(1)

    overall_status = summary.get("overall_status", "yellow")
    num_metrics = len(summary.get("key_metrics", []))
    logger.info(f"✅ Summary generated: {num_metrics} metrics, status: {overall_status}")

    # Step 5: Render HTML email
    logger.info("")
    logger.info("✉️  STEP 5: Rendering HTML email...")
    html_body = render_email(
        summary=summary,
        report_name=config.report_name,
        company_name=config.company_name,
        full_report_url=config.full_report_url,
    )
    email_subject = build_email_subject(config.report_name, overall_status)
    logger.info(f"✅ Email rendered ({len(html_body):,} chars)")
    logger.info(f"   Subject: {email_subject}")

    # Step 6: Send email
    logger.info("")
    logger.info("📤 STEP 6: Sending email to leadership team...")
    try:
        graph.send_html_email(
            subject=email_subject,
            html_body=html_body,
            recipients=config.recipients_list,
        )
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        sys.exit(1)

    # Cleanup temp file
    try:
        pdf_path.unlink()
        pdf_path.parent.rmdir()
    except OSError:
        pass

    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ SUCCESS — Executive summary sent!")
    logger.info(f"   Recipients: {', '.join(config.recipients_list)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
