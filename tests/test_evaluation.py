import json
from pathlib import Path
import pandas as pd
import pytest

from reportops.ingestion import load_data
from reportops.validation import validate_data
from reportops.metrics import (
    calculate_revenue_variance,
    calculate_month_over_month_revenue,
    calculate_operating_margin,
    calculate_labor_expense_percentage,
)


DEMO_DIR = Path("data/demo")
EXPECTED_ERRORS_PATH = DEMO_DIR / "expected_errors.json"
RULE_TO_ISSUE_TYPE = {
    "required_columns": "missing_required_column",
    "duplicate_records": "duplicate_record",
    "missing_values": "missing_value",
    "impossible_values": "impossible_value",
    "reconciliation": "reconciliation_error",
}


def load_expected_errors():
    with open(EXPECTED_ERRORS_PATH, "r") as file:
        return json.load(file)


def test_clean_file_has_no_validation_issues():
    expected_errors = load_expected_errors()

    file_name = expected_errors["clean_file"]
    file_path = DEMO_DIR / file_name

    df = load_data(file_path)
    validation_issues = validate_data(df, file_name)

    assert validation_issues == []


def test_corrupted_files_detect_expected_issues():
    expected_errors = load_expected_errors()

    for corrupted_file in expected_errors["corrupted_files"]:
        file_name = corrupted_file["file"]
        expected_rule = corrupted_file["rule"]
        expected_issue_type = RULE_TO_ISSUE_TYPE[expected_rule]
        expected_issue_count = corrupted_file["expected_issue_count"]

        file_path = DEMO_DIR / file_name

        df = load_data(file_path)
        validation_issues = validate_data(df, file_name)

        detected_rules = [issue.type for issue in validation_issues]

        assert len(validation_issues) == expected_issue_count, (
            f"{file_name}: expected {expected_issue_count} issue(s), "
            f"but detected {len(validation_issues)}: {detected_rules}"
        )

        assert expected_issue_type in detected_rules, (
            f"{file_name}: expected issue type '{expected_issue_type}', "
            f"but detected {detected_rules}"
        )

def test_kpi_values_match_manual_expected_results():
    df = pd.DataFrame(
        {
            "month": pd.to_datetime(["2025-01-01", "2025-02-01"]),
            "revenue": [100000.0, 110000.0],
            "budget_revenue": [90000.0, 110000.0],
            "labor_expense": [30000.0, 35000.0],
            "other_expense": [20000.0, 25000.0],
        }
    )

    revenue_variance = calculate_revenue_variance(df)
    monthly_revenue = calculate_month_over_month_revenue(df)
    operating_margin = calculate_operating_margin(df)
    labor_expense_percentage = calculate_labor_expense_percentage(df)

    # Total revenue = 210,000
    # Total budget = 200,000
    # Variance = 10,000 / 200,000 = 5.0%
    assert revenue_variance["variance_amount"] == pytest.approx(10000.0)
    assert revenue_variance["variance_percent"] == pytest.approx(5.0)

    # February revenue increased from 100,000 to 110,000
    # Change = 10,000 / 100,000 = 10.0%
    latest_month = monthly_revenue.iloc[-1]
    assert latest_month["change_amount"] == pytest.approx(10000.0)
    assert latest_month["change_percent"] == pytest.approx(10.0)

    # Expenses = 65,000 labor + 45,000 other = 110,000
    # Operating income = 210,000 - 110,000 = 100,000
    # Margin = 100,000 / 210,000 = 47.619...%
    assert operating_margin["operating_margin_percent"] == pytest.approx(
        47.619047619
    )

    # Labor expense % = 65,000 / 210,000 = 30.952...%
    assert labor_expense_percentage["labor_expense_percent"] == pytest.approx(
        30.952380952
    )

def test_multiple_validation_issues_detected_together():
    file_name = "clean_operations_data.csv"
    file_path = DEMO_DIR / file_name

    df = load_data(file_path).copy()

    # Seed several different problems into the same dataset
    df.loc[2, "revenue"] = None
    df.loc[3, "volume"] = -25
    df["total_expense"] = (
        df["labor_expense"]
        + df["other_expense"]
    )
    df.loc[4, "total_expense"] += 5000

    # Duplicate an existing location-month record
    df = pd.concat(
        [df, df.iloc[[0]]],
        ignore_index=True,
    )

    validation_issues = validate_data(
        df,
        "multi_error_evaluation.csv",
    )

    detected_types = {
        issue.type
        for issue in validation_issues
    }

    expected_types = {
        "duplicate_record",
        "missing_value",
        "impossible_value",
        "reconciliation_error",
    }

    assert detected_types == expected_types