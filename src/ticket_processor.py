"""Reusable ticket CSV validation, cleaning, and analytics."""

from io import BytesIO

import pandas as pd


REQUIRED_COLUMNS = [
    "priority",
    "category",
    "resolution_time_hours",
]


def load_ticket_csv(file_content: bytes) -> pd.DataFrame:
    """Load a CSV file and normalize column names."""

    if not file_content or not file_content.strip():
        raise ValueError("The uploaded CSV file is empty.")

    try:
        df = pd.read_csv(BytesIO(file_content))
    except pd.errors.EmptyDataError as exc:
        raise ValueError("The uploaded CSV has no readable data.") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(
            "Malformed CSV: please check the file structure and delimiters."
        ) from exc
    except UnicodeDecodeError as exc:
        raise ValueError("The CSV must use a supported text encoding, such as UTF-8.") from exc

    if df.empty or len(df.columns) == 0:
        raise ValueError("The uploaded CSV contains no records.")

    df.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in df.columns
    ]

    if len(set(df.columns)) != len(df.columns):
        raise ValueError("Duplicate column names detected after normalization.")

    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {', '.join(missing)}"
        )

    return df


def process_tickets(df: pd.DataFrame) -> dict:
    """Validate tickets and calculate analytics outside the UI layer."""

    data = df.copy()

    for column in ["priority", "category"]:
        data[column] = data[column].astype("string").str.strip()
        data[column] = data[column].replace("", pd.NA)

    data["resolution_time_hours"] = pd.to_numeric(
        data["resolution_time_hours"],
        errors="coerce",
    )

    missing_required = data[
        ["priority", "category"]
    ].isna().any(axis=1)

    invalid_resolution = (
        data["resolution_time_hours"].isna()
        | (data["resolution_time_hours"] < 0)
    )

    invalid_rows = missing_required | invalid_resolution
    valid_data = data.loc[~invalid_rows].copy()

    priority_counts = (
        valid_data["priority"]
        .value_counts()
        .sort_index()
    )

    category_resolution = (
        valid_data.groupby("category")["resolution_time_hours"]
        .mean()
        .sort_index()
        .round(2)
    )

    quality_summary = {
        "total_rows": len(data),
        "valid_rows": len(valid_data),
        "invalid_rows": int(invalid_rows.sum()),
        "missing_required_fields": int(missing_required.sum()),
        "invalid_resolution_values": int(invalid_resolution.sum()),
        "data_quality_percentage": round(
            len(valid_data) / len(data) * 100, 2
        ),
    }

    return {
        "preview": data,
        "valid_data": valid_data,
        "priority_counts": priority_counts,
        "category_resolution": category_resolution,
        "quality_summary": quality_summary,
    }


def process_ticket_csv(file_content: bytes) -> dict:
    """Public entry point for loading and processing uploaded CSV files."""

    dataframe = load_ticket_csv(file_content)
    return process_tickets(dataframe)
