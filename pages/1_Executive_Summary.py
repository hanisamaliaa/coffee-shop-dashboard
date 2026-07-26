import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, apply_filters, check_empty_data
from utils.formatting import format_currency, format_number, format_percentage, format_date_range, format_delta
from utils.charts import line_chart, pie_chart, dual_axis_chart

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
check_empty_data(df_filtered, "Executive Summary")

st.caption(
    f"Periode: {format_date_range(df_filtered['timestamp'].min(), df_filtered['timestamp'].max())} | "
    f"Total: {len(df_filtered):,} transaksi"
)

st.markdown("## Key Performance Indicators")

total_revenue = df_filtered["total_amount"].sum()
total_transactions = df_filtered["transaction_id"].nunique()
avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
total_quantity = int(df_filtered["quantity"].sum())

best_product = (
    df_filtered.groupby("product_name")["total_amount"]
    .sum()
    .idxmax()
    if len(df_filtered) > 0
    else "-"
)

prev_month_cutoff = df_filtered["timestamp"].max() - pd.DateOffset(months=1)
df_curr = df_filtered[df_filtered["timestamp"] >= prev_month_cutoff]
df_prev = df_filtered[df_filtered["timestamp"] < prev_month_cutoff]

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
        delta=format_delta(delta_rev),
    )
with kpi2:
    st.metric(
        "Total Transactions",
        format_number(total_transactions),
        delta=format_delta(delta_txn),
    )
with kpi3:
    st.metric("Average Transaction Value", format_currency(avg_transaction))
with kpi4:
    display_product = best_product if len(best_product) <= 25 else best_product[:22] + "..."
    st.metric("Best-Selling Product", display_product)

st.markdown("---")

col_main, col_support = st.columns([2, 1])

with col_main:
    st.subheader("Revenue & Transaction Trend (Monthly)")
    monthly = df_filtered.groupby(df_filtered["timestamp"].dt.to_period("M")).agg(
        revenue=("total_amount", "sum"),
        transactions=("transaction_id", "nunique"),
    ).reset_index()
    monthly["timestamp"] = monthly["timestamp"].dt.to_timestamp()

    fig1 = dual_axis_chart(
        monthly, "timestamp", "revenue", "transactions",
        title="Monthly Revenue (Bar) & Transactions (Line)",
        y1_label="Revenue ($)", y2_label="Transactions"
    )
    fig1.update_layout(height=380)
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
total_rev = df_filtered["total_amount"].sum()
top_country_pct = top_country_rev / total_rev * 100

col_i1, col_i2, col_i3 = st.columns(3)

with col_i1:
    rev_range = top_month["revenue"] - bottom_month["revenue"]
    st.info(
        f"**Revenue Gap Bulanan**: {format_currency(rev_range)} antara "
        f"bulan tertinggi ({top_month['timestamp'].strftime('%B')}) dan "
        f"terendah ({bottom_month['timestamp'].strftime('%B')})"
    )

with col_i2:
    st.info(
        f"**Top Country**: {top_country} berkontribusi "
        f"{format_currency(top_country_rev)} ({format_percentage(top_country_pct)})"
    )

with col_i3:
    avg_txn_all = total_revenue / total_transactions if total_transactions > 0 else 0
    st.info(
        f"**Average Transaction**: {format_currency(avg_txn_all)} per transaksi "
        f"dari {format_number(total_transactions)} total transaksi"
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
    top_cat_pct = top_cat_rev / total_rev * 100
    st.warning(
        f"**2. Optimasi Kategori {top_cat_name}**\n\n"
        f"Kategori ini berkontribusi {format_percentage(top_cat_pct)} dari total revenue. "
        f"Pertahankan kualitas dan eksplorasi varian baru."
    )

with col_a3:
    st.warning(
        f"**3. Perluas ke {top_country}**\n\n"
        f"{top_country} menunjukkan performa terbaik dengan "
        f"{format_currency(top_country_rev)}. "
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
