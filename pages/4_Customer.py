"""Halaman 4 — Customer Dashboard.

Menjawab: Siapa pelanggan utama? Bagaimana karakteristik dan perilaku belinya?
Apakah ada segmen pelanggan yang berbeda?
"""

import os
import sys

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.charts import GREY, NAVY, RED, TEAL, _v, compare_bar, ranked_bar
from utils.data_loader import check_empty_data, get_filter_options, load_data
from utils.filters import apply_filters
from utils.formatting import format_currency, format_number_full, format_percentage
from utils.styling import (inject_global_css, render_caveat, render_header,
                           render_kpi_card, render_step, render_takeaway)

st.set_page_config(page_title="Customer - Coffee Shop Dashboard",
                   page_icon=":coffee:", layout="wide")
inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header("CUSTOMER DASHBOARD",
              "Siapa yang membeli, dan apa yang sebenarnya bisa kita ketahui tentang mereka",
              "Halaman 4 dari 8")

df_f = apply_filters(df, options, key_prefix="cust")
check_empty_data(df_f, "Customer")

omzet = df_f["total_amount"].sum()
kunjungan = df_f.groupby("customer_id").size()
n_pelanggan = len(kunjungan)
sekali = (kunjungan == 1).mean()
berulang = (kunjungan > 1).mean()

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Pelanggan Unik", format_number_full(n_pelanggan))
with c2:
    render_kpi_card("Hanya Datang Sekali", format_percentage(sekali * 100))
with c3:
    render_kpi_card("Pelanggan Berulang", format_percentage(berulang * 100))
with c4:
    render_kpi_card("Kunjungan Terbanyak", f"{int(kunjungan.max())}x")

# ── Langkah 1 — apa yang sebenarnya bisa diukur ──────────────────────────────
render_step(1, "Siapa pelanggan yang paling bernilai?",
            "Sebelum menjawab, kita harus tahu dulu apakah data ini memang bisa "
            "menjawabnya.")

