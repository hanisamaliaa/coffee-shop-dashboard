"""Perpustakaan grafik.

Tiga aturan yang dipakai konsisten di seluruh dashboard:

  1. SATU GRAFIK, SATU PESAN. Kalau semua batang berwarna, tidak ada yang
     penting. Yang disorot berwarna AKSEN, sisanya ABU.
  2. LABEL ANGKA DI BATANG. Pembaca tidak perlu menerka dari sumbu.
  3. JUDUL BERISI KESIMPULAN, bukan nama kolom. "Coffee 42% dari omzet",
     bukan "Revenue by Category".
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

NAVY = "#1C174D"
TEAL = "#0D8A92"
YELLOW = "#FFB703"
RED = "#D9535F"
GREEN = "#0F9D58"
GREY = "#C9CBD6"          # untuk yang TIDAK disorot
PURPLE_LIGHT = "#F3F1FA"

CHART_COLORS = [NAVY, TEAL, YELLOW, RED, "#6366F1", "#8B5CF6", "#EC4899", "#F59E0B"]
SEQ_SCALE = [[0, PURPLE_LIGHT], [0.5, TEAL], [1, NAVY]]

LAYOUT_DEFAULTS = dict(
    font=dict(family="Inter, sans-serif", size=12, color="#374151"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=50, b=40, l=60, r=30),
    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter, sans-serif"),
)


# ─────────────────────────────────────────────────────────────────────────────
# Kompatibilitas Plotly — WAJIB dipakai untuk setiap data yang masuk ke grafik
# ─────────────────────────────────────────────────────────────────────────────
#
# plotly (Python) >= 6.0 menyerialisasi array numpy / Series pandas menjadi
#     {"dtype": "f8", "bdata": "<base64>"}
# Plotly.js versi lama (yang dibundel Streamlit < ~1.40) TIDAK mengenal format
# itu. Akibatnya bukan error — grafiknya tetap tampil, tapi Plotly.js diam-diam
# menggambar INDEKS (0, 1, 2, ...) sebagai ganti nilainya. Garis omzet jadi rata
# di nol dan heatmap jadi kosong.
#
# Karena versi Streamlit di setiap mesin bisa berbeda, kita tidak mengandalkan
# upgrade. Semua data dikonversi ke list Python biasa, yang dimengerti Plotly.js
# versi mana pun.

def _v(seq):
    """Array 1D -> list Python biasa (bukan numpy)."""
    if seq is None:
        return None
    arr = np.asarray(seq)
    if arr.dtype.kind in "iuf":                 # angka
        return [float(x) for x in arr.tolist()]
    if arr.dtype.kind in "Mm":                  # tanggal/waktu
        return [str(x) for x in pd.to_datetime(arr)]
    return [str(x) for x in arr.tolist()]       # teks / kategori


def _v2(mat):
    """Array 2D -> list of list Python biasa."""
    if mat is None:
        return None
    arr = np.asarray(mat)
    if arr.dtype.kind in "iuf":
        return [[float(x) for x in baris] for baris in arr.tolist()]
    return [[str(x) for x in baris] for baris in arr.tolist()]


def _apply_layout(fig, height=380, **kwargs):
    layout = {**LAYOUT_DEFAULTS, "height": height}
    layout.update(kwargs)
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6", zeroline=False)
    return fig


def highlight_colors(n, focus, base=GREY, accent=TEAL):
    """Warnai hanya indeks yang disorot; sisanya abu."""
    if focus is None:
        return [accent] * n
    focus = {focus} if isinstance(focus, (int, np.integer)) else set(focus)
    return [accent if i in focus else base for i in range(n)]


# ─────────────────────────────────────────────────────────────────────────────
# Grafik utama yang dipakai berulang kali
# ─────────────────────────────────────────────────────────────────────────────
def ranked_bar(labels, values, highlight=None, title="", height=380,
               value_fmt="${:,.0f}", accent=TEAL, xaxis_title=None):
    """Batang horizontal terurut, dengan label angka dan satu sorotan.

    `highlight` boleh int, list of int, atau None. Indeks mengacu pada urutan
    yang DIBERIKAN (biasanya sudah diurutkan naik supaya nilai terbesar di atas
    setelah sumbu dibalik).
    """
    labels, values = _v(labels), _v(values)
    n = len(values)
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=highlight_colors(n, highlight, accent=accent),
        text=[value_fmt.format(v) for v in values],
        textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color="#374151"),
        hovertemplate="%{y}: <b>%{text}</b><extra></extra>",
    ))
    span = max(values) if values else 1
    fig.update_xaxes(showgrid=True, gridcolor="#F3F4F6",
                     range=[0, span * 1.20], title=xaxis_title)
    fig.update_yaxes(showgrid=False)
    return _apply_layout(fig, height, title=title, showlegend=False)


def trend_line(x, y, title="", height=380, y_fmt="$%{y:,.0f}",
               avg_line=True, avg_label="rata-rata", name="Omzet"):
    """Garis tren dengan area dan garis rata-rata sebagai pembanding."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_v(x), y=_v(y), mode="lines+markers", name=name,
        line=dict(color=NAVY, width=2.8), marker=dict(size=7),
        fill="tozeroy", fillcolor="rgba(28,23,77,0.07)",
        hovertemplate=f"%{{x}}<br><b>{y_fmt}</b><extra></extra>",
    ))
    y = _v(y)
    if avg_line and len(y):
        rata = float(np.mean(y))
        fig.add_hline(y=rata, line_dash="dot", line_color=YELLOW, line_width=2,
                      annotation_text=f"{avg_label}: ${rata:,.0f}",
                      annotation_position="top left",
                      annotation_font=dict(color="#B27300", size=11))
        fig.update_yaxes(range=[0, max(y) * 1.22])
    return _apply_layout(fig, height, title=title, showlegend=False)


