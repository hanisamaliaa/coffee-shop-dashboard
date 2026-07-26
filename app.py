import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.data_loader import load_data
from utils.formatting import format_currency, format_number, format_date_range

st.set_page_config(
    page_title="Coffee Shop Sales Dashboard",
    page_icon=":coffee:",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a2e;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-box {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
    }
    .page-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">:coffee: Coffee Shop Sales Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Capstone Project - Data Analysis | Interactive Business Intelligence Dashboard</p>', unsafe_allow_html=True)

st.markdown("---")

df = load_data()

col_info1, col_info2, col_info3, col_info4 = st.columns(4)
with col_info1:
    st.metric("Total Records", format_number(len(df)))
with col_info2:
    st.metric("Total Revenue", format_currency(df["total_amount"].sum()))
with col_info3:
    total_txn = df["transaction_id"].nunique() if "transaction_id" in df.columns else len(df)
    st.metric("Transactions", format_number(total_txn))
with col_info4:
    if "timestamp" in df.columns and df["timestamp"].notna().any():
        st.metric("Period", format_date_range(df["timestamp"].min(), df["timestamp"].max()))

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### :bar_chart: Dashboard Sections")
    st.markdown("""
    | Halaman | Fokus Analisis |
    |---------|----------------|
    | :house: **Executive Summary** | KPI utama & kondisi bisnis keseluruhan |
    | :moneybag: **Sales** | Tren penjualan, revenue, transaksi |
    | :package: **Product** | Performa produk & kategori |
    | :busts_in_silhouette: **Customer** | Segmen pelanggan & perilaku |
    | :round_pushpin: **Region/Store** | Performa lokasi & toko |
    | :clock1: **Time & Performance** | Pola waktu, jam, hari, & musiman |
    """)

with col2:
    st.markdown("### :information_source: Dataset Information")
    n_cols = len(df.columns)
    countries = df["country"].nunique() if "country" in df.columns else "-"
    cities = df["city"].nunique() if "city" in df.columns else "-"
    products = df["product_name"].nunique() if "product_name" in df.columns else "-"
    st.markdown(f"""
    - **Source**: Coffee Shop Sales Transaction Dataset
    - **Period**: {format_date_range(df['timestamp'].min(), df['timestamp'].max()) if 'timestamp' in df.columns else '-'}
    - **Records**: {len(df):,} transaksi
    - **Features**: {n_cols} kolom setelah feature engineering
    - **Countries**: {countries} negara
    - **Cities**: {cities} kota
    - **Products**: {products} produk
    """)

st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.markdown("### :dart: Dashboard Purpose")
    st.markdown("""
    Dashboard ini dirancang untuk menjawab pertanyaan bisnis utama:

    1. **Kondisi bisnis** - Bagaimana performa keseluruhan?
    2. **Penjualan** - Bagaimana tren dan pola penjualan?
    3. **Produk** - Produk mana yang unggul dan perlu perhatian?
    4. **Pelanggan** - Siapa target pasar dan perilaku mereka?
    5. **Lokasi** - Store dan wilayah mana yang optimal?
    6. **Waktu** - Kapan waktu terbaik untuk promosi dan operasional?
    """)

with col4:
    st.markdown("### :gear: How to Use")
    st.markdown("""
    1. Navigasi menggunakan **sidebar** atau menu di atas
    2. Gunakan **filter** di sidebar setiap halaman untuk menyaring data
    3. Filter tersedia: date range, country, city, store type, kategori, payment, age group
    4. **KPI** di bagian atas menunjukkan metrik utama
    5. **Insights** dan **Rekomendasi** tersedia di bawah setiap visualisasi
    6. Gunakan tombol **Download** untuk export data yang sudah difilter
    """)

st.info(
    "Dataset tidak menyediakan biaya perolehan (cost), sehingga profit dan margin "
    "tidak dapat dihitung secara valid. Dashboard menggunakan **revenue**, "
    "**transaction volume**, **quantity**, dan **discount behavior** sebagai "
    "indikator performa bisnis."
)

st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#888; font-size:0.85rem;'>"
    "Coffee Shop Sales Dashboard | Capstone Data Analysis 2026"
    "</p>",
    unsafe_allow_html=True
)
