"""Halaman 5 — Region & Store Dashboard.

Menjawab: Wilayah mana yang performanya terbaik dan terburuk? Mana yang perlu
perhatian? Apakah ada perbedaan pola penjualan antar wilayah?
"""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.charts import GREY, TEAL, YELLOW, _v, matrix_heatmap, ranked_bar
from utils.data_loader import check_empty_data, get_filter_options, has_profit, load_data
from utils.filters import apply_filters
from utils.formatting import format_currency
from utils.styling import (inject_global_css, render_caveat, render_header,
                           render_kpi_card, render_step, render_takeaway)

st.set_page_config(page_title="Region & Store - Coffee Shop Dashboard",
                   page_icon=":coffee:", layout="wide")
inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header("REGION & STORE DASHBOARD",
              "Lokasi dan format mana yang layak mendapat investasi berikutnya",
              "Halaman 5 dari 8")

df_f = apply_filters(df, options, key_prefix="region")
check_empty_data(df_f, "Region & Store")

omzet = df_f["total_amount"].sum()
n_toko = df_f["store_id"].nunique()

kota = df_f.groupby("city", observed=True).agg(
    omzet=("total_amount", "sum"), toko=("store_id", "nunique"),
    trx=("total_amount", "size"), harga=("price_index", "median"))
kota["per_toko"] = kota["omzet"] / kota["toko"]
kota["trx_per_toko"] = kota["trx"] / kota["toko"]

tipe = df_f.groupby("store_type", observed=True).agg(
    omzet=("total_amount", "sum"), toko=("store_id", "nunique"),
    trx=("total_amount", "size"), harga=("price_index", "median"))
tipe["per_toko"] = tipe["omzet"] / tipe["toko"]
tipe["trx_per_toko"] = tipe["trx"] / tipe["toko"]

omzet_toko = df_f.groupby("store_id")["total_amount"].sum()

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Jumlah Toko",
                    f"{n_toko} di {df_f['city'].nunique()} kota")
with c2:
    render_kpi_card("Format Terbaik", tipe["per_toko"].idxmax())
with c3:
    render_kpi_card("Omzet per Toko", format_currency(omzet / n_toko))
with c4:
    render_kpi_card("Jarak Toko Terbaik–Terlemah",
                    f"{omzet_toko.max()/omzet_toko.min():.2f}x")

# ── Langkah 1 — bandingkan secara adil ───────────────────────────────────────
render_step(1, "Wilayah mana yang performanya terbaik dan terburuk?",
            "Harus dibagi jumlah toko dulu. Kota dengan 8 toko otomatis mengalahkan "
            "kota dengan 3 toko kalau dibandingkan mentah-mentah.")

k1, k2 = st.columns([5, 5])
with k1:
    mentah = kota["omzet"].sort_values()
    fig = ranked_bar([f"{i}  ({int(kota.loc[i,'toko'])} toko)" for i in mentah.index],
                     mentah.values, highlight=len(mentah) - 1, accent=GREY,
                     title="❌ Omzet TOTAL — menyesatkan", height=360)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    adil = kota["per_toko"].sort_values()
    fig = ranked_bar(adil.index, adil.values, highlight=[0, len(adil) - 1],
                     title="✅ Omzet PER TOKO — perbandingan yang adil", height=360)
    st.plotly_chart(fig, use_container_width=True)

terbaik, terlemah = adil.index[-1], adil.index[0]
beda_urutan = mentah.index[-1] != adil.index[-1]
render_takeaway(
    f"<b>{terbaik}</b> adalah kota terbaik ({format_currency(adil.iloc[-1])} per toko) "
    f"dan <b>{terlemah}</b> yang terlemah ({format_currency(adil.iloc[0])}) — "
    f"{terbaik} menghasilkan <b>{adil.iloc[-1]/adil.iloc[0]-1:.0%} lebih banyak</b> "
    f"per toko. "
    + (f"Perhatikan peringkat teratas <b>berubah</b> setelah dibagi jumlah toko: secara "
       f"total {mentah.index[-1]} yang memimpin, tapi itu semata karena punya lebih "
       f"banyak gerai."
       if beda_urutan else
       "Urutannya kebetulan sama, tapi normalisasi tetap wajib supaya perbandingannya "
       "bisa dipertanggungjawabkan."))

# ── Langkah 2 — harga vs volume ──────────────────────────────────────────────
render_step(2, "Kenapa ada wilayah yang lebih unggul?",
            "Dua kemungkinan: menjual lebih banyak, atau menjual lebih mahal. "
            "Jawabannya mengubah tindakan yang harus diambil.")

urut_tipe = tipe.sort_values("per_toko")
fig = go.Figure()
fig.add_trace(go.Bar(x=_v(urut_tipe.index), y=_v(urut_tipe["harga"]),
                     name="Indeks harga (sumbu kiri)", marker_color=TEAL,
                     yaxis="y", offsetgroup=1,
                     text=[f"{v:.2f}x" for v in urut_tipe["harga"]],
                     textposition="outside", cliponaxis=False))
