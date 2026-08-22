import pandas as pd
import pytest
from reportops.metrics import (
    calculate_revenue_variance,
    calculate_month_over_month_revenue,
    calculate_operating_margin,
    calculate_labor_expense_percentage
)

def test_calculate_revenue_variance():
    df = pd.DataFrame(
        {
            "revenue": [120, 90],
            "budget_revenue": [100, 100]
        }
    )

    results = calculate_revenue_variance(df)

    assert results["actual_revenue"] == 210
    assert results["budget_revenue"] == 200
    assert results["variance_amount"] == 10
    assert results["variance_percent"] == pytest.approx(5.0)

def test_calculate_revenue_variance_zero_budget():
    df = pd.DataFrame(
        {
            "revenue": [100, 50],
            "budget_revenue": [0, 0]
        }
    )

    results = calculate_revenue_variance(df)

    assert results["actual_revenue"] == 150
    assert results["budget_revenue"] == 0
    assert results["variance_amount"] == 150
    assert results["variance_percent"] == None

def test_calculate_month_over_month_revenue():
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

    result_df = calculate_month_over_month_revenue(df)

    assert len(result_df) == 2
    assert result_df.loc[0, "month"] == pd.Timestamp("2026-01-01")
    assert result_df.loc[0, "revenue"] == 150
    assert pd.isna(result_df.loc[0, "prior_month_revenue"])
    assert result_df.loc[1, "month"] == pd.Timestamp("2026-02-01")
    assert result_df.loc[1, "revenue"] == 180
    assert result_df.loc[1, "prior_month_revenue"] == 150
    assert result_df.loc[1, "change_amount"] == 30
    assert result_df.loc[1, "change_percent"] == pytest.approx(20.0)

def test_calculate_operating_margin():
    df = pd.DataFrame(
        {
            "revenue": [200, 300],
            "labor_expense": [50, 100],
            "other_expense": [100, 150]
        }
    )

    results = calculate_operating_margin(df)

    assert results["total_revenue"] == 500
    assert results["total_expense"] == 400
    assert results["operating_income"] == 100
    assert results["operating_margin_percent"] == pytest.approx(20.0)

def test_calculate_operating_margin_with_zero_revenue():
    df = pd.DataFrame(
        {
            "revenue": [0, 0],
            "labor_expense": [0, 0],
            "other_expense": [0, 0]
        }
    )

    results = calculate_operating_margin(df)

    assert results["total_revenue"] == 0
    assert results["total_expense"] == 0
    assert results["operating_income"] == 0
    assert results["operating_margin_percent"] == None

def test_calculate_labor_expense_percentage():
    df = pd.DataFrame(
        {
            "revenue": [200, 300],
            "labor_expense": [60, 90]
        }
    )

    results = calculate_labor_expense_percentage(df)

    assert results["total_labor_expense"] == 150
    assert results["total_revenue"] == 500
    assert results["labor_expense_percent"] == pytest.approx(30.0)

def test_calculate_labor_expense_percentage_with_zero_revenue():
    df = pd.DataFrame(
        {
            "revenue": [0, 0],
            "labor_expense": [0, 0]
        }
    )

    results = calculate_labor_expense_percentage(df)

    assert results["total_labor_expense"] == 0
    assert results["total_revenue"] == 0
    assert results["labor_expense_percent"] == None