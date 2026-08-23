import pandas as pd
import json
from google.genai import types

from .metrics import (
    calculate_labor_expense_percentage,
    calculate_month_over_month_revenue,
    calculate_operating_margin,
    calculate_revenue_variance,
)
from .models import ValidationIssue, ReportSummary
from .model_client import create_gemini_client

GEMINI_MODEL = "gemini-3.5-flash-lite"


def generate_fallback_summary(df: pd.DataFrame) -> str:
    """Generate a deterministic summary from calculated KPI results."""

    revenue_variance = calculate_revenue_variance(df)
    operating_margin = calculate_operating_margin(df)
    labor_expense_percentage = calculate_labor_expense_percentage(df)
    monthly_revenue = calculate_month_over_month_revenue(df)

    variance_amount = revenue_variance["variance_amount"]
    variance_percent = revenue_variance["variance_percent"]

    if variance_percent is None:
        variance_description = "The result cannot be expressed as a percentage because the budget is zero."
    elif variance_amount > 0:
        variance_description = (
            f"The amount ${variance_amount:,.0f} "
            f"({variance_percent:.1f}%) is above budget."
        )
    elif variance_amount < 0:
        variance_description = (
            f"The amount ${abs(variance_amount):,.0f} "
            f"({abs(variance_percent):.1f}%) is below budget."
        )
    else:
        variance_description = "Exactly on budget."

    operating_margin_percent = operating_margin["operating_margin_percent"]
    labor_percent = labor_expense_percentage["labor_expense_percent"]

    if operating_margin_percent is None:
        operating_margin_description = (
            "Operating margin is not available because "
            "total revenue is zero."
        )
    else:
        operating_margin_description = (
            f"Operating margin was "
            f"{operating_margin_percent:.1f}%."
        )

    if labor_percent is None:
        labor_description = (
            "Labor expense percentage is not available because "
            "total revenue is zero."
        )
    else:
        labor_description = (
            f"Labor expense represented "
            f"{labor_percent:.1f}% of revenue."
        )

    if monthly_revenue.empty:
        monthly_change_description = (
            "Month-over-month revenue change is not available."
        )
    else:
        latest_change = monthly_revenue.iloc[-1]["change_percent"]

        if pd.isna(latest_change):
            monthly_change_description = (
                "Month-over-month revenue change is not available."
            )
        elif latest_change > 0:
            monthly_change_description = (
                f"Revenue increased {latest_change:.1f}% "
                "from the previous month."
            )
        elif latest_change < 0:
            monthly_change_description = (
                f"Revenue decreased {abs(latest_change):.1f}% "
                "from the previous month."
            )
        else:
            monthly_change_description = (
                "Revenue was unchanged from the previous month."
            )

    return (
        f"Total revenue was "
        f"${revenue_variance['actual_revenue']:,.0f}. "
        f"{variance_description} "
        f"{operating_margin_description} "
        f"{labor_description} "
        f"{monthly_change_description}"
    )

def prepare_summary_facts(
    calculated_metrics: dict[str, object],
    validation_issues: list[ValidationIssue],
) -> dict[str, object]:
    """Package calculated metrics and validation results for the LLM."""

    return {
        "calculated_metrics": calculated_metrics,
        "validation_issues": [issue.model_dump(mode="json") for issue in validation_issues],
    }

def build_summary_prompt(facts: dict[str, object]) -> str:
    """Create a grounded prompt from trusted report facts."""

    facts_json = json.dumps(facts, indent=2, default=str)

    return f"""
You are an operational reporting assistant.

Create a concise report summary using the trusted facts supplied below.

Requirements:

Grounding:
- Use only the supplied facts and treat all supplied calculations as final.
- Support every finding and concern with specific supplied metric or validation evidence.
- Preserve metric names, signs, and values, applying only the display formatting below.
- Describe results neutrally. Use qualitative labels only when a supplied threshold supports them.

Content:
- Make each finding specific and include its primary metric value.
- Return an empty concerns list when the supplied facts contain no concerns.
- Write a two-to-four-sentence executive summary of the supported findings and concerns.

Formatting:
- Present evidence using readable metric labels and values rather than raw Python data.
- Present currency with a dollar sign, comma separators, and no decimal places.
- Present percentages rounded to one decimal place followed by a percent sign.
- Present dates using the month name and year, such as December 2025.

Trusted facts:
{facts_json}
"""

def generate_llm_summary(
    calculated_metrics: dict[str, object],
    validation_issues: list[ValidationIssue],
) -> ReportSummary:
    """Generate a structured summary from trusted report facts."""

    facts = prepare_summary_facts(calculated_metrics, validation_issues)
    prompt = build_summary_prompt(facts)
    client = create_gemini_client()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ReportSummary,
        ),
    )

    if response.parsed is None:
        raise ValueError("Gemini did not return a valid structured summary.")

    return response.parsed

def format_llm_summary(summary: ReportSummary) -> str:
    """Convert a structured LLM summary into Markdown for display."""

    lines = []

    lines.append("### Executive Summary")
    lines.append("")
    lines.append(summary.executive_summary)

    lines.append("")
    lines.append("### Major Findings")
    lines.append("")
    for finding in summary.major_findings:
        evidence_text = ", ".join(finding.evidence)
        lines.append(f"- {finding.statement}")
        lines.append(f"  - Evidence: {evidence_text}")

    if summary.concerns:
        lines.append("")
        lines.append("### Concerns")
        lines.append("")
        for concern in summary.concerns:
            concern_text = ", ".join(concern.evidence)
            lines.append(f"- {concern.statement}")
            lines.append(f"  - Evidence: {concern_text}")

    return "\n".join(lines)

def generate_summary(
    df: pd.DataFrame,
    calculated_metrics: dict[str, object],
    validation_issues: list[ValidationIssue],
) -> tuple[str, str]:
    """Generate summary text with Gemini, using the deterministic fallback if needed."""

    try:
        summary = generate_llm_summary(calculated_metrics, validation_issues)
        formatted_summary = format_llm_summary(summary)

        return formatted_summary, "gemini"
    
    except Exception:
        summary = generate_fallback_summary(df)

        return summary, "fallback"