import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, apply_filters, check_empty_data
from utils.formatting import format_currency, format_number, format_percentage
from utils.charts import line_chart, bar_chart, heatmap_chart

st.set_page_config(
    page_title="Time & Performance - Coffee Shop Dashboard",
    page_icon=":clock1:",
    layout="wide"
)
st.title(":clock1: Time & Performance Analysis")
st.caption("Pola waktu, jam, hari, musiman, dan rekomendasi operasional")

df = load_data()
options = get_filter_options(df)
df_filtered = apply_filters(df, options, key_prefix="time")
check_empty_data(df_filtered, "Time & Performance")

st.markdown("## KPI Overview")

hourly_txn = df_filtered.groupby("hour")["transaction_id"].nunique()
peak_hour = int(hourly_txn.idxmax()) if len(hourly_txn) > 0 else "-"

day_rev = df_filtered.groupby("day_name")["total_amount"].sum()
best_day = day_rev.idxmax() if len(day_rev) > 0 else "-"

month_rev = df_filtered.groupby(df_filtered["timestamp"].dt.to_period("M"))[
    "total_amount"
].sum()
best_month = month_rev.idxmax().strftime("%B %Y") if len(month_rev) > 0 else "-"

total_txn = df_filtered["transaction_id"].nunique()
weekend_txn = (
    df_filtered[df_filtered["is_weekend"] == True]["transaction_id"].nunique()
    if "is_weekend" in df_filtered.columns
    else 0
)
weekend_share = weekend_txn / total_txn * 100 if total_txn > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Peak Hour", f"{peak_hour}:00")
c2.metric("Best Day", best_day)
c3.metric("Best Month", best_month)
c4.metric("Weekend Share", format_percentage(weekend_share))

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Transactions by Hour")
    hourly = df_filtered.groupby("hour")["transaction_id"].nunique().reset_index()
    hourly.columns = ["hour", "transactions"]
    fig1 = line_chart(hourly, "hour", "transactions", title="Transaction Volume by Hour")
    fig1.update_layout(height=340, xaxis_title="Hour", yaxis_title="Transactions")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Revenue by Day of Week")
    day_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"
    ]
    daily = df_filtered.groupby("day_name").agg(
        revenue=("total_amount", "sum"),
        transactions=("transaction_id", "nunique"),
    ).reset_index()
    daily["day_name"] = pd.Categorical(daily["day_name"], categories=day_order, ordered=True)
    daily = daily.sort_values("day_name")

    fig2 = bar_chart(daily, "day_name", "revenue", title="Revenue by Day of Week")
    fig2.update_layout(height=340, xaxis_title="Day", yaxis_title="Revenue ($)")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Monthly Revenue Trend")
monthly = df_filtered.groupby(df_filtered["timestamp"].dt.to_period("M")).agg(
    revenue=("total_amount", "sum"),
    transactions=("transaction_id", "nunique"),
).reset_index()
monthly["timestamp"] = monthly["timestamp"].dt.to_timestamp()

fig3 = line_chart(monthly, "timestamp", "revenue", title="Monthly Revenue Trend")
fig3.update_layout(height=320, xaxis_title="Month", yaxis_title="Revenue ($)")
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

st.subheader("Weekday vs Weekend Comparison")

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
weekend_merged["avg_daily_transactions"] = (
    weekend_merged["transactions"] / weekend_merged["days"]
)
weekend_merged["label"] = weekend_merged["is_weekend"].map(
    {True: "Weekend", False: "Weekday"}
)

col_we1, col_we2 = st.columns(2)
with col_we1:
    fig4 = bar_chart(
        weekend_merged, "label", "revenue",
        title="Total Revenue: Weekday vs Weekend"
    )
    fig4.update_layout(height=300)
    st.plotly_chart(fig4, use_container_width=True)

with col_we2:
    fig5 = bar_chart(
        weekend_merged, "label", "avg_daily_revenue",
        title="Avg Daily Revenue: Weekday vs Weekend"
    )
    fig5.update_layout(height=300)
    st.plotly_chart(fig5, use_container_width=True)

st.subheader("Heatmap: Hour x Day of Week")
heatmap_data = (
    df_filtered.groupby(["hour", "day_name"])["transaction_id"]
    .nunique()
    .reset_index()
)
heatmap_data.columns = ["hour", "day_name", "transactions"]

fig6 = heatmap_chart(
    heatmap_data, "hour", "day_name", "transactions",
    title="Transaction Heatmap: Hour x Day"
)
fig6.update_layout(height=400)
st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

st.subheader("Key Insights")

peak_day_name = daily.loc[daily["revenue"].idxmax(), "day_name"]
peak_day_rev = daily.loc[daily["revenue"].idxmax(), "revenue"]
low_day_name = daily.loc[daily["revenue"].idxmin(), "day_name"]
low_day_rev = daily.loc[daily["revenue"].idxmin(), "revenue"]
avg_weekday = weekend_merged[weekend_merged["label"] == "Weekday"][
    "avg_daily_revenue"
].values[0]
avg_weekend = weekend_merged[weekend_merged["label"] == "Weekend"][
    "avg_daily_revenue"
].values[0]
weekend_lift = (
    (avg_weekend - avg_weekday) / avg_weekday * 100 if avg_weekday > 0 else 0
)

col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.info(
        f"**Peak Hour**: Jam {peak_hour}:00 mencatat {int(hourly_txn.max())} transaksi"
    )
with col_i2:
    st.info(
        f"**Best Day**: {peak_day_name} mencatat {format_currency(peak_day_rev)} revenue, "
        f"terendah: {low_day_name} ({format_currency(low_day_rev)})"
    )
with col_i3:
    st.info(
        f"**Weekend Lift**: Rata-rata revenue harian weekend {format_percentage(weekend_lift)} "
        f"dari weekday"
    )

st.subheader("Recommended Actions")
col_a1, col_a2, col_a3 = st.columns(3)
with col_a1:
    st.warning(
        f"**1. Staffing Optimal di Jam {peak_hour}:00**\n\n"
        f"Jam {peak_hour}:00 adalah puncak transaksi. Pastikan staf cukup."
    )
with col_a2:
    st.warning(
        f"**2. Promosi Hari {low_day_name}**\n\n"
        f"Hari {low_day_name} berkinerja rendah ({format_currency(low_day_rev)}). "
        f"Jalankan promosi khusus."
    )
with col_a3:
    st.warning(
        f"**3. Manfaatkan Weekend Peak**\n\n"
        f"Weekend naik {format_percentage(weekend_lift)} dari weekday. "
        f"Optimalkan stok dan jam operasional."
    )

st.markdown("---")
st.subheader("Download Data")
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.download_button(
        "Download Hourly Summary (CSV)",
        data=hourly.to_csv(index=False),
        file_name="hourly_summary.csv",
        mime="text/csv",
    )
with col_dl2:
    st.download_button(
        "Download Day of Week Summary (CSV)",
        data=daily.to_csv(index=False),
        file_name="day_of_week_summary.csv",
        mime="text/csv",
    )
