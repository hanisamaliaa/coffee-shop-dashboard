import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, check_empty_data
from utils.filters import apply_filters
from utils.formatting import (
    format_currency, format_number, format_number_full,
    format_percentage, format_date_range,
)
from utils.metrics import calc_kpi, calc_delta, calc_monthly_data
from utils.charts import line_chart, bar_chart, horizontal_bar, dual_axis_chart
from utils.styling import (
    inject_global_css, render_header, render_page_header, render_kpi_card,
)

st.set_page_config(
    page_title="Sales - Coffee Shop Dashboard",
    page_icon=":moneybag:",
    layout="wide",
)

inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header(
    "SALES ANALYSIS",
    "Revenue trends, transaction patterns, and category performance",
    format_date_range(options.get("date_min"), options.get("date_max")),
)

df_filtered = apply_filters(df, options, key_prefix="sales")
check_empty_data(df_filtered, "Sales")

kpi = calc_kpi(df_filtered)
delta = calc_delta(df_filtered)

st.markdown("")
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Total Revenue", format_currency(kpi["total_revenue"]), delta.get("revenue"))
with col2:
    render_kpi_card("Total Transactions", format_number_full(kpi["total_transactions"]), delta.get("transactions"))
with col3:
    render_kpi_card("Total Quantity", format_number_full(kpi["total_quantity"]), delta.get("quantity"))
with col4:
    render_kpi_card("Avg Transaction Value", format_currency(kpi["avg_transaction"]), delta.get("avg_txn"))

st.markdown("")

st.markdown(
    "<div class='section-header'>REVENUE & TRANSACTION TREND</div>",
    unsafe_allow_html=True,
)

monthly = calc_monthly_data(df_filtered)

col_a, col_b = st.columns(2)
with col_a:
    if not monthly.empty:
        fig_rev = line_chart(monthly, "timestamp", "revenue", title="Monthly Revenue", height=360)
        fig_rev.update_layout(yaxis_title="Revenue ($)")
        st.plotly_chart(fig_rev, use_container_width=True)

        top_m = monthly.loc[monthly["revenue"].idxmax()]
        bot_m = monthly.loc[monthly["revenue"].idxmin()]
        growth = (
            (monthly.iloc[-1]["revenue"] - monthly.iloc[0]["revenue"])
            / monthly.iloc[0]["revenue"] * 100
            if len(monthly) > 1 and monthly.iloc[0]["revenue"] > 0 else 0
        )
        st.markdown(
            f"<div class='insight-card'>"
            f"<strong>Peak:</strong> {top_m['timestamp'].strftime('%B %Y')} ({format_currency(top_m['revenue'])}) &nbsp;|&nbsp; "
            f"<strong>Lowest:</strong> {bot_m['timestamp'].strftime('%B %Y')} ({format_currency(bot_m['revenue'])}) &nbsp;|&nbsp; "
            f"<strong>Growth:</strong> {growth:+.1f}%</div>",
            unsafe_allow_html=True,
        )

with col_b:
    if not monthly.empty:
        fig_txn = line_chart(monthly, "timestamp", "transactions", title="Monthly Transactions", height=360)
        fig_txn.update_layout(yaxis_title="Transactions")
        st.plotly_chart(fig_txn, use_container_width=True)

st.markdown("")

st.markdown(
    "<div class='section-header'>REVENUE BREAKDOWN</div>",
    unsafe_allow_html=True,
)

col_c, col_d = st.columns(2)
with col_c:
    cat_rev = (
        df_filtered.groupby("product_category")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig_cat = bar_chart(cat_rev, "product_category", "total_amount", title="Revenue by Category", height=360)
    fig_cat.update_layout(yaxis_title="Revenue ($)")
    st.plotly_chart(fig_cat, use_container_width=True)

with col_d:
    pay_rev = (
        df_filtered.groupby("payment_method")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig_pay = bar_chart(pay_rev, "payment_method", "total_amount", title="Revenue by Payment Method", height=360)
    fig_pay.update_layout(yaxis_title="Revenue($)")
    st.plotly_chart(fig_pay, use_container_width=True)

st.markdown("")

st.markdown(
    "<div class='section-header'>TOP PRODUCTS BY REVENUE</div>",
    unsafe_allow_html=True,
)

top_products = (
    df_filtered.groupby("product_name")
    .agg(
        revenue=("total_amount", "sum"),
        quantity=("quantity", "sum"),
        transactions=("transaction_id", "nunique"),
    )
    .reset_index()
    .nlargest(10, "revenue")
)

fig_top = horizontal_bar(
    top_products, "revenue", "product_name",
    title="Top 10 Products by Revenue", top_n=10, height=420,
)
fig_top.update_layout(xaxis_title="Revenue ($)")
st.plotly_chart(fig_top, use_container_width=True)

st.markdown("")

total_rev = df_filtered["total_amount"].sum()
cat_top = cat_rev.iloc[0]["product_category"]
cat_bot = cat_rev.iloc[-1]["product_category"]
cat_top_pct = cat_rev.iloc[0]["total_amount"] / total_rev * 100

col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.markdown(
        f"<div class='insight-card'><strong>Dominant Category:</strong> {cat_top} contributes "
        f"{format_currency(cat_rev.iloc[0]['total_amount'])} ({format_percentage(cat_top_pct)})</div>",
        unsafe_allow_html=True,
    )
with col_i2:
    st.markdown(
        f"<div class='insight-card'><strong>Weakest Category:</strong> {cat_bot} at "
        f"{format_currency(cat_rev.iloc[-1]['total_amount'])}</div>",
        unsafe_allow_html=True,
    )
with col_i3:
    st.markdown(
        f"<div class='insight-card'><strong>Growth:</strong> Revenue changed {growth:+.1f}% from first to last month</div>",
        unsafe_allow_html=True,
    )

st.markdown("")
col_dl1, col_dl2, _ = st.columns([2, 2, 6])
with col_dl1:
    if not monthly.empty:
        st.download_button(
            "Download Monthly Summary",
            data=monthly.to_csv(index=False),
            file_name="monthly_sales_summary.csv",
            mime="text/csv",
        )
with col_dl2:
    st.download_button(
        "Download Category Summary",
        data=cat_rev.to_csv(index=False),
        file_name="category_summary.csv",
        mime="text/csv",
    )
