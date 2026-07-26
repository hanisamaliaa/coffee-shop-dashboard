import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, check_empty_data
from utils.filters import apply_filters
from utils.formatting import format_currency, format_number_full, format_percentage
from utils.charts import horizontal_bar, bar_chart, pie_chart
from utils.styling import (
    inject_global_css, render_header, render_page_header, render_kpi_card,
)

st.set_page_config(
    page_title="Product - Coffee Shop Dashboard",
    page_icon=":package:",
    layout="wide",
)

inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header(
    "PRODUCT ANALYSIS",
    "Product performance, category contribution, and discount impact",
    "",
)

df_filtered = apply_filters(df, options, key_prefix="product")
check_empty_data(df_filtered, "Product")

prod_stats = df_filtered.groupby("product_name").agg(
    revenue=("total_amount", "sum"),
    quantity=("quantity", "sum"),
    transactions=("transaction_id", "nunique"),
    avg_discount=("discount_amount", "mean") if "discount_amount" in df_filtered.columns else ("total_amount", "count"),
).reset_index()

best_selling = prod_stats.loc[prod_stats["quantity"].idxmax(), "product_name"]
highest_rev = prod_stats.loc[prod_stats["revenue"].idxmax(), "product_name"]
lowest_rev = prod_stats.loc[prod_stats["revenue"].idxmin(), "product_name"]
total_products = len(prod_stats)

st.markdown("")
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Best-Selling (Qty)", best_selling[:20] + "..." if len(best_selling) > 20 else best_selling)
with col2:
    render_kpi_card("Highest Revenue", highest_rev[:20] + "..." if len(highest_rev) > 20 else highest_rev)
with col3:
    render_kpi_card("Lowest Revenue", lowest_rev[:20] + "..." if len(lowest_rev) > 20 else lowest_rev)
with col4:
    render_kpi_card("Total Products", format_number_full(total_products))

st.markdown("")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown(
        "<div class='chart-card'><h3>Top 10 Products by Quantity</h3></div>",
        unsafe_allow_html=True,
    )
    top_qty = prod_stats.nlargest(10, "quantity")
    fig1 = horizontal_bar(top_qty, "quantity", "product_name", title="", top_n=10, height=380)
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.markdown(
        "<div class='chart-card'><h3>Top 10 Products by Revenue</h3></div>",
        unsafe_allow_html=True,
    )
    top_rev = prod_stats.nlargest(10, "revenue")
    fig2 = horizontal_bar(top_rev, "revenue", "product_name", title="", top_n=10, height=380)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("")

st.markdown(
    "<div class='section-header'>BOTTOM 10 PRODUCTS BY REVENUE</div>",
    unsafe_allow_html=True,
)

bot_rev = prod_stats.nsmallest(10, "revenue")
fig3 = horizontal_bar(bot_rev, "revenue", "product_name", title="", top_n=10, height=380)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("")

col_c, col_d = st.columns(2)
with col_c:
    st.markdown(
        "<div class='chart-card'><h3>Category Revenue Contribution</h3></div>",
        unsafe_allow_html=True,
    )
    cat_stats = df_filtered.groupby("product_category").agg(
        revenue=("total_amount", "sum"),
        quantity=("quantity", "sum"),
    ).reset_index()
    fig4 = pie_chart(cat_stats, "product_category", "revenue", title="", height=360)
    st.plotly_chart(fig4, use_container_width=True)

with col_d:
    st.markdown(
        "<div class='chart-card'><h3>Discount vs Non-Discount Revenue</h3></div>",
        unsafe_allow_html=True,
    )
    if "discount_applied" in df_filtered.columns:
        disc_stats = df_filtered.groupby("discount_applied").agg(
            revenue=("total_amount", "sum"),
        ).reset_index()
        disc_stats["label"] = disc_stats["discount_applied"].map({True: "Discount", False: "No Discount"})
        fig5 = bar_chart(disc_stats, "label", "revenue", title="", height=360)
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("Discount data not available")

st.markdown("")

total_rev = df_filtered["total_amount"].sum()
top_cat = cat_stats.loc[cat_stats["revenue"].idxmax(), "product_category"]
bot_cat = cat_stats.loc[cat_stats["revenue"].idxmin(), "product_category"]
rev_range = prod_stats["revenue"].max() - prod_stats["revenue"].min()

col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.markdown(
        f"<div class='insight-card'><strong>Revenue Gap:</strong> Difference between top and bottom product is "
        f"{format_currency(rev_range)}</div>",
        unsafe_allow_html=True,
    )
with col_i2:
    st.markdown(
        f"<div class='insight-card'><strong>Top Category:</strong> {top_cat} dominates with "
        f"{format_currency(cat_stats['revenue'].max())}</div>",
        unsafe_allow_html=True,
    )
with col_i3:
    st.markdown(
        f"<div class='insight-card'><strong>Weakest Category:</strong> {bot_cat} at "
        f"{format_currency(cat_stats['revenue'].min())}</div>",
        unsafe_allow_html=True,
    )

st.markdown("")
st.download_button(
    "Download Product Summary",
    data=prod_stats.to_csv(index=False),
    file_name="product_summary.csv",
    mime="text/csv",
)
