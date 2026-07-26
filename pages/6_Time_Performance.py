import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, check_empty_data
from utils.filters import apply_filters
from utils.formatting import format_currency, format_number_full, format_percentage
from utils.charts import line_chart, bar_chart, heatmap_chart
from utils.styling import (
    inject_global_css, render_header, render_page_header, render_kpi_card,
)

st.set_page_config(
    page_title="Time & Performance - Coffee Shop Dashboard",
    page_icon=":clock1:",
    layout="wide",
)

inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header(
    "TIME & PERFORMANCE",
    "Temporal patterns, peak hours, and operational insights",
    "",
)

df_filtered = apply_filters(df, options, key_prefix="time")
check_empty_data(df_filtered, "Time & Performance")

hourly_txn = df_filtered.groupby("hour")["transaction_id"].nunique()
peak_hour = int(hourly_txn.idxmax()) if len(hourly_txn) > 0 else "-"

day_rev = df_filtered.groupby("day_name")["total_amount"].sum()
best_day = day_rev.idxmax() if len(day_rev) > 0 else "-"

month_rev = df_filtered.groupby(df_filtered["timestamp"].dt.to_period("M"))["total_amount"].sum()
best_month = month_rev.idxmax().strftime("%B %Y") if len(month_rev) > 0 else "-"

total_txn = df_filtered["transaction_id"].nunique()
weekend_txn = (
    df_filtered[df_filtered["is_weekend"] == True]["transaction_id"].nunique()
    if "is_weekend" in df_filtered.columns else 0
)
weekend_share = weekend_txn / total_txn * 100 if total_txn > 0 else 0

st.markdown("")
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Peak Hour", f"{peak_hour}:00" if isinstance(peak_hour, int) else "-")
with col2:
    render_kpi_card("Best Day", best_day)
with col3:
    render_kpi_card("Best Month", best_month)
with col4:
    render_kpi_card("Weekend Share", format_percentage(weekend_share))

st.markdown("")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(
        "<div class='chart-card'><h3>Transactions by Hour</h3></div>",
        unsafe_allow_html=True,
    )
    hourly = df_filtered.groupby("hour")["transaction_id"].nunique().reset_index()
    hourly.columns = ["hour", "transactions"]
    fig1 = line_chart(hourly, "hour", "transactions", title="", height=360)
    fig1.update_layout(xaxis_title="Hour", yaxis_title="Transactions")
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.markdown(
        "<div class='chart-card'><h3>Revenue by Day of Week</h3></div>",
        unsafe_allow_html=True,
    )
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    daily = df_filtered.groupby("day_name").agg(
        revenue=("total_amount", "sum"),
        transactions=("transaction_id", "nunique"),
    ).reset_index()
    daily["day_name"] = pd.Categorical(daily["day_name"], categories=day_order, ordered=True)
    daily = daily.sort_values("day_name")

    fig2 = bar_chart(daily, "day_name", "revenue", title="", height=360)
    fig2.update_layout(xaxis_title="Day", yaxis_title="Revenue ($)")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("")

st.markdown(
    "<div class='chart-card'><h3>Monthly Revenue Trend</h3>"
    "<div class='chart-subtitle'>Revenue trajectory over time</div></div>",
    unsafe_allow_html=True,
)

monthly = df_filtered.groupby(df_filtered["timestamp"].dt.to_period("M")).agg(
    revenue=("total_amount", "sum"),
    transactions=("transaction_id", "nunique"),
).reset_index()
monthly["timestamp"] = monthly["timestamp"].dt.to_timestamp()

fig3 = line_chart(monthly, "timestamp", "revenue", title="", height=340)
fig3.update_layout(xaxis_title="Month", yaxis_title="Revenue ($)")
st.plotly_chart(fig3, use_container_width=True)

st.markdown("")

st.markdown(
    "<div class='section-header'>WEEKDAY vs WEEKEND COMPARISON</div>",
    unsafe_allow_html=True,
)

