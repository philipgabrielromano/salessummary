"""
OpenAI-powered summarization engine for Power BI report data.
Generates structured executive summaries with KPI status indicators.
"""

import json
import logging

from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an executive briefing analyst. Your job is to analyze raw data 
extracted from a Power BI report and produce a concise, actionable executive summary.

Your audience is C-level executives and senior leadership who need to understand 
performance at a glance — they have 60 seconds to read this.

RULES:
- Be concise and direct. No filler language.
- Focus on what changed, what matters, and what needs attention.
- Always quantify: use specific numbers, percentages, and comparisons.
- Highlight anomalies, risks, and opportunities.
- Use business language, not technical jargon.
"""

USER_PROMPT_TEMPLATE = """Analyze the following data extracted from today's {report_name} 
and produce a structured executive summary.

REPORT DATA:
---
{report_content}
---

Respond in the following JSON format (and ONLY valid JSON, no markdown):
{{
    "overall_status": "green" | "yellow" | "red",
    "overall_status_reason": "One sentence explaining the overall status",
    "executive_summary": "2-3 sentence high-level overview of performance",
    "key_metrics": [
        {{
            "name": "Metric Name",
            "value": "Current value with units",
            "change": "Change vs prior period (e.g., +5.2% WoW)",
            "status": "green" | "yellow" | "red",
            "note": "Brief context if notable (otherwise empty string)"
        }}
    ],
    "trends_and_insights": [
        "Insight 1: specific observation with data",
        "Insight 2: specific observation with data",
        "Insight 3: specific observation with data"
    ],
    "action_items": [
        "Action 1: specific recommendation",
        "Action 2: specific recommendation"
    ],
    "risks": [
        "Risk 1: what to watch out for"
    ]
}}

GUIDELINES FOR STATUS COLORS:
- 🟢 GREEN: Meeting or exceeding targets, positive trends
- 🟡 YELLOW: Slightly below target, flat/declining trend, needs monitoring
- 🔴 RED: Significantly below target, alarming trend, requires immediate action

Extract 5-10 key metrics. Identify 3-5 trends/insights. Provide 2-4 action items.
If you cannot determine status for a metric, default to "yellow".
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
