"""Generate reproducible clean and corrupted ReportOps demo datasets.

Run from the repository root:

    python scripts/generate_demo_data.py

The script intentionally creates one clean file and five files containing one
known validation problem each. Expected results are written to
``data/demo/expected_errors.json`` for use in tests.
"""

from __future__ import annotations

import csv
import json
import random
from copy import deepcopy
from datetime import date
from pathlib import Path


SEED = 42
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "demo"

CORE_COLUMNS = [
    "location_id",
    "location_name",
    "region",
    "month",
    "revenue",
    "budget_revenue",
    "labor_expense",
    "other_expense",
    "volume",
]

LOCATIONS = [
    ("LOC-001", "Harbor Point", "Northeast"),
    ("LOC-002", "Maple Square", "Northeast"),
    ("LOC-003", "Riverside", "Northeast"),
    ("LOC-004", "Summit Hill", "Northeast"),
    ("LOC-005", "Lakeview", "Midwest"),
    ("LOC-006", "Prairie Center", "Midwest"),
    ("LOC-007", "Oak Crossing", "Midwest"),
    ("LOC-008", "Riverbend", "Midwest"),
    ("LOC-009", "Magnolia Park", "South"),
    ("LOC-010", "Peachtree", "South"),
    ("LOC-011", "Cypress Grove", "South"),
    ("LOC-012", "Blue Ridge", "South"),
    ("LOC-013", "Golden Gate", "West"),
    ("LOC-014", "Desert Springs", "West"),
    ("LOC-015", "Cascade", "West"),
]


def generate_clean_rows() -> list[dict[str, object]]:
    """Return 12 months of clean synthetic data for 15 locations."""
    rng = random.Random(SEED)
    rows: list[dict[str, object]] = []

    for location_index, (location_id, location_name, region) in enumerate(LOCATIONS):
        base_revenue = 175_000 + (location_index * 7_500)
        base_volume = 1_350 + (location_index * 45)

        for month_number in range(1, 13):
            seasonality = 1 + (month_number - 6.5) * 0.006
            revenue = round(base_revenue * seasonality * rng.uniform(0.96, 1.04), 2)
            budget_revenue = round(base_revenue * seasonality * rng.uniform(0.98, 1.03), 2)
            labor_expense = round(revenue * rng.uniform(0.285, 0.345), 2)
            other_expense = round(revenue * rng.uniform(0.39, 0.47), 2)
            volume = round(base_volume * seasonality * rng.uniform(0.95, 1.05))

            rows.append(
                {
                    "location_id": location_id,
                    "location_name": location_name,
                    "region": region,
                    "month": date(2025, month_number, 1).isoformat(),
                    "revenue": revenue,
                    "budget_revenue": budget_revenue,
                    "labor_expense": labor_expense,
                    "other_expense": other_expense,
                    "volume": volume,
                }
            )

    return rows


def find_row(rows: list[dict[str, object]], location_id: str, month: str) -> dict[str, object]:
    """Return a specific location-month row from a generated dataset."""
    return next(
        row
        for row in rows
        if row["location_id"] == location_id and row["month"] == month
    )


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    """Write rows using a stable column order."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def build_corrupted_datasets(clean_rows: list[dict[str, object]]) -> dict[str, tuple[list[dict[str, object]], list[str]]]:
    """Create five datasets, each isolating one validation category."""
    missing_column_rows = [
        {key: value for key, value in row.items() if key != "budget_revenue"}
        for row in deepcopy(clean_rows)
    ]

    duplicate_rows = deepcopy(clean_rows)
    duplicate_rows.append(deepcopy(find_row(duplicate_rows, "LOC-001", "2025-01-01")))

    missing_value_rows = deepcopy(clean_rows)
    find_row(missing_value_rows, "LOC-003", "2025-03-01")["revenue"] = ""

    impossible_value_rows = deepcopy(clean_rows)
    find_row(impossible_value_rows, "LOC-004", "2025-04-01")["volume"] = -25

    reconciliation_rows = deepcopy(clean_rows)
    for row in reconciliation_rows:
        row["total_expense"] = round(
            float(row["labor_expense"]) + float(row["other_expense"]), 2
        )
    reconciliation_target = find_row(reconciliation_rows, "LOC-005", "2025-05-01")
    reconciliation_target["total_expense"] = round(
        float(reconciliation_target["total_expense"]) + 5_000, 2
    )

    return {
        "corrupted_missing_required_column.csv": (
            missing_column_rows,
            [column for column in CORE_COLUMNS if column != "budget_revenue"],
        ),
        "corrupted_duplicate_record.csv": (duplicate_rows, CORE_COLUMNS),
        "corrupted_missing_value.csv": (missing_value_rows, CORE_COLUMNS),
        "corrupted_impossible_value.csv": (impossible_value_rows, CORE_COLUMNS),
        "corrupted_reconciliation_error.csv": (
            reconciliation_rows,
            [*CORE_COLUMNS, "total_expense"],
        ),
    }


EXPECTED_ERRORS = {
    "seed": SEED,
    "clean_file": "clean_operations_data.csv",
    "corrupted_files": [
        {
            "file": "corrupted_missing_required_column.csv",
            "rule": "required_columns",
            "expected_issue_count": 1,
            "expected": {"missing_columns": ["budget_revenue"]},
        },
        {
            "file": "corrupted_duplicate_record.csv",
            "rule": "duplicate_records",
            "expected_issue_count": 1,
            "expected": {
                "location_id": "LOC-001",
                "month": "2025-01-01",
                "duplicate_group_size": 2,
            },
        },
        {
            "file": "corrupted_missing_value.csv",
            "rule": "missing_values",
            "expected_issue_count": 1,
            "expected": {
                "location_id": "LOC-003",
                "month": "2025-03-01",
                "column": "revenue",
            },
        },
        {
            "file": "corrupted_impossible_value.csv",
            "rule": "impossible_values",
            "expected_issue_count": 1,
            "expected": {
                "location_id": "LOC-004",
                "month": "2025-04-01",
                "column": "volume",
                "value": -25,
            },
        },
        {
            "file": "corrupted_reconciliation_error.csv",
            "rule": "reconciliation",
            "expected_issue_count": 1,
            "expected": {
                "location_id": "LOC-005",
                "month": "2025-05-01",
                "difference": 5000.0,
            },
        },
    ],
}


def main() -> None:
    """Regenerate every ReportOps demo file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    clean_rows = generate_clean_rows()
    write_csv(OUTPUT_DIR / "clean_operations_data.csv", clean_rows, CORE_COLUMNS)

    for filename, (rows, columns) in build_corrupted_datasets(clean_rows).items():
        write_csv(OUTPUT_DIR / filename, rows, columns)

    manifest_path = OUTPUT_DIR / "expected_errors.json"
    manifest_path.write_text(
        json.dumps(EXPECTED_ERRORS, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Generated 1 clean file and 5 corrupted files in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