if "is_weekend" in df_filtered.columns:
    weekend_data = df_filtered.groupby("is_weekend").agg(
        revenue=("total_amount", "sum"),
        transactions=("transaction_id", "nunique"),
        quantity=("quantity", "sum"),
    ).reset_index()

    days_count = (
        df_filtered.groupby("is_weekend")["timestamp"]
        .apply(lambda x: x.dt.date.nunique())
        .reset_index()
    )
    days_count.columns = ["is_weekend", "days"]

    weekend_merged = weekend_data.merge(days_count, on="is_weekend")
    weekend_merged["avg_daily_revenue"] = weekend_merged["revenue"] / weekend_merged["days"]
    weekend_merged["label"] = weekend_merged["is_weekend"].map({True: "Weekend", False: "Weekday"})

    col_we1, col_we2 = st.columns(2)
    with col_we1:
        fig4 = bar_chart(weekend_merged, "label", "revenue", title="Total Revenue: Weekday vs Weekend", height=320)
        st.plotly_chart(fig4, use_container_width=True)
    with col_we2:
        fig5 = bar_chart(weekend_merged, "label", "avg_daily_revenue", title="Avg Daily Revenue: Weekday vs Weekend", height=320)
        st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("Weekend data not available")

st.markdown("")

st.markdown(
    "<div class='chart-card'><h3>Transaction Heatmap: Hour x Day</h3>"
    "<div class='chart-subtitle'>Identify peak operating hours</div></div>",
    unsafe_allow_html=True,
)

heatmap_data = (
    df_filtered.groupby(["hour", "day_name"])["transaction_id"]
    .nunique()
    .reset_index()
)
heatmap_data.columns = ["hour", "day_name", "transactions"]

fig6 = heatmap_chart(
    heatmap_data, "hour", "day_name", "transactions",
    title="", height=400,
)
st.plotly_chart(fig6, use_container_width=True)

st.markdown("")

if not daily.empty and "is_weekend" in df_filtered.columns:
    peak_day_name = daily.loc[daily["revenue"].idxmax(), "day_name"]
    peak_day_rev = daily.loc[daily["revenue"].idxmax(), "revenue"]
    low_day_name = daily.loc[daily["revenue"].idxmin(), "day_name"]
    low_day_rev = daily.loc[daily["revenue"].idxmin(), "revenue"]

    avg_weekday = weekend_merged[weekend_merged["label"] == "Weekday"]["avg_daily_revenue"].values
    avg_weekend = weekend_merged[weekend_merged["label"] == "Weekend"]["avg_daily_revenue"].values

    col_i1, col_i2, col_i3 = st.columns(3)
    with col_i1:
        st.markdown(
            f"<div class='insight-card'><strong>Peak Hour:</strong> {peak_hour}:00 records "
            f"{int(hourly_txn.max())} transactions</div>",
            unsafe_allow_html=True,
        )
    with col_i2:
        st.markdown(
            f"<div class='insight-card'><strong>Best Day:</strong> {peak_day_name} with "
            f"{format_currency(peak_day_rev)} revenue, lowest: {low_day_name} "
            f"({format_currency(low_day_rev)})</div>",
            unsafe_allow_html=True,
        )
    with col_i3:
        if len(avg_weekday) > 0 and len(avg_weekend) > 0 and avg_weekday[0] > 0:
            weekend_lift = (avg_weekend[0] - avg_weekday[0]) / avg_weekday[0] * 100
            st.markdown(
                f"<div class='insight-card'><strong>Weekend Lift:</strong> Avg daily weekend revenue "
                f"is {format_percentage(weekend_lift)} higher than weekday</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='insight-card'><strong>Weekend Lift:</strong> Data insufficient</div>",
                unsafe_allow_html=True,
            )

st.markdown("")
col_dl1, col_dl2, _ = st.columns([2, 2, 6])
with col_dl1:
    st.download_button(
        "Download Hourly Summary",
        data=hourly.to_csv(index=False),
        file_name="hourly_summary.csv",
        mime="text/csv",
    )
with col_dl2:
    st.download_button(
        "Download Day of Week Summary",
        data=daily.to_csv(index=False),
        file_name="day_of_week_summary.csv",
        mime="text/csv",
    )