def hour_bar(hours, values, peak_hours=(6, 7, 8, 9, 10), quiet_hours=(),
             title="", height=380, annotation=None):
    """Grafik per jam dengan jam sibuk disorot dan jam sepi diarsir merah."""
    hours, values = _v(hours), _v(values)
    peak = {float(h) for h in peak_hours}
    warna = [TEAL if h in peak else GREY for h in hours]
    fig = go.Figure(go.Bar(
        x=hours, y=values, marker_color=warna,
        hovertemplate="Jam %{x}:00<br><b>$%{y:,.0f}</b><extra></extra>",
    ))
    for h in quiet_hours:
        fig.add_vrect(x0=h - 0.5, x1=h + 0.5, fillcolor=RED, opacity=0.06,
                      layer="below", line_width=0)
    if annotation:
        puncak = int(np.argmax(values))
        fig.add_annotation(
            x=list(hours)[puncak], y=list(values)[puncak], text=annotation,
            showarrow=True, arrowhead=2, arrowcolor=NAVY, ax=60, ay=-45,
            font=dict(color=NAVY, size=12, family="Inter"),
            bgcolor="rgba(255,255,255,0.9)", bordercolor=NAVY, borderwidth=1,
            borderpad=6)
    fig.update_xaxes(dtick=2, title="Jam")
    fig.update_yaxes(range=[0, max(values) * 1.22])
    return _apply_layout(fig, height, title=title, showlegend=False)


def compare_bar(categories, series, title="", height=380, colors=None,
                value_fmt="{:,.2f}", yaxis_title=None):
    """Batang berkelompok untuk membandingkan 2-3 kelompok.

    `series` adalah dict {nama: [nilai per kategori]}.
    """
    colors = colors or [GREY, TEAL, YELLOW]
    fig = go.Figure()
    for i, (nama, nilai) in enumerate(series.items()):
        fig.add_trace(go.Bar(
            name=nama, x=_v(categories), y=_v(nilai),
            marker_color=colors[i % len(colors)],
            text=[value_fmt.format(v) for v in nilai],
            textposition="outside", cliponaxis=False,
            textfont=dict(size=11),
            hovertemplate=f"{nama}<br>%{{x}}: <b>%{{y:,.2f}}</b><extra></extra>",
        ))
    semua = [float(v) for s in series.values() for v in s]
    fig.update_yaxes(range=[0, max(semua) * 1.25], title=yaxis_title)
    return _apply_layout(fig, height, title=title, barmode="group",
                         legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                     xanchor="right", x=1))


