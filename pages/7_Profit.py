"""Halaman 7 — Profit Dashboard.

Menjawab pertanyaan PPT:
  - Apa penyebab utama penurunan profit?
  - Bagaimana dampak diskon terhadap profit?
"""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.business_logic import COGS_RATIO, PROFIT_DISCLAIMER, QUIET_HOURS
from utils.charts import (NAVY, RED, TEAL, compare_bar, hour_bar, ranked_bar,
                          threshold_bar, trend_line, waterfall)
from utils.data_loader import check_empty_data, get_filter_options, has_profit, load_data
from utils.filters import apply_filters
from utils.formatting import format_currency, format_number_full, format_percentage
from utils.metrics import calc_kpi, calc_delta, calc_monthly_data
from utils.styling import (inject_global_css, render_caveat, render_header,
                           render_kpi_card, render_step, render_takeaway)

st.set_page_config(page_title="Profit - Coffee Shop Dashboard",
                   page_icon=":coffee:", layout="wide")
inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header("PROFIT & DISKON",
              "Dari mana laba datang, dan di mana ia bocor",
              "Halaman 7 dari 8")

if not has_profit(df):
    st.error("Kolom estimasi laba tidak ditemukan. "
             "Jalankan `python scripts/build_processed.py` terlebih dahulu.")
    st.stop()

df_f = apply_filters(df, options, key_prefix="profit")
check_empty_data(df_f, "Profit")

kpi = calc_kpi(df_f)
delta = calc_delta(df_f)
omzet = kpi["total_revenue"]
laba = kpi["total_profit"]
kotor = df_f["gross_amount"].sum()
diskon = kpi["total_discount"]

st.caption(f"{len(df_f):,} transaksi  ·  perbandingan KPI: {delta.get('label') or 'n/a'}")

# ── KPI ──────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Estimasi Laba Kotor", format_currency(laba), delta.get("profit"))
with c2:
    render_kpi_card("Margin Kotor", format_percentage(kpi["profit_margin"] * 100))
with c3:
    render_kpi_card("Total Diskon Diberikan", format_currency(diskon))
with c4:
    render_kpi_card("Realisasi Harga",
                    format_percentage(omzet / kotor * 100 if kotor else 0))

render_caveat(f"<b>Penting:</b> {PROFIT_DISCLAIMER}")

# ── Langkah 1 — transparansi asumsi ──────────────────────────────────────────
render_step(1, "Dari mana angka laba ini berasal?",
            "Dataset tidak punya kolom biaya, jadi kita harus membangunnya — "
            "dan menunjukkan caranya secara terbuka.")

kiri, kanan = st.columns([5, 5])

with kiri:
    asumsi = pd.DataFrame({
        "Kategori": list(COGS_RATIO.keys()),
        "HPP (% harga dasar)": [f"{v:.0%}" for v in COGS_RATIO.values()],
        "Alasan": ["Daun teh sangat murah; harga jual didominasi jasa & tempat",
                   "Biji + susu; margin tinggi adalah ciri khas kedai kopi",
                   "Buah segar, cepat rusak, porsi besar",
                   "Bahan roti + tingkat basi tinggi",
                   "Protein & sayur segar — HPP tertinggi di makanan",
                   "Barang jadi dari pemasok, margin ritel biasa"],
    })
    st.dataframe(asumsi, hide_index=True, use_container_width=True)
    st.markdown(
        "<div style='font-size:0.8rem;color:#6B7280;line-height:1.6;'>"
        "HPP dipatok ke <b>harga dasar produk</b> (harga terendah di jaringan), "
        "bukan ke harga jual di toko itu. Biji kopi harganya sama di mana pun — "
        "kalau HPP dihitung sebagai persen dari harga jual, margin setiap toko "
        "jadi identik dan temuan soal harga lokasi lenyap.</div>",
        unsafe_allow_html=True)

with kanan:
    fig = waterfall(
        ["Omzet Kotor", "Diskon", "HPP (estimasi)", "Laba Kotor"],
        [kotor, -diskon, -df_f["est_cost"].sum(), laba],
        title="Dari omzet kotor sampai laba kotor", height=400)
    st.plotly_chart(fig, use_container_width=True)

