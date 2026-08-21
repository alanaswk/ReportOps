import pandas as pd
import pytest
from reportops.ingestion import load_data,normalize_column_names,normalize_data_types

def test_load_csv():
    df = load_data("data/demo/clean_operations_data.csv")

    assert isinstance(df, pd.DataFrame), "load_data() did not return a DataFrame"
    assert len(df) == 180
    assert "location_id" and "budget_revenue" in df.columns, "Expected columns not found in DataFrame"

def test_load_data_rejects_unsupported_file_extension():
    with pytest.raises(ValueError):
        load_data("sample.txt")

def test_load_excel(tmp_path):
    source_df = pd.DataFrame(
        {
            " Location ID ": ["LOC-001"],
            "Budget Revenue": [100000],
        }
    )

    excel_path = tmp_path / "sample.xlsx"
    source_df.to_excel(excel_path, index=False)
    loaded_df = load_data(excel_path)

    assert isinstance(loaded_df, pd.DataFrame), "load_data() did not return a DataFrame"
    assert loaded_df.columns.tolist() == ["location_id", "budget_revenue"], "Column names were not normalized correctly"
    assert loaded_df.loc[0, "budget_revenue"] == 100000, "Data was not loaded correctly from the Excel file"


def test_normalize_column_names():
    df = pd.DataFrame(columns=[" Location ID ","Budget Revenue","labor-expense"])
    
    normalized_df = normalize_column_names(df)

    assert normalized_df.columns.tolist() == ["location_id", "budget_revenue", "labor_expense"], "normalize_column_names() did not work as expected"
    assert df.columns[0] == " Location ID ", "Original DataFrame should remain unchanged"

def test_normalize_data_types():
    df = pd.DataFrame(
        {
            "location_id": ["LOC-001", None],
            "revenue": ["100000", "bad-value"],
            "month": ["2025-01-01", "not-a-date"],
        }
    )

    normalized_df = normalize_data_types(df)

    assert pd.api.types.is_numeric_dtype(normalized_df["revenue"]), "Revenue column should be numeric"
    assert pd.isna(normalized_df.loc[1, "revenue"]), "Invalid revenue value should be converted to NaN"
    assert pd.api.types.is_datetime64_any_dtype(normalized_df["month"]), "Month column should be datetime"
    assert pd.isna(normalized_df.loc[1, "month"]), "Invalid month value should be converted to NaN"
    assert pd.isna(normalized_df.loc[1, "location_id"]), "Invalid location_id value should be converted to NaN"