def threshold_bar(labels, values, threshold, title="", height=380,
                  above_color=GREEN, below_color=RED, threshold_label="",
                  value_fmt="{:.2f}", yaxis_title=None):
    """Batang yang diwarnai berdasarkan lolos/tidak lolos sebuah ambang.

    Dipakai untuk pertanyaan "tingkat diskon mana yang benar-benar bekerja?" —
    hijau kalau menjual lebih banyak dari tanpa diskon, merah kalau tidak.
    """
    labels, values = _v(labels), _v(values)
    warna = [above_color if v > threshold else below_color for v in values]
    fig = go.Figure(go.Bar(
        x=labels, y=values, marker_color=warna,
        text=[value_fmt.format(v) for v in values],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(size=12, color="white", family="Inter"),
        hovertemplate="%{x}: <b>%{y:.2f}</b><extra></extra>",
    ))
    fig.add_hline(y=threshold, line_dash="dash", line_color=NAVY, line_width=2,
                  annotation_text=threshold_label,
                  annotation_position="top right",
                  annotation_font=dict(color=NAVY, size=11))
    fig.update_yaxes(range=[0, max(max(values), threshold) * 1.28], title=yaxis_title)
    return _apply_layout(fig, height, title=title, showlegend=False)


def matrix_heatmap(pivot, title="", height=400, value_fmt=None, colorbar=False,
                   x_tick_every=1, x_title=None):
    """Peta panas dari DataFrame pivot (index = baris, columns = kolom).

    Sumbu DIPAKSA bertipe "category". Tanpa itu, kolom berupa angka-dalam-teks
    ("0".."23" untuk jam) akan dianggap numerik oleh Plotly, dan label harinya
    ikut rusak. Untuk menjarangkan label jam, pakai `x_tick_every` — jangan
    `dtick`, karena dtick memaksa sumbu kembali jadi numerik.
    """
    x_labels = [str(c) for c in pivot.columns]
    y_labels = [str(i) for i in pivot.index]

    fig = go.Figure(go.Heatmap(
        z=_v2(pivot.values), x=x_labels, y=y_labels,
        colorscale=SEQ_SCALE, showscale=colorbar,
        xgap=2, ygap=2,
        text=(_v2(np.vectorize(lambda v: value_fmt.format(v))(pivot.values))
              if value_fmt else None),
        texttemplate="%{text}" if value_fmt else None,
        textfont=dict(size=10),
        hovertemplate="%{y} · %{x}<br><b>%{z:,.2f}</b><extra></extra>",
    ))
    fig.update_xaxes(type="category", showgrid=False, title=x_title,
                     tickmode="array",
                     tickvals=x_labels[::max(int(x_tick_every), 1)],
                     ticktext=x_labels[::max(int(x_tick_every), 1)])
    fig.update_yaxes(type="category", showgrid=False, autorange="reversed")
    return _apply_layout(fig, height, title=title)


def donut(labels, values, title="", height=380, center_text=None):
    fig = go.Figure(go.Pie(
        labels=_v(labels), values=_v(values), hole=0.58,
        marker=dict(colors=CHART_COLORS, line=dict(color="white", width=2)),
        textposition="outside", textinfo="label+percent",
        hovertemplate="%{label}<br><b>$%{value:,.0f}</b> (%{percent})<extra></extra>",
    ))
    if center_text:
        fig.add_annotation(text=center_text, x=0.5, y=0.5, showarrow=False,
                           font=dict(size=15, color=NAVY, family="Inter"))
    return _apply_layout(fig, height, title=title, showlegend=False)


def waterfall(labels, values, title="", height=400):
    """Air terjun — dipakai untuk omzet kotor -> diskon -> HPP -> laba."""
    ukuran = ["absolute"] + ["relative"] * (len(values) - 2) + ["total"]
    fig = go.Figure(go.Waterfall(
        orientation="v", measure=ukuran, x=_v(labels), y=_v(values),
        text=[f"${abs(v):,.0f}" for v in values], textposition="outside",
        connector=dict(line=dict(color="#D1D5DB", width=1)),
        increasing=dict(marker=dict(color=TEAL)),
        decreasing=dict(marker=dict(color=RED)),
        totals=dict(marker=dict(color=NAVY)),
        hovertemplate="%{x}: <b>$%{y:,.0f}</b><extra></extra>",
    ))
    return _apply_layout(fig, height, title=title, showlegend=False)


