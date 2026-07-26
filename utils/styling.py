import streamlit as st

COLORS = {
    "navy": "#1C174D",
    "purple_light": "#F3F1FA",
    "yellow": "#FFB703",
    "teal": "#0D8A92",
    "red": "#D9535F",
    "bg_main": "#FAFAFC",
    "card_bg": "#FFFFFF",
    "card_border": "#E5E7EB",
    "text_primary": "#1C174D",
    "text_secondary": "#6B7280",
    "text_muted": "#9CA3AF",
}

FONT_FAMILY = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"


def inject_global_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {{
            --navy: {COLORS['navy']};
            --purple-light: {COLORS['purple_light']};
            --yellow: {COLORS['yellow']};
            --teal: {COLORS['teal']};
            --red: {COLORS['red']};
            --bg-main: {COLORS['bg_main']};
            --card-bg: {COLORS['card_bg']};
            --card-border: {COLORS['card_border']};
            --text-primary: {COLORS['text_primary']};
            --text-secondary: {COLORS['text_secondary']};
        }}

        /* Global */
        .stApp {{
            background-color: var(--bg-main);
            font-family: {FONT_FAMILY};
        }}

        section[data-testid="stSidebar"] {{
            background-color: #FFFFFF;
            border-right: 1px solid var(--card-border);
        }}

        section[data-testid="stSidebar"] .stMarkdown h1,
        section[data-testid="stSidebar"] .stMarkdown h2,
        section[data-testid="stSidebar"] .stMarkdown h3 {{
            color: var(--navy);
        }}

        /* Hide default Streamlit padding */
        .block-container {{
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }}

        /* Dashboard Header */
        .dashboard-header {{
            background: linear-gradient(135deg, #1C174D 0%, #2D2566 100%);
            color: white;
            padding: 28px 36px;
            border-radius: 16px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 20px rgba(28, 23, 77, 0.15);
        }}

        .dashboard-header h1 {{
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: 2px;
            margin: 0;
            color: white;
        }}

        .dashboard-header .subtitle {{
            font-size: 0.95rem;
            color: rgba(255, 255, 255, 0.75);
            margin-top: 4px;
            font-weight: 400;
        }}

        .dashboard-header .period {{
            font-size: 0.85rem;
            color: var(--yellow);
            font-weight: 600;
            text-align: right;
        }}

        /* KPI Card */
        .kpi-card {{
            background: var(--purple-light);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 22px 24px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            min-height: 130px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            transition: box-shadow 0.2s;
        }}

        .kpi-card:hover {{
            box-shadow: 0 4px 16px rgba(28, 23, 77, 0.1);
        }}

        .kpi-label {{
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }}

        .kpi-value {{
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--navy);
            line-height: 1.2;
        }}

        .kpi-delta {{
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 6px;
        }}

        .kpi-delta.positive {{
            color: var(--teal);
        }}

        .kpi-delta.negative {{
            color: var(--red);
        }}

        /* Chart Card */
        .chart-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 22px 24px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            margin-bottom: 16px;
        }}

        .chart-card h3 {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--navy);
            margin-bottom: 4px;
        }}

        .chart-card .chart-subtitle {{
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 16px;
        }}

        /* Findings Card */
        .findings-card {{
            background: linear-gradient(135deg, #1C174D 0%, #2D2566 100%);
            border-radius: 16px;
            padding: 30px 36px;
            color: white;
            box-shadow: 0 4px 20px rgba(28, 23, 77, 0.15);
            margin: 24px 0;
        }}

        .findings-card h3 {{
            font-size: 1.1rem;
            font-weight: 700;
            letter-spacing: 1.5px;
            margin-bottom: 20px;
            color: white;
        }}

        .finding-item {{
            display: flex;
            align-items: flex-start;
            gap: 14px;
            margin-bottom: 16px;
            font-size: 0.95rem;
            line-height: 1.6;
            color: rgba(255, 255, 255, 0.92);
        }}

        .finding-number {{
            background: var(--yellow);
            color: var(--navy);
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 0.8rem;
            flex-shrink: 0;
        }}

        .finding-highlight {{
            color: var(--yellow);
            font-weight: 700;
        }}

        /* Recommendation Card */
        .recommendation-card {{
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-left: 4px solid var(--teal);
            border-radius: 14px;
            padding: 24px 28px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            margin-bottom: 16px;
        }}

        .recommendation-card h3 {{
            font-size: 1rem;
            font-weight: 700;
            color: var(--navy);
            letter-spacing: 1px;
            margin-bottom: 14px;
        }}

        .rec-item {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 12px;
            font-size: 0.9rem;
            color: var(--text-secondary);
            line-height: 1.6;
        }}

        .rec-icon {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: var(--purple-light);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            flex-shrink: 0;
            margin-top: 2px;
        }}

        /* Section Header */
        .section-header {{
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--navy);
            margin: 24px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--purple-light);
        }}

        /* Sidebar Reset Button */
        .stButton > button {{
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.85rem;
            transition: all 0.2s;
        }}

        /* Page title style */
        .page-title {{
            font-size: 1.4rem;
            font-weight: 800;
            color: var(--navy);
            margin-bottom: 4px;
        }}

        .page-subtitle {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 20px;
        }}

        /* Data table styling */
        .dataframe {{
            border-radius: 10px;
            overflow: hidden;
        }}

        /* Insight card */
        .insight-card {{
            background: #F0FDF4;
            border: 1px solid #BBF7D0;
            border-radius: 10px;
            padding: 16px 20px;
            font-size: 0.88rem;
            color: #166534;
            line-height: 1.6;
        }}

        .insight-card strong {{
            color: #14532D;
        }}

        /* Warning card */
        .warning-card {{
            background: #FEF3C7;
            border: 1px solid #FDE68A;
            border-radius: 10px;
            padding: 16px 20px;
            font-size: 0.88rem;
            color: #92400E;
            line-height: 1.6;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header(title, subtitle, period=""):
    period_html = f'<div class="period">{period}</div>' if period else ''
    st.markdown(
        f"""
        <div class="dashboard-header">
            <div>
                <h1>{title}</h1>
                <div class="subtitle">{subtitle}</div>
            </div>
            {period_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title, subtitle):
    st.markdown(
        f"""
        <div class="page-title">{title}</div>
        <div class="page-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label, value, delta=None, delta_suffix="%"):
    delta_html = ""
    if delta is not None:
        try:
            d = float(str(delta).replace("%", "").replace("+", ""))
            css_class = "positive" if d >= 0 else "negative"
            sign = "+" if d >= 0 else ""
            delta_html = f'<div class="kpi-delta {css_class}">{sign}{d:.1f}{delta_suffix}</div>'
        except (ValueError, TypeError):
            delta_html = f'<div class="kpi-delta">{delta}</div>'

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_findings(findings):
    items_html = ""
    for i, finding in enumerate(findings, 1):
        items_html += f"""
        <div class="finding-item">
            <div class="finding-number">{i}</div>
            <div>{finding}</div>
        </div>
        """

    st.markdown(
        f"""
        <div class="findings-card">
            <h3>KEY BUSINESS FINDINGS</h3>
            {items_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_recommendations(recommendations):
    items_html = ""
    for i, rec in enumerate(recommendations, 1):
        items_html += f"""
        <div class="rec-item">
            <div class="rec-icon">{i}</div>
            <div>{rec}</div>
        </div>
        """

    st.markdown(
        f"""
        <div class="recommendation-card">
            <h3>RECOMMENDED ACTIONS</h3>
            {items_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chart_card(title, subtitle=None):
    subtitle_html = f'<div class="chart-subtitle">{subtitle}</div>' if subtitle else ''
    st.markdown(
        f"""
        <div class="chart-card">
            <h3>{title}</h3>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
