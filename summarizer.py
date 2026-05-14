"""
OpenAI-powered summarization engine for Power BI report data.
Generates structured executive summaries with KPI status indicators.
"""

import json
import logging

from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior retail operations analyst for a Goodwill organization. 
Your job is to analyze daily and month-to-date store performance data and produce 
an executive briefing that helps retail leadership allocate resources and intervene 
at underperforming stores BEFORE problems become entrenched.

You think like a retail director: Which stores need my attention TODAY? Where should 
I send support? What's trending the wrong direction? What pattern across multiple KPIs 
tells me a store is unhealthy — not just having a bad day?

Your audience is the executive leadership team. They have 60 seconds to scan this 
and decide where to focus.

CRITICAL BUSINESS CONTEXT:
- This organization uses DONOR-BASED BUDGETING. Donors are the lifeblood of revenue.
- DPSF (Donors Per Square Foot) is the #1 leading indicator of store health. If DPSF 
  is below goal, the store CANNOT make budget — it simply doesn't have enough product 
  flowing through the building to generate the required revenue.
- Company-wide DONOR VALUE goal is $43. Stores below this are underperforming on 
  monetization — they have donors but aren't extracting enough value per donor.
- eCOMMERCE PERCENTAGE goal is above 10%. Stores below this are leaving money on 
  the table by not routing enough high-value product to online channels.
- A store can have ONE bad day. But if yesterday was bad AND the MTD trend is declining, 
  that's a pattern that requires intervention.

ANALYSIS FRAMEWORK:
1. Combine yesterday's results with MTD to classify each store:
   - THRIVING: Above goal yesterday AND above goal MTD
   - MAINTAINING: Mixed signals (one good, one below) — monitor
   - DECLINING: Below goal yesterday AND MTD trending down — needs intervention
   - CRITICAL: Significantly below on multiple KPIs — immediate action required

2. Look for compound problems: A store that's low on DPSF AND donor value AND 
   eCommerce is in serious trouble across multiple dimensions.

3. Prioritize by IMPACT: A large store underperforming has more budget impact than 
   a small store underperforming.
"""

USER_PROMPT_TEMPLATE = """Analyze the following Retail Sales Report data and produce 
a structured executive briefing focused on resource allocation and early intervention.

REPORT DATA:
---
{report_content}
---

Respond in the following JSON format (and ONLY valid JSON, no markdown):
{{
    "overall_status": "green" | "yellow" | "red",
    "overall_status_reason": "One sentence on overall organization health with key numbers",
    "executive_summary": "2-3 sentences: How did we do yesterday? How are we trending MTD? What's the biggest concern?",
    "critical_alerts": [
        {{
            "store": "Store Name",
            "severity": "critical" | "warning",
            "issue": "Clear description of the compound problem",
            "metrics": "DPSF: X vs Y goal | Donor Value: $X vs $43 goal | eCom: X% vs 10% goal",
            "trend": "Declining/Flat/etc — what MTD tells us",
            "recommendation": "Specific action to take"
        }}
    ],
    "store_health_summary": [
        {{
            "store": "Store Name",
            "status": "thriving" | "maintaining" | "declining" | "critical",
            "yesterday_vs_goal": "Brief comparison",
            "mtd_trend": "Above/Below/Declining — key numbers",
            "primary_concern": "Main issue or 'None — performing well'"
        }}
    ],
    "key_metrics_company_wide": [
        {{
            "name": "Metric Name (e.g., Total DPSF, Avg Donor Value, eCom %)",
            "yesterday": "Yesterday's value",
            "mtd": "Month-to-date value",
            "goal": "Goal/target",
            "status": "green" | "yellow" | "red",
            "note": "Brief context"
        }}
    ],
    "resource_allocation": [
        "Recommendation 1: Where to send support and why",
        "Recommendation 2: Which stores can be deprioritized (thriving)",
        "Recommendation 3: Any systemic issues across multiple stores"
    ],
    "bright_spots": [
        "Store/win that should be recognized or replicated"
    ],
    "watch_list": [
        {{
            "store": "Store Name",
            "reason": "Why this store needs monitoring in the next 48-72 hours",
            "trigger": "What would escalate this to critical"
        }}
    ]
}}

RULES:
- ALWAYS call out stores below $43 donor value, below 10% eCommerce, or below DPSF goal.
- Prioritize compound problems (multiple KPIs failing) over single-metric misses.
- Compare yesterday to MTD to identify TRENDS, not just point-in-time snapshots.
- Be specific with numbers. Never say "below goal" without stating the actual value and the goal.
- Limit critical_alerts to stores needing IMMEDIATE action (max 5).
- Include ALL stores in store_health_summary.
- resource_allocation should be actionable — tell leadership WHERE to focus this week.
"""


def generate_summary(report_content: str, config: Config) -> dict:
    """
    Send extracted report content to OpenAI and get a structured summary.

    Args:
        report_content: The extracted text/tables from the PDF.
        config: Application configuration.

    Returns:
        Parsed JSON dict with the structured summary.
    """
    client = OpenAI(api_key=config.openai_api_key)

    user_prompt = USER_PROMPT_TEMPLATE.format(
        report_name=config.report_name,
        report_content=report_content[:50000],  # Cap to avoid token limits
    )

    logger.info(f"Sending {len(report_content):,} chars to OpenAI ({config.openai_model})...")

    response = client.chat.completions.create(
        model=config.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,  # Low temp for consistent, factual output
        max_tokens=4000,
        response_format={"type": "json_object"},
    )

    raw_response = response.choices[0].message.content
    logger.info(
        f"OpenAI response received: {len(raw_response):,} chars, "
        f"tokens used: {response.usage.total_tokens:,}"
    )

    # Parse JSON response
    try:
        summary = json.loads(raw_response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        logger.error(f"Raw response: {raw_response[:500]}")
        # Return a fallback structure
        summary = {
            "overall_status": "yellow",
            "overall_status_reason": "Unable to fully parse report data",
            "executive_summary": raw_response[:500],
            "key_metrics": [],
            "trends_and_insights": ["Analysis could not be fully structured"],
            "action_items": ["Review the full report manually"],
            "risks": [],
        }

    # Validate expected keys exist
    expected_keys = [
        "overall_status", "executive_summary", "key_metrics",
        "trends_and_insights", "action_items",
    ]
    for key in expected_keys:
        if key not in summary:
            summary[key] = [] if key in ("key_metrics", "trends_and_insights", "action_items", "risks") else ""

    logger.info(
        f"Summary generated: {len(summary.get('key_metrics', []))} metrics, "
        f"overall status: {summary.get('overall_status', 'unknown')}"
    )
    return summary
