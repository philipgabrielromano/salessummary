"""
HTML email template for executive summary emails.
Designed to render well in Outlook, Gmail, and mobile email clients.
Uses inline CSS for maximum compatibility.
"""

from datetime import datetime


STATUS_COLORS = {
    "green": {"bg": "#E8F5E9", "text": "#2E7D32", "dot": "🟢", "label": "On Track"},
    "yellow": {"bg": "#FFF8E1", "text": "#F57F17", "dot": "🟡", "label": "Needs Attention"},
    "red": {"bg": "#FFEBEE", "text": "#C62828", "dot": "🔴", "label": "Critical"},
}


def render_email(summary: dict, report_name: str, company_name: str, full_report_url: str = "") -> str:
    """
    Render the structured summary dict into a polished HTML email.

    Args:
        summary: The parsed JSON summary from OpenAI.
        report_name: Name of the report for the subject.
        company_name: Company name for branding.
        full_report_url: Optional link to the full Power BI report.

    Returns:
        Complete HTML string ready to send.
    """
    today = datetime.now().strftime("%A, %B %d, %Y")
    overall = summary.get("overall_status", "yellow")
    overall_style = STATUS_COLORS.get(overall, STATUS_COLORS["yellow"])

    # Build key metrics rows
    metrics_html = _build_metrics_table(summary.get("key_metrics", []))

    # Build insights list
    insights = summary.get("trends_and_insights", [])
    insights_html = "".join(
        f'<li style="margin-bottom:8px;color:#333333;font-size:14px;line-height:1.5;">{insight}</li>'
        for insight in insights
    )

    # Build action items list
    actions = summary.get("action_items", [])
    actions_html = "".join(
        f'<li style="margin-bottom:8px;color:#333333;font-size:14px;line-height:1.5;">{action}</li>'
        for action in actions
    )

    # Build risks list
    risks = summary.get("risks", [])
    risks_html = ""
    if risks:
        risk_items = "".join(
            f'<li style="margin-bottom:8px;color:#333333;font-size:14px;line-height:1.5;">{risk}</li>'
            for risk in risks
        )
        risks_html = f"""
        <tr>
            <td style="padding:0 24px 24px 24px;">
                <h2 style="margin:0 0 12px 0;font-size:16px;color:#C62828;font-weight:600;">
                    ⚠️ Risks &amp; Watchpoints
                </h2>
                <ul style="margin:0;padding-left:20px;">
                    {risk_items}
                </ul>
            </td>
        </tr>
        """

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

<!-- Wrapper -->
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" 
       style="background-color:#F5F5F5;padding:20px 0;">
    <tr>
        <td align="center">

<!-- Main Container -->
<table role="presentation" width="640" cellspacing="0" cellpadding="0" border="0" 
       style="background-color:#FFFFFF;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.08);
              max-width:640px;width:100%;">

    <!-- Header -->
    <tr>
        <td style="background:linear-gradient(135deg,#1565C0,#1976D2);padding:24px;
                   border-radius:8px 8px 0 0;">
            <h1 style="margin:0;color:#FFFFFF;font-size:20px;font-weight:600;">
                📈 {report_name}
            </h1>
            <p style="margin:4px 0 0 0;color:#BBDEFB;font-size:13px;">
                Executive Summary &bull; {today}
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

    <!-- Key Metrics Table -->
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 12px 0;font-size:16px;color:#1565C0;font-weight:600;">
                📊 Key Metrics
            </h2>
            {metrics_html}
        </td>
    </tr>

    <!-- Trends & Insights -->
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 12px 0;font-size:16px;color:#1565C0;font-weight:600;">
                📈 Trends &amp; Insights
            </h2>
            <ul style="margin:0;padding-left:20px;">
                {insights_html}
            </ul>
        </td>
    </tr>

    <!-- Action Items -->
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 12px 0;font-size:16px;color:#1565C0;font-weight:600;">
                ✅ Recommended Actions
            </h2>
            <ol style="margin:0;padding-left:20px;">
                {actions_html}
            </ol>
        </td>
    </tr>

    <!-- Risks -->
    {risks_html}

    <!-- View Full Report Button -->
    {report_button}

    <!-- Footer -->
    <tr>
        <td style="padding:16px 24px;background-color:#FAFAFA;border-radius:0 0 8px 8px;
                   border-top:1px solid #EEEEEE;">
            <p style="margin:0;font-size:11px;color:#999999;text-align:center;line-height:1.5;">
                This summary was auto-generated from the {report_name} by the 
                {company_name} AI Briefing System.<br>
                Data reflects the most recent report received on {today}.
            </p>
        </td>
    </tr>

</table>
<!-- End Main Container -->

        </td>
    </tr>
</table>
<!-- End Wrapper -->

</body>
</html>
"""
    return html


def _build_metrics_table(metrics: list[dict]) -> str:
    """Build an HTML table of key metrics with status indicators."""
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
            <td style="padding:10px 12px;font-size:13px;color:#333333;border-bottom:1px solid #EEEEEE;">
                {style['dot']} {metric.get('name', '')}
            </td>
            <td style="padding:10px 12px;font-size:13px;color:#333333;font-weight:600;
                       border-bottom:1px solid #EEEEEE;text-align:right;">
                {metric.get('value', '')}
            </td>
            <td style="padding:10px 12px;font-size:13px;color:{style['text']};font-weight:600;
                       border-bottom:1px solid #EEEEEE;text-align:right;">
                {metric.get('change', '')}{note_html}
            </td>
        </tr>
        """

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
           style="border:1px solid #E0E0E0;border-radius:6px;border-collapse:separate;
                  overflow:hidden;">
        <tr style="background-color:#1565C0;">
            <th style="padding:10px 12px;font-size:12px;color:#FFFFFF;text-align:left;
                       font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">
                Metric
            </th>
            <th style="padding:10px 12px;font-size:12px;color:#FFFFFF;text-align:right;
                       font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">
                Value
            </th>
            <th style="padding:10px 12px;font-size:12px;color:#FFFFFF;text-align:right;
                       font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">
                Change
            </th>
        </tr>
        {rows}
    </table>
    """


def build_email_subject(report_name: str, overall_status: str) -> str:
    """Build the email subject line with status indicator."""
    style = STATUS_COLORS.get(overall_status, STATUS_COLORS["yellow"])
    today = datetime.now().strftime("%m/%d/%Y")
    return f"{style['dot']} {report_name} Summary — {today}"
