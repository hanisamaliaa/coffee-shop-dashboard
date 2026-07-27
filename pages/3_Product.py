"""Halaman 3 — Product Dashboard.

Menjawab: Produk apa yang paling laris? Mana yang menghasilkan laba terbesar?
Mana yang marginnya rendah? Produk mana yang dipertahankan, mana yang dievaluasi?
"""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.charts import NAVY, RED, TEAL, matrix_heatmap, pareto, ranked_bar
from utils.data_loader import check_empty_data, get_filter_options, has_profit, load_data
from utils.filters import apply_filters
from utils.formatting import format_currency, format_number_full, format_percentage
from utils.styling import (inject_global_css, render_caveat, render_header,
                           render_kpi_card, render_step, render_takeaway)

st.set_page_config(page_title="Product - Coffee Shop Dashboard",
                   page_icon=":coffee:", layout="wide")
inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header("PRODUCT DASHBOARD",
              "Apa yang laku, apa yang menghasilkan, dan apa yang harus dievaluasi",
              "Halaman 3 dari 8")

df_f = apply_filters(df, options, key_prefix="product")
check_empty_data(df_f, "Product")

omzet = df_f["total_amount"].sum()
punya_laba = has_profit(df_f)

# Ringkasan per produk — dipakai di beberapa langkah
agg = {"omzet": ("total_amount", "sum"), "unit": ("quantity", "sum"),
       "transaksi": ("total_amount", "size"), "nilai_rata": ("total_amount", "mean"),
       "bulan_tersedia": ("month", "nunique")}
if punya_laba:
    agg["laba"] = ("est_profit", "sum")
produk = df_f.groupby(["product_category", "product_name"], observed=True) \
             .agg(**agg).reset_index()
if punya_laba:
    produk["margin"] = produk["laba"] / produk["omzet"]
produk["omzet_per_bulan"] = produk["omzet"] / produk["bulan_tersedia"]

urut = df_f.groupby("product_name")["total_amount"].sum().sort_values(ascending=False)
n80 = int(((urut.cumsum() / omzet) <= 0.80).sum() + 1)

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Jumlah Produk", format_number_full(len(produk)))
with c2:
    render_kpi_card("Produk untuk 80% Omzet", str(n80), None)
with c3:
    render_kpi_card("Produk Beromzet Tertinggi", urut.index[0])
with c4:
    if punya_laba:
        render_kpi_card("Produk Merugi", str(int((produk["laba"] < 0).sum())))
    else:
        render_kpi_card("Kategori", str(df_f["product_category"].nunique()))

# ── Langkah 1 — laris menurut ukuran apa? ────────────────────────────────────
render_step(1, "Produk apa yang paling laris?",
            "Jawabannya berbeda tergantung diukur dari unit atau dari omzet — "
            "dan perbedaan itu penting.")

k1, k2 = st.columns([5, 5])
with k1:
    top_unit = df_f.groupby("product_name")["quantity"].sum().nlargest(10).sort_values()
    fig = ranked_bar(top_unit.index, top_unit.values, highlight=len(top_unit) - 1,
                     value_fmt="{:,.0f}", title="10 teratas berdasarkan UNIT terjual",
                     height=380)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    top_omzet = urut.nlargest(10).sort_values()
    fig = ranked_bar(top_omzet.index, top_omzet.values, highlight=len(top_omzet) - 1,
                     title="10 teratas berdasarkan OMZET", height=380)
    st.plotly_chart(fig, use_container_width=True)

hanya_omzet = [p for p in top_omzet.index if p not in set(top_unit.index)]
render_takeaway(
    f"Juara unit adalah <b>{top_unit.index[-1]}</b>, juara omzet adalah "
    f"<b>{top_omzet.index[-1]}</b>. "
    + (f"Ada <b>{len(hanya_omzet)} produk</b> yang masuk 10 besar omzet tapi tidak masuk "
       f"10 besar unit: {', '.join(hanya_omzet)}. Produk-produk ini jarang dibeli tapi "
       f"nilainya besar — kalau evaluasi produk memakai jumlah transaksi, mereka akan "
       f"terlihat 'tidak laku' dan jadi kandidat pertama untuk dihapus."
       if hanya_omzet else
       "Kedua daftar sangat mirip, jadi ukuran mana pun memberi kesimpulan yang sama."))

# ── Langkah 2 — apakah ada produk bintang? ───────────────────────────────────
render_step(2, "Apakah ada produk 'bintang' yang bisa digenjot?",
            "Kurva Pareto menjawabnya dalam satu grafik.")

fig, n = pareto(urut.values, title="Berapa produk untuk mencapai 80% omzet?",
                height=340, xaxis_title="Produk (diurutkan dari omzet terbesar)")
