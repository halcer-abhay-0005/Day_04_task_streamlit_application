
# Day 04 — Streamlit Ticket Analytics Dashboard

## Overview
An internal ticket-data dashboard built using Python, Pandas, and Streamlit.

## Features
- CSV upload
- Dataset preview
- Row and column counts
- Dataset dimensions
- Column data types
- Missing-value information
- Ticket validation
- Priority-wise ticket counts
- Category-wise average resolution time
- Data-quality summary
- Error handling for invalid uploads

## Required CSV Columns

| Column | Description |
|---|---|
| priority | Ticket priority |
| category | Ticket category |
| resolution_time_hours | Resolution time in hours |

Other columns are preserved.

## Prerequisites
- Python 3.10+
- pip

## Installation

Create virtual environment:

```bash
python3 -m venv .venv
```

Activate:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Run Application

```bash
python3 -m streamlit run app.py
```

## Run Tests

```bash
python3 -m pytest -v
```

## Project Structure

```text
Day 4/
app.py
├── requirements.txt
├── README.md
├── src/
├── tests/
├── data/
├── evidence/
└── screenshots/
```

## Assumptions
- CSV files are supported.
- Priority, category, and resolution time are required.
- Resolution time must be numeric and non-negative.
- Invalid records are excluded from analytics.
- Original uploaded columns are preserved.

## Limitations
- No database persistence.
- No authentication.
- No multi-user access control.
