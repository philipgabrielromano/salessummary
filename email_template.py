"""
HTML email template for retail executive summary emails.
Designed for Goodwill retail leadership — focused on store health,
resource allocation, and early warning signals.
Renders well in Outlook, Gmail, and mobile clients. All CSS is inline.
"""

from datetime import datetime


STATUS_COLORS = {
    "green": {"bg": "#E8F5E9", "text": "#2E7D32", "dot": "🟢", "label": "On Track"},
    "yellow": {"bg": "#FFF8E1", "text": "#F57F17", "dot": "🟡", "label": "Needs Attention"},
    "red": {"bg": "#FFEBEE", "text": "#C62828", "dot": "🔴", "label": "Critical"},
}

HEALTH_STYLES = {
    "thriving": {"bg": "#E8F5E9", "text": "#2E7D32", "dot": "🟢", "label": "Thriving"},
    "maintaining": {"bg": "#E3F2FD", "text": "#1565C0", "dot": "🔵", "label": "Maintaining"},
    "declining": {"bg": "#FFF8E1", "text": "#F57F17", "dot": "🟡", "label": "Declining"},
    "critical": {"bg": "#FFEBEE", "text": "#C62828", "dot": "🔴", "label": "Critical"},
}


def render_email(summary: dict, report_name: str, company_name: str, full_report_url: str = "") -> str:
    """Render the structured summary dict into a polished HTML email."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    overall = summary.get("overall_status", "yellow")
    overall_style = STATUS_COLORS.get(overall, STATUS_COLORS["yellow"])

    # Build all sections
    critical_alerts_html = _build_critical_alerts(summary.get("critical_alerts", []))
    store_health_html = _build_store_health_table(summary.get("store_health_summary", []))
    company_metrics_html = _build_company_metrics(summary.get("key_metrics_company_wide", []))
    resource_html = _build_list_section(summary.get("resource_allocation", []))
    bright_spots_html = _build_list_section(summary.get("bright_spots", []))
    watch_list_html = _build_watch_list(summary.get("watch_list", []))

    # Full report button
    report_button = ""
    if full_report_url:
        report_button = f"""
        <tr>
            <td style="padding:0 24px 24px 24px;text-align:center;">
                <a href="{full_report_url}"
                   style="display:inline-block;padding:12px 32px;background-color:#1565C0;
                          color:#ffffff;text-decoration:none;border-radius:6px;
                          font-size:14px;font-weight:600;">
                    📊 View Full Report in Power BI
                </a>
            </td>
        </tr>
        """

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_name} - Executive Summary</title>
</head>
<body style="margin:0;padding:0;background-color:#F5F5F5;font-family:Segoe UI,Helvetica,Arial,sans-serif;">

<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
       style="background-color:#F5F5F5;padding:20px 0;">
    <tr>
        <td align="center">

<table role="presentation" width="680" cellspacing="0" cellpadding="0" border="0"
       style="background-color:#FFFFFF;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.08);
              max-width:680px;width:100%;">

    <!-- Header -->
    <tr>
        <td style="background:linear-gradient(135deg,#1565C0,#1976D2);padding:24px;
                   border-radius:8px 8px 0 0;">
            <h1 style="margin:0;color:#FFFFFF;font-size:20px;font-weight:600;">
                📈 {report_name}
            </h1>
            <p style="margin:4px 0 0 0;color:#BBDEFB;font-size:13px;">
                Executive Briefing &bull; {today}
            </p>
        </td>
    </tr>

    <!-- Overall Status Banner -->
    <tr>
        <td style="padding:20px 24px 16px 24px;">
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                   style="background-color:{overall_style['bg']};border-radius:8px;
                          border-left:4px solid {overall_style['text']};">
                <tr>
                    <td style="padding:16px 20px;">
                        <span style="font-size:22px;vertical-align:middle;">{overall_style['dot']}</span>
                        <span style="font-size:16px;font-weight:700;color:{overall_style['text']};
                                     vertical-align:middle;margin-left:8px;">
                            Overall: {overall_style['label']}
                        </span>
                        <p style="margin:8px 0 0 0;font-size:14px;color:#333333;line-height:1.5;">
                            {summary.get('overall_status_reason', '')}
                        </p>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- Executive Summary -->
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 8px 0;font-size:16px;color:#1565C0;font-weight:600;">
                Executive Summary
            </h2>
            <p style="margin:0;font-size:14px;color:#333333;line-height:1.6;">
                {summary.get('executive_summary', '')}
            </p>
        </td>
    </tr>

    <!-- Critical Alerts -->
    {critical_alerts_html}

    <!-- Company-Wide Metrics -->
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 12px 0;font-size:16px;color:#1565C0;font-weight:600;">
                📊 Company-Wide KPIs: Yesterday vs. MTD
            </h2>
            {company_metrics_html}
        </td>
    </tr>

    <!-- Store Health Summary -->
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 12px 0;font-size:16px;color:#1565C0;font-weight:600;">
                🏪 Store Health Overview
            </h2>
            {store_health_html}
        </td>
    </tr>

    <!-- Resource Allocation -->
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 12px 0;font-size:16px;color:#1565C0;font-weight:600;">
                🎯 Resource Allocation Recommendations
            </h2>
            <ol style="margin:0;padding-left:20px;">
                {resource_html}
            </ol>
        </td>
    </tr>

    <!-- Watch List -->
    {watch_list_html}

    <!-- Bright Spots -->
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 12px 0;font-size:16px;color:#2E7D32;font-weight:600;">
                ⭐ Bright Spots
            </h2>
            <ul style="margin:0;padding-left:20px;">
                {bright_spots_html}
            </ul>
        </td>
    </tr>

    <!-- View Full Report Button -->
    {report_button}

    <!-- Footer -->
    <tr>
        <td style="padding:16px 24px;background-color:#FAFAFA;border-radius:0 0 8px 8px;
                   border-top:1px solid #EEEEEE;">
            <p style="margin:0;font-size:11px;color:#999999;text-align:center;line-height:1.5;">
                This briefing was auto-generated from the {report_name} by the
                {company_name} AI Briefing System.<br>
                Thresholds: DPSF vs. store goal | Donor Value ≥ $43 | eCommerce ≥ 10%<br>
                Data reflects the most recent report received on {today}.
            </p>
        </td>
    </tr>

</table>
        </td>
    </tr>
</table>

</body>
</html>
"""
    return html


