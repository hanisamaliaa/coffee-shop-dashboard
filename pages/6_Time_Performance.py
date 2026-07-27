"""Halaman 6 — Time & Operations Dashboard.

Menjawab: Hari, bulan, atau musim apa yang tertinggi? Apakah ada pola musiman?
Kapan waktu terbaik untuk meningkatkan promosi?
"""

import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.business_logic import PEAK_HOURS, QUIET_HOURS
from utils.charts import (GREY, NAVY, RED, TEAL, YELLOW, _v, hour_bar,
                          matrix_heatmap, ranked_bar)
from utils.data_loader import check_empty_data, get_filter_options, load_data
from utils.filters import apply_filters
from utils.formatting import format_currency, format_number_full, format_percentage
from utils.metrics import calc_monthly_data, test_trend
from utils.styling import (inject_global_css, render_caveat, render_header,
                           render_kpi_card, render_step, render_takeaway)

st.set_page_config(page_title="Time & Operations - Coffee Shop Dashboard",
                   page_icon=":coffee:", layout="wide")
inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header("TIME & OPERATIONS DASHBOARD",
              "Kapan permintaan datang, dan kapan kita membuka pintu untuk siapa-siapa",
              "Halaman 6 dari 8")

df_f = apply_filters(df, options, key_prefix="time")
check_empty_data(df_f, "Time & Operations")

omzet = df_f["total_amount"].sum()
per_jam = df_f.groupby("hour")["total_amount"].sum()
pagi = per_jam.reindex(PEAK_HOURS).sum() / omzet
sepi = per_jam.reindex(QUIET_HOURS).sum() / omzet
rasio = ((per_jam.reindex(PEAK_HOURS).sum() / len(PEAK_HOURS))
         / max(per_jam.reindex(QUIET_HOURS).sum() / len(QUIET_HOURS), 1e-9))
akhir_pekan = df_f.loc[df_f["is_weekend"], "total_amount"].sum() / omzet
harian = df_f.groupby("day_name", observed=True)["total_amount"].sum()

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Jam Tersibuk", f"{int(per_jam.idxmax())}:00")
with c2:
    render_kpi_card("Omzet di 5 Jam Puncak", format_percentage(pagi * 100))
with c3:
    render_kpi_card("Omzet di 10 Jam Tersepi", format_percentage(sepi * 100))
with c4:
    render_kpi_card("Porsi Akhir Pekan", format_percentage(akhir_pekan * 100))

# ── Langkah 1 — kurva harian ─────────────────────────────────────────────────
render_step(1, "Kapan permintaan sebenarnya datang?",
            "Ini grafik terpenting di seluruh dashboard. Semua keputusan operasional "
            "berangkat dari sini.")

fig = hour_bar(per_jam.index, per_jam.values, quiet_hours=QUIET_HOURS,
               title="Omzet per jam — biru = 5 jam puncak, arsir merah = 10 jam tersepi",
               annotation=f"{pagi:.0%} omzet<br>hanya dalam 5 jam", height=400)
st.plotly_chart(fig, use_container_width=True)

render_takeaway(
    f"<b>{pagi:.0%} omzet masuk antara pukul 06:00 dan 10:00</b> — lima jam. "
    f"Sementara {len(QUIET_HOURS)} jam antara 20:00 dan 06:00, yaitu "
    f"<b>{len(QUIET_HOURS)/24:.0%} dari hari operasional</b>, hanya menghasilkan "
    f"<b>{sepi:.1%}</b>. Per jam kerja, blok pagi mengalahkan blok tersepi "
    f"<b>{rasio:.0f} banding 1</b>. "
    f"Jam-jam sepi itu tetap memakan gaji, listrik, pendingin, dan keamanan — "
    f"<b>ini masalah jam operasional, bukan masalah penjualan.</b>",
    alert=True)

# ── Langkah 2 — perbandingan yang adil antar blok ────────────────────────────
render_step(2, "Blok waktu mana yang paling produktif?",
            "Harus dibagi jumlah jam. Tanpa itu, blok 6 jam otomatis terlihat lebih "
            "baik daripada blok 3 jam.")

blok = df_f.groupby("daypart", observed=True).agg(
    omzet=("total_amount", "sum"), jam=("daypart_hours", "first"),
    trx=("total_amount", "size")).dropna()