fig.add_trace(go.Bar(x=_v(urut_tipe.index), y=_v(urut_tipe["trx_per_toko"]),
                     name="Transaksi per toko (sumbu kanan)", marker_color=GREY,
                     yaxis="y2", offsetgroup=2,
                     text=[f"{v:.0f}" for v in urut_tipe["trx_per_toko"]],
                     textposition="outside", cliponaxis=False))
fig.update_layout(
    title="Format yang lebih mahal TIDAK kehilangan pelanggan",
    yaxis=dict(title="Indeks harga", range=[0, urut_tipe["harga"].max() * 1.35]),
    yaxis2=dict(title="Transaksi per toko", overlaying="y", side="right",
                showgrid=False, range=[0, urut_tipe["trx_per_toko"].max() * 1.35]),
    barmode="group", height=380, plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Inter, sans-serif", size=12, color="#374151"),
    margin=dict(t=60, b=40, l=60, r=60),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6")
st.plotly_chart(fig, use_container_width=True)

mahal, murah = tipe["harga"].idxmax(), tipe["harga"].idxmin()
premi = tipe.loc[mahal, "harga"] / tipe.loc[murah, "harga"] - 1
beda_vol = tipe.loc[mahal, "trx_per_toko"] / tipe.loc[murah, "trx_per_toko"] - 1
beda_rev = tipe.loc[mahal, "per_toko"] - tipe.loc[murah, "per_toko"]

render_takeaway(
    f"<b>Perbedaannya adalah HARGA, bukan jumlah pelanggan.</b> Toko <b>{mahal}</b> "
    f"menjual <b>{premi:.0%} lebih mahal</b> daripada {murah} dan tetap melayani "
    f"<b>{beda_vol:+.1%} pelanggan</b> — kenaikan harga itu praktis "
    f"<b>tidak menghilangkan satu pun pelanggan</b>. Hasilnya "
    f"<b>{format_currency(beda_rev)} lebih banyak per toko per tahun</b>. "
    f"Kita sudah membuktikan ini bekerja, tapi baru dipakai di "
    f"<b>{int(tipe.loc[mahal,'toko'])} dari {n_toko} toko</b>. "
    f"Artinya pertumbuhan di sini adalah <b>keputusan pricing dan properti</b>, "
    f"bukan keputusan marketing.")

# ── Langkah 3 — kebijakan harga ──────────────────────────────────────────────
render_step(3, "Seperti apa kebijakan harga kita sekarang?",
            "Indeks 1,00 berarti menjual dengan harga termurah di seluruh jaringan.")

k1, k2 = st.columns([6, 4])
with k1:
    peta = df_f.pivot_table(index="city", columns="store_type", values="price_index",
                            aggfunc="median", observed=True)
    fig = matrix_heatmap(peta, title="Indeks harga menurut kota x format",
                         height=360, value_fmt="{:.2f}")
    st.plotly_chart(fig, use_container_width=True)
with k2:
    h = kota["harga"].sort_values()
    fig = ranked_bar(h.index, h.values, highlight=[0, len(h) - 1],
                     value_fmt="{:.2f}x", title="Indeks harga per kota", height=360)
    st.plotly_chart(fig, use_container_width=True)

termurah = kota["harga"].idxmin()
n_format_termurah = df_f.loc[df_f["city"] == termurah, "store_type"].nunique()
render_takeaway(
    f"<b>{termurah}</b> menjadi patokan harga terendah di seluruh jaringan "
    f"(indeks {kota.loc[termurah,'harga']:.2f})"
    + (f" — dan kebetulan juga kota dengan omzet per toko terendah."
       if termurah == terlemah else ".")
    + f" Kotak kosong di peta panas juga bercerita: {termurah} hanya punya "
    f"<b>{n_format_termurah} dari {df_f['store_type'].nunique()} format toko</b>, "
    f"jadi kelemahannya <b>sebagian masalah format, bukan hanya harga</b>. "
    f"Langkah yang masuk akal: uji kenaikan harga bertahap menuju indeks kota lain di "
    f"negara yang sama — buktinya sudah ada di dalam perusahaan sendiri.")

# ── Langkah 4 — adakah toko bermasalah ───────────────────────────────────────
render_step(4, "Wilayah atau toko mana yang perlu perhatian khusus?",
            "Sebelum membuat program perbaikan per toko, pastikan dulu memang ada "
            "toko yang bermasalah.")

k1, k2 = st.columns([6, 4])
with k1:
    s = omzet_toko.sort_values()
    fig = go.Figure(go.Bar(x=[float(i) for i in range(len(s))], y=_v(s.values),
                           marker_color=GREY,
                           hovertemplate="<b>$%{y:,.0f}</b><extra></extra>"))
    fig.add_hline(y=s.mean(), line_dash="dash", line_color=YELLOW, line_width=2,
                  annotation_text=f"rata-rata ${s.mean():,.0f}",
                  annotation_position="top left",
                  annotation_font=dict(color="#B27300", size=11))
    fig.update_xaxes(showticklabels=False, showgrid=False,
                     title=f"Seluruh {n_toko} toko, diurutkan")
    fig.update_yaxes(showgrid=True, gridcolor="#F3F4F6")
    fig.update_layout(
        title=f"Toko terbaik hanya {s.max()/s.min():.1f}x toko terlemah",
        height=360, plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12, color="#374151"),
        margin=dict(t=50, b=50, l=60, r=30), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    pola = df_f.pivot_table(index="city", columns="hour", values="total_amount",
                            aggfunc="sum", observed=True)
    pola = pola.div(pola.sum(axis=1), axis=0)
    fig = matrix_heatmap(pola, title="Pola jam tiap kota (dinormalisasi)",
                         height=360, x_tick_every=4, x_title="Jam")
    st.plotly_chart(fig, use_container_width=True)

render_takeaway(
    f"<b>Tidak ada toko yang gagal.</b> Toko terbaik hanya <b>{s.max()/s.min():.1f}x</b> "
    f"toko terlemah — untuk jaringan {n_toko} toko itu luar biasa merata, dan sebagian "
    f"besar selisihnya sudah dijelaskan oleh format dan kota. Peta panas di kanan "
    f"memperkuatnya: <b>bentuk kurva jam identik di {df_f['city'].nunique()} kota</b>. "
    f"Artinya <b>masalahnya struktural, bukan lokal</b> — program turnaround per toko "
    f"tidak akan menemukan apa pun untuk diperbaiki. Yang perlu diubah adalah "
    f"<b>kebijakan</b>: jam operasional, harga, dan komposisi produk.")

# ── Langkah 5 — laba per wilayah ─────────────────────────────────────────────
if has_profit(df_f):
    render_step(5, "Format mana yang paling menguntungkan?",
                "Karena HPP dipatok ke harga dasar, kelebihan harga di lokasi premium "
                "langsung menjadi laba.")

    laba_tipe = df_f.groupby("store_type", observed=True).agg(
        laba=("est_profit", "sum"), toko=("store_id", "nunique"),
        omzet=("total_amount", "sum"))
    laba_tipe["laba_per_toko"] = laba_tipe["laba"] / laba_tipe["toko"]
    laba_tipe["margin"] = laba_tipe["laba"] / laba_tipe["omzet"]
    lt = laba_tipe.sort_values("laba_per_toko")

    k1, k2 = st.columns([5, 5])
    with k1:
        fig = ranked_bar(lt.index, lt["laba_per_toko"], highlight=len(lt) - 1,
                         title="Estimasi laba kotor per toko", height=340)
        st.plotly_chart(fig, use_container_width=True)
    with k2:
        fig = ranked_bar(lt.index, lt["margin"] * 100, highlight=len(lt) - 1,
                         value_fmt="{:.1f}%", title="Margin per format toko", height=340)
        st.plotly_chart(fig, use_container_width=True)

    render_takeaway(
        f"Format <b>{lt.index[-1]}</b> menghasilkan margin "
        f"<b>{lt['margin'].iloc[-1]:.1%}</b> versus {lt['margin'].iloc[0]:.1%} di "
        f"{lt.index[0]} — selisih "
        f"{(lt['margin'].iloc[-1]-lt['margin'].iloc[0])*100:.1f} poin persen. "
        f"Selisih ini muncul karena <b>biaya produknya sama di mana pun</b>, sementara "
        f"harga jualnya berbeda. Setiap dolar kelebihan harga di lokasi premium masuk "
        f"langsung ke laba tanpa tambahan biaya bahan baku.")

render_caveat(
    f"<b>Catatan.</b> Format <b>{mahal}</b> hanya diwakili "
    f"<b>{int(tipe.loc[mahal,'toko'])} toko</b>. Sinyalnya kuat dan konsisten, tapi "
    f"sampelnya kecil — perlakukan pembukaan gerai berikutnya sebagai konfirmasi, bukan "
    f"jaminan. Angka laba di halaman ini adalah estimasi (lihat halaman Profit, "
    f"Langkah 1) dan <b>belum memotong biaya sewa</b>, yang justru biasanya jauh lebih "
    f"tinggi di lokasi bandara.")

st.markdown("")
d1, d2, _ = st.columns([2, 2, 6])
with d1:
    st.download_button("Unduh Ringkasan Kota", data=kota.to_csv(),
                       file_name="ringkasan_kota.csv", mime="text/csv")
with d2:
    st.download_button("Unduh Ringkasan Format Toko", data=tipe.to_csv(),
                       file_name="ringkasan_format_toko.csv", mime="text/csv")
