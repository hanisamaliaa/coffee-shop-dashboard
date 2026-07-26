import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.styling import inject_global_css

st.set_page_config(
    page_title="Coffee Shop Dashboard",
    page_icon=":coffee:",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

st.markdown(
    """
    <div class="dashboard-header">
        <div>
            <h1>COFFEE SHOP</h1>
            <div class="subtitle">Executive Business Intelligence Dashboard</div>
        </div>
        <div class="period">Sales Performance & Business Insights</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="text-align:center; padding: 60px 20px; color: #6B7280;">
        <div style="font-size: 3rem; margin-bottom: 16px; opacity: 0.3;">:coffee:</div>
        <div style="font-size: 1.1rem; font-weight: 600; color: #1C174D; margin-bottom: 8px;">
            Welcome to the Coffee Shop Dashboard
        </div>
        <div style="font-size: 0.9rem;">
            Navigate using the pages in the sidebar to explore detailed analytics.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    "<div style='font-size:1.1rem;font-weight:800;color:#1C174D;margin-bottom:4px;'>"
    "COFFEE SHOP</div>"
    "<div style='font-size:0.75rem;color:#6B7280;margin-bottom:16px;'>"
    "Business Intelligence</div>",
    unsafe_allow_html=True,
)
