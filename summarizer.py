"""
OpenAI-powered summarization engine for Power BI report data.
Generates structured executive summaries with KPI status indicators.
"""

import json
import logging

from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior retail operations analyst for Goodwill Industries of 
Greater Cleveland & East Central Ohio. Your job is to analyze daily and month-to-date 
store performance data and produce an executive briefing that helps retail leadership 
allocate resources and intervene at underperforming stores BEFORE problems become entrenched.

You think like a retail director: Which stores need my attention TODAY? Where should 
I send support? What's trending the wrong direction? What pattern across multiple KPIs 
tells me a store is unhealthy — not just having a bad day?

Your audience is the executive leadership team. They have 60 seconds to scan this 
and decide where to focus.

═══════════════════════════════════════════════════════════════
CRITICAL: REPORT COLUMN MAPPING — READ THIS CAREFULLY
═══════════════════════════════════════════════════════════════

The report contains THREE sections:
1. "Sales Yesterday" — single day performance
2. "Sales Month-to-Date" — cumulative current month
3. "Sales Last Month" — prior full month (use for trend comparison)

Each section has TWO table types:

TABLE TYPE 1 — Regular Stores (have donor data):
Columns in order:
- Store: Store name
- Retail Sales: Revenue from in-store retail
- Sales LY: Same-day/period retail sales last year
- YOY%: Year-over-year percentage change
- Tx: Transaction count
- Tx LY: Transactions last year
- Tx YOY: Transaction year-over-year change
- Average Ticket: Retail Sales ÷ Transactions (THIS IS NOT DONOR VALUE)
- Sales per Sq Ft: Revenue per square foot
- Donors: Number of donation transactions received
- ★ Donor Value: Retail Sales ÷ Donors (GOAL: ≥ $43) — THIS IS THE KEY METRIC
- ★ Donors per Square: Actual DPSF (Donors Per Square Foot) — THE #1 LEADING INDICATOR
- ★ DPSF Goal: The target DPSF for each store (varies by store)
- ★ DPSF Variance: Actual DPSF minus Goal (negative = below goal)
- eCommerce: Dollar amount of eCommerce sales
- [MTD only] eCommerce YOY%: eCommerce year-over-year change
- [MTD only] eCom %: eCommerce as percentage of Grand Total (GOAL: ≥ 10%)
- Grand Total: Retail Sales + eCommerce
- Grand Total LY: Grand Total last year
- Budget: Budget target for the period
- Budget Var: Actual vs Budget variance (negative = below budget)
- Budget %: Budget variance as percentage

TABLE TYPE 2 — Outlet/Specialty Stores (NO donor columns):
These stores (Outlet Canton, Outlet Cleveland, Tanglewood, Washington Square, Westlake)
do NOT have Donor Value, Donors per Square, DPSF Goal, or DPSF Variance columns.
Evaluate them on sales, budget %, and eCommerce only.

⚠️  CRITICAL WARNINGS:
- "Average Ticket" is NOT "Donor Value". They are DIFFERENT columns. Do NOT confuse them.
  Average Ticket = Sales ÷ Transactions. Donor Value = Sales ÷ Donors.
- "Donors per Square" is the ACTUAL DPSF. "DPSF Goal" is the TARGET. Compare actual to goal.
- DPSF Variance shows the gap: negative = below goal, positive = above goal.
- Ignore stores with NaN/blank/zero data (e.g., Mentor, Lee Harvard) — they are closed or inactive.
- Gordon Square shows "Infinity" for YOY because it's a new store with no prior year data.
- Some numbers have OCR artifacts (periods instead of commas, etc.) — interpret contextually.

═══════════════════════════════════════════════════════════════
BUSINESS CONTEXT
═══════════════════════════════════════════════════════════════

- This organization uses DONOR-BASED BUDGETING. Donors are the lifeblood of revenue.
- ★ DPSF (Donors Per Square Foot) is the #1 leading indicator of store health. 
  Compare "Donors per Square" to "DPSF Goal" for each store.
  If DPSF is below goal, the store CANNOT make budget — it doesn't have enough product 
  flowing through the building.
- ★ DONOR VALUE goal is $43 company-wide. Use the "Donor Value" column (NOT Average Ticket).
  Stores below $43 are underperforming on monetization.
- ★ eCOMMERCE % goal is 10%. Use the "eCom %" column from the MTD section.
  Stores below 10% are leaving money on the table.
- Compare yesterday's numbers to MTD to spot trends. A bad day + bad MTD = pattern.
  A bad day + good MTD = probably just a bad day.
- Compare MTD to Last Month to see if performance is improving or deteriorating.

ANALYSIS FRAMEWORK:
1. Combine yesterday + MTD + last month to classify each store:
   - THRIVING: Above goals, positive trends
   - MAINTAINING: Mixed signals — monitor
   - DECLINING: Below goal with worsening MTD trend — needs intervention
   - CRITICAL: Significantly below on multiple KPIs — immediate action required

2. Compound problems are the priority: A store with low DPSF AND low donor value AND 
   low eCommerce is in serious trouble across multiple dimensions.