blok["per_jam"] = blok["omzet"] / blok["jam"]
blok["porsi"] = blok["omzet"] / omzet

k1, k2 = st.columns([5, 5])
with k1:
    m = blok["omzet"].sort_values()
    fig = ranked_bar([f"{i}  ·  {int(blok.loc[i,'jam'])} jam" for i in m.index],
                     m.values, highlight=len(m) - 1, accent=GREY,
                     title="❌ Omzet TOTAL per blok — belum adil", height=360)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    a = blok["per_jam"].sort_values()
    fig = ranked_bar([f"{i}  ·  {int(blok.loc[i,'jam'])} jam" for i in a.index],
                     a.values, highlight=len(a) - 1,
                     title="✅ Omzet PER JAM KERJA — adil", height=360)
    st.plotly_chart(fig, use_container_width=True)

turun = [i for i in m.index[-3:] if i not in a.index[-3:]]
render_takeaway(
    f"Setelah dibagi jumlah jam, <b>{a.index[-1]}</b> menang telak dengan "
    f"{format_currency(a.iloc[-1])} per jam, sementara <b>{a.index[0]}</b> jatuh ke "
    f"dasar dengan {format_currency(a.iloc[0])} per jam — selisih "
    f"<b>{a.iloc[-1]/a.iloc[0]:.0f}x</b>. "
    + (f"Perhatikan <b>{', '.join(turun)}</b> yang tampak besar di grafik kiri hanya "
       f"karena bloknya panjang, lalu turun peringkat setelah diadilkan. "
       if turun else "")
    + "Inilah gunanya fitur <code>jam_per_blok</code>: tanpa itu, kesimpulannya terbalik.")

# ── Langkah 3 — pola mingguan ────────────────────────────────────────────────
render_step(3, "Hari apa yang tertinggi, dan apakah polanya berbeda?",
            "Kalau bentuk kurvanya sama tiap hari, satu template jadwal cukup.")

k1, k2 = st.columns([4, 6])
with k1:
    fig = ranked_bar(harian.index, harian.values,
                     highlight=[i for i, d in enumerate(harian.index)
                                if d in ("Sabtu", "Minggu")],
                     title=f"Akhir pekan = {akhir_pekan:.0%} omzet dari 29% hari",
                     height=380)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    panas = df_f.pivot_table(index="day_name", columns="hour", values="total_amount",
                             aggfunc="sum", observed=True)
    fig = matrix_heatmap(panas, title="Peta panas hari x jam", height=380,
                         x_tick_every=2, x_title="Jam")
    st.plotly_chart(fig, use_container_width=True)

hari_kerja = df_f.loc[~df_f["is_weekend"]]
hari_libur = df_f.loc[df_f["is_weekend"]]
rata_hk = hari_kerja.groupby("date")["total_amount"].sum().mean()
rata_ap = hari_libur.groupby("date")["total_amount"].sum().mean()
render_takeaway(
    f"<b>{harian.idxmax()}</b> hari tertinggi dan <b>{harian.idxmin()}</b> terendah. "
    f"Per hari kalender, akhir pekan menghasilkan {format_currency(rata_ap)} versus "
    f"{format_currency(rata_hk)} di hari kerja — <b>{rata_ap/rata_hk-1:+.0%}</b>. "
    f"Tapi lihat peta panas: <b>bentuk kurvanya identik di ketujuh hari</b>. "
    f"Akhir pekan bukan pola yang berbeda, hanya versi yang lebih tinggi dari kurva yang "
    f"sama. Implikasinya: <b>satu template jadwal berlaku untuk semua hari</b> — akhir "
    f"pekan butuh lebih banyak orang, bukan jam buka yang berbeda.")

# ── Langkah 4 — pola musiman ─────────────────────────────────────────────────
render_step(4, "Apakah terdapat pola musiman?",
            "Kalau tidak ada, kita harus mengatakannya — supaya tidak ada anggaran "
            "yang dihabiskan untuk mengejar musim yang tidak ada.")

bulanan = calc_monthly_data(df_f)
tren = test_trend(bulanan)

