import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import load_data, get_filter_options, check_empty_data
from utils.filters import apply_filters
from utils.formatting import (
    format_currency, format_number, format_number_full,
    format_percentage, format_date_range, format_delta,
)
from utils.metrics import calc_kpi, calc_delta, calc_monthly_data, calc_findings, calc_recommendations
from utils.charts import dual_axis_chart, horizontal_bar
from utils.styling import (
    inject_global_css, render_header, render_page_header,
    render_kpi_card, render_findings, render_recommendations,
)

st.set_page_config(
    page_title="Executive Summary - Coffee Shop Dashboard",
    page_icon=":coffee:",
    layout="wide",
)

inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header(
    "COFFEE SHOP — EXECUTIVE SUMMARY",
    "Sales Performance and Business Insights",
    format_date_range(options.get("date_min"), options.get("date_max")),
)

df_filtered = apply_filters(df, options, key_prefix="exec")
check_empty_data(df_filtered, "Executive Summary")

period = format_date_range(
    df_filtered["timestamp"].min() if df_filtered["timestamp"].notna().any() else None,
    df_filtered["timestamp"].max() if df_filtered["timestamp"].notna().any() else None,
)
st.caption(f"Showing data for: {period}  |  {len(df_filtered):,} transactions")

kpi = calc_kpi(df_filtered)
delta = calc_delta(df_filtered)
monthly = calc_monthly_data(df_filtered)

st.markdown("")
col1, col2, col3, col4 = st.columns(4)
with col1:
    render_kpi_card("Total Revenue", format_currency(kpi["total_revenue"]), delta.get("revenue"))
with col2:
    render_kpi_card("Total Transactions", format_number_full(kpi["total_transactions"]), delta.get("transactions"))
with col3:
    render_kpi_card("Avg Transaction Value", format_currency(kpi["avg_transaction"]), delta.get("avg_txn"))
with col4:
    render_kpi_card("Total Quantity Sold", format_number_full(kpi["total_quantity"]), delta.get("quantity"))

st.markdown("")

left, right = st.columns([7, 3])

with left:
    st.markdown(
        "<div class='chart-card'>"
        "<h3>Revenue & Transaction Trend</h3>"
        "<div class='chart-subtitle'>Monthly performance overview</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    if not monthly.empty:
        avg_rev = monthly["revenue"].mean()
        top_month = monthly.loc[monthly["revenue"].idxmax()]
        bot_month = monthly.loc[monthly["revenue"].idxmin()]

        fig_main = dual_axis_chart(
            monthly, "timestamp", "revenue", "transactions",
            y1_label="Revenue ($)", y2_label="Transactions",
        )

        fig_main.add_hline(
            y=avg_rev, line_dash="dot", line_color="#9CA3AF", line_width=1.5,
            annotation_text=f"Avg: ${avg_rev:,.0f}",
            annotation_position="top left",
        )

        fig_main.add_annotation(
            x=top_month["timestamp"], y=top_month["revenue"],
            text=f"Peak: ${top_month['revenue']:,.0f}",
            showarrow=True, arrowhead=2, arrowcolor="#0D8A92",
            font=dict(color="#0D8A92", size=11),
            ax=0, ay=-40,
        )
        fig_main.add_annotation(
            x=bot_month["timestamp"], y=bot_month["revenue"],
            text=f"Low: ${bot_month['revenue']:,.0f}",
            showarrow=True, arrowhead=2, arrowcolor="#D9535F",
            font=dict(color="#D9535F", size=11),
            ax=0, ay=40,
        )

        fig_main.update_layout(height=420)
        st.plotly_chart(fig_main, use_container_width=True)
    else:
        st.info("No data available for the selected period.")

with right:
    st.markdown(
        "<div class='chart-card'>"
        "<h3>Top 5 Categories by Revenue</h3>"
        "<div class='chart-subtitle'>Category contribution</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    cat_rev = (
        df_filtered.groupby("product_category")["total_amount"]
        .sum()
        .reset_index()
        .sort_values("total_amount", ascending=False)
        .head(5)
    )

    if not cat_rev.empty:
        fig_cat = horizontal_bar(
            cat_rev, "total_amount", "product_category",
            title="", top_n=5, height=380,
        )
        fig_cat.update_layout(margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_cat, use_container_width=True)

        total_rev = df_filtered["total_amount"].sum()
        for _, row in cat_rev.iterrows():
            pct = row["total_amount"] / total_rev * 100
            st.markdown(
                f"<div style='font-size:0.82rem;color:#374151;padding:2px 0;'>"
                f"{row['product_category']}: "
                f"<strong>${row['total_amount']:,.0f}</strong> ({pct:.1f}%)</div>",
                unsafe_allow_html=True,
            )

findings = calc_findings(df_filtered, monthly)
render_findings(findings)

recommendations = calc_recommendations(df_filtered, monthly)
render_recommendations(recommendations)

st.markdown("")
col_dl1, col_dl2, _ = st.columns([2, 2, 6])
with col_dl1:
    st.download_button(
        "Download Filtered Data",
        data=df_filtered.to_csv(index=False),
        file_name="executive_summary_filtered.csv",
        mime="text/csv",
    )
with col_dl2:
    if not monthly.empty:
        st.download_button(
            "Download Monthly Summary",
            data=monthly.to_csv(index=False),
            file_name="monthly_summary.csv",
            mime="text/csv",
        )
