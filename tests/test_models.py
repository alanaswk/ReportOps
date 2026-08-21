import pytest
from pydantic import ValidationError
from reportops.models import ValidationIssue

def test_validation_issue_accepts_valid_data():
    issue = ValidationIssue(
        type="missing_value",
        severity="error",
        source="corrupted_missing_value.csv",
        explanation="Revenue is missing for LOC-003",
        suggested_action="Provide the missing revenue value."
    )

    assert issue.type == "missing_value"
    assert issue.severity == "error"
    assert issue.source == "corrupted_missing_value.csv"

def test_validation_issue_rejects_invalid_severity():
    with pytest.raises(ValidationError):
        ValidationIssue(
            type="missing_value",
            severity="urgent",  # Invalid severity
            source="corrupted_missing_value.csv",
            explanation="Revenue is missing for LOC-003",
            suggested_action="Provide the missing revenue value."
        )