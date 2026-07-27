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
    # Warna teks isi. Sengaja dipisah dari text_primary (navy) karena navy
    # terlalu pekat untuk paragraf panjang, dan dipakai sebagai penangkal
    # kalau tema gelap Streamlit membuat teks bawaan jadi putih.
    "text_primary_body": "#1F2937",
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
            --text-primary-body: {COLORS['text_primary_body']};
            --text-secondary: {COLORS['text_secondary']};
        }}

        /* Global */
        .stApp {{
            background-color: var(--bg-main);
            font-family: {FONT_FAMILY};
        }}

        /* ── Pertahanan kontras ──────────────────────────────────────────
           Seluruh CSS di bawah memakai palet TERANG (kartu putih, teks navy).
           Kalau Streamlit terlanjur memakai tema gelap — entah karena OS
           pengguna dark mode atau karena tema diganti dari menu Streamlit —
           teks bawaannya menjadi putih dan hilang di atas kartu putih kita.

           .streamlit/config.toml sudah mengunci base="light". Blok ini adalah
           lapis kedua supaya dashboard tetap terbaca walau config itu hilang
           atau ditimpa. */
        .stApp, .stApp p, .stApp li, .stApp label,
        .stApp .stMarkdown, [data-testid="stCaptionContainer"],
        [data-testid="stMetricValue"], [data-testid="stDataFrame"],
        [data-testid="stExpander"] summary,
        .stDataFrame, .stTable {{
            color: var(--text-primary-body);
        }}

        /* Sidebar — sumber keluhan paling sering: label filter jadi tak
           terlihat karena teks putih di atas latar putih. */
        section[data-testid="stSidebar"] {{
            background-color: #FFFFFF;
            border-right: 1px solid var(--card-border);
        }}

        section[data-testid="stSidebar"] * {{
            color: var(--text-primary-body);
        }}

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
        section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{
            color: var(--navy) !important;
            font-weight: 600;
            font-size: 0.84rem;
        }}

        section[data-testid="stSidebar"] .stMarkdown h1,
        section[data-testid="stSidebar"] .stMarkdown h2,
        section[data-testid="stSidebar"] .stMarkdown h3 {{
            color: var(--navy);
        }}

        /* Kotak input di sidebar: multiselect, date input, dropdown */
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] [data-baseweb="input"] > div,
        section[data-testid="stSidebar"] [data-testid="stDateInput"] input {{
            background-color: #FFFFFF !important;
            border-color: var(--card-border) !important;
            color: var(--text-primary-body) !important;
        }}

        /* Tag terpilih di multiselect */
        section[data-testid="stSidebar"] [data-baseweb="tag"] {{
            background-color: var(--teal) !important;
        }}
        section[data-testid="stSidebar"] [data-baseweb="tag"] span {{
            color: #FFFFFF !important;
        }}

        /* Menu dropdown mengambang — dirender di luar sidebar */
        [data-baseweb="popover"] li,
        [data-baseweb="popover"] div {{
            color: var(--text-primary-body);
        }}

        /* Navigasi halaman di sidebar */
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span {{
            color: var(--text-primary-body) !important;
        }}
        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] span {{
            color: var(--navy) !important;
            font-weight: 700;
        }}

        /* Tabel: teks bawaan ikut tema, latarnya milik kita */
        [data-testid="stDataFrame"] {{
            background-color: #FFFFFF;
            border-radius: 10px;
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

        /* "Apa artinya" — kesimpulan di bawah setiap grafik.
           Grafik tanpa kesimpulan tidak menjawab apa pun. */
        .takeaway {{
            background: {COLORS['purple_light']};
            border-left: 4px solid {COLORS['teal']};
            border-radius: 0 8px 8px 0;
            padding: 12px 18px;
            margin: 4px 0 22px 0;
            font-size: 0.87rem;
            color: #374151;
            line-height: 1.65;
        }}
        .takeaway .tl {{
            display: block;
            font-size: 0.68rem;
            font-weight: 800;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            color: {COLORS['teal']};
            margin-bottom: 5px;
        }}
        .takeaway strong {{ color: {COLORS['navy']}; font-weight: 700; }}
        .takeaway.alert {{
            background: #FEF2F2;
            border-left-color: {COLORS['red']};
        }}
        .takeaway.alert .tl {{ color: {COLORS['red']}; }}

        /* Header langkah bernomor — supaya halaman terbaca berurutan */
        .step {{
            display: flex;
            align-items: baseline;
            gap: 12px;
            margin: 30px 0 6px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid {COLORS['card_border']};
        }}
        .step .num {{
            flex: none;
            width: 27px; height: 27px;
            border-radius: 7px;
            background: {COLORS['navy']};
            color: #fff;
            font-size: 0.78rem; font-weight: 800;
            display: flex; align-items: center; justify-content: center;
            transform: translateY(3px);
        }}
        .step .txt h4 {{
            margin: 0; padding: 0;
            font-size: 1.06rem; font-weight: 800;
            color: {COLORS['navy']};
        }}
        .step .txt p {{
            margin: 2px 0 0 0;
            font-size: 0.82rem; color: {COLORS['text_secondary']};
        }}

        /* Baris caveat kecil di kaki halaman */
        .caveat {{
            background: #FFFBEB;
            border: 1px solid #FDE68A;
            border-radius: 8px;
            padding: 11px 16px;
            font-size: 0.79rem;
            color: #92400E;
            line-height: 1.6;
            margin-top: 8px;
        }}
        .caveat b {{ color: #78350F; }}
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


def render_step(number, title, question=None):
    """Header langkah bernomor. Setiap halaman dibaca berurutan 1, 2, 3."""
    q = f"<p>{question}</p>" if question else ""
    st.markdown(
        f"""
        <div class="step">
            <div class="num">{number}</div>
            <div class="txt"><h4>{title}</h4>{q}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_takeaway(text, alert=False, label="Apa artinya"):
    """Kesimpulan satu paragraf di bawah grafik.

    Aturan main: setiap grafik di dashboard ini wajib punya satu. Grafik tanpa
    kesimpulan memaksa pembaca menebak sendiri apa yang harus dilakukan.
    """
    css = "takeaway alert" if alert else "takeaway"
    st.markdown(
        f'<div class="{css}"><span class="tl">{label}</span>{text}</div>',
        unsafe_allow_html=True,
    )


def render_caveat(text):
    """Batasan analisis. Ditulis di halaman, bukan disembunyikan di catatan kaki."""
    st.markdown(f'<div class="caveat">{text}</div>', unsafe_allow_html=True)
