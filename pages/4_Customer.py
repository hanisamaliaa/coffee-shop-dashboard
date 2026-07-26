import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, check_empty_data
from utils.filters import apply_filters
from utils.formatting import format_currency, format_number_full, format_percentage
from utils.charts import horizontal_bar, bar_chart
from utils.styling import (
    inject_global_css, render_header, render_page_header, render_kpi_card,
)

st.set_page_config(
    page_title="Customer - Coffee Shop Dashboard",
    page_icon=":busts_in_silhouette:",
    layout="wide",
)

inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header(
    "CUSTOMER ANALYSIS",
    "Customer segments, demographics, and transaction behavior",
    "",
)

df_filtered = apply_filters(df, options, key_prefix="cust")
check_empty_data(df_filtered, "Customer")

unique_customers = df_filtered["customer_id"].nunique()
total_txn = df_filtered["transaction_id"].nunique()
cust_txn = df_filtered.groupby("customer_id")["transaction_id"].nunique().reset_index()
repeat_customers = (cust_txn["transaction_id"] > 1).sum()
repeat_rate = repeat_customers / unique_customers * 100 if unique_customers > 0 else 0
avg_rev_per_cust = (
    df_filtered.groupby("customer_id")["total_amount"].sum().mean()
    if unique_customers > 0 else 0
)

st.markdown("")
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Unique Customers", format_number_full(unique_customers))
with col2:
    render_kpi_card("Repeat Customer Rate", format_percentage(repeat_rate))
with col3:
    render_kpi_card("Avg Revenue/Customer", format_currency(avg_rev_per_cust))
with col4:
    total_rev = df_filtered["total_amount"].sum()
    cust_contribution = total_rev / unique_customers if unique_customers > 0 else 0
    render_kpi_card("Revenue per Customer", format_currency(cust_contribution))

st.markdown("")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(
        "<div class='chart-card'><h3>Top 10 Customers by Revenue</h3></div>",
        unsafe_allow_html=True,
    )
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
    fig1 = horizontal_bar(cust_rev, "total_revenue", "customer_id", title="", top_n=10, height=380)
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.markdown(
        "<div class='chart-card'><h3>Revenue by Customer Segment</h3></div>",
        unsafe_allow_html=True,
    )
    if "customer_segment" in df_filtered.columns:
        seg_stats = df_filtered.groupby("customer_segment").agg(
            n_customers=("customer_id", "nunique"),
            revenue=("total_amount", "sum"),
        ).reset_index().sort_values("revenue", ascending=False)
        fig2 = bar_chart(seg_stats, "customer_segment", "revenue", title="", height=380)
        fig2.update_layout(xaxis_title="Segment", yaxis_title="Revenue ($)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Customer segment data not available")

st.markdown("")

col_c, col_d = st.columns(2)
with col_c:
    st.markdown(
        "<div class='chart-card'><h3>Revenue by Age Group</h3></div>",
        unsafe_allow_html=True,
    )
    age_rev = (
        df_filtered.groupby("customer_age_group")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig3 = bar_chart(age_rev, "customer_age_group", "total_amount", title="", height=360)
    fig3.update_layout(xaxis_title="Age Group", yaxis_title="Revenue ($)")
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.markdown(
        "<div class='chart-card'><h3>Avg Transaction Value by Age Group</h3></div>",
        unsafe_allow_html=True,
    )
    age_avg = df_filtered.groupby("customer_age_group").agg(
        avg_transaction=("total_amount", "mean"),
    ).reset_index()
    fig4 = bar_chart(age_avg, "customer_age_group", "avg_transaction", title="", height=360)
    fig4.update_layout(xaxis_title="Age Group", yaxis_title="Avg Transaction ($)")
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("")

col_e, col_f = st.columns(2)
with col_e:
    if "customer_gender" in df_filtered.columns:
        st.markdown(
            "<div class='chart-card'><h3>Revenue by Gender</h3></div>",
            unsafe_allow_html=True,
        )
        gender_rev = (
            df_filtered.groupby("customer_gender")["total_amount"]
            .sum()
            .reset_index()
            .sort_values("total_amount", ascending=False)
        )
        fig5 = bar_chart(gender_rev, "customer_gender", "total_amount", title="", height=340)
        fig5.update_layout(xaxis_title="Gender", yaxis_title="Revenue ($)")
        st.plotly_chart(fig5, use_container_width=True)

with col_f:
    if "loyalty_member" in df_filtered.columns:
        st.markdown(
            "<div class='chart-card'><h3>Loyalty Member Distribution</h3></div>",
            unsafe_allow_html=True,
        )
        loyalty_rev = (
            df_filtered.groupby("loyalty_member")["total_amount"]
            .sum()
            .reset_index()
        )
        loyalty_rev["label"] = loyalty_rev["loyalty_member"].map({True: "Loyalty Member", False: "Non-Member"})
        fig6 = bar_chart(loyalty_rev, "label", "total_amount", title="", height=340)
        st.plotly_chart(fig6, use_container_width=True)

st.markdown("")

top_age = age_rev.iloc[0]["customer_age_group"]
top_age_rev = age_rev.iloc[0]["total_amount"]
top_age_pct = top_age_rev / total_rev * 100
loyalty_share = (
    df_filtered["loyalty_member"].value_counts(normalize=True).get(True, 0) * 100
    if "loyalty_member" in df_filtered.columns else 0
)

col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.markdown(
        f"<div class='insight-card'><strong>Top Age Group:</strong> {top_age} contributes "
        f"{format_currency(top_age_rev)} ({format_percentage(top_age_pct)})</div>",
        unsafe_allow_html=True,
    )
with col_i2:
    st.markdown(
        f"<div class='insight-card'><strong>Repeat Rate:</strong> {format_percentage(repeat_rate)} customers "
        f"made more than one transaction</div>",
        unsafe_allow_html=True,
    )
with col_i3:
    st.markdown(
        f"<div class='insight-card'><strong>Loyalty Members:</strong> {format_percentage(loyalty_share)} "
        f"of customers are loyalty program members</div>",
        unsafe_allow_html=True,
    )

st.markdown("")
st.download_button(
    "Download Customer Summary",
    data=cust_rev.to_csv(index=False),
    file_name="customer_summary.csv",
    mime="text/csv",
)
