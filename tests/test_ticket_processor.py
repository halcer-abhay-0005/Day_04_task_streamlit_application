import pytest

from src.ticket_processor import (
    load_ticket_csv,
    process_ticket_csv,
)


VALID_CSV = b"""ticket_id,priority,category,resolution_time_hours
TKT001,High,Technical,5
TKT002,Low,Billing,2
TKT003,High,Technical,7
TKT004,Medium,Account,3
"""


def test_valid_csv_loading():
    df = load_ticket_csv(VALID_CSV)

    assert len(df) == 4
    assert "priority" in df.columns


def test_valid_ticket_processing():
    result = process_ticket_csv(VALID_CSV)

    assert result["quality_summary"]["valid_rows"] == 4
    assert result["quality_summary"]["invalid_rows"] == 0


def test_priority_counts():
    result = process_ticket_csv(VALID_CSV)

    assert result["priority_counts"]["High"] == 2
    assert result["priority_counts"]["Low"] == 1


def test_category_average_resolution():
    result = process_ticket_csv(VALID_CSV)

    assert result["category_resolution"]["Technical"] == 6.0
    assert result["category_resolution"]["Billing"] == 2.0


def test_empty_file():
    with pytest.raises(ValueError, match="empty"):
        process_ticket_csv(b"")


def test_missing_required_columns():
    csv_data = b"ticket_id,status\nTKT001,Open\n"

    with pytest.raises(ValueError, match="Missing required columns"):
        process_ticket_csv(csv_data)


def test_invalid_resolution_value():
    csv_data = b"""priority,category,resolution_time_hours
High,Technical,5
Low,Billing,invalid
"""

    result = process_ticket_csv(csv_data)

    assert result["quality_summary"]["valid_rows"] == 1
    assert result["quality_summary"]["invalid_rows"] == 1


def test_negative_resolution_value():
    csv_data = b"""priority,category,resolution_time_hours
High,Technical,-5
Low,Billing,2
"""

    result = process_ticket_csv(csv_data)

    assert result["quality_summary"]["invalid_rows"] == 1


def test_missing_required_values():
    csv_data = b"""priority,category,resolution_time_hours
High,Technical,5
, Billing,2
"""

    result = process_ticket_csv(csv_data)

    assert result["quality_summary"]["invalid_rows"] == 1


def test_malformed_csv():
    csv_data = (
        b"priority,category,resolution_time_hours\n"
        b"High,Technical,5\n"
        b"Low,Billing,2,unexpected\n"
    )

    with pytest.raises(ValueError, match="Malformed CSV"):
        process_ticket_csv(csv_data)


def test_original_dataframe_is_not_modified():
    import pandas as pd
    from src.ticket_processor import process_tickets

    df = pd.DataFrame({
        "priority": ["High"],
        "category": ["Technical"],
        "resolution_time_hours": ["5"],
    })

    original = df.copy(deep=True)
    process_tickets(df)

    assert df.equals(original)


def test_quality_percentage():
    csv_data = b"""priority,category,resolution_time_hours
High,Technical,5
Low,Billing,invalid
"""

    result = process_ticket_csv(csv_data)

    assert result["quality_summary"]["data_quality_percentage"] == 50.0



@pytest.mark.parametrize("bad_value", ["inf", "-inf", "Infinity", "-Infinity"])
def test_non_finite_resolution_values_are_rejected(bad_value):
    csv_data = (
        "priority,category,resolution_time_hours\n"
        f"High,Technical,{bad_value}\n"
        "Low,Billing,2\n"
    ).encode()

    result = process_ticket_csv(csv_data)

    assert result["quality_summary"]["valid_rows"] == 1
    assert result["quality_summary"]["invalid_rows"] == 1
    assert result["quality_summary"]["invalid_resolution_values"] == 1
    assert result["category_resolution"].to_dict() == {"Billing": 2.0}
    assert result["category_resolution"].map(lambda value: __import__("math").isfinite(value)).all()


def test_extra_field_in_csv_row_is_rejected_with_clear_error():
    csv_data = (
        b"ticket_id,priority,category,resolution_time_hours\n"
        b"TKT001,High,Technical,5,unexpected\n"
    )

    with pytest.raises(ValueError, match=r"row 2 contains 5 fields; expected 4"):
        process_ticket_csv(csv_data)


def test_short_csv_row_is_rejected():
    csv_data = (
        b"ticket_id,priority,category,resolution_time_hours\n"
        b"TKT001,High,Technical\n"
    )

    with pytest.raises(ValueError, match=r"row 2 contains 3 fields; expected 4"):
        process_ticket_csv(csv_data)


@pytest.mark.parametrize(
    "header",
    [
        "priority,priority,category,resolution_time_hours",
        "priority, Priority ,category,resolution_time_hours",
        "priority,PRIORITY,category,resolution_time_hours",
    ],
)
def test_duplicate_raw_headers_are_rejected_before_pandas(header):
    csv_data = (header + "\nHigh,Low,Technical,5\n").encode()

    with pytest.raises(ValueError, match="Duplicate column names detected"):
        process_ticket_csv(csv_data)