def _build_critical_alerts(alerts: list[dict]) -> str:
    """Build the critical alerts section — only shown if there are alerts."""
    if not alerts:
        return ""

    rows = ""
    for alert in alerts:
        severity = alert.get("severity", "warning")
        if severity == "critical":
            icon = "🚨"
            border_color = "#C62828"
            bg_color = "#FFEBEE"
        else:
            icon = "⚠️"
            border_color = "#F57F17"
            bg_color = "#FFF8E1"

        rows += f"""
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
               style="background-color:{bg_color};border-radius:6px;border-left:4px solid {border_color};
                      margin-bottom:10px;">
            <tr>
                <td style="padding:12px 16px;">
                    <strong style="font-size:14px;color:{border_color};">
                        {icon} {alert.get('store', 'Unknown Store')}
                    </strong>
                    <p style="margin:6px 0 4px 0;font-size:13px;color:#333;line-height:1.5;">
                        {alert.get('issue', '')}
                    </p>
                    <p style="margin:0 0 4px 0;font-size:12px;color:#666;font-family:monospace;">
                        {alert.get('metrics', '')}
                    </p>
                    <p style="margin:0 0 4px 0;font-size:12px;color:#666;">
                        <strong>Trend:</strong> {alert.get('trend', '')}
                    </p>
                    <p style="margin:0;font-size:12px;color:{border_color};font-weight:600;">
                        → {alert.get('recommendation', '')}
                    </p>
                </td>
            </tr>
        </table>
        """

    return f"""
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 12px 0;font-size:16px;color:#C62828;font-weight:600;">
                🚨 Critical Alerts — Immediate Attention Required
            </h2>
            {rows}
        </td>
    </tr>
    """


