"""Streamlit interface for the internal ticket analytics dashboard."""

import streamlit as st

from src.ticket_processor import process_ticket_csv


st.set_page_config(
    page_title="Ticket Analytics Dashboard",
    page_icon="🎫",
    layout="wide",
)

st.title("🎫 Internal Ticket Analytics Dashboard")
st.write(
    "Upload a ticket CSV file to preview records, "
    "validate data, and explore ticket analytics."
)

uploaded_file = st.file_uploader(
    "Upload ticket CSV",
    type=["csv"],
    help="Upload a CSV containing priority, category, "
         "and resolution_time_hours columns.",
)

if uploaded_file is None:
    st.info("Upload a CSV file to get started.")
    st.stop()

try:
    result = process_ticket_csv(uploaded_file.getvalue())

except ValueError as error:
    st.error(f"Upload validation failed: {error}")
    st.stop()

except Exception:
    st.error(
        "An unexpected processing error occurred. "
        "Please verify your CSV file and try again."
    )
    st.stop()


preview = result["preview"]
valid_data = result["valid_data"]
quality = result["quality_summary"]

st.subheader("1. Dataset Overview")

col1, col2, col3 = st.columns(3)

col1.metric("Total Rows", len(preview))
col2.metric("Total Columns", len(preview.columns))
col3.metric("Dataset Dimensions", f"{preview.shape[0]} × {preview.shape[1]}")

st.subheader("2. CSV Preview")

st.dataframe(preview.head(20), use_container_width=True)

st.subheader("3. Column Information")

column_info = {
    "Column": preview.columns,
    "Data Type": preview.dtypes.astype(str).values,
    "Missing Values": preview.isna().sum().values,
}

st.dataframe(column_info, use_container_width=True)

st.subheader("4. Data Quality Summary")

q1, q2, q3 = st.columns(3)

q1.metric("Valid Records", quality["valid_rows"])
q2.metric("Invalid Records", quality["invalid_rows"])
q3.metric(
    "Data Quality",
    f'{quality["data_quality_percentage"]}%'
)

st.write(
    "Missing required fields:",
    quality["missing_required_fields"],
)

st.write(
    "Invalid resolution values:",
    quality["invalid_resolution_values"],
)

if quality["invalid_rows"] > 0:
    st.warning(
        "Some records were excluded from analytics "
        "because they contain invalid required values."
    )
else:
    st.success("All uploaded records passed validation.")

st.subheader("5. Ticket Analytics")

if valid_data.empty:
    st.warning(
        "No valid records are available for analytics. "
        "Please upload a CSV with valid ticket data."
    )
    st.stop()

left, right = st.columns(2)

with left:
    st.markdown("**Priority-wise Ticket Counts**")
    st.bar_chart(result["priority_counts"])

with right:
    st.markdown("**Category-wise Average Resolution Time (Hours)**")
    st.bar_chart(result["category_resolution"])

st.subheader("6. Processed Ticket Records")

st.dataframe(
    valid_data,
    use_container_width=True,
)

st.success("Ticket dashboard processing completed successfully.")
