"""Halaman 1 — Executive Summary.

Menjawab: Bagaimana kondisi bisnis secara keseluruhan? Apakah bisnis sehat?
KPI utama apa yang perlu diperhatikan?
"""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.business_logic import PEAK_HOURS, PROFIT_DISCLAIMER, QUIET_HOURS
from utils.charts import NAVY, TEAL, donut, hour_bar, ranked_bar, trend_line
from utils.data_loader import check_empty_data, get_filter_options, has_profit, load_data
from utils.filters import apply_filters
from utils.formatting import (format_currency, format_date_range,
                              format_number_full, format_percentage)
from utils.metrics import (calc_delta, calc_findings, calc_kpi, calc_monthly_data,
                           calc_opportunities, calc_recommendations, test_trend)
from utils.styling import (inject_global_css, render_caveat, render_findings,
                           render_header, render_kpi_card, render_recommendations,
                           render_step, render_takeaway)

st.set_page_config(page_title="Executive Summary - Coffee Shop Dashboard",
                   page_icon=":coffee:", layout="wide")
inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header("EXECUTIVE SUMMARY",
              "Apakah bisnis ini sehat, dan di mana keputusan terbesarnya?",
              format_date_range(options.get("date_min"), options.get("date_max")))

df_f = apply_filters(df, options, key_prefix="exec")
check_empty_data(df_f, "Executive Summary")

kpi = calc_kpi(df_f)
delta = calc_delta(df_f)
bulanan = calc_monthly_data(df_f)
tren = test_trend(bulanan)
omzet = kpi["total_revenue"]

periode = format_date_range(df_f["timestamp"].min(), df_f["timestamp"].max())
st.caption(
    f"{periode}  ·  {len(df_f):,} transaksi  ·  "
    f"{df_f['store_id'].nunique() if 'store_id' in df_f else 0} toko  ·  "
    f"Angka perubahan di bawah membandingkan **{delta.get('label') or 'periode terakhir'}**"
)

# ── KPI ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    render_kpi_card("Total Omzet", format_currency(omzet), delta.get("revenue"))
with c2:
    if has_profit(df_f):
        render_kpi_card("Estimasi Laba Kotor", format_currency(kpi["total_profit"]),
                        delta.get("profit"))
    else:
        render_kpi_card("Total Kuantitas", format_number_full(kpi["total_quantity"]))
with c3:
    render_kpi_card("Transaksi", format_number_full(kpi["total_transactions"]),
                    delta.get("transactions"))
with c4:
    render_kpi_card("Nilai Transaksi Rata-rata", format_currency(kpi["avg_transaction"]),
                    delta.get("avg_txn"))
with c5:
    render_kpi_card("Pelanggan Unik", format_number_full(kpi["unique_customers"]))

# ── Langkah 1 — sehat atau tidak ─────────────────────────────────────────────
render_step(1, "Apakah bisnis ini sehat?",
            "Pertanyaan pertama yang selalu ditanya direksi. Jawabannya ada di "
            "bentuk garis, bukan di angka satu bulan.")

k1, k2 = st.columns([7, 3])
with k1:
    if not bulanan.empty:
        fig = trend_line(bulanan["timestamp"], bulanan["revenue"],
                         title="Omzet bulanan", name="Omzet", height=380)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Data tidak cukup untuk menampilkan tren.")
with k2:
    kat = df_f.groupby("product_category", observed=True)["total_amount"].sum() \
              .sort_values(ascending=False)
    fig = donut(kat.index, kat.values, title="Kontribusi kategori", height=380,
                center_text=f"{format_currency(omzet)}<br><span style='font-size:11px'>total omzet</span>")
    st.plotly_chart(fig, use_container_width=True)

if tren.get("cukup_data"):
    if tren["ada_tren"]:
        arah = "naik" if tren["slope_per_bulan"] > 0 else "turun"
        render_takeaway(
            f"Omzet <b>{arah} secara konsisten</b> — regresi linier pada omzet per hari "
            f"memberi slope ${tren['slope_per_bulan']:+,.1f} per bulan dengan "
            f"p={tren['p_value']:.3f}. Ini tren nyata yang perlu ditindaklanjuti.",
            alert=(tren["slope_per_bulan"] < 0))
    else:
        render_takeaway(
            f"<b>Bisnis ini sehat, tapi tidak tumbuh.</b> Omzet datar sepanjang periode: "
            f"regresi pada omzet per hari memberi slope hampir nol "
            f"(p={tren['p_value']:.2f}, R²={tren['r_squared']:.2f}). "
            f"Sebaran antarbulan {tren['sebaran_pct']:.0%} <b>masih di dalam batas "
            f"fluktuasi acak</b>, jadi tidak ada pola musiman yang bisa dimanfaatkan — "
            f"dan tidak ada 'bulan puncak' yang perlu ditiru. "
            f"Artinya <b>tidak satu pun program yang berjalan tahun ini menghasilkan "
            f"pertumbuhan</b>.")

# ── Langkah 2 — dari mana omzet datang ───────────────────────────────────────
render_step(2, "Dari mana omzet itu datang?",
            "Kalau permintaan menumpuk di jam tertentu, itu mengubah keputusan "
            "jadwal staf, jam buka, dan waktu promosi.")

