import pandas as pd
from .models import ValidationIssue

REQUIRED_COLUMNS = {
    "location_id",
    "location_name",
    "region",
    "month",
    "revenue",
    "budget_revenue",
    "labor_expense",
    "other_expense",
    "volume",
}

DUPLICATE_KEY_COLUMNS = ["location_id", "month"]

RECONCILIATION_COLUMNS = {
    "labor_expense",
    "other_expense",
    "total_expense",
}

def validate_required_columns(
    df: pd.DataFrame,
    source: str,
) -> list[ValidationIssue]:
    """
    Validate that the required columns are present in the DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        source (str): The source of the data (e.g., file name).

    Returns:
        list[ValidationIssue]: A list of validation issues found.
    """
    issues = []
    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    for col in sorted(missing_columns):
        issues.append(
            ValidationIssue(
                type="missing_required_column",
                severity="error",
                source=source,
                explanation=f"Required column '{col}' is missing.",
                suggested_action=f"Add the '{col}' column to the data.",
            )
        )
    
    return issues

def validate_duplicate_records(
    df: pd.DataFrame,
    source: str,
) -> list[ValidationIssue]:
    """
    Validate that there are no duplicate records based on the specified key columns.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        source (str): The source of the data (e.g., file name).

    Returns:
        list[ValidationIssue]: A list of validation issues found.
    """
    issues = []
    if not set(DUPLICATE_KEY_COLUMNS).issubset(df.columns):
        return issues
    
    duplicate_mask = df.duplicated(subset=DUPLICATE_KEY_COLUMNS, keep=False)
    duplicates = df.loc[duplicate_mask, DUPLICATE_KEY_COLUMNS].drop_duplicates()
    for _, row in duplicates.iterrows():
        issues.append(
            ValidationIssue(
                type="duplicate_record",
                severity="error",
                source=source,
                explanation=f"Duplicate record found for location_id '{row['location_id']}' and month '{row['month']}'.",
                suggested_action=f"Remove or correct the duplicate record for location_id '{row['location_id']}' and month '{row['month']}'.",
            )
        )
    return issues

def validate_missing_values(
    df: pd.DataFrame,
    source: str,
) -> list[ValidationIssue]:
    """
    Validate that there are no missing values in the required columns.

    Args:
        df (pd.DataFrame): The DataFrame to validate.
        source (str): The source of the data (e.g., file name).

    Returns:
        list[ValidationIssue]: A list of validation issues found.
    """
    issues = []
    columns_to_check = sorted(REQUIRED_COLUMNS.intersection(df.columns))
    missing_mask = df[columns_to_check].isna()

    for row_index, row in missing_mask.iterrows():
        for col in columns_to_check:
            if row[col]:
                issues.append(
                    ValidationIssue(
                        type="missing_value",
                        severity="error",
                        source=source,
                        explanation=f"Missing value in column '{col}' at row {row_index}.",
                        suggested_action=f"Provide a value for column '{col}' at row {row_index}.",
                    )
                )

    return issues

def validate_impossible_values(
    df: pd.DataFrame,
    source: str,
) -> list[ValidationIssue]:
    """Detect negative operational volume values."""
    issues = []

    if "volume" not in df.columns:
        return issues

    # TODO: Select only rows where volume is below zero.
    invalid_rows = df[df["volume"] < 0]

    for row_index, row in invalid_rows.iterrows():
        issues.append(
            ValidationIssue(
                type="impossible_value",
                severity="error",
                source=source,
                explanation=f"Impossible negative value in column 'volume' at row {row_index}: {row['volume']}.",
                suggested_action=(
                    f"Replace the volume at row {row_index} "
                    "with a valid nonnegative value."
                ),
            )
        )

    return issues

def validate_reconciliation(
    df: pd.DataFrame,
    source: str,
    tolerance: float = 0.01,
) -> list[ValidationIssue]:
    """Detect differences between component and reported expenses."""
    issues = []
    if not RECONCILIATION_COLUMNS.issubset(df.columns):
        return issues

    differences = (df["labor_expense"] + df["other_expense"] - df["total_expense"]).abs()
    invalid_rows = df.loc[differences > tolerance]

    for row_index, row in invalid_rows.iterrows():
        difference = differences.loc[row_index]

        issues.append(
            ValidationIssue(
                type="reconciliation_error",
                severity="error",
                source=source,
                explanation=(
                    f"Expense reconciliatiom differs by ${difference:,.2f} at row {row_index}"
                ),
                suggested_action=(
                    "Review the component expenses and reported total."
                ),
            )
        )

    return issues

def validate_data(
    df: pd.DataFrame,
    source: str,
) -> list[ValidationIssue]:
    """Run all ReportOps validation rules."""
    issues = []

    validators = [
        validate_required_columns,
        validate_duplicate_records,
        validate_missing_values,
        validate_impossible_values,
        validate_reconciliation,
    ]

    for validator in validators:
        new_issue = validator(df, source)
        issues.extend(new_issue)
    
    return issues