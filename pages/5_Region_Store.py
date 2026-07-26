import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, apply_filters
from utils.formatting import format_currency, format_number, format_percentage
from utils.charts import bar_chart, horizontal_bar, pie_chart, heatmap_chart

st.set_page_config(
    page_title="Region & Store - Coffee Shop Dashboard",
    page_icon=":round_pushpin:",
    layout="wide"
)
st.title(":round_pushpin: Region & Store Analysis")
st.caption("Performa negara, kota, toko, dan tipe toko")

df = load_data()
options = get_filter_options(df)
df_filtered = apply_filters(df, options, key_prefix="region")

if df_filtered.empty:
    st.warning("Data kosong setelah filter diterapkan. Silakan ubah filter.")
    st.stop()

st.markdown("## KPI Overview")

best_country = (
    df_filtered.groupby("country")["total_amount"].sum().idxmax()
    if "country" in df_filtered.columns
    else "-"
)
best_city = (
    df_filtered.groupby("city")["total_amount"].sum().idxmax()
    if "city" in df_filtered.columns
    else "-"
)
best_store = (
    df_filtered.groupby("store_id")["total_amount"].sum().idxmax()
    if "store_id" in df_filtered.columns
    else "-"
)
best_store_type = (
    df_filtered.groupby("store_type")["total_amount"].sum().idxmax()
    if "store_type" in df_filtered.columns
    else "-"
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Best Country", best_country)
c2.metric("Best City", best_city)
c3.metric("Best Store", f"Store {best_store}")
c4.metric("Best Store Type", best_store_type)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Revenue by Country")
    country_rev = (
        df_filtered.groupby("country")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig1 = bar_chart(
        country_rev, "country", "total_amount", title="Revenue by Country"
    )
    fig1.update_layout(height=340, xaxis_title="Country", yaxis_title="Revenue ($)")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Revenue by City")
    city_rev = (
        df_filtered.groupby("city")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig2 = bar_chart(
        city_rev, "city", "total_amount", title="Revenue by City"
    )
    fig2.update_layout(height=340, xaxis_title="City", yaxis_title="Revenue ($)")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    st.subheader("Top 10 Stores by Revenue")
    store_rev = (
        df_filtered.groupby("store_id")["total_amount"]
        .sum()
        .reset_index()
        .nlargest(10, "total_amount")
    )
    fig3 = horizontal_bar(
        store_rev, "total_amount", "store_id", title="Top 10 Stores", top_n=10
    )
    fig3.update_layout(height=380)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Bottom 10 Stores by Revenue")
    store_bot = (
        df_filtered.groupby("store_id")["total_amount"]
        .sum()
        .reset_index()
        .nsmallest(10, "total_amount")
    )
    fig4 = horizontal_bar(
        store_bot, "total_amount", "store_id", title="Bottom 10 Stores", top_n=10
    )
    fig4.update_layout(height=380)
    st.plotly_chart(fig4, use_container_width=True)

st.subheader("Performance by Store Type")
store_type_stats = df_filtered.groupby("store_type").agg(
    revenue=("total_amount", "sum"),
    transactions=("transaction_id", "nunique"),
    avg_transaction=("total_amount", "mean"),
).reset_index()

fig5 = bar_chart(
    store_type_stats, "store_type", "revenue", title="Revenue by Store Type"
)
fig5.update_layout(height=320, xaxis_title="Store Type", yaxis_title="Revenue ($)")
st.plotly_chart(fig5, use_container_width=True)

if len(store_type_stats) > 1:
    col_st1, col_st2 = st.columns(2)
    with col_st1:
        fig5b = bar_chart(
            store_type_stats, "store_type", "transactions",
            title="Transactions by Store Type"
        )
        fig5b.update_layout(height=300)
        st.plotly_chart(fig5b, use_container_width=True)
    with col_st2:
        fig5c = bar_chart(
            store_type_stats, "store_type", "avg_transaction",
            title="Avg Transaction by Store Type"
        )
        fig5c.update_layout(height=300)
        st.plotly_chart(fig5c, use_container_width=True)

st.markdown("---")

st.subheader("Heatmap: City x Product Category")
if "city" in df_filtered.columns and "product_category" in df_filtered.columns:
    heatmap_data = (
        df_filtered.groupby(["city", "product_category"])["total_amount"]
        .sum()
        .reset_index()
    )
    fig6 = heatmap_chart(
        heatmap_data, "city", "product_category", "total_amount",
        title="Revenue Heatmap: City x Category"
    )
    fig6.update_layout(height=400)
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

st.subheader("Key Insights")

top_city_rev = city_rev.iloc[0]["total_amount"]
bot_city_rev = city_rev.iloc[-1]["total_amount"]
store_type_top = store_type_stats.loc[
    store_type_stats["revenue"].idxmax(), "store_type"
]
rev_gap = country_rev["total_amount"].max() - country_rev["total_amount"].min()
total_rev = df_filtered["total_amount"].sum()
top_city_pct = top_city_rev / total_rev * 100

col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.info(
        f"**Revenue Gap Country**: Perbedaan antara negara tertinggi dan terendah "
        f"adalah {format_currency(rev_gap)}"
    )
with col_i2:
    st.info(
        f"**Top City**: {city_rev.iloc[0]['city']} dengan "
        f"{format_currency(top_city_rev)} ({format_percentage(top_city_pct)})"
    )
with col_i3:
    st.info(f"**Best Store Type**: {store_type_top} menghasilkan revenue paling tinggi")

st.subheader("Recommended Actions")
col_a1, col_a2 = st.columns(2)
with col_a1:
    st.warning(
        f"**1. Evaluasi Store Berkinerja Rendah**\n\n"
        f"Store dengan revenue terendah perlu audit operasional dan strategi perbaikan."
    )
with col_a2:
    st.warning(
        f"**2. Investasi di {store_type_top}**\n\n"
        f"Tipe toko ini menunjukkan performa terbaik. "
        f"Pertimbangkan ekspansi format ini."
    )

st.markdown("---")
st.subheader("Download Data")
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.download_button(
        "Download Store Summary (CSV)",
        data=store_rev.to_csv(index=False),
        file_name="store_summary.csv",
        mime="text/csv",
    )
with col_dl2:
    st.download_button(
        "Download City Summary (CSV)",
        data=city_rev.to_csv(index=False),
        file_name="city_summary.csv",
        mime="text/csv",
    )