st.plotly_chart(fig, use_container_width=True)

render_takeaway(
    f"Butuh <b>{n} dari {len(urut)} produk</b> ({n/len(urut):.0%} dari lini) untuk "
    f"mencapai 80% omzet. Di ritel pada umumnya angka ini sekitar 20%. "
    f"Artinya <b>tidak ada produk bintang yang bisa digenjot</b>, dan juga "
    f"<b>tidak ada ekor panjang yang bisa dipangkas</b>. "
    f"Pertumbuhan harus datang dari <b>komposisi penjualan</b> — mendorong pelanggan "
    f"yang sudah ada ke keranjang bernilai lebih tinggi — bukan dari mempromosikan "
    f"satu-dua produk.")

# ── Langkah 3 — siapa yang menghasilkan laba ─────────────────────────────────
if punya_laba:
    render_step(3, "Produk mana yang menghasilkan laba terbesar?",
                "Omzet besar belum tentu laba besar — HPP tiap kategori berbeda jauh.")

    kat = df_f.groupby("product_category", observed=True).agg(
        omzet=("total_amount", "sum"), laba=("est_profit", "sum"),
        trx=("total_amount", "size"))
    kat["% omzet"] = kat["omzet"] / kat["omzet"].sum()
    kat["% laba"] = kat["laba"] / kat["laba"].sum()
    kat["margin"] = kat["laba"] / kat["omzet"]
    kat["indeks nilai"] = kat["% omzet"] / (kat["trx"] / len(df_f))

    k1, k2 = st.columns([5, 5])
    with k1:
        top_laba = produk.nlargest(10, "laba").sort_values("laba")
        fig = ranked_bar(top_laba["product_name"], top_laba["laba"],
                         highlight=len(top_laba) - 1,
                         title="10 produk penghasil laba terbesar", height=380)
        st.plotly_chart(fig, use_container_width=True)
    with k2:
        m = kat.sort_values("margin")
        fig = ranked_bar(m.index, m["margin"] * 100, highlight=[0, len(m) - 1],
                         value_fmt="{:.0f}%", title="Margin per kategori", height=380)
        st.plotly_chart(fig, use_container_width=True)

    geser = kat.assign(selisih=kat["% laba"] - kat["% omzet"]).sort_values("selisih")
    naik, turun = geser.index[-1], geser.index[0]
    render_takeaway(
        f"<b>{naik}</b> menyumbang porsi laba yang <b>lebih besar</b> dari porsi omzetnya "
        f"({kat.loc[naik,'% laba']:.0%} laba vs {kat.loc[naik,'% omzet']:.0%} omzet) "
        f"karena HPP-nya paling rendah. Sebaliknya <b>{turun}</b> menyumbang laba lebih "
        f"kecil dari omzetnya ({kat.loc[turun,'% laba']:.0%} vs "
        f"{kat.loc[turun,'% omzet']:.0%}) — margin {kat.loc[turun,'margin']:.0%}, "
        f"paling tipis di antara semua kategori. "
        f"<b>Tapi tidak satu pun kategori merugi</b>, jadi tidak ada yang perlu "
        f"dihentikan karena alasan margin.")

    with st.expander("Lihat tabel lengkap per kategori"):
        tampil = kat.copy()
        for c in ["omzet", "laba"]:
            tampil[c] = tampil[c].map(lambda v: f"${v:,.0f}")
        for c in ["% omzet", "% laba", "margin"]:
            tampil[c] = tampil[c].map(lambda v: f"{v:.1%}")
        tampil["indeks nilai"] = tampil["indeks nilai"].map(lambda v: f"{v:.2f}x")
        tampil["trx"] = tampil["trx"].map(lambda v: f"{v:,}")
        st.dataframe(tampil, use_container_width=True)

# ── Langkah 4 — jebakan musiman ──────────────────────────────────────────────
render_step(4, "Produk mana yang harus dihentikan?",
            "Ini pertanyaan paling berisiko di seluruh analisis. Jawaban yang "
            "terlihat jelas justru salah.")

produk["peringkat_tahunan"] = produk["omzet"].rank(ascending=False).astype(int)
produk["peringkat_per_bulan"] = produk["omzet_per_bulan"].rank(ascending=False).astype(int)
produk["lompatan"] = produk["peringkat_tahunan"] - produk["peringkat_per_bulan"]
terbawah = produk.nsmallest(8, "omzet").copy()
musiman = int((terbawah["bulan_tersedia"] < df_f["month"].nunique()).sum())

