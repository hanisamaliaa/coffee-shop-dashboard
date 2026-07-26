import streamlit as st
import pandas as pd
import os

DATA_PATH = "processed/coffee_shop_sales_featured.csv"


@st.cache_data
def load_data():
    if not os.path.exists(DATA_PATH):
        st.error(
            f"File dataset tidak ditemukan: `{DATA_PATH}`.\n\n"
            "Pastikan file `coffee_shop_sales_featured.csv` tersedia di folder `processed/`."
        )
        st.stop()

    try:
        df = pd.read_csv(DATA_PATH)
    except Exception as e:
        st.error(f"Gagal memuat dataset: {e}")
        st.stop()

    date_cols = ["timestamp"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "timestamp" in df.columns and df["timestamp"].notna().any():
        df["date"] = df["timestamp"].dt.date
        df["year"] = df["timestamp"].dt.year
        df["month_num"] = df["timestamp"].dt.month
        df["year_month"] = df["timestamp"].dt.to_period("M")

    return df


def get_filter_options(df):
    options = {}
    filter_cols = [
        "country", "city", "store_type", "product_category",
        "payment_method", "customer_age_group"
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


def apply_filters(df, options, key_prefix=""):
    st.sidebar.header("Filter")

    date_min = options.get("date_min")
    date_max = options.get("date_max")
    if date_min and date_max:
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
            key=f"{key_prefix}_date"
        )
        if len(date_range) == 2:
            df = df[
                (df["timestamp"].dt.date >= date_range[0]) &
                (df["timestamp"].dt.date <= date_range[1])
            ]

    filter_mapping = [
        ("country", "Country"),
        ("city", "City"),
        ("store_type", "Store Type"),
        ("product_category", "Product Category"),
        ("payment_method", "Payment Method"),
        ("customer_age_group", "Age Group"),
    ]

    for col, label in filter_mapping:
        if col in df.columns and options.get(col):
            vals = st.sidebar.multiselect(
                label,
                options=options[col],
                default=[],
                key=f"{key_prefix}_{col}"
            )
            if vals:
                df = df[df[col].isin(vals)]

    return df
