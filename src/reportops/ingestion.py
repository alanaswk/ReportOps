from pathlib import Path
import pandas as pd
from io import BytesIO

NUMERIC_COLUMNS = [
    "revenue",
    "budget_revenue",
    "labor_expense",
    "other_expense",
    "total_expense",
    "volume",
]

TEXT_COLUMNS = [
    "location_id",
    "location_name",
    "region",
]

def load_data(filepath: str | Path) -> pd.DataFrame:
    """
    Load data from a CSV/XLSX/XLS file into a pandas DataFrame.

    Args:
        filepath (str): The path to the file.

    Returns:
        pd.DataFrame: The loaded DataFrame.
    """
    file_name = getattr(filepath, "name", str(filepath))
    extension = Path(file_name).suffix.lower()

    if extension == ".csv":
        df = pd.read_csv(filepath)
    elif extension in [".xls", ".xlsx"]:
        df = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file extension: {extension}. Supported extensions are .csv, .xls, and .xlsx.")
    
    df = normalize_column_names(df)
    df = normalize_data_types(df)

    return df


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names by converting them to lowercase and replacing spaces with underscores.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with normalized column names.
    """
    normalized_df = df.copy()
    normalized_df.columns = normalized_df.columns.str.strip().str.lower().str.replace(" ","_").str.replace("-", "_")
    return normalized_df


def normalize_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize data types of specific columns in the DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with normalized data types.
    """
    normalized_df = df.copy()

    for column in NUMERIC_COLUMNS:
        if column in normalized_df.columns:
            normalized_df[column] = pd.to_numeric(normalized_df[column], errors='coerce')
    
    for column in TEXT_COLUMNS:
        if column in normalized_df.columns:
            normalized_df[column] = normalized_df[column].astype("string")
    
    if "month" in normalized_df.columns:
        normalized_df["month"] = pd.to_datetime(normalized_df["month"], errors='coerce')

    return normalized_df

def test_load_uploaded_csv():
    uploaded_file = BytesIO(
        b"location_id,revenue\nL001,100000\n"
    )
    uploaded_file.name = "uploaded.csv"

    result = load_data(uploaded_file)

    assert len(result) == 1
    assert result.loc[0, "location_id"] == "L001"
    assert result.loc[0, "revenue"] == 100000