k1, k2 = st.columns([6, 4])
with k1:
    banding = terbawah.sort_values("omzet")
    fig = ranked_bar(
        [f"{r.product_name}  ({int(r.bulan_tersedia)} bln)"
         for r in banding.itertuples()],
        banding["omzet"],
        highlight=[i for i, r in enumerate(banding.itertuples())
                   if r.bulan_tersedia < df_f["month"].nunique()],
        accent=RED,
        title=f"8 produk omzet terendah — {musiman} di antaranya MUSIMAN",
        height=360)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    tampil = terbawah.sort_values("lompatan", ascending=False)[
        ["product_name", "bulan_tersedia", "peringkat_tahunan", "peringkat_per_bulan"]]
    tampil.columns = ["Produk", "Bulan tersedia", "Peringkat tahunan",
                      "Peringkat per bulan"]
    st.dataframe(tampil, hide_index=True, use_container_width=True, height=360)

lompat_terbesar = produk.loc[produk["lompatan"].idxmax()]
render_takeaway(
    f"<b>Jangan hentikan satu pun berdasarkan peringkat tahunan.</b> "
    f"{musiman} dari 8 produk teromzet terendah ternyata <b>produk musiman</b> yang hanya "
    f"dijual {int(terbawah['bulan_tersedia'].min())} bulan. "
    f"Contoh paling tajam: <b>{lompat_terbesar['product_name']}</b> berada di peringkat "
    f"<b>{int(lompat_terbesar['peringkat_tahunan'])} dari {len(produk)}</b> secara tahunan, "
    f"tapi peringkat <b>{int(lompat_terbesar['peringkat_per_bulan'])} dari {len(produk)}</b> "
    f"kalau dihitung per bulan ketersediaannya — melompat "
    f"{int(lompat_terbesar['lompatan'])} posisi. "
    f"Memotong lini terbawah akan <b>menghapus seluruh rangkaian musiman kita</b>, "
    f"termasuk salah satu produk berkinerja terbaik per bulan aktifnya.",
    alert=True)

# ── Langkah 5 — keputusan ────────────────────────────────────────────────────
render_step(5, "Jadi, apa keputusannya?",
            "Dipertahankan, didorong, atau dievaluasi — beserta alasannya.")

if punya_laba:
    kat_rank = df_f.groupby("product_category", observed=True).agg(
        trx=("total_amount", "size"), rev=("total_amount", "sum"),
        aov=("total_amount", "mean"), laba=("est_profit", "sum"))
    kat_rank["indeks"] = (kat_rank["rev"] / omzet) / (kat_rank["trx"] / len(df_f))
    nilai_tinggi = kat_rank["indeks"].idxmax()
    laba_utama = kat_rank["laba"].idxmax()

    KEPUTUSAN = pd.DataFrame([
        ("DIPERTAHANKAN & DIDORONG", laba_utama,
         f"Penyumbang laba terbesar ({format_currency(kat_rank.loc[laba_utama,'laba'])}) "
         f"dengan margin {kat_rank.loc[laba_utama,'laba']/kat_rank.loc[laba_utama,'rev']:.0%}. "
         f"Inti bisnis — jaga ketersediaan dan kualitas."),
        ("DIDORONG (peluang terbesar)", nilai_tinggi,
         f"Hanya {kat_rank.loc[nilai_tinggi,'trx']/len(df_f):.1%} transaksi tapi nilainya "
         f"{format_currency(kat_rank.loc[nilai_tinggi,'aov'])} per penjualan "
         f"({kat_rank.loc[nilai_tinggi,'indeks']:.1f}x rata-rata). "
         f"Pindahkan ke meja kasir, tawarkan saat jam sibuk pagi."),
        ("DIEVALUASI (bukan dihentikan)", "Varian ukuran",
         f"Butuh {n} dari {len(urut)} produk untuk 80% omzet — tidak ada ekor panjang. "
         f"Rasionalisasi varian ukuran produk yang sama, jangan hapus produknya."),
        ("JANGAN DISENTUH", "Produk musiman",
         f"{musiman} dari 8 produk terbawah adalah musiman. Nilai ulang berdasarkan "
         f"omzet per bulan ketersediaan, bukan omzet tahunan."),
    ], columns=["Keputusan", "Target", "Alasan berbasis data"])
    st.dataframe(KEPUTUSAN, hide_index=True, use_container_width=True)

render_caveat(
    "<b>Catatan margin.</b> Angka laba dan margin di halaman ini adalah <b>estimasi</b> "
    "dari benchmark HPP per kategori (lihat halaman Profit, Langkah 1), bukan angka "
    "akuntansi. Sah dipakai untuk <b>membandingkan</b> produk satu sama lain, tidak sah "
    "sebagai laporan laba rugi.")

st.markdown("")
st.download_button("Unduh Ringkasan Produk (CSV)",
                   data=produk.to_csv(index=False),
                   file_name="ringkasan_produk.csv", mime="text/csv")
