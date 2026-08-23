import pandas as pd
import plotly.graph_objects as go
from .metrics import calculate_month_over_month_revenue

def create_actual_vs_budget_chart(df: pd.DataFrame) -> go.Figure:
    """Create a monthly grouped bar chart of actual and budget revenue."""

    monthly_data = (
        df.groupby("month", as_index=False)[
            ["revenue", "budget_revenue"]
        ]
        .sum()
        .sort_values("month")
        .reset_index(drop=True)
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=monthly_data["month"],
            y=monthly_data["revenue"],
            name="Actual Revenue",
        )
    )

    fig.add_trace(
        go.Bar(
            x=monthly_data["month"],
            y=monthly_data["budget_revenue"],
            name="Budget Revenue",
        )
    )

    fig.update_layout(
        barmode="group",
        title="Actual Revenue vs. Budget",
        xaxis_title="Month",
        yaxis_title="Revenue",
    )

    return fig


def create_monthly_revenue_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Create a line chart showing total revenue by month"""

    monthly_data = calculate_month_over_month_revenue(df)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=monthly_data["month"],
            y=monthly_data["revenue"],
            mode="lines+markers",
            name="Revenue",
        )

    )

    fig.update_layout(
        title="Monthly Revenue Trend",
        xaxis_title="Month",
        yaxis_title="Revenue",
    )

    return fig


def create_largest_variances_chart(
        df: pd.DataFrame,
        top_n: int=10,
) -> go.Figure:
    """Create a horizontal bar chart of the largest location variances."""

    location_data = (
        df.groupby("location_name", as_index=False)[
            ["revenue", "budget_revenue"]
        ]
        .sum()
        .reset_index(drop=True)
    )

    location_data["variance_amount"] = location_data["revenue"] - location_data["budget_revenue"]
    location_data["absolute_variance"] = (
        location_data["variance_amount"].abs()
    )
    largest_variances = (
        location_data
        .sort_values("absolute_variance", ascending=False)
        .head(top_n)
        .sort_values("variance_amount")
        .reset_index(drop=True)
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=largest_variances["variance_amount"],
            y=largest_variances["location_name"],
            orientation="h",
            name="Revenue Variance",
        )
    )

    fig.update_layout(
        title="Largest Revenue Variances by Location",
        xaxis_title="Revenue Variance",
        yaxis_title="Location",
    )

    return fig