sebaran = kunjungan.value_counts().sort_index()
k1, k2 = st.columns([6, 4])
with k1:
    import plotly.graph_objects as go
    fig = go.Figure(go.Bar(
        x=_v(sebaran.index.astype(str)), y=_v(sebaran.values),
        marker_color=[RED if i == 1 else TEAL for i in sebaran.index],
        text=[f"{v:,}" for v in sebaran.values], textposition="outside",
        cliponaxis=False,
        hovertemplate="%{x} kunjungan: <b>%{y:,} pelanggan</b><extra></extra>"))
    fig.update_yaxes(type="log", title="Jumlah pelanggan (skala log)")
    fig.update_xaxes(title="Jumlah kunjungan dalam periode")
    fig.update_layout(
        title=f"{sekali:.0%} pelanggan hanya muncul SEKALI",
        height=360, plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        margin=dict(t=50, b=40, l=60, r=30), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    st.markdown(
        f"""
        <div style="padding:18px 4px;line-height:1.85;font-size:0.9rem;color:#374151;">
        <div style="font-size:2.3rem;font-weight:800;color:#D9535F;line-height:1.1;">
        {sekali:.1%}</div>
        <div style="color:#6B7280;margin-bottom:16px;">dari {n_pelanggan:,} pelanggan
        hanya bertransaksi satu kali</div>
        <b>Konsekuensinya, dari data ini kita TIDAK bisa menghitung:</b><br>
        • Customer Lifetime Value (CLV)<br>
        • Tingkat churn<br>
        • Analisis cohort<br>
        • "Pelanggan VIP" yang layak diprogramkan<br><br>
        <b>Yang masih bisa diukur:</b> nilai per <i>transaksi</i>, bukan per
        <i>pelanggan</i>.
        </div>
        """, unsafe_allow_html=True)

render_takeaway(
    f"<b>Jawaban jujurnya: kita tidak bisa tahu.</b> Dengan {sekali:.1%} pelanggan hanya "
    f"muncul sekali dan yang paling setia pun cuma {int(kunjungan.max())} kali, tidak ada "
    f"cukup riwayat untuk menentukan siapa pelanggan bernilai. "
    f"Ada dua kemungkinan yang <b>tidak bisa kita bedakan</b> dari data ini: "
    f"(1) memang benar-benar pelanggan sekali datang — wajar untuk lokasi transit, atau "
    f"(2) <b>customer_id tidak tersimpan lintas kunjungan</b> di sistem kasir. "
    f"Keduanya menuntut strategi yang sama sekali berbeda. "
    f"<b>Tindakan: tanyakan ke tim IT sebelum ada angka CLV yang dipresentasikan.</b>",
    alert=True)

# ── Langkah 2 — yang bisa diukur: nilai transaksi ────────────────────────────
render_step(2, "Bagaimana perilaku pembelian mereka?",
            "Karena pelanggan tidak bisa dilacak, kita ukur perilakunya di tingkat "
            "transaksi.")

k1, k2 = st.columns([5, 5])
with k1:
    if "value_segment" in df_f.columns:
        seg = df_f.groupby("value_segment", observed=True).agg(
            trx=("total_amount", "size"), omzet=("total_amount", "sum"))
        seg["porsi"] = seg["omzet"] / omzet
        fig = ranked_bar(seg.index, seg["porsi"] * 100, highlight=len(seg) - 1,
                         value_fmt="{:.0f}%",
                         title=f"Segmen Premium (25% transaksi teratas) = "
                               f"{seg['porsi'].iloc[-1]:.0%} omzet", height=360)
        st.plotly_chart(fig, use_container_width=True)
with k2:
    if "basket_size" in df_f.columns:
        keranjang = df_f.groupby("basket_size", observed=True).agg(
            trx=("total_amount", "size"), omzet=("total_amount", "sum"))
        keranjang["porsi"] = keranjang["omzet"] / omzet
        fig = ranked_bar(keranjang.index, keranjang["porsi"] * 100,
                         highlight=int(np.argmax(keranjang["porsi"].values)),
                         value_fmt="{:.0f}%",
                         title="Kontribusi omzet menurut ukuran keranjang", height=360)
        st.plotly_chart(fig, use_container_width=True)

if "value_segment" in df_f.columns:
    render_takeaway(
        f"Segmen <b>Premium</b> — 25% transaksi bernilai tertinggi — menyumbang "
        f"<b>{seg['porsi'].iloc[-1]:.0%} omzet</b>, sementara segmen Rendah dengan jumlah "
        f"transaksi yang sama hanya {seg['porsi'].iloc[0]:.0%}. "
        f"Artinya <b>nilai transaksi jauh lebih penting daripada jumlah transaksi</b>. "
        f"Program yang menaikkan nilai keranjang (attach merchandise, upsize) akan lebih "
        f"berdampak daripada program yang mengejar jumlah kunjungan.")

# ── Langkah 3 — apakah ada segmen demografis ─────────────────────────────────
render_step(3, "Apakah ada segmen pelanggan yang berbeda?",
            "Kalau demografi tidak membedakan perilaku, segmentasi berbasis demografi "
            "hanya membuang anggaran.")

k1, k2 = st.columns([5, 5])
with k1:
    usia = df_f.groupby("customer_age_group", observed=True)["total_amount"].sum()
    usia_bersih = usia.drop("Tidak Diketahui", errors="ignore").sort_values()
    fig = ranked_bar(usia_bersih.index, usia_bersih.values, highlight=None,
                     accent=GREY, title="Omzet per kelompok usia", height=360)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    nilai_usia = df_f.groupby("customer_age_group", observed=True)["total_amount"].mean()
    nilai_bersih = nilai_usia.drop("Tidak Diketahui", errors="ignore").sort_values()
    fig = ranked_bar(nilai_bersih.index, nilai_bersih.values, highlight=None,
                     accent=GREY, value_fmt="${:.2f}",
                     title="Nilai transaksi rata-rata per kelompok usia", height=360)
    st.plotly_chart(fig, use_container_width=True)

sebar_omzet = usia_bersih.max() / usia_bersih.min() - 1
sebar_nilai = nilai_bersih.max() / nilai_bersih.min() - 1
render_takeaway(
    f"<b>Tidak ada segmen demografis yang berbeda.</b> Perbedaan omzet antar kelompok "
    f"usia {sebar_omzet:.0%} sebagian besar hanya mencerminkan berapa banyak orang di "
    f"tiap kelompok. Yang lebih menentukan adalah grafik kanan: <b>nilai transaksi "
    f"rata-rata hanya berbeda {sebar_nilai:.0%}</b> dari kelompok tertinggi ke terendah — "
    f"pelanggan 18-24 dan 65+ berbelanja dengan nilai yang praktis sama. "
    f"<b>Segmentasi berdasarkan usia atau gender tidak akan menghasilkan apa pun.</b> "
    f"Segmen yang benar-benar berbeda di bisnis ini adalah <b>waktu dan lokasi</b>.")

# ── Langkah 4 — program loyalty ──────────────────────────────────────────────
if "loyalty_member" in df_f.columns and df_f["loyalty_member"].nunique() > 1:
    render_step(4, "Apakah program loyalty bekerja?",
                "Program ini punya tiga klaim. Kita uji ketiganya ke data.")

    anggota = df_f[df_f["loyalty_member"]]
    non = df_f[~df_f["loyalty_member"]]
    vis = df_f.groupby("customer_id").agg(n=("transaction_id", "size"),
                                          m=("loyalty_member", "first"))
    ret_a = (vis.loc[vis["m"], "n"] > 1).mean()
    ret_n = (vis.loc[~vis["m"], "n"] > 1).mean()

    k1, k2 = st.columns([6, 4])
    with k1:
        fig = compare_bar(
            ["Sering dapat diskon (%)", "Datang lagi (%)", "Belanja sebelum diskon ($)"],
            {"Non-anggota": [non["is_discounted"].mean() * 100, ret_n * 100,
                             non["gross_amount"].mean()],
             "Anggota loyalty": [anggota["is_discounted"].mean() * 100, ret_a * 100,
                                 anggota["gross_amount"].mean()]},
            colors=[GREY, RED], title="Tiga klaim program loyalty, diuji ke data",
            height=380)
        st.plotly_chart(fig, use_container_width=True)
    with k2:
        UJI = pd.DataFrame([
            ("Datang lebih sering?", f"{ret_a:.2%}", f"{ret_n:.2%}", "Tidak ada beda"),
            ("Belanja lebih besar?", f"${anggota['gross_amount'].mean():.2f}",
             f"${non['gross_amount'].mean():.2f}", "Anggota LEBIH KECIL"),
            ("Sering dapat diskon?", f"{anggota['is_discounted'].mean():.1%}",
             f"{non['is_discounted'].mean():.1%}",
             f"{anggota['is_discounted'].mean()/non['is_discounted'].mean():.1f}x"),
        ], columns=["Klaim", "Anggota", "Non-anggota", "Hasil"])
        st.dataframe(UJI, hide_index=True, use_container_width=True, height=180)
        porsi = anggota["discount_amount"].sum() / df_f["discount_amount"].sum()
        st.markdown(
            f"<div style='font-size:0.86rem;color:#374151;line-height:1.7;'>"
            f"Anggota = <b>{df_f['loyalty_member'].mean():.0%} transaksi</b><br>"
            f"tapi menyerap <b>{porsi:.0%} biaya diskon</b><br>"
            f"= <b>{format_currency(anggota['discount_amount'].sum())}/tahun</b></div>",
            unsafe_allow_html=True)

    render_takeaway(
        f"<b>Program ini gagal di ketiga klaimnya sendiri.</b> Anggota tidak datang lebih "
        f"sering ({ret_a:.2%} vs {ret_n:.2%}), tidak belanja lebih besar (justru "
        f"{format_currency(non['gross_amount'].mean()-anggota['gross_amount'].mean())} "
        f"lebih kecil sebelum diskon), dan mendapat diskon "
        f"{anggota['is_discounted'].mean()/non['is_discounted'].mean():.1f}x lebih sering. "
        f"Ini bukan program loyalitas — ini <b>potongan harga tanpa syarat</b> untuk orang "
        f"yang perilakunya tidak berubah. "
        f"<b>Tapi jangan langsung dibatalkan:</b> satu tahun data tidak bisa melihat efek "
        f"merek atau pelanggan yang akan pergi. Jalankan <b>uji holdout di ⅓ toko selama "
        f"satu kuartal</b>, lalu putuskan dengan bukti.",
        alert=True)

# ── Langkah 5 — kesimpulan ───────────────────────────────────────────────────
render_step(5, "Jadi siapa pelanggan utama kita?", "Kesimpulan yang bisa dipertahankan.")

st.markdown(
    f"""
    <div style="background:#F3F1FA;border-radius:12px;padding:20px 24px;
                font-size:0.92rem;color:#374151;line-height:1.85;">
    <b style="color:#1C174D;">Pelanggan utama kita bukan sebuah demografi — melainkan
    sebuah kejadian.</b><br><br>
    Bukan "wanita 25-34" atau "anggota loyalty", karena kedua kelompok itu tidak
    berperilaku berbeda dari siapa pun. Pelanggan utama kita adalah
    <b>orang yang lewat antara pukul 06:00 dan 10:00</b> — siapa pun dia.<br><br>
    Konsekuensinya untuk marketing:
    <br>• Berhenti membeli data segmentasi demografis — tidak ada sinyal di sana
    <br>• Alihkan ke <b>penawaran berbasis waktu dan lokasi</b>
    <br>• Naikkan <b>nilai keranjang</b>, bukan jumlah kunjungan — karena kunjungan
    ulang praktis tidak ada dan tidak bisa diukur
    </div>
    """, unsafe_allow_html=True)

render_caveat(
    f"<b>Batasan halaman ini.</b> {sekali:.0%} pelanggan hanya muncul sekali, sehingga "
    f"CLV, churn, cohort, dan daftar 'pelanggan VIP' <b>tidak dilaporkan</b> di dashboard "
    f"ini — bukan karena tidak dibuat, tapi karena angkanya tidak akan bertahan saat "
    f"ditanya. Grafik 'Top 10 Pelanggan' sengaja dihilangkan: dengan data seperti ini, "
    f"grafik itu hanya menampilkan sepuluh ID acak yang kebetulan membeli barang mahal "
    f"satu kali, dan akan menyesatkan pembaca seolah kita punya pelanggan VIP.")

st.markdown("")
st.download_button("Unduh Data Pelanggan (CSV)",
                   data=df_f.groupby("customer_id").agg(
                       kunjungan=("transaction_id", "size"),
                       total_belanja=("total_amount", "sum"),
                       rata_transaksi=("total_amount", "mean"),
                       anggota_loyalty=("loyalty_member", "first")).to_csv(),
                   file_name="ringkasan_pelanggan.csv", mime="text/csv")
