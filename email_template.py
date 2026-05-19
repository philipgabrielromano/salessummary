"""
HTML email template for retail executive summary emails.
Designed for Goodwill retail leadership — focused on store health,
early warning signals, and at-a-glance readability.
Renders well in Outlook, Gmail, and mobile clients. All CSS is inline.
"""

from datetime import datetime


STATUS_COLORS = {
    "green": {"bg": "#E8F5E9", "text": "#2E7D32", "dot": "🟢", "label": "On Track"},
    "yellow": {"bg": "#FFF8E1", "text": "#F57F17", "dot": "🟡", "label": "Needs Attention"},
    "red": {"bg": "#FFEBEE", "text": "#C62828", "dot": "🔴", "label": "Critical"},
}

HEALTH_STYLES = {
    "thriving": {"bg": "#E8F5E9", "text": "#2E7D32", "dot": "🟢"},
    "maintaining": {"bg": "#E3F2FD", "text": "#1565C0", "dot": "🔵"},
    "declining": {"bg": "#FFF8E1", "text": "#F57F17", "dot": "🟡"},
    "critical": {"bg": "#FFEBEE", "text": "#C62828", "dot": "🔴"},
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
    bright_spots_html = _build_list_section(summary.get("bright_spots", []))
    watch_list_html = _build_watch_list(summary.get("watch_list", []))
    rolling_7day_html = _build_rolling_7day_insights(summary.get("rolling_7day_insights", []))

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

<table role="presentation" width="720" cellspacing="0" cellpadding="0" border="0"
       style="background-color:#FFFFFF;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.08);
              max-width:720px;width:100%;">

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

    <!-- Rolling 7-Day Trend Insights -->
    {rolling_7day_html}

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
            <h2 style="margin:0 0 4px 0;font-size:16px;color:#1565C0;font-weight:600;">
                🏪 Store Health Overview
            </h2>
            <p style="margin:0 0 8px 0;font-size:11px;color:#999;">
                Sorted by status (critical first). Flags: ⬇ below goal &nbsp; ✓ at/above goal
            </p>
            <p style="margin:0 0 12px 0;font-size:11px;color:#666;">
                <span style="color:#C62828;">🔴 Critical</span> &nbsp;&nbsp;
                <span style="color:#F57F17;">🟡 Declining</span> &nbsp;&nbsp;
                <span style="color:#1565C0;">🔵 Maintaining</span> &nbsp;&nbsp;
                <span style="color:#2E7D32;">🟢 Thriving</span>
            </p>
            {store_health_html}
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
    """Build the critical alerts section with visual KPI chips per store."""
    if not alerts:
        return ""

    def _kpi_chip(label, value, timeframe, is_ok):
        """Render a single KPI as a color-coded chip."""
        if not value or value == "—":
            return ""
        if is_ok:
            bg = "#E8F5E9"
            color = "#2E7D32"
            icon = "✓"
        else:
            bg = "#FFEBEE"
            color = "#C62828"
            icon = "✗"
        return (
            f'<span style="display:inline-block;padding:3px 8px;margin:2px 4px 2px 0;'
            f'border-radius:4px;background-color:{bg};font-size:11px;'
            f'color:{color};font-weight:600;white-space:nowrap;">'
            f'{icon} {label}: {value}'
            f'<span style="font-weight:400;color:#888;font-size:9px;"> ({timeframe})</span>'
            f'</span>'
        )

    cards = ""
    for alert in alerts:
        severity = alert.get("severity", "warning")
        if severity == "critical":
            icon = "🚨"
            border_color = "#C62828"
            bg_color = "#FFF5F5"
        else:
            icon = "⚠️"
            border_color = "#F57F17"
            bg_color = "#FFFDF5"

        store = alert.get("store", "")
        issue = alert.get("issue", "")
        trend = alert.get("trend", "")

        # Build KPI chips
        chips = ""
        chips += _kpi_chip("DPSF", alert.get("dpsf", ""), alert.get("dpsf_timeframe", ""), alert.get("dpsf_ok", True))
        chips += _kpi_chip("DV", alert.get("donor_value", ""), alert.get("dv_timeframe", ""), alert.get("dv_ok", True))
        chips += _kpi_chip("Budget", alert.get("budget_pct", ""), alert.get("budget_timeframe", ""), alert.get("budget_ok", True))

        cards += f"""
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
               style="margin-bottom:8px;border-radius:6px;border-left:5px solid {border_color};
                      background-color:{bg_color};">
            <tr>
                <td style="padding:12px 14px;">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                        <tr>
                            <td style="vertical-align:top;">
                                <strong style="font-size:14px;color:{border_color};">
                                    {icon} {store}
                                </strong>
                                <span style="font-size:12px;color:#555;margin-left:8px;">{issue}</span>
                            </td>
                            <td style="vertical-align:top;text-align:right;white-space:nowrap;">
                                <span style="font-size:11px;color:#888;font-style:italic;">{trend}</span>
                            </td>
                        </tr>
                        <tr>
                            <td colspan="2" style="padding-top:6px;">
                                {chips}
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        """

    return f"""
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 12px 0;font-size:16px;color:#C62828;font-weight:600;">
                🚨 Action Required
            </h2>
            {cards}
        </td>
    </tr>
    """


def _format_kpi_cell(value: str, is_good: bool) -> str:
    """Format a KPI cell with color and arrow indicator."""
    if is_good:
        return f'<span style="color:#2E7D32;font-weight:600;">✓ {value}</span>'
    else:
        return f'<span style="color:#C62828;font-weight:600;">⬇ {value}</span>'


def _build_store_health_table(stores: list[dict]) -> str:
    """Build a clean, scannable store health table with dedicated columns."""
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

        # Get individual KPI values
        budget_yesterday = store.get("budget_yesterday", "—")
        budget_mtd = store.get("budget_mtd", "—")
        dpsf_actual = store.get("dpsf_actual", "—")
        dpsf_goal = store.get("dpsf_goal", "—")
        dpsf_ok = store.get("dpsf_ok", True)
        donor_value = store.get("donor_value_mtd", "—")
        dv_ok = store.get("dv_ok", True)
        ecom = store.get("ecom_pct", "—")
        ecom_ok = store.get("ecom_ok", True)
        concern = store.get("primary_concern", "")

        # Color the budget cells
        def _budget_cell(val):
            if val == "—":
                return '<span style="color:#999;">—</span>'
            # Try to detect negative
            clean = str(val).replace("%", "").replace("+", "").strip()
            try:
                num = float(clean)
                if num >= 0:
                    return f'<span style="color:#2E7D32;font-weight:600;">{val}</span>'
                else:
                    return f'<span style="color:#C62828;font-weight:600;">{val}</span>'
            except ValueError:
                return val

        # DPSF cell: show actual vs goal with color
        if dpsf_actual != "—" and dpsf_goal != "—":
            dpsf_display = f"{dpsf_actual}"
            if dpsf_ok:
                dpsf_html = f'<span style="color:#2E7D32;font-weight:600;">✓ {dpsf_display}</span>'
            else:
                dpsf_html = f'<span style="color:#C62828;font-weight:600;">⬇ {dpsf_display}</span>'
            dpsf_html += f'<br><span style="font-size:10px;color:#999;">goal: {dpsf_goal}</span>'
        else:
            dpsf_html = '<span style="color:#999;">—</span>'

        # Donor Value cell
        if donor_value != "—":
            if dv_ok:
                dv_html = f'<span style="color:#2E7D32;font-weight:600;">✓ {donor_value}</span>'
            else:
                dv_html = f'<span style="color:#C62828;font-weight:600;">⬇ {donor_value}</span>'
        else:
            dv_html = '<span style="color:#999;">—</span>'

        # eCom cell
        if ecom != "—":
            if ecom_ok:
                ecom_html = f'<span style="color:#2E7D32;font-weight:600;">✓ {ecom}</span>'
            else:
                ecom_html = f'<span style="color:#C62828;font-weight:600;">⬇ {ecom}</span>'
        else:
            ecom_html = '<span style="color:#999;">—</span>'

        # Status badge
        badge_html = (
            f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
            f'font-size:10px;font-weight:600;color:{style["text"]};'
            f'background-color:{style["bg"]};">{style["dot"]}</span>'
        )

        rows += f"""
        <tr style="background-color:{bg};">
            <td style="padding:7px 8px;font-size:12px;color:#333;border-bottom:1px solid #EEE;
                       white-space:nowrap;vertical-align:top;">
                <strong>{store.get('store', '')}</strong><br>
                {badge_html}
            </td>
            <td style="padding:7px 6px;font-size:12px;border-bottom:1px solid #EEE;
                       text-align:center;vertical-align:top;">
                {_budget_cell(budget_yesterday)}
            </td>
            <td style="padding:7px 6px;font-size:12px;border-bottom:1px solid #EEE;
                       text-align:center;vertical-align:top;">
                {_budget_cell(budget_mtd)}
            </td>
            <td style="padding:7px 6px;font-size:12px;border-bottom:1px solid #EEE;
                       text-align:center;vertical-align:top;">
                {dpsf_html}
            </td>
            <td style="padding:7px 6px;font-size:12px;border-bottom:1px solid #EEE;
                       text-align:center;vertical-align:top;">
                {dv_html}
            </td>
            <td style="padding:7px 6px;font-size:12px;border-bottom:1px solid #EEE;
                       text-align:center;vertical-align:top;">
                {ecom_html}
            </td>
        </tr>
        """

    return f"""
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
           style="border:1px solid #E0E0E0;border-radius:6px;border-collapse:separate;overflow:hidden;">
        <tr style="background-color:#1565C0;">
            <th style="padding:8px;font-size:11px;color:#FFF;text-align:left;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.3px;min-width:100px;">Store</th>
            <th style="padding:8px 6px;font-size:11px;color:#FFF;text-align:center;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.3px;">Budget<br>
                <span style="font-size:9px;font-weight:400;opacity:0.8;">Yesterday</span></th>
            <th style="padding:8px 6px;font-size:11px;color:#FFF;text-align:center;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.3px;">Budget<br>
                <span style="font-size:9px;font-weight:400;opacity:0.8;">MTD</span></th>
            <th style="padding:8px 6px;font-size:11px;color:#FFF;text-align:center;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.3px;">DPSF<br>
                <span style="font-size:9px;font-weight:400;opacity:0.8;">MTD vs Goal</span></th>
            <th style="padding:8px 6px;font-size:11px;color:#FFF;text-align:center;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.3px;">Donor Val<br>
                <span style="font-size:9px;font-weight:400;opacity:0.8;">MTD (≥$43)</span></th>
            <th style="padding:8px 6px;font-size:11px;color:#FFF;text-align:center;font-weight:600;
                       text-transform:uppercase;letter-spacing:0.3px;">eCom %<br>
                <span style="font-size:9px;font-weight:400;opacity:0.8;">MTD (≥10%)</span></th>
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


DIRECTION_STYLES = {
    "improving": {"icon": "📈", "color": "#2E7D32", "label": "Improving"},
    "stable": {"icon": "➡️", "color": "#1565C0", "label": "Stable"},
    "declining": {"icon": "📉", "color": "#C62828", "label": "Declining"},
}


def _build_rolling_7day_insights(insights: list[dict]) -> str:
    """Build the rolling 7-day trend insights section."""
    if not insights:
        return ""

    rows = ""
    for i, insight in enumerate(insights):
        direction = insight.get("direction", "stable")
        style = DIRECTION_STYLES.get(direction, DIRECTION_STYLES["stable"])
        bg = "#FFFFFF" if i % 2 == 0 else "#FAFAFA"

        store = insight.get("store", "")
        metric = insight.get("metric", "")
        rolling_avg = insight.get("rolling_avg", "—")
        vs_goal = insight.get("vs_goal", "")
        interpretation = insight.get("interpretation", "")

        direction_badge = (
            f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
            f'font-size:10px;font-weight:600;color:{style["color"]};'
            f'background-color:{style["color"]}15;">{style["icon"]} {style["label"]}</span>'
        )

        rows += f"""
        <tr style="background-color:{bg};">
            <td style="padding:8px 10px;font-size:12px;color:#333;border-bottom:1px solid #EEE;
                       vertical-align:top;">
                <strong>{store}</strong>
            </td>
            <td style="padding:8px 8px;font-size:12px;color:#333;border-bottom:1px solid #EEE;
                       text-align:center;vertical-align:top;">
                {metric}
            </td>
            <td style="padding:8px 8px;font-size:12px;color:#333;border-bottom:1px solid #EEE;
                       text-align:center;vertical-align:top;font-weight:600;">
                {rolling_avg}
                {"<br><span style='font-size:10px;color:#999;font-weight:400;'>" + vs_goal + "</span>" if vs_goal else ""}
            </td>
            <td style="padding:8px 8px;font-size:12px;border-bottom:1px solid #EEE;
                       text-align:center;vertical-align:top;">
                {direction_badge}
            </td>
            <td style="padding:8px 10px;font-size:11px;color:#555;border-bottom:1px solid #EEE;
                       vertical-align:top;line-height:1.4;">
                {interpretation}
            </td>
        </tr>
        """

    return f"""
    <tr>
        <td style="padding:0 24px 20px 24px;">
            <h2 style="margin:0 0 4px 0;font-size:16px;color:#1565C0;font-weight:600;">
                📉 Rolling 7-Day Trend Insights
            </h2>
            <p style="margin:0 0 12px 0;font-size:11px;color:#999;">
                Smoothed 7-day averages to separate real trends from daily noise
            </p>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"
                   style="border:1px solid #E0E0E0;border-radius:6px;border-collapse:separate;overflow:hidden;">
                <tr style="background-color:#1565C0;">
                    <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:left;font-weight:600;
                               text-transform:uppercase;letter-spacing:0.3px;">Store</th>
                    <th style="padding:8px 8px;font-size:11px;color:#FFF;text-align:center;font-weight:600;
                               text-transform:uppercase;letter-spacing:0.3px;">Metric</th>
                    <th style="padding:8px 8px;font-size:11px;color:#FFF;text-align:center;font-weight:600;
                               text-transform:uppercase;letter-spacing:0.3px;">7-Day Avg</th>
                    <th style="padding:8px 8px;font-size:11px;color:#FFF;text-align:center;font-weight:600;
                               text-transform:uppercase;letter-spacing:0.3px;">Trend</th>
                    <th style="padding:8px 10px;font-size:11px;color:#FFF;text-align:left;font-weight:600;
                               text-transform:uppercase;letter-spacing:0.3px;">Insight</th>
                </tr>
                {rows}
            </table>
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
