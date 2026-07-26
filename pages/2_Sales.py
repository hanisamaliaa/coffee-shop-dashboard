import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, apply_filters, check_empty_data
from utils.formatting import format_currency, format_number, format_percentage
from utils.charts import line_chart, bar_chart, horizontal_bar

st.set_page_config(
    page_title="Sales - Coffee Shop Dashboard",
    page_icon=":moneybag:",
    layout="wide"
)
st.title(":moneybag: Sales Analysis")
st.caption("Tren penjualan, revenue, transaksi, dan pola kontribusi")

df = load_data()
options = get_filter_options(df)
df_filtered = apply_filters(df, options, key_prefix="sales")
check_empty_data(df_filtered, "Sales")

st.markdown("## KPI Overview")

total_revenue = df_filtered["total_amount"].sum()
total_transactions = df_filtered["transaction_id"].nunique()
total_quantity = int(df_filtered["quantity"].sum())
avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", format_currency(total_revenue))
c2.metric("Total Transactions", format_number(total_transactions))
c3.metric("Total Quantity", format_number(total_quantity))
c4.metric("Avg Transaction Value", format_currency(avg_transaction))

st.markdown("---")

st.subheader("Monthly Revenue & Transaction Trend")

monthly = df_filtered.groupby(df_filtered["timestamp"].dt.to_period("M")).agg(
    revenue=("total_amount", "sum"),
    transactions=("transaction_id", "nunique"),
    quantity=("quantity", "sum"),
).reset_index()
monthly["timestamp"] = monthly["timestamp"].dt.to_timestamp()

col1, col2 = st.columns(2)
with col1:
    fig1 = line_chart(monthly, "timestamp", "revenue", title="Monthly Revenue")
    fig1.update_layout(height=340, yaxis_title="Revenue ($)")
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    fig2 = line_chart(monthly, "timestamp", "transactions", title="Monthly Transactions")
    fig2.update_layout(height=340, yaxis_title="Transactions")
    st.plotly_chart(fig2, use_container_width=True)

peak = monthly.loc[monthly["revenue"].idxmax()]
low = monthly.loc[monthly["revenue"].idxmin()]
growth = (
    ((monthly.iloc[-1]["revenue"] - monthly.iloc[0]["revenue"]) / monthly.iloc[0]["revenue"] * 100)
    if monthly.iloc[0]["revenue"] > 0
    else 0
)

st.info(
    f"**Peak**: {peak['timestamp'].strftime('%B %Y')} ({format_currency(peak['revenue'])}) | "
    f"**Lowest**: {low['timestamp'].strftime('%B %Y')} ({format_currency(low['revenue'])}) | "
    f"**Growth**: {growth:+.1f}% dari bulan pertama ke terakhir"
)

st.markdown("---")

st.subheader("Revenue Breakdown")

col3, col4 = st.columns(2)
with col3:
    cat_rev = (
        df_filtered.groupby("product_category")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig3 = bar_chart(cat_rev, "product_category", "total_amount", title="Revenue by Product Category")
    fig3.update_layout(height=340, xaxis_title="Category", yaxis_title="Revenue ($)")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    pay_rev = (
        df_filtered.groupby("payment_method")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
    )
    fig4 = bar_chart(pay_rev, "payment_method", "total_amount", title="Revenue by Payment Method")
    fig4.update_layout(height=340, xaxis_title="Payment Method", yaxis_title="Revenue ($)")
    st.plotly_chart(fig4, use_container_width=True)

st.subheader("Top 10 Products by Revenue")
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

fig5 = horizontal_bar(
    top_products, "revenue", "product_name",
    title="Top 10 Products by Revenue", top_n=10
)
fig5.update_layout(height=400, xaxis_title="Revenue ($)")
st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

st.subheader("Key Insights")

cat_top = cat_rev.iloc[0]["product_category"]
cat_bot = cat_rev.iloc[-1]["product_category"]
cat_top_share = cat_rev.iloc[0]["total_amount"] / total_revenue * 100
cat_bot_share = cat_rev.iloc[-1]["total_amount"] / total_revenue * 100

col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    st.info(
        f"**Dominant Category**: {cat_top} berkontribusi "
        f"{format_currency(cat_rev.iloc[0]['total_amount'])} "
        f"({format_percentage(cat_top_share)} dari total)"
    )
with col_i2:
    st.info(
        f"**Revenue Growth**: Dari awal ke akhir periode, revenue berubah {growth:+.1f}%"
    )
with col_i3:
    st.info(
        f"**Weakest Category**: {cat_bot} hanya "
        f"{format_currency(cat_rev.iloc[-1]['total_amount'])} "
        f"({format_percentage(cat_bot_share)})"
    )

st.subheader("Recommended Actions")
col_a1, col_a2 = st.columns(2)
with col_a1:
    st.warning(
        f"**1. Perkuat Kategori {cat_top}**\n\n"
        f"Pertahankan stok dan variasi produk di kategori terlaris ini."
    )
with col_a2:
    st.warning(
        f"**2. Evaluasi {cat_bot}**\n\n"
        f"Pertimbangkan strategi promosi atau bundle untuk kategori berkinerja rendah."
    )

st.markdown("---")
st.subheader("Download Data")
col_dl1, col_dl2 = st.columns(2)
with col_dl1:
    st.download_button(
        "Download Monthly Sales Summary (CSV)",
        data=monthly.to_csv(index=False),
        file_name="monthly_sales_summary.csv",
        mime="text/csv",
    )
with col_dl2:
    st.download_button(
        "Download Category Summary (CSV)",
        data=cat_rev.to_csv(index=False),
        file_name="category_summary.csv",
        mime="text/csv",
    )
