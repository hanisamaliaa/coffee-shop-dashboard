import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, apply_filters, check_empty_data
from utils.formatting import format_currency, format_number, format_percentage
from utils.charts import horizontal_bar, bar_chart, pie_chart

st.set_page_config(
    page_title="Customer - Coffee Shop Dashboard",
    page_icon=":busts_in_silhouette:",
    layout="wide"
)
st.title(":busts_in_silhouette: Customer Analysis")
st.caption("Segmen pelanggan, perilaku transaksi, dan loyalitas")

df = load_data()
options = get_filter_options(df)
df_filtered = apply_filters(df, options, key_prefix="cust")
check_empty_data(df_filtered, "Customer")

st.markdown("## KPI Overview")

unique_customers = df_filtered["customer_id"].nunique()
total_txn = df_filtered["transaction_id"].nunique()
cust_txn = df_filtered.groupby("customer_id")["transaction_id"].nunique().reset_index()
repeat_customers = (cust_txn["transaction_id"] > 1).sum()
repeat_rate = repeat_customers / unique_customers * 100 if unique_customers > 0 else 0
avg_rev_per_cust = (
    df_filtered.groupby("customer_id")["total_amount"].sum().mean()
    if unique_customers > 0
    else 0
)
top_cust = (
    df_filtered.groupby("customer_id")["total_amount"].sum().idxmax()
    if unique_customers > 0
    else "-"
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Unique Customers", format_number(unique_customers))
c2.metric("Repeat Customer Rate", format_percentage(repeat_rate))
c3.metric("Avg Revenue / Customer", format_currency(avg_rev_per_cust))
c4.metric("Highest-Value Customer", str(top_cust)[:15])

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Top 10 Customers by Total Revenue")
    cust_rev = (
        df_filtered.groupby("customer_id")
        .agg(
            total_revenue=("total_amount", "sum"),
            transactions=("transaction_id", "nunique"),
            avg_transaction=("total_amount", "mean"),
        )
        .reset_index()
        .nlargest(10, "total_revenue")
    )

    fig1 = horizontal_bar(
        cust_rev, "total_revenue", "customer_id",
        title="Top 10 Customers by Revenue", top_n=10
    )
    fig1.update_layout(height=380)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Customer Frequency Segment")
    if "customer_segment" in df_filtered.columns:
        seg_stats = df_filtered.groupby("customer_segment").agg(
            n_customers=("customer_id", "nunique"),
            revenue=("total_amount", "sum"),
        ).reset_index()
        seg_stats = seg_stats.sort_values("revenue", ascending=False)

        fig2 = bar_chart(
            seg_stats, "customer_segment", "revenue",
            title="Revenue by Customer Segment"
        )
        fig2.update_layout(height=380, xaxis_title="Segment", yaxis_title="Revenue ($)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Kolom customer_segment tidak tersedia")

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    st.subheader("Revenue per Age Group")
    age_rev = (
        df_filtered.groupby("customer_age_group")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig3 = bar_chart(
        age_rev, "customer_age_group", "total_amount",
        title="Total Revenue by Age Group"
    )
    fig3.update_layout(height=340, xaxis_title="Age Group", yaxis_title="Revenue ($)")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Avg Transaction Value per Age Group")
    age_avg = df_filtered.groupby("customer_age_group").agg(
        avg_transaction=("total_amount", "mean"),
        count=("transaction_id", "nunique"),
    ).reset_index()
    fig4 = bar_chart(
        age_avg, "customer_age_group", "avg_transaction",
        title="Avg Transaction Value by Age Group"
    )
    fig4.update_layout(height=340, xaxis_title="Age Group", yaxis_title="Avg Transaction ($)")
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

st.subheader("Key Insights")

top_age = age_rev.iloc[0]["customer_age_group"]
top_age_rev = age_rev.iloc[0]["total_amount"]
top_cust_rev = cust_rev.iloc[0]["total_revenue"]
loyalty_share = (
    df_filtered["loyalty_member"].value_counts(normalize=True).get(True, 0) * 100
    if "loyalty_member" in df_filtered.columns
    else 0
)
total_rev = df_filtered["total_amount"].sum()
top_age_pct = top_age_rev / total_rev * 100

col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.info(
        f"**Top Age Group**: {top_age} berkontribusi "
        f"{format_currency(top_age_rev)} ({format_percentage(top_age_pct)}) dari total revenue"
    )
with col_i2:
    st.info(
        f"**Repeat Rate**: {format_percentage(repeat_rate)} pelanggan "
        f"melakukan transaksi lebih dari sekali"
    )
with col_i3:
    st.info(
        f"**Loyalty Members**: {format_percentage(loyalty_share)} pelanggan adalah anggota loyalitas"
    )

st.subheader("Recommended Actions")
col_a1, col_a2 = st.columns(2)
with col_a1:
    st.warning(
        f"**1. Program Loyalitas untuk {top_age}**\n\n"
        f"Age group {top_age} adalah segmen terbesar. "
        f"Tingkatkan engagement dengan reward program."
    )
with col_a2:
    st.warning(
        f"**2. Strategi Retensi Repeat Customer**\n\n"
        f"Dengan {format_percentage(repeat_rate)} repeat rate, "
        f"investasi di retention lebih efektif dari akuisisi baru."
    )

st.markdown("---")
st.subheader("Download Data")
st.download_button(
    "Download Customer Summary (CSV)",
    data=cust_rev.to_csv(index=False),
    file_name="customer_summary.csv",
    mime="text/csv",
)
