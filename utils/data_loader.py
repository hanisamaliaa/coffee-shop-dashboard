import streamlit as st
import pandas as pd
import os

DATA_SOURCES = [
    "processed/coffee_shop_sales_featured.csv",
    "processed/coffee_shop_sales_clean.csv",
    "coffee_shop_sales.csv",
    "data/coffee_shop_sales.csv",
]


@st.cache_data
def load_data():
    loaded_path = None
    for path in DATA_SOURCES:
        if os.path.exists(path):
            loaded_path = path
            break

    if loaded_path is None:
        st.error(
            "Dataset not found. Please ensure one of the following files exists:\n"
            + "\n".join(f"- `{p}`" for p in DATA_SOURCES)
        )
        st.stop()

    try:
        df = pd.read_csv(loaded_path)
    except Exception as e:
        st.error(f"Failed to load dataset: {e}")
        st.stop()

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    if "timestamp" in df.columns and df["timestamp"].notna().any():
        df["date"] = df["timestamp"].dt.date
        df["year"] = df["timestamp"].dt.year
        df["month_num"] = df["timestamp"].dt.month
        df["year_month"] = df["timestamp"].dt.to_period("M")

    required_cols = [
        "transaction_id", "total_amount", "quantity", "product_name",
        "product_category", "timestamp",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {', '.join(missing)}")
        st.stop()

    return df


def get_filter_options(df):
    options = {}
    filter_cols = [
        "country", "city", "store_type", "product_category",
        "payment_method", "customer_age_group", "customer_gender",
    ]
    for col in filter_cols:
        if col in df.columns:
            options[col] = sorted(df[col].dropna().unique().tolist())
        else:
            options[col] = []

    if "timestamp" in df.columns and df["timestamp"].notna().any():
        options["date_min"] = df["timestamp"].min().date()
        options["date_max"] = df["timestamp"].max().date()
    else:
        options["date_min"] = None
        options["date_max"] = None

    return options


def check_empty_data(df, page_name=""):
    if df.empty:
        st.warning(
            f"Data is empty after filters are applied on **{page_name}**. "
            "Please adjust filters in the sidebar."
        )
        st.stop()