def pareto(values, title="", height=380, target=0.80, xaxis_title="Produk"):
    """Kurva kumulatif — berapa banyak item untuk mencapai `target` omzet."""
    total = float(np.sum(values))
    kum = np.cumsum(sorted(values, reverse=True)) / total
    n = int((kum <= target).sum() + 1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[float(i) for i in range(1, len(kum) + 1)], y=_v(kum), mode="lines",
        line=dict(color=NAVY, width=3), fill="tozeroy",
        fillcolor="rgba(13,138,146,0.10)",
        hovertemplate="%{x} item pertama = <b>%{y:.0%}</b> omzet<extra></extra>",
    ))
    fig.add_hline(y=target, line_dash="dash", line_color=RED, line_width=1.6)
    fig.add_vline(x=n, line_dash="dash", line_color=YELLOW, line_width=2,
                  annotation_text=f"butuh {n} dari {len(kum)}",
                  annotation_position="top left",
                  annotation_font=dict(color="#B27300", size=12))
    fig.update_yaxes(tickformat=".0%", range=[0, 1.03])
    fig.update_xaxes(title=xaxis_title)
    return _apply_layout(fig, height, title=title, showlegend=False), n


# ─────────────────────────────────────────────────────────────────────────────
# Fungsi lama — dipertahankan supaya halaman yang belum diperbarui tetap jalan
# ─────────────────────────────────────────────────────────────────────────────
def bar_chart(df, x, y, title="", height=380, color=None):
    fig = px.bar(df, x=x, y=y, title=title, color=color,
                 color_discrete_sequence=CHART_COLORS)
    fig.update_layout(showlegend=bool(color))
    return _apply_layout(fig, height)


def line_chart(df, x, y, title="", height=380, color=None, markers=True):
    fig = px.line(df, x=x, y=y, title=title, color=color,
                  color_discrete_sequence=CHART_COLORS, markers=markers)
    return _apply_layout(fig, height)


def horizontal_bar(df, x, y, title="", height=380, top_n=10):
    data = df.nlargest(top_n, x).copy()
    fig = px.bar(data, x=x, y=y, title=title, orientation="h",
                 color_discrete_sequence=[TEAL])
    fig.update_layout(yaxis=dict(autorange="reversed"))
    fig.update_xaxes(showgrid=True, gridcolor="#F3F4F6")
    fig.update_yaxes(showgrid=False)
    return _apply_layout(fig, height)


def pie_chart(df, names, values, title="", height=380):
    fig = px.pie(df, names=names, values=values, title=title, hole=0.5,
                 color_discrete_sequence=CHART_COLORS)
    fig.update_traces(textposition="outside", textinfo="percent+label")
    return _apply_layout(fig, height)


def heatmap_chart(df, x, y, z, title="", height=400):
    fig = px.density_heatmap(df, x=x, y=y, z=z, color_continuous_scale=SEQ_SCALE,
                             title=title)
    return _apply_layout(fig, height)


def dual_axis_chart(df, x, y1, y2, title="", height=380, y1_label="", y2_label=""):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=_v(df[x]), y=_v(df[y1]), name=y1.replace("_", " ").title(),
                         marker_color=TEAL, yaxis="y", opacity=0.85))
    fig.add_trace(go.Scatter(x=_v(df[x]), y=_v(df[y2]), name=y2.replace("_", " ").title(),
                             mode="lines+markers", line=dict(color=YELLOW, width=2.5),
                             marker=dict(size=6), yaxis="y2"))
    fig.update_layout(
        title=title,
        yaxis=dict(title=y1_label or y1.replace("_", " ").title()),
        yaxis2=dict(title=y2_label or y2.replace("_", " ").title(),
                    overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        barmode="group")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6")
    return _apply_layout(fig, height)


def area_chart(df, x, y, title="", height=380, color=None):
    fig = px.area(df, x=x, y=y, title=title, color=color,
                  color_discrete_sequence=CHART_COLORS)
    return _apply_layout(fig, height)