if "hour" in df_f.columns:
    per_jam = df_f.groupby("hour")["total_amount"].sum()
    pagi = per_jam.reindex(PEAK_HOURS).sum() / omzet
    sepi = per_jam.reindex(QUIET_HOURS).sum() / omzet
    rasio = ((per_jam.reindex(PEAK_HOURS).sum() / len(PEAK_HOURS))
             / max(per_jam.reindex(QUIET_HOURS).sum() / len(QUIET_HOURS), 1e-9))

    fig = hour_bar(per_jam.index, per_jam.values, quiet_hours=QUIET_HOURS,
                   title="Omzet per jam — biru = jam sibuk, arsir merah = jam tersepi",
                   annotation=f"{pagi:.0%} omzet<br>hanya dalam 5 jam", height=380)
    st.plotly_chart(fig, use_container_width=True)

    render_takeaway(
        f"<b>{pagi:.0%} omzet masuk hanya dalam 5 jam</b> (06:00–10:00), sementara "
        f"{len(QUIET_HOURS)} jam tersepi (20:00–06:00) — <b>{len(QUIET_HOURS)/24:.0%} dari "
        f"hari operasional</b> — cuma menghasilkan {sepi:.1%}. Per jam kerja, pagi "
        f"mengalahkan blok tersepi <b>{rasio:.0f} banding 1</b>. "
        f"Ini bisnis minuman pagi yang membayar untuk beroperasi seperti toko 24 jam.",
        alert=True)

# ── Langkah 3 — peluang terukur ──────────────────────────────────────────────
render_step(3, "Di mana peluang terbesarnya?",
            "Hanya aksi yang punya angka dari data. Yang tidak bisa dihitung, "
            "kami katakan tidak bisa dihitung.")

peluang = calc_opportunities(df_f)
if not peluang.empty:
    k1, k2 = st.columns([5, 5])
    with k1:
        urut = peluang.sort_values("Nilai per tahun")
        fig = ranked_bar(urut["Aksi"], urut["Nilai per tahun"],
                         highlight=len(urut) - 1,
                         title=f"Total terukur: +{peluang['% omzet'].sum():.1%} omzet "
                               f"({format_currency(peluang['Nilai per tahun'].sum())}/tahun)",
                         height=340)
        st.plotly_chart(fig, use_container_width=True)
    with k2:
        tampil = peluang.copy()
        tampil["Nilai per tahun"] = tampil["Nilai per tahun"].map(lambda v: f"${v:,.0f}")
        tampil["% omzet"] = tampil["% omzet"].map(lambda v: f"{v:.2%}")
        st.dataframe(tampil[["Aksi", "Nilai per tahun", "% omzet", "Dasarnya"]],
                     hide_index=True, use_container_width=True, height=340)

    render_takeaway(
        f"Empat aksi ini <b>tidak tumpang tindih</b> — angka loyalty sudah dikurangi "
        f"diskon yang masuk hitungan 'batasi 15%+', jadi totalnya tidak menghitung dolar "
        f"yang sama dua kali. Bersama-sama nilainya "
        f"<b>+{peluang['% omzet'].sum():.1%} omzet</b>. "
        f"<b>Tapi peluang terbesar tidak ada di tabel ini:</b> menutup 20:00–06:00 "
        f"menyentuh 42% jam operasional. Kami sengaja tidak memberinya angka dolar karena "
        f"biaya gaji dan listrik <b>tidak ada di dataset</b> — satu angka dari Finance "
        f"akan menyelesaikannya.")

# ── Temuan & rekomendasi ─────────────────────────────────────────────────────
render_step(4, "Temuan utama", "Lima hal yang paling perlu diketahui direksi.")
render_findings(calc_findings(df_f, bulanan))

render_step(5, "Tindakan yang direkomendasikan",
            "Setiap rekomendasi membawa angkanya sendiri. Daftar lengkap 12 rekomendasi "
            "ada di halaman Rekomendasi.")
render_recommendations(calc_recommendations(df_f, bulanan))

# ── Catatan batasan ──────────────────────────────────────────────────────────
batasan = [f"<b>Laba adalah estimasi.</b> {PROFIT_DISCLAIMER}"]
if "customer_id" in df_f.columns:
    sekali = (df_f.groupby("customer_id").size() == 1).mean()
    if sekali > 0.5:
        batasan.append(
            f"<b>Retensi tidak bisa diukur.</b> {sekali:.0%} pelanggan hanya muncul "
            f"sekali dalam periode ini, sehingga CLV, churn, dan analisis cohort tidak "
            f"bisa dihitung dari data ini. Perlu konfirmasi apakah customer_id tersimpan "
            f"lintas kunjungan.")
batasan.append(
    "<b>Verdict loyalty adalah hipotesis, bukan kesimpulan.</b> Satu tahun data tidak "
    "bisa melihat efek merek — karena itu rekomendasinya uji holdout, bukan pembatalan.")
render_caveat("<br><br>".join(batasan))

st.markdown("")
d1, d2, _ = st.columns([2, 2, 6])
with d1:
    st.download_button("Unduh Data Terfilter", data=df_f.to_csv(index=False),
                       file_name="executive_summary_filtered.csv", mime="text/csv")
with d2:
    if not bulanan.empty:
        st.download_button("Unduh Ringkasan Bulanan", data=bulanan.to_csv(index=False),
                           file_name="ringkasan_bulanan.csv", mime="text/csv")