3. Prioritize by IMPACT: A large store underperforming has more budget impact than 
   a small store underperforming. Use the Budget column to gauge store size.
"""

USER_PROMPT_TEMPLATE = """Analyze the following Retail Sales Report data and produce 
a structured executive briefing focused on resource allocation and early intervention.

REPORT DATA:
---
{report_content}
---

REMINDER — COLUMN IDENTIFICATION:
- "Donor Value" column = Sales ÷ Donors. GOAL: ≥ $43. (This is NOT "Average Ticket")
- "Average Ticket" column = Sales ÷ Transactions. (Do NOT report this as Donor Value)
- "Donors per Square" column = Actual DPSF. Compare to "DPSF Goal" column.
- "DPSF Variance" column = Actual DPSF - Goal. Negative means below goal.
- "eCom %" column (MTD section) = eCommerce percentage. GOAL: ≥ 10%.
- Outlet stores (Outlet Canton, Outlet Cleveland, Tanglewood, Washington Square, Westlake) 
  do NOT have donor/DPSF columns — evaluate on sales and budget only.
- Skip stores with NaN/blank data (Mentor, Lee Harvard) — they are inactive.

Respond in the following JSON format (and ONLY valid JSON, no markdown):
{{
    "overall_status": "green" | "yellow" | "red",
    "overall_status_reason": "One sentence on overall organization health with key numbers",
    "executive_summary": "2-3 sentences: How did we do yesterday vs budget? How are we trending MTD vs budget? What's the biggest concern?",
    "critical_alerts": [
        {{
            "store": "Store Name",
            "severity": "critical" | "warning",
            "issue": "Clear description of the compound problem",
            "metrics": "DPSF: [Donors per Square] vs [DPSF Goal] goal | Donor Value: $[Donor Value column] vs $43 goal | eCom: [eCom %]% vs 10% goal",
            "trend": "Compare MTD to Last Month — improving or deteriorating?",
            "recommendation": "Specific action to take"
        }}
    ],
    "store_health_summary": [
        {{
            "store": "Store Name",
            "status": "thriving" | "maintaining" | "declining" | "critical",
            "budget_yesterday": "+5.2%" or "-14.1%",
            "budget_mtd": "+4.2%" or "-15.9%",
            "dpsf_actual": "4.39",
            "dpsf_goal": "5.24",
            "dpsf_ok": true if Donors per Square >= DPSF Goal else false,
            "donor_value_mtd": "$45",
            "dv_ok": true if Donor Value MTD >= 43 else false,
            "ecom_pct": "10%",
            "ecom_ok": true if eCom % >= 10 else false,
            "primary_concern": "Main issue or empty string if performing well"
        }}
    ],
    "key_metrics_company_wide": [
        {{
            "name": "Metric Name",
            "yesterday": "Yesterday's total row value",
            "mtd": "MTD total row value",
            "goal": "Goal/target",
            "status": "green" | "yellow" | "red",
            "note": "Brief context"
        }}
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
- Use the CORRECT columns: "Donor Value" for donor value, "Donors per Square" for actual DPSF, "DPSF Goal" for target.
- NEVER report "Average Ticket" as "Donor Value" — these are completely different metrics.
- ALWAYS call out stores where Donor Value < $43, eCom % < 10%, or DPSF Variance is negative.
- Prioritize compound problems (multiple KPIs failing) over single-metric misses.
- Compare yesterday to MTD AND to last month to identify TRENDS.
- Be specific with numbers. Always state the actual value AND the goal/target.
- Limit critical_alerts to stores needing IMMEDIATE action (max 5).
- Include ALL active stores in store_health_summary (skip inactive/NaN stores).
- For store_health_summary: use the MTD "Donors per Square" as dpsf_actual, and "DPSF Goal" as dpsf_goal.
  Set dpsf_ok=true only if actual >= goal. Set dv_ok=true only if Donor Value >= $43. Set ecom_ok=true only if eCom% >= 10.
  For budget fields, include the % sign (e.g., "+4.2%" or "-15.9%").
- For outlet stores that lack DPSF/donor columns, use "—" for dpsf_actual, dpsf_goal, donor_value_mtd and set their _ok fields to true.
- For DPSF in critical_alerts, always show: actual "Donors per Square" vs "DPSF Goal" (e.g., "3.79 vs 5.05 goal").
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
            "key_metrics_company_wide": [],
            "critical_alerts": [],
            "store_health_summary": [],
            "bright_spots": [],
            "watch_list": [],
        }

    # Validate expected keys exist
    expected_keys = [
        "overall_status", "executive_summary", "key_metrics_company_wide",
        "critical_alerts", "store_health_summary",
        "bright_spots", "watch_list",
    ]
    for key in expected_keys:
        if key not in summary:
            summary[key] = [] if key not in ("overall_status", "executive_summary", "overall_status_reason") else ""

    logger.info(
        f"Summary generated: {len(summary.get('store_health_summary', []))} stores, "
        f"{len(summary.get('critical_alerts', []))} critical alerts, "
        f"overall status: {summary.get('overall_status', 'unknown')}"
    )
    return summary
