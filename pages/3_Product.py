import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, apply_filters, check_empty_data
from utils.formatting import format_currency, format_number, format_percentage
from utils.charts import horizontal_bar, bar_chart, pie_chart

st.set_page_config(
    page_title="Product - Coffee Shop Dashboard",
    page_icon=":package:",
    layout="wide"
)
st.title(":package: Product Analysis")
st.caption("Performa produk, kategori, dan dampak diskon")

df = load_data()
options = get_filter_options(df)
df_filtered = apply_filters(df, options, key_prefix="product")
check_empty_data(df_filtered, "Product")

st.markdown("## KPI Overview")

prod_stats = df_filtered.groupby("product_name").agg(
    revenue=("total_amount", "sum"),
    quantity=("quantity", "sum"),
    transactions=("transaction_id", "nunique"),
    avg_discount=("discount_amount", "mean"),
).reset_index()

best_selling = prod_stats.loc[prod_stats["quantity"].idxmax(), "product_name"]
highest_rev = prod_stats.loc[prod_stats["revenue"].idxmax(), "product_name"]
lowest_rev = prod_stats.loc[prod_stats["revenue"].idxmin(), "product_name"]
most_discounted = (
    prod_stats.loc[prod_stats["avg_discount"].idxmax(), "product_name"]
    if "discount_amount" in df_filtered.columns
    else "-"
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Best-Selling (Qty)", best_selling[:22] if len(best_selling) > 22 else best_selling)
c2.metric("Highest Revenue", highest_rev[:22] if len(highest_rev) > 22 else highest_rev)
c3.metric("Lowest Revenue", lowest_rev[:22] if len(lowest_rev) > 22 else lowest_rev)
c4.metric("Most Discounted", most_discounted[:22] if len(most_discounted) > 22 else most_discounted)

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Top 10 Products by Quantity")
    top_qty = prod_stats.nlargest(10, "quantity")
    fig1 = horizontal_bar(
        top_qty, "quantity", "product_name",
        title="Top 10 Products by Quantity Sold", top_n=10
    )
    fig1.update_layout(height=380)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Top 10 Products by Revenue")
    top_rev = prod_stats.nlargest(10, "revenue")
    fig2 = horizontal_bar(
        top_rev, "revenue", "product_name",
        title="Top 10 Products by Revenue", top_n=10
    )
    fig2.update_layout(height=380)
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Bottom 10 Products by Revenue")
bot_rev = prod_stats.nsmallest(10, "revenue")
fig3 = horizontal_bar(
    bot_rev, "revenue", "product_name",
    title="Bottom 10 Products by Revenue", top_n=10
)
fig3.update_layout(height=350)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    st.subheader("Category Contribution")
    cat_stats = df_filtered.groupby("product_category").agg(
        revenue=("total_amount", "sum"),
        quantity=("quantity", "sum"),
    ).reset_index()
    fig4 = pie_chart(
        cat_stats, "product_category", "revenue",
        title="Revenue Share by Category"
    )
    fig4.update_layout(height=350)
    st.plotly_chart(fig4, use_container_width=True)

with col4:
    st.subheader("Discount vs Non-Discount Performance")
    if "discount_applied" in df_filtered.columns:
        disc_stats = df_filtered.groupby("discount_applied").agg(
            revenue=("total_amount", "sum"),
            avg_value=("total_amount", "mean"),
            count=("transaction_id", "nunique"),
        ).reset_index()
        disc_stats["label"] = disc_stats["discount_applied"].map(
            {True: "Discount", False: "No Discount"}
        )

        fig5 = bar_chart(
            disc_stats, "label", "revenue",
            title="Revenue: Discount vs Non-Discount"
        )
        fig5.update_layout(height=350)
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("Kolom discount_applied tidak tersedia")

st.markdown("---")

st.subheader("Key Insights")

top_cat = cat_stats.loc[cat_stats["revenue"].idxmax(), "product_category"]
bot_cat = cat_stats.loc[cat_stats["revenue"].idxmin(), "product_category"]
rev_range = prod_stats["revenue"].max() - prod_stats["revenue"].min()
top_cat_share = cat_stats["revenue"].max() / cat_stats["revenue"].sum() * 100

col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.info(
        f"**Revenue Gap**: Perbedaan antara produk terlaris dan terendah mencapai "
        f"{format_currency(rev_range)}"
    )
with col_i2:
    st.info(
        f"**Top Category**: {top_cat} mendominasi dengan "
        f"{format_currency(cat_stats.loc[cat_stats['revenue'].idxmax(), 'revenue'])} "
        f"({format_percentage(top_cat_share)})"
    )
with col_i3:
    st.info(
        f"**Weakest Category**: {bot_cat} hanya "
        f"{format_currency(cat_stats.loc[cat_stats['revenue'].idxmin(), 'revenue'])}"
    )

st.subheader("Recommended Actions")
col_a1, col_a2 = st.columns(2)
with col_a1:
    st.warning(
        f"**1. Bundle atau Promosi Produk Bawah**\n\n"
        f"{len(bot_rev)} produk dengan revenue rendah perlu strategi bundling atau promosi khusus."
    )
with col_a2:
    st.warning(
        f"**2. Jaga Konsistensi {top_cat}**\n\n"
        f"Kategori ini adalah tulang punggung revenue. Pastikan kualitas dan variasi tetap optimal."
    )

st.markdown("---")
st.subheader("Download Data")
st.download_button(
    "Download Product Summary (CSV)",
    data=prod_stats.to_csv(index=False),
    file_name="product_summary.csv",
    mime="text/csv",
)
