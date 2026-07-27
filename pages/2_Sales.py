"""Halaman 2 — Sales Dashboard.

Menjawab: Bagaimana performa penjualan? Bagaimana tren dari waktu ke waktu?
Kapan penjualan tertinggi dan terendah? Kategori apa yang paling berkontribusi?
"""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.charts import matrix_heatmap, ranked_bar, trend_line
from utils.data_loader import check_empty_data, get_filter_options, load_data
from utils.filters import apply_filters
from utils.formatting import format_currency, format_date_range, format_number_full
from utils.metrics import calc_delta, calc_kpi, calc_monthly_data, test_trend
from utils.styling import (inject_global_css, render_header, render_kpi_card,
                           render_step, render_takeaway)

st.set_page_config(page_title="Sales - Coffee Shop Dashboard",
                   page_icon=":coffee:", layout="wide")
inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header("SALES DASHBOARD",
              "Kapan dan dari mana omzet benar-benar masuk",
              "Halaman 2 dari 8")

df_f = apply_filters(df, options, key_prefix="sales")
check_empty_data(df_f, "Sales")

kpi = calc_kpi(df_f)
delta = calc_delta(df_f)
bulanan = calc_monthly_data(df_f)
tren = test_trend(bulanan)
omzet = kpi["total_revenue"]

st.caption(f"{format_date_range(df_f['timestamp'].min(), df_f['timestamp'].max())}  ·  "
           f"{len(df_f):,} transaksi  ·  perbandingan KPI: {delta.get('label') or 'n/a'}")

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    render_kpi_card("Total Omzet", format_currency(omzet), delta.get("revenue"))
with c2:
    render_kpi_card("Transaksi", format_number_full(kpi["total_transactions"]),
                    delta.get("transactions"))
with c3:
    render_kpi_card("Unit Terjual", format_number_full(kpi["total_quantity"]),
                    delta.get("quantity"))
with c4:
    render_kpi_card("Nilai Rata-rata", format_currency(kpi["avg_transaction"]),
                    delta.get("avg_txn"))
with c5:
    render_kpi_card("Nilai Median", format_currency(kpi["median_transaction"]))

if kpi["median_transaction"] and kpi["avg_transaction"] > kpi["median_transaction"] * 1.2:
    render_takeaway(
        f"Perhatikan selisih <b>rata-rata ({format_currency(kpi['avg_transaction'])})</b> "
        f"dan <b>median ({format_currency(kpi['median_transaction'])})</b>: rata-rata "
        f"{kpi['avg_transaction']/kpi['median_transaction']-1:.0%} lebih tinggi. "
        f"Distribusinya miring ke kanan — banyak transaksi kecil, sedikit transaksi "
        f"sangat besar (pesanan rombongan). Untuk menggambarkan 'transaksi biasa' "
        f"<b>pakai median</b>; rata-rata akan terlalu optimistis.")

# ── Langkah 1 — tren ─────────────────────────────────────────────────────────
render_step(1, "Bagaimana tren penjualan dari waktu ke waktu?",
            "Satu bulan naik bukan berarti tren. Kita uji apakah pergerakannya nyata.")

k1, k2 = st.columns([5, 5])
with k1:
    fig = trend_line(bulanan["timestamp"], bulanan["revenue"],
                     title="Omzet bulanan (nilai mentah)", height=360)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    fig = trend_line(bulanan["timestamp"], bulanan["revenue_per_day"],
                     title="Omzet PER HARI (adil antar bulan)", height=360)
    st.plotly_chart(fig, use_container_width=True)

if tren.get("cukup_data"):
    tertinggi = bulanan.loc[bulanan["revenue"].idxmax()]
    terendah = bulanan.loc[bulanan["revenue"].idxmin()]
    if tren["ada_tren"]:
        arah = "naik" if tren["slope_per_bulan"] > 0 else "turun"
        render_takeaway(
            f"Ada tren <b>{arah}</b> yang nyata: ${tren['slope_per_bulan']:+,.1f} per hari "
            f"setiap bulan (p={tren['p_value']:.3f}, R²={tren['r_squared']:.2f}).",
            alert=(tren["slope_per_bulan"] < 0))
    else:
        render_takeaway(
            f"Bulan tertinggi <b>{tertinggi['timestamp'].strftime('%B')}</b> "
            f"({format_currency(tertinggi['revenue'])}) dan terendah "
            f"<b>{terendah['timestamp'].strftime('%B')}</b> "
            f"({format_currency(terendah['revenue'])}) — <b>tapi jangan menirunya.</b> "
            f"Regresi pada omzet per hari memberi slope hampir nol "
            f"(p={tren['p_value']:.2f}), dan sebaran {tren['sebaran_pct']:.0%} masih di "
            f"dalam batas fluktuasi acak. Grafik kanan membuktikan ini bukan soal jumlah "
            f"hari: setelah dibagi jumlah hari, sebarannya tidak mengecil. "
            f"<b>Tidak ada 'bulan puncak' yang punya penjelasan.</b>")

# ── Langkah 2 — kapan tertinggi & terendah ───────────────────────────────────
render_step(2, "Kapan penjualan tertinggi dan terendah?",
            "Pola mingguan jauh lebih kuat dan lebih bisa ditindaklanjuti "
            "daripada pola bulanan.")

