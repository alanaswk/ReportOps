from typing import Any, Literal
import pandas as pd
import plotly.graph_objects as go

from .metrics import (
    calculate_labor_expense_percentage,
    calculate_month_over_month_revenue,
    calculate_operating_margin,
    calculate_revenue_variance,
)
from .charts import (
    create_actual_vs_budget_chart,
    create_largest_variances_chart,
    create_monthly_revenue_trend_chart,
)
from .validation import validate_data


def get_report_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """Run all report metric calculations and return their results."""

    monthly_revenue = calculate_month_over_month_revenue(df)

    return {
        "revenue_variance": calculate_revenue_variance(df),
        "month_over_month_revenue": monthly_revenue.to_dict(orient="records"),
        "operating_margin": calculate_operating_margin(df),
        "labor_expense_percentage": calculate_labor_expense_percentage(df)
    }

def create_report_chart(
    df: pd.DataFrame,
    chart_type: Literal[
        "actual_vs_budget",
        "monthly_revenue",
        "largest_variances",
    ],
) -> go.Figure:
    """Create the requested report chart."""

    if chart_type == "actual_vs_budget":
        return create_actual_vs_budget_chart(df)

    if chart_type == "monthly_revenue":
        return create_monthly_revenue_trend_chart(df)

    if chart_type == "largest_variances":
        return create_largest_variances_chart(df)

    raise ValueError(f"Unsupported chart type: {chart_type}")

def get_validation_explanations(
    df: pd.DataFrame,
    source: str,
) -> list[dict[str, Any]]:
    """Run validation and return serializable explanations."""

    issues = validate_data(df, source)
    serialized_issues = []

    for issue in issues:
        serialized_issues.append(issue.model_dump())

    return serialized_issues