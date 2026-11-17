"""Reusable ticket CSV validation, cleaning, and analytics."""

import csv
from io import BytesIO, StringIO

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "priority",
    "category",
    "resolution_time_hours",
]


def _normalize_column_name(column: str) -> str:
    """Normalize a CSV header in the same way as the dashboard."""
    return str(column).strip().lower().replace(" ", "_")


def _validate_csv_structure(file_content: bytes) -> None:
    """Validate raw CSV headers and record widths before Pandas reads them.

    Pandas may rename duplicate headers and can otherwise obscure the original
    CSV structure, so these checks deliberately happen first.
    """
    try:
        text = file_content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "The CSV must use a supported text encoding, such as UTF-8."
        ) from exc

    try:
        rows = csv.reader(StringIO(text, newline=""), strict=True)
        header = next(rows, None)
        if header is None or not header:
            raise ValueError("The uploaded CSV has no readable header.")

        normalized_headers = [_normalize_column_name(item) for item in header]
        if len(set(normalized_headers)) != len(normalized_headers):
            raise ValueError(
                "Duplicate column names detected in the CSV header "
                "(including case/whitespace variants)."
            )

        expected_width = len(header)
        for line_number, row in enumerate(rows, start=2):
            # Match the common CSV convention that completely blank lines are ignored.
            if not row:
                continue
            if len(row) != expected_width:
                raise ValueError(
                    f"Malformed CSV: row {line_number} contains {len(row)} "
                    f"fields; expected {expected_width}."
                )
    except csv.Error as exc:
        raise ValueError(
            "Malformed CSV: please check the file structure and delimiters."
        ) from exc
    except StopIteration:
        raise ValueError("The uploaded CSV has no readable header.")


def load_ticket_csv(file_content: bytes) -> pd.DataFrame:
    """Load a CSV file and normalize column names."""

    if not file_content or not file_content.strip():
        raise ValueError("The uploaded CSV file is empty.")

    _validate_csv_structure(file_content)

    try:
        df = pd.read_csv(BytesIO(file_content), index_col=False)
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

    df.columns = [_normalize_column_name(column) for column in df.columns]

    # Keep this post-normalization check as defense in depth.
    if len(set(df.columns)) != len(df.columns):
        raise ValueError("Duplicate column names detected after normalization.")

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

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

    missing_required = data[["priority", "category"]].isna().any(axis=1)

    # NaN, +inf, and -inf are all invalid; only finite, non-negative values
    # are permitted into the analytics dataset.
    finite_resolution = np.isfinite(data["resolution_time_hours"].to_numpy(dtype=float))
    invalid_resolution = (
        ~finite_resolution
        | (data["resolution_time_hours"] < 0).fillna(True).to_numpy()
    )
    invalid_resolution = pd.Series(invalid_resolution, index=data.index)

    invalid_rows = missing_required | invalid_resolution
    valid_data = data.loc[~invalid_rows].copy()

    priority_counts = valid_data["priority"].value_counts().sort_index()
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
        "data_quality_percentage": round(len(valid_data) / len(data) * 100, 2),
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