render_takeaway(
    f"Dari <b>{format_currency(kotor)}</b> omzet kotor, <b>{format_currency(diskon)}</b> "
    f"({diskon/kotor:.2%}) hilang ke diskon dan <b>{format_currency(df_f['est_cost'].sum())}</b> "
    f"ke HPP, menyisakan <b>{format_currency(laba)}</b> laba kotor "
    f"(margin {kpi['profit_margin']:.0%}). Margin setinggi ini normal untuk kedai kopi "
    f"karena <b>gaji, sewa, dan listrik belum dipotong</b> — biaya itu tidak ada di dataset.")

# ── Langkah 2 — tren laba ────────────────────────────────────────────────────
render_step(2, "Bagaimana tren profit?",
            "Apakah laba menurun, dan kalau ya, karena omzet atau karena margin?")

bulanan = calc_monthly_data(df_f)
if len(bulanan) >= 2:
    bulanan["margin"] = bulanan["profit"] / bulanan["revenue"]
    k1, k2 = st.columns([6, 4])
    with k1:
        fig = trend_line(bulanan["timestamp"], bulanan["profit"],
                         title="Laba kotor bulanan", name="Laba", height=360)
        st.plotly_chart(fig, use_container_width=True)
    with k2:
        fig = trend_line(bulanan["timestamp"], bulanan["margin"] * 100,
                         title="Margin bulanan (%)", name="Margin",
                         avg_line=False, height=360)
        fig.update_yaxes(range=[0, 100], ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True)

    spread_margin = bulanan["margin"].max() - bulanan["margin"].min()
    arah = ("naik" if bulanan["profit"].iloc[-1] > bulanan["profit"].iloc[0] else "turun")
    render_takeaway(
        f"Laba bergerak <b>persis sejajar dengan omzet</b>, dan margin hampir tidak "
        f"bergerak sepanjang periode (rentang hanya {spread_margin:.1%} poin). "
        f"Artinya <b>tidak ada masalah efisiensi</b> yang muncul tiba-tiba — komposisi "
        f"penjualan stabil. Jawaban jujur untuk 'apa penyebab profit turun?': "
        f"<b>profit tidak turun, tapi juga tidak tumbuh</b> ({arah} "
        f"{abs(bulanan['profit'].iloc[-1]/bulanan['profit'].iloc[0]-1):.1%} dari bulan "
        f"pertama ke bulan terakhir).")
else:
    st.info("Perlu minimal 2 bulan data untuk melihat tren.")

# ── Langkah 3 — siapa penghasil laba ─────────────────────────────────────────
render_step(3, "Kategori mana yang menghasilkan laba?",
            "Yang beromzet besar belum tentu yang berlaba besar.")

kat = df_f.groupby("product_category", observed=True).agg(
    omzet=("total_amount", "sum"), laba=("est_profit", "sum"),
    trx=("total_amount", "size")).sort_values("laba")
kat["margin"] = kat["laba"] / kat["omzet"]

k1, k2 = st.columns(2)
with k1:
    fig = ranked_bar(kat.index, kat["laba"], highlight=len(kat) - 1,
                     title=f"{kat.index[-1]} menyumbang laba terbesar", height=380)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    banding = kat.sort_values("margin")
    fig = ranked_bar(banding.index, banding["margin"] * 100,
                     highlight=[0, len(banding) - 1],
                     title="Margin per kategori (%)", value_fmt="{:.0f}%", height=380)
    st.plotly_chart(fig, use_container_width=True)

paling_tipis, paling_tebal = kat["margin"].idxmin(), kat["margin"].idxmax()
rugi_trx = int((df_f["est_profit"] < 0).sum())
rugi_prod = int((df_f.groupby("product_name")["est_profit"].sum() < 0).sum())
render_takeaway(
    f"<b>{kat.index[-1]}</b> penghasil laba terbesar "
    f"({format_currency(kat['laba'].iloc[-1])}). Margin paling tipis ada di "
    f"<b>{paling_tipis}</b> ({kat.loc[paling_tipis,'margin']:.0%}) dan paling tebal di "
    f"<b>{paling_tebal}</b> ({kat.loc[paling_tebal,'margin']:.0%}). "
    f"Tapi perhatikan: <b>{rugi_trx} transaksi dan {rugi_prod} produk yang merugi</b>. "
    f"Kerugian di bisnis ini bukan di produk — melainkan di kebijakan.")

