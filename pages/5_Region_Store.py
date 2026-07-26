import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, check_empty_data
from utils.filters import apply_filters
from utils.formatting import format_currency, format_number_full, format_percentage
from utils.charts import bar_chart, horizontal_bar, pie_chart, heatmap_chart
from utils.styling import (
    inject_global_css, render_header, render_page_header, render_kpi_card,
)

st.set_page_config(
    page_title="Region & Store - Coffee Shop Dashboard",
    page_icon=":round_pushpin:",
    layout="wide",
)

inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header(
    "REGION & STORE ANALYSIS",
    "Geographic performance, store metrics, and location insights",
    "",
)

df_filtered = apply_filters(df, options, key_prefix="region")
check_empty_data(df_filtered, "Region & Store")

best_country = (
    df_filtered.groupby("country")["total_amount"].sum().idxmax()
    if "country" in df_filtered.columns else "-"
)
best_city = (
    df_filtered.groupby("city")["total_amount"].sum().idxmax()
    if "city" in df_filtered.columns else "-"
)
best_store = (
    df_filtered.groupby("store_id")["total_amount"].sum().idxmax()
    if "store_id" in df_filtered.columns else "-"
)
best_store_type = (
    df_filtered.groupby("store_type")["total_amount"].sum().idxmax()
    if "store_type" in df_filtered.columns else "-"
)

st.markdown("")
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Best Country", best_country)
with col2:
    render_kpi_card("Best City", best_city)
with col3:
    render_kpi_card("Best Store", f"Store {best_store}")
with col4:
    render_kpi_card("Best Store Type", best_store_type)

st.markdown("")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(
        "<div class='chart-card'><h3>Revenue by Country</h3></div>",
        unsafe_allow_html=True,
    )
    country_rev = (
        df_filtered.groupby("country")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig1 = bar_chart(country_rev, "country", "total_amount", title="", height=360)
    fig1.update_layout(yaxis_title="Revenue ($)")
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.markdown(
        "<div class='chart-card'><h3>Revenue by City</h3></div>",
        unsafe_allow_html=True,
    )
    city_rev = (
        df_filtered.groupby("city")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig2 = bar_chart(city_rev, "city", "total_amount", title="", height=360)
    fig2.update_layout(yaxis_title="Revenue ($)")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("")

col_c, col_d = st.columns(2)
with col_c:
    st.markdown(
        "<div class='chart-card'><h3>Top 10 Stores by Revenue</h3></div>",
        unsafe_allow_html=True,
    )
    store_rev = (
        df_filtered.groupby("store_id")["total_amount"]
        .sum()
        .reset_index()
        .nlargest(10, "total_amount")
    )
    fig3 = horizontal_bar(store_rev, "total_amount", "store_id", title="", top_n=10, height=380)
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.markdown(
        "<div class='chart-card'><h3>Bottom 10 Stores by Revenue</h3></div>",
        unsafe_allow_html=True,
    )
    store_bot = (
        df_filtered.groupby("store_id")["total_amount"]
        .sum()
        .reset_index()
        .nsmallest(10, "total_amount")
    )
    fig4 = horizontal_bar(store_bot, "total_amount", "store_id", title="", top_n=10, height=380)
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("")

st.markdown(
    "<div class='section-header'>PERFORMANCE BY STORE TYPE</div>",
    unsafe_allow_html=True,
)

store_type_stats = df_filtered.groupby("store_type").agg(
    revenue=("total_amount", "sum"),
    transactions=("transaction_id", "nunique"),
    avg_transaction=("total_amount", "mean"),
    n_stores=("store_id", "nunique"),
).reset_index()

fig5 = bar_chart(store_type_stats, "store_type", "revenue", title="", height=340)
fig5.update_layout(yaxis_title="Revenue ($)")
st.plotly_chart(fig5, use_container_width=True)

if len(store_type_stats) > 1:
    col_st1, col_st2 = st.columns(2)
    with col_st1:
        fig5b = bar_chart(store_type_stats, "store_type", "transactions", title="Transactions by Store Type", height=300)
        st.plotly_chart(fig5b, use_container_width=True)
    with col_st2:
        fig5c = bar_chart(store_type_stats, "store_type", "avg_transaction", title="Avg Transaction by Store Type", height=300)
        st.plotly_chart(fig5c, use_container_width=True)

st.markdown("")

st.markdown(
    "<div class='section-header'>HEATMAP: CITY x PRODUCT CATEGORY</div>",
    unsafe_allow_html=True,
)

if "city" in df_filtered.columns and "product_category" in df_filtered.columns:
    heatmap_data = (
        df_filtered.groupby(["city", "product_category"])["total_amount"]
        .sum()
        .reset_index()
    )
    fig6 = heatmap_chart(
        heatmap_data, "city", "product_category", "total_amount",
        title="Revenue Heatmap: City x Category", height=400,
    )
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("")

total_rev = df_filtered["total_amount"].sum()
top_city_rev = city_rev.iloc[0]["total_amount"] if not city_rev.empty else 0
top_city_pct = top_city_rev / total_rev * 100 if total_rev > 0 else 0
store_type_top = store_type_stats.loc[store_type_stats["revenue"].idxmax(), "store_type"] if not store_type_stats.empty else "-"

col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.markdown(
        f"<div class='insight-card'><strong>Top City:</strong> {city_rev.iloc[0]['city'] if not city_rev.empty else '-'} "
        f"with {format_currency(top_city_rev)} ({format_percentage(top_city_pct)})</div>",
        unsafe_allow_html=True,
    )
with col_i2:
    st.markdown(
        f"<div class='insight-card'><strong>Best Store Type:</strong> {store_type_top} "
        f"generates the highest revenue</div>",
        unsafe_allow_html=True,
    )
with col_i3:
    st.markdown(
        f"<div class='insight-card'><strong>Store Count:</strong> "
        f"{df_filtered['store_id'].nunique()} unique stores across "
        f"{df_filtered['city'].nunique()} cities</div>",
        unsafe_allow_html=True,
    )

st.markdown("")
col_dl1, col_dl2, _ = st.columns([2, 2, 6])
with col_dl1:
    st.download_button(
        "Download Store Summary",
        data=store_rev.to_csv(index=False),
        file_name="store_summary.csv",
        mime="text/csv",
    )
with col_dl2:
    st.download_button(
        "Download City Summary",
        data=city_rev.to_csv(index=False),
        file_name="city_summary.csv",
        mime="text/csv",
    )
