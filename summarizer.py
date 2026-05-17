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
BUSINESS CONTEXT — THIS IS A THRIFT STORE OPERATION
═══════════════════════════════════════════════════════════════

This is a THRIFT STORE retail operation. Community members donate goods at the store's 
donation door. Store team members receive, sort, price, and place items on the sales floor.

- This organization uses DONOR-BASED BUDGETING. Donors are the lifeblood of revenue.
- ★ DPSF (Donors Per Square Foot) is the #1 leading indicator of store health. 
  Compare "Donors per Square" to "DPSF Goal" for each store.
  If DPSF is below goal, the store CANNOT make budget — it doesn't have enough product 
  flowing through the building.

  ⚠️ CRITICAL INTERPRETATION OF LOW DPSF:
  Low DPSF is a STORE PRODUCTIVITY / STAFFING / EFFICIENCY problem.
  It is NOT a donor outreach, community engagement, or "donor volume" problem.
  
  When DPSF is below goal, it signals a store operations problem that needs investigation:
    • The store may not be running at the productivity level it needs to
    • Possible causes include scheduling, staffing, training, or workflow issues
    • The donation door may not have adequate coverage during peak hours
    • Sorting, pricing, and floor replenishment may be falling behind
  The AI should FLAG the DPSF gap but NOT assume a specific root cause.
  
  ⚠️ BANNED LANGUAGE — NEVER USE THESE PHRASES:
    ✗ "donor outreach"
    ✗ "community outreach" 
    ✗ "attract more donors"
    ✗ "donor recruitment"
    ✗ "donor intake"
    ✗ "donor volume" (as if it's an external supply problem)
    ✗ "not enough product flow" (too vague)
    ✗ "can't monetize donors"
    ✗ "address donor volume"
    ✗ "understaffed" (don't assume the root cause)
  
  ✓ CORRECT FRAMING FOR LOW DPSF — USE THESE INSTEAD:
    ✓ "Store productivity below target"
    ✓ "DPSF below goal — operations need review"
    ✓ "Not processing at required capacity"
    ✓ "Operational efficiency gap"
    ✓ "DPSF [actual] vs [goal] — needs attention"
  Do NOT diagnose the specific cause (don't say "understaffed" or "scheduling gap").
  Just flag the gap and let leadership investigate.
  
  High DPSF = the store team is efficiently receiving donations, sorting, pricing, 
  and getting product to the sales floor at the right pace.

- ★ DONOR VALUE goal is $43 company-wide. Use the "Donor Value" column (NOT Average Ticket).
  Low Donor Value means the store is not extracting enough retail revenue per donation.
  This is a PRICING and PRODUCT GRADING issue — the team needs to price better or 
  identify higher-value items more effectively.
  
  ✓ CORRECT FRAMING FOR LOW DONOR VALUE:
    ✓ "Review pricing and product grading"
    ✓ "Team underpricing goods — training needed"
    ✓ "Not capturing full value from donations — check pricing discipline"
    ✓ "Audit pricing practices"
  
  ✗ WRONG: "can't monetize donors" / "donor monetization issue"

- ★ eCOMMERCE % goal is 10%. Use the "eCom %" column from the MTD section.
  Stores below 10% are leaving money on the table — the eCommerce pull list 
  may not be getting worked effectively.
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
   points to STAFFING and PRODUCTIVITY issues. Low Donor Value points to PRICING issues.

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

⚠️ LANGUAGE RULES — READ CAREFULLY:
- Low DPSF = STAFFING / PRODUCTIVITY problem. Not a donor outreach issue.
- Low Donor Value = PRICING / PRODUCT GRADING problem. Not a "monetizing donors" issue.
- NEVER say: "donor outreach", "community outreach", "attract donors", "donor intake", 
  "donor volume", "monetize donors", "not enough product flow", "address donor volume",
  or "understaffed."

REMINDER — ROLLING 7-DAY AVERAGE USAGE:
- Use the "Rolling 7-Day Average" section to validate trends and distinguish anomalies from patterns.
- If a store had a bad yesterday but healthy 7-day averages, note it's likely a one-off.
- If a store's 7-day average is below goal, that's a confirmed operational trend requiring action.
- Look for stores where 7-day averages are improving (positive momentum) or deteriorating (early warning).

Respond in the following JSON format (and ONLY valid JSON, no markdown):
{{
    "overall_status": "green" | "yellow" | "red",
    "overall_status_reason": "One sentence on overall organization health with key numbers",
    "executive_summary": "2-3 sentences: How did we do yesterday vs budget? How are we trending MTD? What's the biggest concern? Reference rolling 7-day trends where relevant.",
    "critical_alerts": [
        {{
            "store": "Store Name",
            "severity": "critical" | "warning",
            "issue": "≤10 words. (e.g., 'DPSF + DV both below goal — productivity gap')",
            "metrics": "DPSF: 3.79 vs 5.05 | DV: $34 vs $43 | eCom: 8% vs 10%",
            "trend": "≤8 words. (e.g., '7-day confirms decline' or 'Worsening from last month')"
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
            "primary_concern": "Short phrase. For DPSF: flag the gap (e.g., 'DPSF below goal — needs review'). For DV: pricing issue. Or empty string."
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
            "metric": "DPSF | Donor Value | Budget %",
            "rolling_avg": "The 7-day rolling average value",
            "vs_goal": "4.13 vs 5.05 goal",
            "direction": "improving" | "stable" | "declining",
            "interpretation": "1 sentence. What this means for this store right now."
        }}
    ],
    "bright_spots": [
        "Store/win that should be recognized — mention if 7-day confirms sustained performance"
    ],
    "watch_list": [
        {{
            "store": "Store Name",
            "reason": "Why this store needs monitoring. Reference 7-day trend if relevant.",
            "trigger": "What would escalate this to critical"
        }}
    ]
}}

RULES:
- critical_alerts MUST be terse. "issue" ≤10 words. "trend" ≤8 words. No filler. These are dashboard alerts, not paragraphs.
- NEVER use banned language (see list above). Low DPSF = operational issue needing review. Low DV = pricing/grading issue. Do NOT diagnose specific root causes for DPSF — just flag the gap.
- Use the CORRECT columns: "Donor Value" for donor value, "Donors per Square" for actual DPSF, "DPSF Goal" for target.
- NEVER report "Average Ticket" as "Donor Value" — these are completely different metrics.
- ALWAYS call out stores where Donor Value < $43, eCom % < 10%, or DPSF Variance is negative.
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