# ── Langkah 4 — dampak diskon (pertanyaan inti PPT) ──────────────────────────
render_step(4, "Bagaimana dampak diskon terhadap profit?",
            "Diskon hanya masuk akal kalau ia membuat orang membeli lebih banyak. "
            "Mari kita uji.")

dasar_unit = df_f.loc[df_f["discount_pct"] == 0, "quantity"].mean()
per_tier = (df_f[df_f["discount_pct"] > 0]
            .groupby("discount_tier", observed=True)
            .agg(unit=("quantity", "mean"), biaya=("discount_amount", "sum"),
                 trx=("quantity", "size")).dropna(subset=["unit"]))

if not per_tier.empty:
    k1, k2 = st.columns([6, 4])
    with k1:
        gagal = int((per_tier["unit"] < dasar_unit).sum())
        fig = threshold_bar(
            [i.replace(" (", "<br>(") for i in per_tier.index],
            per_tier["unit"], threshold=dasar_unit,
            threshold_label=f"tanpa diskon = {dasar_unit:.2f} unit",
            title=f"{gagal} dari {len(per_tier)} tingkat diskon menjual LEBIH SEDIKIT unit",
            yaxis_title="Unit per transaksi", height=380)
        st.plotly_chart(fig, use_container_width=True)
    with k2:
        fig = ranked_bar(
            [i.replace(" (", " (") for i in per_tier.index], per_tier["biaya"],
            highlight=None, accent=RED,
            title="Biaya diskon per tingkat", height=380)
        st.plotly_chart(fig, use_container_width=True)

    bekerja = per_tier[per_tier["unit"] > dasar_unit]
    tidak = per_tier[per_tier["unit"] <= dasar_unit]
    biaya_sia = tidak["biaya"].sum()
    nama_bekerja = ", ".join(bekerja.index) if len(bekerja) else "tidak ada"
    render_takeaway(
        f"Tanpa diskon, pelanggan membeli <b>{dasar_unit:.2f} unit</b> per transaksi. "
        f"Hanya tingkat <b>{nama_bekerja}</b> yang berhasil melampaui angka itu. "
        f"{len(tidak)} tingkat sisanya justru menjual lebih sedikit — artinya diskon itu "
        f"jatuh ke orang yang <b>memang sudah mau membeli</b>. "
        f"Biaya untuk tingkat yang tidak bekerja: <b>{format_currency(biaya_sia)}/tahun</b>, "
        f"dan setiap dolarnya langsung mengurangi laba.",
        alert=True)

# ── Langkah 5 — ke mana uang diskon mengalir ─────────────────────────────────
if "loyalty_member" in df_f.columns and df_f["loyalty_member"].nunique() > 1:
    render_step(5, "Ke mana uang diskon itu mengalir?",
                "Kalau ada satu kelompok yang menyerap sebagian besar diskon, "
                "kita berhak menuntut buktinya.")

    anggota = df_f[df_f["loyalty_member"]]
    non = df_f[~df_f["loyalty_member"]]
    porsi_diskon = anggota["discount_amount"].sum() / diskon if diskon else 0
    porsi_trx = df_f["loyalty_member"].mean()

    kunjungan = df_f.groupby("customer_id").agg(
        n=("transaction_id", "size"), member=("loyalty_member", "first"))
    ret_anggota = (kunjungan.loc[kunjungan["member"], "n"] > 1).mean()
    ret_non = (kunjungan.loc[~kunjungan["member"], "n"] > 1).mean()

    k1, k2 = st.columns([5, 5])
    with k1:
        fig = compare_bar(
            ["Sering dapat diskon (%)", "Datang lagi (%)", "Belanja sebelum diskon ($)"],
            {"Non-anggota": [non["is_discounted"].mean() * 100, ret_non * 100,
                             non["gross_amount"].mean()],
             "Anggota loyalty": [anggota["is_discounted"].mean() * 100, ret_anggota * 100,
                                 anggota["gross_amount"].mean()]},
            colors=["#C9CBD6", RED],
            title="Tiga klaim program loyalty, diuji ke data", height=400)
        st.plotly_chart(fig, use_container_width=True)
    with k2:
        fig = ranked_bar(["Non-anggota", "Anggota loyalty"],
                         [non["discount_amount"].sum(), anggota["discount_amount"].sum()],
                         highlight=1, accent=RED,
                         title="Uang diskon dibagi ke siapa", height=400)
        st.plotly_chart(fig, use_container_width=True)

    lipat = (anggota["is_discounted"].mean() / non["is_discounted"].mean()
             if non["is_discounted"].mean() else 0)
    selisih = non["gross_amount"].mean() - anggota["gross_amount"].mean()
    render_takeaway(
        f"Program loyalty gagal di <b>ketiga klaimnya sendiri</b>: anggota tidak datang "
        f"lebih sering ({ret_anggota:.2%} vs {ret_non:.2%}), tidak belanja lebih besar "
        f"(justru <b>{format_currency(selisih)} lebih kecil</b> sebelum diskon), dan "
        f"mendapat diskon <b>{lipat:.1f}x lebih sering</b>. Mereka hanya {porsi_trx:.0%} "
        f"transaksi tapi menyerap <b>{porsi_diskon:.0%} seluruh biaya diskon</b> "
        f"({format_currency(anggota['discount_amount'].sum())}/tahun). "
        f"Ini bukan program loyalitas — ini potongan harga tanpa syarat. "
        f"<b>Rekomendasi: uji holdout dulu, jangan langsung dibatalkan</b> — satu tahun "
        f"data tidak bisa melihat efek merek.",
        alert=True)

