import pandas as pd
import plotly.graph_objects as go

from reportops.charts import (
    create_actual_vs_budget_chart,
    create_monthly_revenue_trend_chart,
    create_largest_variances_chart
)

def test_create_actual_vs_budget_chart():
    df = pd.DataFrame(
        {
            "month": pd.to_datetime(
                [
                    "2026-02-01",
                    "2026-01-01",
                    "2026-02-01",
                    "2026-01-01",
                ]
            ),
            "revenue": [120, 100, 60, 50],
            "budget_revenue": [130, 90, 70, 60],
        }
    )

    fig = create_actual_vs_budget_chart(df)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert fig.data[0].name == "Actual Revenue"
    assert fig.data[1].name == "Budget Revenue"
    assert list(fig.data[0].y) == [150, 180]
    assert list(fig.data[1].y) == [150, 200]

def test_create_monthly_revenue_trend_chart():
    df = pd.DataFrame(
        {
            "month": pd.to_datetime(
                [
                    "2026-02-01",
                    "2026-01-01",
                    "2026-02-01",
                    "2026-01-01",
                ]
            ),
            "revenue": [120, 100, 60, 50],
        }
    )

    fig = create_monthly_revenue_trend_chart(df)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].name == "Revenue"
    assert fig.data[0].mode == "lines+markers"
    assert list(fig.data[0].y) == [150, 180]
    assert list(fig.data[0].x) == [
        pd.Timestamp("2026-01-01"),
        pd.Timestamp("2026-02-01"),
    ]

def test_create_largest_variances_chart():
    df = pd.DataFrame(
        {
            "location_name": ["Alpha", "Alpha", "Beta", "Beta", "Gamma", "Gamma"],
            "revenue": [100, 100, 90, 90, 100, 100],
            "budget_revenue": [80, 80, 120, 120, 95, 95],
        }
    )

    fig = create_largest_variances_chart(df, top_n=2)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].orientation == "h"
    assert fig.data[0].name == "Revenue Variance"
    assert list(fig.data[0].y) == ["Beta", "Alpha"]
    assert list(fig.data[0].x) == [-60, 40]