def _build_store_health_table(stores: list[dict]) -> str:
    """Build the store health summary table."""
    if not stores:
        return '<p style="font-size:14px;color:#666;">No store data available.</p>'

    # Sort: critical first, then declining, maintaining, thriving
    priority = {"critical": 0, "declining": 1, "maintaining": 2, "thriving": 3}
    stores.sort(key=lambda s: priority.get(s.get("status", "maintaining"), 2))

    rows = ""
    for i, store in enumerate(stores):
        status = store.get("status", "maintaining")
        style = HEALTH_STYLES.get(status, HEALTH_STYLES["maintaining"])
        bg = "#FFFFFF" if i % 2 == 0 else "#FAFAFA"

        rows += f"""
        <tr style="background-color:{bg};">
            <td style="padding:8px 10px;font-size:13px;color:#333;border-bottom:1px solid #EEE;
                       white-space:nowrap;">
                {style['dot']} <strong>{store.get('store', '')}</strong>
            </td>
            <td style="padding:8px 10px;font-size:12px;color:{style['text']};border-bottom:1px solid #EEE;
                       font-weight:600;text-align:center;">
                {style['label']}
            </td>
            <td style="padding:8px 10px;font-size:12px;color:#333;border-bottom:1px solid #EEE;">
                {store.get('yesterday_vs_goal', '')}
            </td>
            <td style="padding:8px 10px;font-size:12px;color:#333;border-bottom:1px solid #EEE;">
                {store.get('mtd_trend', '')}
            </td>
            <td style="padding:8px 10px;font-size:12px;color:#666;border-bottom:1px solid #EEE;">
                {store.get('primary_concern', '')}
            </td>
        </tr>
        """

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
           style="border:1px solid #E0E0E0;border-radius:6px;border-collapse:separate;overflow:hidden;">
        <tr style="background-color:#1565C0;">
            <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:left;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.5px;">Store</th>
            <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:center;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.5px;">Status</th>
            <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:left;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.5px;">Yesterday</th>
            <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:left;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.5px;">MTD Trend</th>
            <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:left;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.5px;">Primary Concern</th>
        </tr>
        {rows}
    </table>
    """


def _build_company_metrics(metrics: list[dict]) -> str:
    """Build company-wide KPI table with yesterday, MTD, and goal columns."""
    if not metrics:
        return '<p style="font-size:14px;color:#666;">No metrics extracted.</p>'

    rows = ""
    for i, metric in enumerate(metrics):
        status = metric.get("status", "yellow")
        style = STATUS_COLORS.get(status, STATUS_COLORS["yellow"])
        bg = "#FFFFFF" if i % 2 == 0 else "#FAFAFA"
        note = metric.get("note", "")
        note_html = f'<br><span style="font-size:11px;color:#888;">{note}</span>' if note else ""

        rows += f"""
        <tr style="background-color:{bg};">
            <td style="padding:8px 10px;font-size:13px;color:#333;border-bottom:1px solid #EEE;">
                {style['dot']} {metric.get('name', '')}
            </td>
            <td style="padding:8px 10px;font-size:13px;color:#333;font-weight:600;
                       border-bottom:1px solid #EEE;text-align:right;">
                {metric.get('yesterday', '')}
            </td>
            <td style="padding:8px 10px;font-size:13px;color:#333;font-weight:600;
                       border-bottom:1px solid #EEE;text-align:right;">
                {metric.get('mtd', '')}
            </td>
            <td style="padding:8px 10px;font-size:13px;color:#666;
                       border-bottom:1px solid #EEE;text-align:right;">
                {metric.get('goal', '')}
            </td>
            <td style="padding:8px 10px;font-size:13px;color:{style['text']};font-weight:600;
                       border-bottom:1px solid #EEE;text-align:center;">
                {style['label']}{note_html}
            </td>
        </tr>
        """

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
           style="border:1px solid #E0E0E0;border-radius:6px;border-collapse:separate;overflow:hidden;">
        <tr style="background-color:#1565C0;">
            <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:left;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.5px;">Metric</th>
            <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:right;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.5px;">Yesterday</th>
            <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:right;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.5px;">MTD</th>
            <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:right;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.5px;">Goal</th>
            <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:center;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.5px;">Status</th>
        </tr>
        {rows}
    </table>
    """


def _build_watch_list(items: list[dict]) -> str:
    """Build the watch list section."""
    if not items:
        return ""

    rows = ""
    for item in items:
        rows += f"""
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
               style="background-color:#FFF8E1;border-radius:6px;border-left:4px solid #F57F17;
                      margin-bottom:8px;">
            <tr>
                <td style="padding:10px 14px;">
                    <strong style="font-size:13px;color:#F57F17;">
                        👁️ {item.get('store', '')}
                    </strong>
                    <span style="font-size:12px;color:#333;"> — {item.get('reason', '')}</span>
                    <br>
                    <span style="font-size:11px;color:#888;">
                        Escalation trigger: {item.get('trigger', '')}
                    </span>
                </td>
            </tr>
        </table>
        """

    return f"""
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 12px 0;font-size:16px;color:#F57F17;font-weight:600;">
                👁️ Watch List — Monitor Next 48-72 Hours
            </h2>
            {rows}
        </td>
    </tr>
    """


def _build_list_section(items: list[str]) -> str:
    """Build a simple HTML list from string items."""
    if not items:
        return '<li style="color:#666;font-size:14px;">No items.</li>'
    return "".join(
        f'<li style="margin-bottom:8px;color:#333;font-size:14px;line-height:1.5;">{item}</li>'
        for item in items
    )


def build_email_subject(report_name: str, overall_status: str) -> str:
    """Build the email subject line with status indicator."""
    style = STATUS_COLORS.get(overall_status, STATUS_COLORS["yellow"])
    today = datetime.now().strftime("%m/%d/%Y")
    return f"{style['dot']} {report_name} — Executive Briefing {today}"
