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

The report contains FOUR sections:
1. "Sales Yesterday" — single day performance
2. "Sales Month-to-Date" — cumulative current month
3. "Sales Last Month" — prior full month (use for trend comparison)
4. "Rolling 7-Day Average" — smoothed 7-day rolling average of all metrics (use for trend validation)

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

  ⚠️ CRITICAL INTERPRETATION: Low DPSF is an OPERATIONAL/STAFFING/EFFICIENCY issue, 
  NOT a donor outreach or community engagement problem. When DPSF is below goal, it means:
    • The store may be understaffed on the donation dock (not enough team members to process donors)
    • Operational workflows may be creating bottlenecks that slow donor processing
    • Store productivity and efficiency are not where they need to be
    • The store is not maximizing its capacity to convert available donations into processed inventory
  
  DO NOT frame low DPSF as "need more community outreach" or "need to attract more donors."
  Instead, frame it as "need to improve store operations, staffing levels, or processing efficiency."
  
  High DPSF = operations are running smoothly, donations are being processed efficiently, 
  staff levels are adequate to handle donor volume.

- ★ DONOR VALUE goal is $43 company-wide. Use the "Donor Value" column (NOT Average Ticket).
  Stores below $43 are underperforming on monetization — they're not extracting enough 
  retail value from each donation they receive.
- ★ eCOMMERCE % goal is 10%. Use the "eCom %" column from the MTD section.
  Stores below 10% are leaving money on the table.
- Compare yesterday's numbers to MTD to spot trends. A bad day + bad MTD = pattern.
  A bad day + good MTD = probably just a bad day.
- Compare MTD to Last Month to see if performance is improving or deteriorating.

═══════════════════════════════════════════════════════════════
ROLLING 7-DAY AVERAGE — TREND VALIDATION
═══════════════════════════════════════════════════════════════

The Rolling 7-Day Average page smooths out day-to-day noise and reveals TRUE trends.
Use it to:
1. VALIDATE whether yesterday's performance is a genuine trend or a one-off anomaly.
   - If yesterday was bad BUT the 7-day average is healthy → likely just a bad day.
   - If yesterday was bad AND the 7-day average is also below goal → confirmed trend, needs action.
2. IDENTIFY stores where the 7-day average is diverging from goals even if MTD still looks OK 
   (early warning signal — the trend is turning before it shows up in the cumulative MTD).
3. COMPARE the 7-day rolling DPSF, Donor Value, and Budget % to their respective goals 
   to determine operational momentum.
4. SPOT stores where the rolling average is IMPROVING (even if still below goal) — 
   these stores may be responding to interventions already in place.

When the rolling 7-day average tells a different story than yesterday alone, TRUST THE 
7-DAY AVERAGE for trend assessment. Yesterday is a single data point; the rolling average 
represents sustained performance.

═══════════════════════════════════════════════════════════════
ANALYSIS FRAMEWORK
═══════════════════════════════════════════════════════════════

1. Combine yesterday + MTD + last month + rolling 7-day average to classify each store:
   - THRIVING: Above goals, positive trends, rolling 7-day confirms strong momentum
   - MAINTAINING: Mixed signals — monitor. Rolling 7-day may show early directional shift
   - DECLINING: Below goal with worsening MTD trend AND rolling 7-day confirms downward trajectory — needs intervention
   - CRITICAL: Significantly below on multiple KPIs with rolling 7-day average confirming sustained underperformance — immediate action required

2. Compound problems are the priority: A store with low DPSF AND low donor value AND 
   low eCommerce is in serious trouble across multiple dimensions. Low DPSF specifically 
   points to OPERATIONAL issues (staffing, efficiency, processing capacity).

3. Prioritize by IMPACT: A large store underperforming has more budget impact than 
   a small store underperforming. Use the Budget column to gauge store size.

4. Use the rolling 7-day average to distinguish between:
   - Stores having a temporary bad day (yesterday bad, 7-day OK) → monitor, don't panic
   - Stores in genuine decline (yesterday bad, 7-day trending down) → intervene now
   - Stores recovering (yesterday may still look rough, but 7-day is improving) → recognize progress
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

REMINDER — DPSF INTERPRETATION:
- Low DPSF = OPERATIONAL problem (staffing, efficiency, processing bottlenecks). 
  Do NOT describe it as a donor outreach or community engagement issue.
- Recommendations for low DPSF should focus on: staffing adjustments, operational efficiency 
  improvements, dock workflow optimization, processing capacity, or productivity coaching.

REMINDER — ROLLING 7-DAY AVERAGE USAGE:
- Use the "Rolling 7-Day Average" section to validate trends and distinguish anomalies from patterns.
- If a store had a bad yesterday but healthy 7-day averages, note it's likely a one-off.
- If a store's 7-day average is below goal, that's a confirmed operational trend requiring action.
- Look for stores where 7-day averages are improving (positive momentum) or deteriorating (early warning).