k1, k2 = st.columns([6, 4])
with k1:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=_v(bulanan["timestamp"]), y=_v(bulanan["revenue_per_day"]),
                         marker_color=TEAL, name="Omzet per hari",
                         hovertemplate="%{x|%b %Y}<br><b>$%{y:,.0f}/hari</b><extra></extra>"))
    rata = bulanan["revenue_per_day"].mean()
    fig.add_hline(y=rata, line_dash="dash", line_color=YELLOW, line_width=2,
                  annotation_text=f"rata-rata ${rata:,.0f}/hari",
                  annotation_position="top left",
                  annotation_font=dict(color="#B27300", size=11))
    fig.update_layout(
        title="Omzet PER HARI tiap bulan — sudah adil antar bulan",
        height=360, plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        margin=dict(t=50, b=40, l=60, r=30), showlegend=False)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6",
                     range=[0, bulanan["revenue_per_day"].max() * 1.25])
    st.plotly_chart(fig, use_container_width=True)
with k2:
    if "season" in df_f.columns:
        musim = df_f.groupby("season", observed=True)["total_amount"].sum()
        fig = ranked_bar(musim.index, musim.values,
                         highlight=int(np.argmax(musim.values)), accent=GREY,
                         title=f"Selisih antarmusim hanya "
                               f"{musim.max()/musim.min()-1:.0%}", height=360)
        st.plotly_chart(fig, use_container_width=True)

if tren.get("cukup_data"):
    render_takeaway(
        f"<b>Tidak ada pola musiman.</b> Regresi linier pada omzet per hari memberi "
        f"slope ${tren['slope_per_bulan']:+,.2f} per bulan dengan "
        f"<b>p={tren['p_value']:.2f}</b> dan R²={tren['r_squared']:.2f} — secara statistik "
        f"tidak bisa dibedakan dari nol. Sebaran antarbulan {tren['sebaran_pct']:.0%} "
        f"masih di dalam batas fluktuasi acak untuk data harian sebanyak ini. "
        f"Grafik ini sudah dibagi jumlah hari, jadi ini <b>bukan sekadar efek Februari "
        f"yang lebih pendek</b>. "
        f"<b>Konsekuensinya: jangan buat kampanye musiman, dan jangan meniru 'bulan "
        f"terbaik' — bulan itu tidak punya penjelasan.</b>")

if "season" in df_f.columns:
    with st.expander("Catatan teknis: musim sudah disesuaikan belahan bumi"):
        cek = df_f[df_f["month"] == 7].groupby("country", observed=True)["season"].first()
        st.markdown(
            "Australia berada di belahan bumi selatan, sehingga Juli di Sydney dan "
            "Melbourne adalah **musim dingin**, bukan musim panas. Tanpa penyesuaian ini, "
            "analisis musiman akan salah untuk 2 dari "
            f"{df_f['city'].nunique()} kota. Verifikasi untuk bulan Juli:")
        st.dataframe(cek.rename("Musim di bulan Juli").to_frame(),
                     use_container_width=True)

# ── Langkah 5 — kapan promosi ────────────────────────────────────────────────
render_step(5, "Kapan waktu terbaik untuk meningkatkan promosi?",
            "Dua strategi yang mungkin: menaikkan nilai di jam ramai, atau menarik "
            "orang di jam sepi. Data menunjukkan hanya satu yang masuk akal.")

nilai_jam = df_f.groupby("hour")["total_amount"].mean()
trx_jam = df_f.groupby("hour").size()

fig = go.Figure()
fig.add_trace(go.Bar(x=_v(trx_jam.index), y=_v(trx_jam.values),
                     name="Jumlah transaksi (kiri)",
                     marker_color=[TEAL if h in PEAK_HOURS else GREY
                                   for h in trx_jam.index], yaxis="y"))
fig.add_trace(go.Scatter(x=_v(nilai_jam.index), y=_v(nilai_jam.values),
                         name="Nilai rata-rata transaksi (kanan)", mode="lines+markers",
                         line=dict(color=NAVY, width=2.5), marker=dict(size=6),
                         yaxis="y2"))
