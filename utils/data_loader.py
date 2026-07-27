import os

import pandas as pd
import streamlit as st

from utils.business_logic import ensure_features

DATA_SOURCES = [
    "processed/coffee_shop_sales_featured.csv",
    "processed/coffee_shop_sales_clean.csv",
    "data/coffee_shop_sales.csv",
    "coffee_shop_sales.csv",
]

REQUIRED_COLS = ["transaction_id", "total_amount", "quantity",
                 "product_name", "product_category", "timestamp"]


@st.cache_data(show_spinner="Memuat data...")
def load_data():
    path = next((p for p in DATA_SOURCES if os.path.exists(p)), None)
    if path is None:
        st.error("Dataset tidak ditemukan. Pastikan salah satu file ini ada:\n"
                 + "\n".join(f"- `{p}`" for p in DATA_SOURCES))
        st.stop()

    try:
        df = pd.read_csv(path)
    except Exception as e:
        st.error(f"Gagal memuat dataset: {e}")
        st.stop()

    kurang = [c for c in REQUIRED_COLS if c not in df.columns]
    if kurang:
        st.error(f"Kolom wajib tidak ada: {', '.join(kurang)}")
        st.stop()

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Kalau CSV yang dimuat versi lama tanpa fitur turunan, hitung sekarang.
    # Idempoten — kolom yang sudah ada tidak dihitung ulang.
    try:
        df = ensure_features(df)
    except Exception as e:
        st.warning(f"Sebagian fitur turunan gagal dibuat ({e}). "
                   "Jalankan `python scripts/build_processed.py` untuk memperbaiki.")

    df["year_month"] = df["timestamp"].dt.to_period("M")
    return df


def has_profit(df):
    """Halaman profit memerlukan kolom estimasi laba."""
    return "est_profit" in df.columns and df["est_profit"].notna().any()


def get_filter_options(df):
    options = {}
    for col in ["country", "city", "store_type", "product_category",
                "payment_method", "customer_age_group", "customer_gender"]:
        options[col] = sorted(df[col].dropna().unique().tolist()) if col in df.columns else []

    if df["timestamp"].notna().any():
        options["date_min"] = df["timestamp"].min().date()
        options["date_max"] = df["timestamp"].max().date()
    else:
        options["date_min"] = options["date_max"] = None

    return options


def check_empty_data(df, page_name=""):
    if df.empty:
        st.warning(
            f"Tidak ada data setelah filter diterapkan pada **{page_name}**. "
            "Silakan ubah filter di sidebar.")
        st.stop()