Respond in the following JSON format (and ONLY valid JSON, no markdown):
{{
    "overall_status": "green" | "yellow" | "red",
    "overall_status_reason": "One sentence on overall organization health with key numbers",
    "executive_summary": "2-3 sentences: How did we do yesterday vs budget? How are we trending MTD vs budget? What's the biggest concern? Reference rolling 7-day trends where relevant.",
    "critical_alerts": [
        {{
            "store": "Store Name",
            "severity": "critical" | "warning",
            "issue": "Clear description of the compound problem. For DPSF issues, frame as operational/staffing/efficiency problems.",
            "metrics": "DPSF: [Donors per Square] vs [DPSF Goal] goal | Donor Value: $[Donor Value column] vs $43 goal | eCom: [eCom %]% vs 10% goal",
            "trend": "Compare MTD to Last Month AND note what the rolling 7-day average shows — improving or deteriorating?",
            "recommendation": "Specific action to take. For low DPSF: focus on staffing, operational efficiency, dock workflow, processing capacity. NOT community outreach."
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
            "primary_concern": "Main issue or empty string if performing well. For DPSF issues, cite operational/staffing/efficiency concerns."
        }}
    ],
    "key_metrics_company_wide": [
        {{
            "name": "Metric Name",
            "yesterday": "Yesterday's total row value",
            "mtd": "MTD total row value",
            "goal": "Goal/target",
            "status": "green" | "yellow" | "red",
            "note": "Brief context — reference 7-day trend if helpful"
        }}
    ],
    "rolling_7day_insights": [
        {{
            "store": "Store Name",
            "metric": "Which metric this insight is about (e.g., DPSF, Donor Value, Budget %)",
            "rolling_avg": "The 7-day rolling average value for this metric",
            "vs_goal": "How the rolling average compares to the goal (e.g., '4.13 vs 5.05 goal')",
            "direction": "improving" | "stable" | "declining",
            "interpretation": "What this means operationally — is the store recovering, stagnating, or deteriorating? Distinguish from single-day noise."
        }}
    ],
    "bright_spots": [
        "Store/win that should be recognized or replicated — mention if rolling 7-day confirms sustained strong performance"
    ],
    "watch_list": [
        {{
            "store": "Store Name",
            "reason": "Why this store needs monitoring in the next 48-72 hours. Reference 7-day rolling trend if relevant.",
            "trigger": "What would escalate this to critical"
        }}
    ]
}}

RULES:
- Use the CORRECT columns: "Donor Value" for donor value, "Donors per Square" for actual DPSF, "DPSF Goal" for target.
- NEVER report "Average Ticket" as "Donor Value" — these are completely different metrics.
- ALWAYS call out stores where Donor Value < $43, eCom % < 10%, or DPSF Variance is negative.
- For low DPSF, ALWAYS frame the issue as operational/staffing/efficiency — NEVER as donor outreach or community engagement.
- Prioritize compound problems (multiple KPIs failing) over single-metric misses.
- Compare yesterday to MTD AND to last month AND to rolling 7-day averages to identify TRENDS.
- Use the rolling 7-day average to validate whether issues are one-off anomalies or confirmed trends.
- Be specific with numbers. Always state the actual value AND the goal/target.
- Limit critical_alerts to stores needing IMMEDIATE action (max 5).
- Include ALL active stores in store_health_summary (skip inactive/NaN stores).
- For store_health_summary: use the MTD "Donors per Square" as dpsf_actual, and "DPSF Goal" as dpsf_goal.
  Set dpsf_ok=true only if actual >= goal. Set dv_ok=true only if Donor Value >= $43. Set ecom_ok=true only if eCom% >= 10.
  For budget fields, include the % sign (e.g., "+4.2%" or "-15.9%").
- For outlet stores that lack DPSF/donor columns, use "—" for dpsf_actual, dpsf_goal, donor_value_mtd and set their _ok fields to true.
- For DPSF in critical_alerts, always show: actual "Donors per Square" vs "DPSF Goal" (e.g., "3.79 vs 5.05 goal").
- Include 3-7 entries in rolling_7day_insights, focusing on stores where the 7-day trend tells a meaningful story 
  (either confirming a problem, revealing an early warning, or showing recovery).
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
        max_tokens=14000,
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
            "rolling_7day_insights": [],
        }

    # Validate expected keys exist
    expected_keys = [
        "overall_status", "executive_summary", "key_metrics_company_wide",
        "critical_alerts", "store_health_summary",
        "bright_spots", "watch_list", "rolling_7day_insights",
    ]
    for key in expected_keys:
        if key not in summary:
            summary[key] = [] if key not in ("overall_status", "executive_summary", "overall_status_reason") else ""

    logger.info(
        f"Summary generated: {len(summary.get('store_health_summary', []))} stores, "
        f"{len(summary.get('critical_alerts', []))} critical alerts, "
        f"{len(summary.get('rolling_7day_insights', []))} rolling 7-day insights, "
        f"overall status: {summary.get('overall_status', 'unknown')}"
    )
    return summary
