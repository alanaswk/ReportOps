import pandas as pd
from .metrics import (
    calculate_labor_expense_percentage,
    calculate_month_over_month_revenue,
    calculate_operating_margin,
    calculate_revenue_variance,
)


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