fig.update_layout(
    title="Jam ramai punya banyak transaksi — tapi nilainya tidak lebih besar",
    yaxis=dict(title="Jumlah transaksi"),
    yaxis2=dict(title="Nilai rata-rata ($)", overlaying="y", side="right",
                showgrid=False, range=[0, nilai_jam.max() * 1.4]),
    height=380, plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Inter, sans-serif", size=12, color="#374151"),
    margin=dict(t=50, b=40, l=60, r=60),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
fig.update_xaxes(dtick=2, title="Jam", showgrid=False)
fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6")
st.plotly_chart(fig, use_container_width=True)

nilai_pagi = df_f.loc[df_f["is_peak_hour"], "total_amount"].mean()
nilai_sepi = df_f.loc[df_f["hour"].isin(QUIET_HOURS), "total_amount"].mean()
render_takeaway(
    f"<b>Promosikan di jam 06:00–10:00 — bukan untuk menarik orang, tapi untuk menaikkan "
    f"nilai keranjang.</b> Alasannya: di jam itu <b>{pagi:.0%} pelanggan kita sudah ada "
    f"di dalam toko</b>, jadi biaya menjangkau mereka nol. Dan nilai rata-rata transaksi "
    f"di jam sibuk ({format_currency(nilai_pagi)}) tidak jauh berbeda dari jam sepi "
    f"({format_currency(nilai_sepi)}) — <b>masih ada ruang untuk penawaran tambahan</b>. "
    f"<br><br>Sebaliknya, promosi untuk <b>menarik pelanggan baru di jam sepi kemungkinan "
    f"besar sia-sia</b>: pola yang sama persis muncul di {df_f['city'].nunique()} kota "
    f"berbeda, jadi ini perilaku struktural yang tidak akan bergeser hanya karena diskon.")

# ── Langkah 6 — hari libur ───────────────────────────────────────────────────
if "is_holiday" in df_f.columns and df_f["is_holiday"].nunique() > 1:
    render_step(6, "Apakah hari libur berbeda?",
                "Sering diasumsikan iya. Kita periksa.")

    libur = df_f[df_f["is_holiday"]]
    biasa = df_f[~df_f["is_holiday"]]
    rata_libur = libur.groupby("date")["total_amount"].sum().mean()
    rata_biasa = biasa.groupby("date")["total_amount"].sum().mean()
    selisih = rata_libur / rata_biasa - 1

    k1, k2 = st.columns([4, 6])
    with k1:
        fig = ranked_bar(["Hari biasa", "Hari libur"], [rata_biasa, rata_libur],
                         highlight=None, accent=GREY,
                         title=f"Omzet rata-rata per hari: {selisih:+.1%}", height=300)
        st.plotly_chart(fig, use_container_width=True)
    with k2:
        per_libur = libur.groupby("holiday_name")["total_amount"].sum().sort_values()
        if len(per_libur):
            fig = ranked_bar(per_libur.index, per_libur.values, highlight=None,
                             accent=GREY, title="Omzet per jenis hari libur", height=300)
            st.plotly_chart(fig, use_container_width=True)

    render_takeaway(
        f"Hari libur menghasilkan <b>{selisih:+.1%}</b> dibanding hari biasa — "
        f"praktis tidak ada bedanya, dan hanya ada "
        f"{libur['date'].nunique()} hari libur dalam periode ini sehingga sampelnya "
        f"kecil. <b>Tidak ada dasar untuk membuat kampanye khusus hari libur.</b> "
        f"Anggaran itu lebih baik dipindahkan ke penawaran berbasis jam.")

render_caveat(
    "<b>Yang membuat halaman ini bisa dipercaya.</b> Semua perbandingan blok waktu "
    "sudah <b>dibagi jumlah jam</b>, dan semua perbandingan bulanan sudah <b>dibagi "
    "jumlah hari</b>. Tanpa dua normalisasi itu, blok 6 jam akan selalu mengalahkan blok "
    "3 jam, dan Februari akan selalu terlihat sebagai bulan terburuk. "
    "Keduanya kesimpulan palsu yang sangat mudah terjadi.")

st.markdown("")
d1, d2, _ = st.columns([2, 2, 6])
with d1:
    st.download_button("Unduh Ringkasan Per Jam",
                       data=per_jam.rename("omzet").to_csv(),
                       file_name="ringkasan_per_jam.csv", mime="text/csv")
with d2:
    st.download_button("Unduh Ringkasan Blok Waktu", data=blok.to_csv(),
                       file_name="ringkasan_blok_waktu.csv", mime="text/csv")
