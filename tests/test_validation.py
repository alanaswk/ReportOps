import pytest
from reportops.ingestion import load_data
from reportops.validation import (
    validate_required_columns, validate_duplicate_records,
    validate_missing_values, validate_impossible_values,
    validate_reconciliation, validate_data
)

def test_clean_file_has_all_required_columns():
    file_path = "data/demo/clean_operations_data.csv"
    df = load_data(file_path)
    issues = validate_required_columns(df, source=file_path)

    assert issues == [], f"Expected no validation issues, but found: {issues}"

def test_detects_missing_required_columns():
    file_path = "data/demo/corrupted_missing_required_column.csv"
    df = load_data(file_path)
    issues = validate_required_columns(df, source=file_path)

    assert len(issues) == 1, f"Expected 1 validation issue, but found: {len(issues)}"
    assert "budget_revenue" in issues[0].explanation, f"Expected missing column 'budget_revenue', but found: {issues[0].explanation}"
    assert issues[0].source == file_path, f"Expected source to be '{file_path}', but found: {issues[0].source}"

def test_detects_duplicate_records():
    file_path = "data/demo/corrupted_duplicate_record.csv"
    df = load_data(file_path)
    issues = validate_duplicate_records(df, source=file_path)

    assert len(issues) == 1, f"Expected 1 validation issue, but found: {len(issues)}"
    assert issues[0].type == "duplicate_record", f"Expected issue type 'duplicate_record', but found: {issues[0].type}"
    assert "LOC-001" in issues[0].explanation, f"Expected duplicate record for 'LOC-001', but found: {issues[0].explanation}"
    assert "2025-01-01" in issues[0].explanation, f"Expected duplicate record for '2025-01-01', but found: {issues[0].explanation}"

def test_detects_missing_value():
    file_path = "data/demo/corrupted_missing_value.csv"
    df = load_data(file_path)
    issues = validate_missing_values(df, source=file_path)

    assert len(issues) == 1, f"Expected 1 validation issue, but found: {len(issues)}"
    assert issues[0].type == "missing_value", f"Expected issue type 'missing_value', but found: {issues[0].type}"
    assert "revenue" in issues[0].explanation, f"Expected missing value for 'revenue', but found: {issues[0].explanation}"

def test_detects_impossible_value():
    file_path = "data/demo/corrupted_impossible_value.csv"
    df = load_data(file_path)
    issues = validate_impossible_values(df, file_path)

    assert len(issues) == 1, f"Expected 1 validation issue, but found: {len(issues)}"
    assert issues[0].type == "impossible_value", f"Expected issue type 'missing_value', but found: {issues[0].type}"
    assert "-25" in issues[0].explanation, f"Expected impossible value for 'volume', but found: {issues[0].explanation}"
    assert "volume" in issues[0].explanation.lower(), f"Expected impossible value for 'volume', but found: {issues[0].explanation}"

def test_detects_reconciliation_error():
    file_path = "data/demo/corrupted_reconciliation_error.csv"
    df = load_data(file_path)
    issues = validate_reconciliation(df, file_path)

    assert len(issues) == 1, f"Expected 1 validation issue, but found: {len(issues)}"
    assert issues[0].type == "reconciliation_error", f"Expected issue type 'reconciliation_error', but found: {issues[0].type}"
    assert "5,000" in issues[0].explanation, f"Expected reconciliation error for '5,000', but found: {issues[0].explanation}"

def test_clean_file_passes_all_validation():
    file_path = "data/demo/clean_operations_data.csv"
    df = load_data(file_path)
    issues = validate_data(df, file_path)

    assert issues == []

@pytest.mark.parametrize(
    ("filename", "expected_type"),
    [
        (
            "corrupted_missing_required_column.csv",
            "missing_required_column",
        ),
        (
            "corrupted_duplicate_record.csv",
            "duplicate_record",
        ),
        (
            "corrupted_missing_value.csv",
            "missing_value",
        ),
        (
            "corrupted_impossible_value.csv",
            "impossible_value",
        ),
        (
            "corrupted_reconciliation_error.csv",
            "reconciliation_error",
        ),
    ],
)
def test_corrupted_file_detects_expected_issue(
    filename,
    expected_type,
):
    file_path = f"data/demo/{filename}"
    df = load_data(file_path)
    issues = validate_data(df, file_path)

    detected_types = {issue.type for issue in issues}
    
    assert expected_type in detected_types, (
        f"Expected {expected_type} for {filename}, "
        f"but detected {detected_types}"
    )