akhir_pekan = df_f.loc[df_f["is_weekend"], "total_amount"].sum() / omzet
k1, k2 = st.columns([5, 5])
with k1:
    harian = df_f.groupby("day_name", observed=True)["total_amount"].sum()
    fig = ranked_bar(harian.index, harian.values,
                     highlight=[i for i, d in enumerate(harian.index)
                                if d in ("Sabtu", "Minggu")],
                     title=f"Akhir pekan menyumbang {akhir_pekan:.0%} omzet dari 29% hari",
                     height=360)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    blok = df_f.groupby("daypart", observed=True).agg(
        omzet=("total_amount", "sum"), jam=("daypart_hours", "first")).dropna()
    blok["per_jam"] = blok["omzet"] / blok["jam"]
    blok = blok.sort_values("per_jam")
    label = [f"{i}  ·  {int(h)} jam" for i, h in zip(blok.index, blok["jam"])]
    fig = ranked_bar(label, blok["per_jam"], highlight=len(blok) - 1,
                     title="Omzet PER JAM KERJA tiap blok waktu", height=360)
    st.plotly_chart(fig, use_container_width=True)

render_takeaway(
    f"<b>Sabtu dan Minggu adalah dua hari terbaik</b> — akhir pekan menghasilkan "
    f"{akhir_pekan:.0%} omzet padahal cuma 29% dari jumlah hari. "
    f"Grafik kanan sengaja dibagi jumlah jam tiap blok: tanpa itu, blok 6 jam otomatis "
    f"terlihat lebih baik dari blok 3 jam. Setelah diadilkan, "
    f"<b>Puncak Pagi menang telak</b> — dan blok Dini Hari serta Malam jatuh ke dasar "
    f"meskipun jamnya paling panjang.")

# ── Langkah 3 — kontributor omzet ────────────────────────────────────────────
render_step(3, "Kategori dan produk apa yang paling berkontribusi?",
            "Kontribusi diukur dari omzet, bukan dari jumlah transaksi.")

kat = df_f.groupby("product_category", observed=True)["total_amount"].sum().sort_values()
k1, k2 = st.columns([5, 5])
with k1:
    fig = ranked_bar(kat.index, kat.values, highlight=len(kat) - 1,
                     title=f"{kat.index[-1]} menyumbang {kat.iloc[-1]/omzet:.0%} omzet",
                     height=360)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    top = df_f.groupby("product_name")["total_amount"].sum().nlargest(10).sort_values()
    fig = ranked_bar(top.index, top.values, highlight=len(top) - 1,
                     title=f"{top.index[-1]} — produk beromzet tertinggi", height=360)
    st.plotly_chart(fig, use_container_width=True)

teratas = df_f.groupby("product_name")["total_amount"].sum().nlargest(1)
kat_teratas = df_f.loc[df_f["product_name"] == teratas.index[0], "product_category"].iloc[0]
render_takeaway(
    f"<b>{kat.index[-1]}</b> mendominasi dengan {kat.iloc[-1]/omzet:.0%} omzet. "
    f"Tapi produk tunggal beromzet tertinggi adalah <b>{teratas.index[0]}</b> "
    f"({format_currency(teratas.iloc[0])}) dari kategori <b>{kat_teratas}</b> — "
    f"kategori yang justru paling jarang dibeli. "
    f"Dua grafik ini menjawab pertanyaan berbeda: kiri untuk keputusan "
    f"<b>persediaan</b>, kanan untuk keputusan <b>penempatan di toko</b>.")

# ── Langkah 4 — pola gabungan hari x jam ─────────────────────────────────────
render_step(4, "Apakah polanya berubah antar hari?",
            "Kalau bentuk kurvanya sama setiap hari, satu template jadwal cukup "
            "untuk seminggu penuh.")

panas = df_f.pivot_table(index="day_name", columns="hour", values="total_amount",
                         aggfunc="sum", observed=True)
fig = matrix_heatmap(panas, title="Omzet per hari x jam", height=340,
                     x_tick_every=2, x_title="Jam")
st.plotly_chart(fig, use_container_width=True)

render_takeaway(
    "<b>Bentuk kurvanya identik di ketujuh hari.</b> Akhir pekan bukan pola yang "
    "berbeda — hanya versi yang lebih tinggi dari kurva yang sama. "
    "Implikasi operasionalnya langsung: <b>satu template jadwal berlaku untuk semua "
    "hari</b>; akhir pekan butuh lebih banyak orang, bukan jam buka yang berbeda.")

# ── Langkah 5 — metode pembayaran ────────────────────────────────────────────
if "payment_method" in df_f.columns:
    render_step(5, "Bagaimana pelanggan membayar?",
                "Relevan untuk keputusan biaya transaksi dan kebutuhan kas di toko.")
    bayar = df_f.groupby("payment_method")["total_amount"].sum().sort_values()
    fig = ranked_bar(bayar.index, bayar.values, highlight=len(bayar) - 1,
                     title="Omzet per metode pembayaran", height=300)
    st.plotly_chart(fig, use_container_width=True)
    tunai = bayar.get("Cash", 0) / omzet
    render_takeaway(
        f"Metode pembayaran tersebar cukup merata — hanya "
        f"{bayar.max()/bayar.min():.2f}x antara yang tertinggi dan terendah, jadi tidak "
        f"ada satu metode yang bisa dinegosiasikan biayanya secara signifikan. "
        f"Uang tunai masih <b>{tunai:.0%} omzet</b>, sehingga kebutuhan kas di toko "
        f"belum bisa dihilangkan.")

st.markdown("")
d1, d2, _ = st.columns([2, 2, 6])
with d1:
    st.download_button("Unduh Ringkasan Bulanan", data=bulanan.to_csv(index=False),
                       file_name="ringkasan_bulanan.csv", mime="text/csv")
with d2:
    st.download_button("Unduh Ringkasan Kategori",
                       data=kat.sort_values(ascending=False).to_csv(),
                       file_name="ringkasan_kategori.csv", mime="text/csv")