# ── Langkah 6 — laba per jam ─────────────────────────────────────────────────
render_step(6, "Jam mana yang benar-benar menghasilkan laba?",
            "Setiap jam buka memakan biaya, walau tidak ada pembeli.")

per_jam = df_f.groupby("hour").agg(omzet=("total_amount", "sum"),
                                   laba=("est_profit", "sum"))
sepi_share = per_jam.loc[per_jam.index.isin(QUIET_HOURS), "laba"].sum() / laba if laba else 0

fig = hour_bar(per_jam.index, per_jam["laba"], quiet_hours=QUIET_HOURS,
               title="Laba per jam — area merah = 10 jam tersepi", height=400,
               annotation=None)
st.plotly_chart(fig, use_container_width=True)

render_takeaway(
    f"<b>{len(QUIET_HOURS)} dari 24 jam</b> ({len(QUIET_HOURS)/24:.0%} hari operasional) "
    f"hanya menghasilkan <b>{sepi_share:.1%} laba kotor</b>. Jam-jam itu tetap memakan "
    f"gaji, listrik, pendingin, dan keamanan — biaya yang <b>tidak ada di dataset ini</b>, "
    f"sehingga kita sengaja TIDAK menaruh angka dolar di sini. "
    f"Ini keputusan terbesar di seluruh dashboard, dan hanya butuh satu angka dari "
    f"Finance untuk menyelesaikannya: berapa biaya membuka pintu dari 20:00 sampai 06:00?")

# ── Ringkasan kebocoran ──────────────────────────────────────────────────────
render_step(7, "Ringkasan: di mana laba bocor?", "Yang bisa diukur, dan yang tidak.")

bocor = [
    ("Diskon ke anggota loyalty tanpa hasil terukur",
     anggota["discount_amount"].sum() if "loyalty_member" in df_f.columns else 0,
     "✅ Terukur"),
    ("Diskon 15% & 20% yang justru menurunkan unit",
     df_f.loc[df_f["is_deep_discount"], "discount_amount"].sum(), "✅ Terukur"),
    ("Biaya operasional 10 jam tersepi", None, "❌ Tidak ada di dataset"),
]
tabel = pd.DataFrame({
    "Sumber kebocoran": [b[0] for b in bocor],
    "Nilai per tahun": [format_currency(b[1]) if b[1] is not None else "?" for b in bocor],
    "Bisa diukur?": [b[2] for b in bocor],
})
st.dataframe(tabel, hide_index=True, use_container_width=True)

st.download_button("Unduh Data Profit (CSV)",
                   data=df_f[["transaction_id", "timestamp", "product_category",
                              "product_name", "quantity", "gross_amount",
                              "discount_amount", "total_amount", "est_cost",
                              "est_profit", "profit_margin"]].to_csv(index=False),
                   file_name="profit_analysis.csv", mime="text/csv")
