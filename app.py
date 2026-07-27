"""Halaman utama — peta isi dashboard.

Halaman ini sengaja tidak berisi grafik. Tugasnya satu: memberi tahu pembaca
harus ke mana untuk menjawab pertanyaannya.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.business_logic import PROFIT_DISCLAIMER
from utils.data_loader import load_data
from utils.formatting import format_currency, format_date_range, format_number_full
from utils.metrics import calc_kpi
from utils.styling import inject_global_css, render_caveat, render_header, render_step

st.set_page_config(page_title="Coffee Shop Dashboard", page_icon=":coffee:",
                   layout="wide", initial_sidebar_state="expanded")
inject_global_css()

df = load_data()
kpi = calc_kpi(df)

render_header("COFFEE SHOP — EXECUTIVE DASHBOARD",
              "Analisis penjualan, profit, dan rekomendasi bisnis",
              format_date_range(df["timestamp"].min(), df["timestamp"].max()))

st.markdown(
    f"""
    <div style="background:#1C174D;color:#fff;border-radius:14px;padding:26px 30px;
                margin-bottom:26px;">
      <div style="font-size:0.72rem;letter-spacing:0.1em;color:#FFB703;font-weight:800;">
      KESIMPULAN UTAMA</div>
      <div style="font-size:1.5rem;font-weight:800;margin-top:10px;line-height:1.4;">
      Ini bisnis minuman pagi yang membayar untuk beroperasi 24 jam
      seperti toko serba ada.</div>
      <div style="font-size:0.92rem;color:#BFBAB4;margin-top:12px;line-height:1.7;">
      Perusahaan ini dikelola dengan baik — tidak ada toko yang gagal, tidak ada produk
      yang merugi, datanya bersih. Dan omzetnya tidak tumbuh sedikit pun selama
      dua belas bulan.</div>
    </div>
    """, unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)
for kol, (label, nilai) in zip(
    [c1, c2, c3, c4, c5],
    [("Total Omzet", format_currency(kpi["total_revenue"])),
     ("Estimasi Laba Kotor", format_currency(kpi["total_profit"])),
     ("Transaksi", format_number_full(kpi["total_transactions"])),
     ("Toko", f"{df['store_id'].nunique()} di {df['city'].nunique()} kota"),
     ("Periode", f"{df['timestamp'].dt.date.nunique()} hari")],
):
    with kol:
        st.markdown(
            f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
            <div class="kpi-value" style="font-size:1.32rem;">{nilai}</div></div>""",
            unsafe_allow_html=True)

# ── Peta halaman ─────────────────────────────────────────────────────────────
render_step(1, "Delapan halaman, satu pertanyaan per halaman",
            "Pilih halaman di sidebar sesuai pertanyaan yang ingin dijawab.")

HALAMAN = [
    ("1", "Executive Summary", "Direksi",
     "Apakah bisnis ini sehat, dan di mana keputusan terbesarnya?"),
    ("2", "Sales", "Sales Director",
     "Bagaimana tren penjualan? Kapan tertinggi dan terendah?"),
    ("3", "Product", "Category Manager",
     "Produk mana yang dipertahankan, didorong, dan dievaluasi?"),
    ("4", "Customer", "Marketing",
     "Siapa pelanggan utama, dan apakah program loyalty bekerja?"),
    ("5", "Region & Store", "Regional Manager",
     "Wilayah mana yang terbaik, dan mana yang perlu perhatian?"),
    ("6", "Time & Operations", "Operasional",
     "Kapan permintaan datang, dan kapan waktu terbaik promosi?"),
    ("7", "Profit", "CFO",
     "Dari mana laba datang, dan bagaimana dampak diskon terhadap profit?"),
    ("8", "Recommendations", "Semua",
     "Dua belas rekomendasi dan alur presentasi 10 menit."),
]

baris = ""
for nomor, nama, untuk, pertanyaan in HALAMAN:
    baris += f"""
    <div style="display:flex;gap:14px;align-items:flex-start;padding:13px 0;
                border-bottom:1px solid #EFEDF6;">
      <div style="flex:none;width:26px;height:26px;border-radius:7px;background:#1C174D;
                  color:#fff;font-size:0.75rem;font-weight:800;display:flex;
                  align-items:center;justify-content:center;">{nomor}</div>
      <div style="flex:1;">
        <div style="font-weight:700;color:#1C174D;font-size:0.96rem;">{nama}
          <span style="font-weight:500;color:#0D8A92;font-size:0.76rem;
                       margin-left:8px;">untuk: {untuk}</span></div>
        <div style="color:#6B7280;font-size:0.85rem;margin-top:2px;">{pertanyaan}</div>
      </div>
    </div>"""

st.markdown(f'<div style="margin-bottom:8px;">{baris}</div>', unsafe_allow_html=True)

# ── Cara membaca ─────────────────────────────────────────────────────────────
render_step(2, "Cara membaca dashboard ini",
            "Empat aturan yang dipakai konsisten di semua halaman.")

k1, k2 = st.columns(2)
with k1:
    st.markdown(
        """
        <div style="font-size:0.89rem;line-height:1.85;color:#374151;">
        <b style="color:#1C174D;">1. Setiap halaman dibaca berurutan.</b><br>
        Langkah bernomor 1, 2, 3 — masing-masing menjawab satu pertanyaan.<br><br>
        <b style="color:#1C174D;">2. Setiap grafik punya kotak "Apa artinya".</b><br>
        Grafik tanpa kesimpulan memaksa pembaca menebak sendiri. Kotak biru berisi
        kesimpulan; kotak merah berarti butuh perhatian.
        </div>
        """, unsafe_allow_html=True)
with k2:
    st.markdown(
        """
        <div style="font-size:0.89rem;line-height:1.85;color:#374151;">
        <b style="color:#1C174D;">3. Judul grafik berisi kesimpulan.</b><br>
        "Coffee 42% dari omzet", bukan "Revenue by Category".<br><br>
        <b style="color:#1C174D;">4. Warna berarti sesuatu.</b><br>
        Hanya hal penting yang berwarna; sisanya abu-abu. Kalau semua berwarna,
        tidak ada yang penting.
        </div>
        """, unsafe_allow_html=True)

# ── Batasan ──────────────────────────────────────────────────────────────────
render_step(3, "Yang tidak bisa dijawab dashboard ini",
            "Ditulis di depan, bukan disembunyikan di catatan kaki.")

sekali = (df.groupby("customer_id").size() == 1).mean()
render_caveat(
    f"<b>1. Laba adalah estimasi.</b> {PROFIT_DISCLAIMER}<br><br>"
    f"<b>2. Retensi pelanggan tidak bisa diukur.</b> {sekali:.0%} dari "
    f"{df['customer_id'].nunique():,} pelanggan hanya muncul sekali dalam setahun, "
    f"sehingga CLV, churn, dan analisis cohort tidak dilaporkan di sini.<br><br>"
    f"<b>3. Biaya operasional tidak ada di dataset.</b> Karena itu rekomendasi terbesar "
    f"— menutup jam 20:00–06:00 — sengaja <b>tidak diberi angka dolar</b>. "
    f"Satu angka dari Finance akan menyelesaikannya.")

st.sidebar.markdown(
    "<div style='font-size:1.1rem;font-weight:800;color:#1C174D;margin-bottom:2px;'>"
    "COFFEE SHOP</div>"
    "<div style='font-size:0.74rem;color:#6B7280;margin-bottom:14px;'>"
    "Executive Business Intelligence</div>",
    unsafe_allow_html=True)
