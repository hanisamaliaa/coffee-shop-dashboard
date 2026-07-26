import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, apply_filters
from utils.formatting import format_currency, format_number, format_percentage, format_date_range
from utils.charts import line_chart, bar_chart, pie_chart

st.set_page_config(
    page_title="Executive Summary - Coffee Shop Dashboard",
    page_icon=":coffee:",
    layout="wide"
)
st.title(":house: Executive Summary")
st.caption("Kondisi bisnis secara keseluruhan dalam satu tampilan")

df = load_data()
options = get_filter_options(df)
df_filtered = apply_filters(df, options, key_prefix="exec")

if df_filtered.empty:
    st.warning("Data kosong setelah filter diterapkan. Silakan ubah filter.")
    st.stop()

st.markdown("---")

col_date1, col_date2 = st.columns(2)
with col_date1:
    st.caption(
        f"Date range: {format_date_range(df_filtered['timestamp'].min(), df_filtered['timestamp'].max())}"
    )
with col_date2:
    st.caption(f"Total records: {len(df_filtered):,}")

st.markdown("## Key Performance Indicators")

total_revenue = df_filtered["total_amount"].sum()
total_transactions = df_filtered["transaction_id"].nunique()
avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
best_product = (
    df_filtered.groupby("product_name")["total_amount"]
    .sum()
    .idxmax()
    if len(df_filtered) > 0
    else "-"
)

prev_month_cutoff = df_filtered["timestamp"].max() - pd.DateOffset(months=1)
df_prev = df[
    (df["timestamp"] >= df_filtered["timestamp"].min()) &
    (df["timestamp"] < prev_month_cutoff)
]
df_curr = df_filtered[df_filtered["timestamp"] >= prev_month_cutoff]

rev_curr = df_curr["total_amount"].sum()
rev_prev = df_prev["total_amount"].sum()
delta_rev = ((rev_curr - rev_prev) / rev_prev * 100) if rev_prev > 0 else None

txn_curr = df_curr["transaction_id"].nunique()
txn_prev = df_prev["transaction_id"].nunique()
delta_txn = ((txn_curr - txn_prev) / txn_prev * 100) if txn_prev > 0 else None

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        "Total Revenue",
        format_currency(total_revenue),
        delta=f"{delta_rev:.1f}%" if delta_rev is not None else None,
    )
with kpi2:
    st.metric(
        "Total Transactions",
        format_number(total_transactions),
        delta=f"{delta_txn:.1f}%" if delta_txn is not None else None,
    )
with kpi3:
    st.metric("Average Transaction Value", format_currency(avg_transaction))
with kpi4:
    display_name = best_product if len(best_product) <= 25 else best_product[:22] + "..."
    st.metric("Best-Selling Product", display_name)

st.markdown("---")

col_main, col_support = st.columns([2, 1])

with col_main:
    st.subheader("Revenue & Transaction Trend")
    monthly = df_filtered.groupby(df_filtered["timestamp"].dt.to_period("M")).agg(
        revenue=("total_amount", "sum"),
        transactions=("transaction_id", "nunique"),
    ).reset_index()
    monthly["timestamp"] = monthly["timestamp"].dt.to_timestamp()

    fig1 = line_chart(monthly, "timestamp", "revenue", title="Monthly Revenue Trend")
    fig1.update_layout(xaxis_title="Month", yaxis_title="Revenue ($)", height=380)
    st.plotly_chart(fig1, use_container_width=True)

with col_support:
    st.subheader("Revenue by Category")
    cat_rev = (
        df_filtered.groupby("product_category")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig2 = pie_chart(
        cat_rev, "product_category", "total_amount", title="Category Contribution"
    )
    fig2.update_layout(height=380)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

st.subheader("Key Insights")

top_month = monthly.loc[monthly["revenue"].idxmax()]
bottom_month = monthly.loc[monthly["revenue"].idxmin()]
top_country = (
    df_filtered.groupby("country")["total_amount"].sum().idxmax()
    if "country" in df_filtered.columns
    else "-"
)
top_country_rev = (
    df_filtered.groupby("country")["total_amount"].sum().max()
    if "country" in df_filtered.columns
    else 0
)

col_i1, col_i2, col_i3 = st.columns(3)

with col_i1:
    st.info(
        f"**Peak Revenue Month**: {top_month['timestamp'].strftime('%B %Y')} "
        f"dengan {format_currency(top_month['revenue'])}"
    )

with col_i2:
    st.info(
        f"**Lowest Revenue Month**: {bottom_month['timestamp'].strftime('%B %Y')} "
        f"dengan {format_currency(bottom_month['revenue'])}"
    )

with col_i3:
    st.info(
        f"**Top Performing Country**: {top_country} - "
        f"{format_currency(top_country_rev)}"
    )

st.markdown("## Recommended Actions")

col_a1, col_a2, col_a3 = st.columns(3)

with col_a1:
    st.warning(
        f"**1. Investigasi Penurunan di {bottom_month['timestamp'].strftime('%B')}**\n\n"
        f"Revenue turun ke {format_currency(bottom_month['revenue'])}. "
        f"Evaluasi faktor musiman, promosi, atau kondisi eksternal."
    )

with col_a2:
    top_cat_name = cat_rev.iloc[0]["product_category"]
    top_cat_rev = cat_rev.iloc[0]["total_amount"]
    st.warning(
        f"**2. Optimasi Kategori Terlaris**\n\n"
        f"Kategori {top_cat_name} mendominasi dengan {format_currency(top_cat_rev)}. "
        f"Pertahankan kualitas dan eksplorasi varian baru."
    )

with col_a3:
    st.warning(
        f"**3. Perluas ke {top_country}**\n\n"
        f"{top_country} menunjukkan performa terbaik. "
        f"Pertimbangkan ekspansi atau peningkatan kapasitas."
    )

st.markdown("---")

st.subheader("Download Data")
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.download_button(
        "Download Filtered Data (CSV)",
        data=df_filtered.to_csv(index=False),
        file_name="executive_summary_filtered.csv",
        mime="text/csv",
    )
with col_dl2:
    st.download_button(
        "Download Monthly Summary (CSV)",
        data=monthly.to_csv(index=False),
        file_name="monthly_summary.csv",
        mime="text/csv",
    )
