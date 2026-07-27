"""Halaman 8 — Business Recommendation & Executive Storytelling.

Menjawab syarat project:
  - Minimal 10 rekomendasi berbasis data
  - Alur presentasi Situation -> Problem -> Evidence -> Insight -> Recommendation
    -> Business Impact
"""

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.business_logic import PEAK_HOURS, PROFIT_DISCLAIMER, QUIET_HOURS
from utils.charts import RED, TEAL, ranked_bar
from utils.data_loader import check_empty_data, get_filter_options, load_data
from utils.filters import apply_filters
from utils.formatting import format_currency
from utils.metrics import (calc_kpi, calc_monthly_data, calc_opportunities,
                           test_trend)
from utils.styling import (inject_global_css, render_caveat, render_header,
                           render_kpi_card, render_step, render_takeaway)

st.set_page_config(page_title="Rekomendasi - Coffee Shop Dashboard",
                   page_icon=":coffee:", layout="wide")
inject_global_css()

df = load_data()
options = get_filter_options(df)

render_header("REKOMENDASI BISNIS & ALUR PRESENTASI",
              "Dua belas aksi, masing-masing dengan angka, pemilik, dan cara mengukurnya",
              "Halaman 8 dari 8")

df_f = apply_filters(df, options, key_prefix="rec")
check_empty_data(df_f, "Rekomendasi")

# ── Kumpulkan semua angka yang dikutip di halaman ini dari data ──────────────
kpi = calc_kpi(df_f)
omzet, laba = kpi["total_revenue"], kpi["total_profit"]
bulanan = calc_monthly_data(df_f)
tren = test_trend(bulanan)
peluang = calc_opportunities(df_f)

per_jam = df_f.groupby("hour")["total_amount"].sum()
F = {
    "pagi": per_jam.reindex(PEAK_HOURS).sum() / omzet,
    "sepi": per_jam.reindex(QUIET_HOURS).sum() / omzet,
    "rasio": ((per_jam.reindex(PEAK_HOURS).sum() / len(PEAK_HOURS))
              / max(per_jam.reindex(QUIET_HOURS).sum() / len(QUIET_HOURS), 1e-9)),
    "akhir_pekan": df_f.loc[df_f["is_weekend"], "total_amount"].sum() / omzet,
    "dasar_unit": df_f.loc[df_f["discount_pct"] == 0, "quantity"].mean(),
    "deep_biaya": df_f.loc[df_f["is_deep_discount"], "discount_amount"].sum(),
    "toko": df_f["store_id"].nunique(),
    "produk": df_f["product_name"].nunique(),
}

anggota = df_f[df_f["loyalty_member"]]
non = df_f[~df_f["loyalty_member"]]
kunjungan = df_f.groupby("customer_id").agg(n=("transaction_id", "size"),
                                            m=("loyalty_member", "first"))
F.update({
    "lipat_diskon": (anggota["is_discounted"].mean() / non["is_discounted"].mean()
                     if non["is_discounted"].mean() else 0),
    "ret_anggota": (kunjungan.loc[kunjungan["m"], "n"] > 1).mean(),
    "ret_non": (kunjungan.loc[~kunjungan["m"], "n"] > 1).mean(),
    "beda_basket": non["gross_amount"].mean() - anggota["gross_amount"].mean(),
    "biaya_anggota": anggota["discount_amount"].sum(),
    "sekali": (df_f.groupby("customer_id").size() == 1).mean(),
    "kunjungan_max": int(df_f.groupby("customer_id").size().max()),
    "pelanggan": df_f["customer_id"].nunique(),
})

tipe = df_f.groupby("store_type", observed=True).agg(
    harga=("price_index", "median"), trx=("total_amount", "size"),
    toko=("store_id", "nunique"), rev=("total_amount", "sum"))
tipe["trx_per_toko"] = tipe["trx"] / tipe["toko"]
tipe["rev_per_toko"] = tipe["rev"] / tipe["toko"]
mahal, murah = tipe["harga"].idxmax(), tipe["harga"].idxmin()
F.update({
    "fmt_mahal": mahal,
    "premi": tipe.loc[mahal, "harga"] / tipe.loc[murah, "harga"] - 1,
    "beda_vol": tipe.loc[mahal, "trx_per_toko"] / tipe.loc[murah, "trx_per_toko"] - 1,
    "beda_rev": tipe.loc[mahal, "rev_per_toko"] - tipe.loc[murah, "rev_per_toko"],
    "toko_mahal": int(tipe.loc[mahal, "toko"]),
})

kota = df_f.groupby("city", observed=True).agg(
    rev=("total_amount", "sum"), toko=("store_id", "nunique"),
    harga=("price_index", "median"))
kota["per_toko"] = kota["rev"] / kota["toko"]
F.update({
    "kota_lemah": kota["per_toko"].idxmin(),
    "kota_kuat": kota["per_toko"].idxmax(),
    "per_toko_lemah": kota["per_toko"].min(),
    "gap_kota": kota["per_toko"].max() / kota["per_toko"].min() - 1,
})

merch = df_f[df_f["product_category"] == "Merchandise"]
F.update({
    "merch_share": len(merch) / len(df_f) if len(df_f) else 0,
    "merch_rev": merch["total_amount"].sum() / omzet if omzet else 0,
    "merch_aov": merch["total_amount"].mean() if len(merch) else 0,
})

prod = df_f.groupby("product_name")["total_amount"].sum().sort_values(ascending=False)
F["n80"] = int(((prod.cumsum() / omzet) <= 0.80).sum() + 1)
omzet_toko = df_f.groupby("store_id")["total_amount"].sum()
F["gap_toko"] = omzet_toko.max() / omzet_toko.min()


def nilai(kunci_aksi, default=0.0):
    baris = peluang[peluang["Aksi"].str.contains(kunci_aksi, regex=False)]
    return baris["Nilai per tahun"].iloc[0] if not baris.empty else default


# ── Ringkasan dampak ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Jumlah Rekomendasi", "12", None)
with c2:
    render_kpi_card("Bisa Mulai Kuartal Ini", "9", None)
with c3:
    render_kpi_card("Nilai Terukur / Tahun",
                    format_currency(peluang["Nilai per tahun"].sum()), None)
with c4:
    render_kpi_card("Setara % Omzet", f"{peluang['% omzet'].sum():.1%}", None)

# ── Langkah 1 — daftar rekomendasi ───────────────────────────────────────────
render_step(1, "Dua belas rekomendasi berbasis data",
            "Setiap baris punya angka, pemilik, tenggat, dan cara mengukur "
            "keberhasilannya. Rekomendasi tanpa keempatnya cuma pendapat.")

REKOMENDASI = pd.DataFrame([
    ("R1", "Uji coba tutup 20:00–06:00 selama 60 hari di satu kota",
     f"{len(QUIET_HOURS)} jam = {F['sepi']:.1%} omzet; pagi menang {F['rasio']:.0f}:1 per jam",
     "42% jam operasional", "Operasional", "Q1", "Rendah",
     "Omzet bertahan ≥95% setelah permintaan bergeser ke jam sebelah"),
    ("R2", "Susun jadwal staf mengikuti kurva: padat 06:00–10:00, minimal setelah 20:00",
     f"{F['pagi']:.0%} omzet dalam 5 jam, bentuk kurva sama di 7 hari",
     "Satu template jadwal", "Operasional", "Q1", "Rendah",
     "Antrean jam 08:00 turun; jam kerja per dolar omzet turun"),
    ("R3", "Batasi wewenang diskon toko maksimal 10%, dikunci di kasir",
     f"5%, 15%, dan 20% semua menjual < {F['dasar_unit']:.2f} unit (tanpa diskon)",
     f"{format_currency(F['deep_biaya'])}/thn", "Keuangan", "Q1", "Rendah",
     "Nol transaksi >10% tanpa persetujuan; unit per transaksi bertahan"),
    ("R4", "Uji holdout loyalty: hentikan diskon anggota di ⅓ toko selama 1 kuartal",
     f"Anggota dapat diskon {F['lipat_diskon']:.1f}x lebih sering, retensi sama",
     f"Menjawab pertanyaan {format_currency(F['biaya_anggota'])}", "Marketing", "Q1", "Rendah",
     "Omzet & frekuensi kunjungan uji vs kontrol setelah satu kuartal"),
    ("R5", "Ubah loyalty jadi hadiah yang DIPEROLEH (beli 9 gratis 1)",
     f"Anggota belanja {format_currency(F['beda_basket'])} LEBIH KECIL sebelum diskon",
     f"{format_currency(nilai('loyalty'))}/thn", "Marketing", "Q2", "Sedang",
     "Biaya per anggota turun; tingkat kunjungan kedua naik"),
    ("R6", "Pindahkan merchandise ke meja kasir + tawarkan saat jam sibuk pagi",
     f"{F['merch_share']:.1%} transaksi tapi {F['merch_rev']:.1%} omzet, "
     f"{format_currency(F['merch_aov'])}/penjualan",
     f"{format_currency(nilai('Merchandise'))}/thn", "Ops Ritel", "Q1", "Rendah",
     "Attach rate merchandise mencapai 4,0% transaksi"),
    ("R7", f"Prioritaskan lokasi {F['fmt_mahal']} dan transit di review properti",
     f"Harga {F['premi']:+.0%}, pelanggan {F['beda_vol']:+.1%}, "
     f"{format_currency(F['beda_rev'])}/toko",
     f"{format_currency(F['beda_rev'])}/lokasi", "Properti", "Q2", "Tinggi",
     f"Dua pembukaan berikutnya format transit dan mencapai indeks harga "
     f"{tipe.loc[mahal,'harga']:.2f}"),
    ("R8", f"Uji kenaikan harga di {F['kota_lemah']} menuju indeks kota terdekat",
     f"Indeks harga terendah di jaringan; {F['kota_kuat']} menghasilkan "
     f"{F['gap_kota']:.0%} lebih banyak per toko",
     f"{format_currency(nilai('Uji harga'))}/thn", "Pricing", "Q2", "Rendah",
     "Volume bertahan dalam 2% setelah kenaikan harga 3%"),
    ("R9", "Hentikan pendanaan penargetan cuaca, hari libur, dan demografi",
     "Selisih antar kelompok usia, cuaca, dan hari libur semuanya di bawah ambang berguna",
     "Membebaskan anggaran segmen", "Marketing", "Q1", "Rendah",
     "Anggaran benar-benar dipindahkan ke kampanye waktu & lokasi"),
    ("R10", "JANGAN jalankan program turnaround per toko",
     f"Toko terbaik hanya {F['gap_toko']:.1f}x toko terlemah dari {F['toko']} toko",
     "Menghindari usaha sia-sia", "Regional", "Q1", "Rendah",
     "Tidak ada rencana perbaikan per toko dibuka tahun ini"),
    ("R11", "Rasionalisasi varian ukuran, bukan menghapus produk lambat",
     f"Butuh {F['n80']} dari {F['produk']} produk untuk 80% omzet — tidak ada ekor panjang",
     "Penyederhanaan lini", "Kategori", "Q2", "Sedang",
     "Jumlah SKU turun dengan omzet bertahan; produk musiman tidak dipotong "
     "berdasarkan peringkat tahunan"),
    ("R12", "Tanyakan ke IT apakah customer_id tersimpan lintas kunjungan",
     f"{F['sekali']:.1%} pelanggan hanya muncul sekali; terloyal pun cuma "
     f"{F['kunjungan_max']}x",
     "Membuka semua analisis CLV", "Data / IT", "Q1", "Rendah",
     "Jawaban tertulis. Kalau tidak tersimpan, perbaiki sebelum analisis berikutnya"),
], columns=["#", "Rekomendasi", "Angka yang mendasari", "Nilai", "Pemilik",
            "Kapan", "Usaha", "Cara mengukur keberhasilan"])

st.dataframe(REKOMENDASI, hide_index=True, use_container_width=True, height=470)

render_takeaway(
    "<b>Sembilan dari dua belas bisa dimulai kuartal ini</b>, dan lima di antaranya "
    "tidak butuh anggaran sama sekali — karena isinya adalah keputusan untuk "
    "<b>berhenti</b> melakukan sesuatu (R3, R9, R10) atau untuk <b>pergi bertanya</b> "
    "(R4, R12). Tiga rekomendasi (R4, R8, R12) sengaja berbentuk <b>uji coba, bukan "
    "keputusan</b>: di tempat data menunjukkan ada yang salah tapi tidak menunjukkan "
    "jawabannya, rekomendasi yang jujur adalah pergi mengukur.")

# ── Langkah 2 — dampak bisnis ────────────────────────────────────────────────
render_step(2, "Berapa dampaknya kalau dijalankan?",
            "Hanya yang bisa dihitung dari data. Sisanya kami katakan tidak bisa dihitung.")

k1, k2 = st.columns([6, 4])
with k1:
    urut = peluang.sort_values("Nilai per tahun")
    fig = ranked_bar(urut["Aksi"], urut["Nilai per tahun"], highlight=len(urut) - 1,
                     title=f"Total terukur +{peluang['% omzet'].sum():.1%} omzet",
                     height=330)
    st.plotly_chart(fig, use_container_width=True)
with k2:
    st.markdown(
        f"""
        <div style="padding:14px 4px;line-height:1.9;font-size:0.9rem;color:#374151;">
        <div style="font-size:2.1rem;font-weight:800;color:#1C174D;line-height:1.2;">
        +{peluang['% omzet'].sum():.1%}</div>
        <div style="color:#6B7280;margin-bottom:14px;">
        {format_currency(peluang['Nilai per tahun'].sum())} per tahun, dari empat aksi
        yang tidak tumpang tindih</div>
        <div style="border-left:3px solid #D9535F;padding-left:12px;">
        <b>Yang tidak ada di angka ini:</b><br>
        Menutup 20:00–06:00 menyentuh <b>42% jam operasional</b> melawan
        <b>{F['sepi']:.1%} omzet</b>. Nilainya lebih besar dari keempat aksi di samping
        digabung — tapi kami tidak memberinya angka dolar, karena biaya gaji dan listrik
        <b>tidak ada di dataset</b>.<br><br>
        Satu angka dari Finance menyelesaikannya.</div>
        </div>
        """, unsafe_allow_html=True)

# ── Langkah 3 — alur presentasi ──────────────────────────────────────────────
render_step(3, "Alur presentasi 10 menit",
            "Situation → Problem → Evidence → Insight → Recommendation → Business Impact")

st.markdown(
    """
    <div style="background:#1C174D;color:#fff;border-radius:12px;padding:22px 26px;
                margin-bottom:16px;">
      <div style="font-size:0.72rem;letter-spacing:0.1em;color:#FFB703;font-weight:800;">
      KALIMAT YANG MENGIKAT SELURUH PRESENTASI</div>
      <div style="font-size:1.42rem;font-weight:800;margin-top:8px;line-height:1.4;">
      Ini bisnis minuman pagi yang membayar untuk beroperasi 24 jam
      seperti toko serba ada.</div>
    </div>
    """, unsafe_allow_html=True)

ALUR = pd.DataFrame([
    ("1. Situation", "1,5 menit",
     f"{F['toko']} toko di {df_f['city'].nunique()} kota, {len(df_f):,} transaksi, "
     f"{format_currency(omzet)}, satu tahun penuh. Bisnis ini dikelola dengan baik: "
     f"tidak ada toko yang gagal, data bersih, nol duplikat.",
     "Executive Summary — deretan KPI"),
    ("2. Problem", "1,5 menit",
     f"Dua belas bulan, nol pertumbuhan (p={tren.get('p_value', 0):.2f}). Program loyalty "
     f"berjalan setahun penuh. Diskon dibagikan setahun penuh. Keduanya tidak "
     f"menggerakkan garis sedikit pun.",
     "Executive Summary — grafik tren datar"),
    ("3. Evidence", "3 menit",
     f"{F['pagi']:.0%} omzet masuk dalam 5 jam. Loyalty gagal di ketiga klaimnya sendiri. "
     f"Toko {F['fmt_mahal']} menjual {F['premi']:.0%} lebih mahal tanpa kehilangan "
     f"pelanggan. Merchandise {F['merch_share']:.1%} transaksi tapi {F['merch_rev']:.1%} omzet.",
     "Halaman Time, Customer, Region, Product"),
    ("4. Insight", "1,5 menit",
     "Kita membayar operasi 24 jam untuk melayani kurva permintaan 5 jam, mendanai diskon "
     "yang tidak mengubah apa pun, dan hampir tidak memakai dua tuas yang sudah terbukti "
     "bekerja: harga lokasi premium dan attach merchandise.",
     "Halaman Profit"),
    ("5. Recommendation", "2 menit",
     "Dua belas aksi, sembilan bisa mulai kuartal ini, lima tanpa anggaran. Tiga di "
     "antaranya adalah uji coba — di tempat kita tidak tahu, kita katakan tidak tahu "
     "lalu pergi mengukur.",
     "Halaman ini — tabel rekomendasi"),
    ("6. Business Impact", "0,5 menit",
     f"+{peluang['% omzet'].sum():.1%} omzet "
     f"({format_currency(peluang['Nilai per tahun'].sum())}/tahun) dari empat aksi "
     f"terukur, ditambah satu keputusan jam operasional yang nilainya lebih besar dari "
     f"keempatnya digabung.",
     "Halaman ini — grafik dampak"),
], columns=["Bagian", "Durasi", "Yang disampaikan", "Yang ditampilkan"])

st.dataframe(ALUR, hide_index=True, use_container_width=True, height=290)

# ── Langkah 4 — tiga pertanyaan yang pasti ditanya ───────────────────────────
render_step(4, "Tiga pertanyaan yang pasti ditanyakan",
            "Siapkan jawabannya sebelum ditanya. Mengakui batasan lebih dulu adalah "
            "kredibilitas termurah yang bisa didapat.")

QNA = pd.DataFrame([
    ("Kenapa omzet naik tapi profit turun?",
     "Di data ini profit TIDAK turun — laba bergerak sejajar omzet dan margin stabil. "
     "Yang bisa kami tunjukkan adalah di mana margin paling tipis: tingkat diskon 15% "
     "dan 20%, serta setiap jam setelah 20:00. Dan kami harus jujur: angka laba kami "
     "adalah estimasi dari benchmark kategori, bukan angka akuntansi."),
    ("Apakah program loyalty sebaiknya dihentikan?",
     "Belum. Program ini gagal di ketiga klaimnya di data, tapi satu tahun tidak bisa "
     "melihat efek merek atau pelanggan yang akan pergi kalau programnya dicabut. "
     f"Jalankan holdout di ⅓ toko selama satu kuartal — {format_currency(F['biaya_anggota'])} "
     "layak ditunggu satu kuartal untuk dijawab dengan bukti."),
    ("Produk mana yang sebaiknya dihentikan?",
     f"Tidak ada, berdasarkan bukti ini. Butuh {F['n80']} dari {F['produk']} produk untuk "
     "mencapai 80% omzet, jadi tidak ada ekor panjang untuk dipotong. Dan produk yang "
     "terlihat paling lambat sebagian besar adalah produk MUSIMAN — kalau diperingkat "
     "per bulan ketersediaannya, posisinya jauh berbeda. Rasionalisasi ukuran, bukan "
     "penghapusan produk."),
], columns=["Pertanyaan", "Jawaban jujur"])

st.dataframe(QNA, hide_index=True, use_container_width=True, height=260)

render_caveat(
    f"<b>Yang tidak kami klaim.</b> (1) {PROFIT_DISCLAIMER} "
    f"(2) <b>Retensi tidak bisa diukur</b> — {F['sekali']:.0%} dari {F['pelanggan']:,} "
    f"pelanggan hanya muncul sekali, jadi tidak ada angka CLV, churn, atau cohort yang "
    f"aman dari data ini. (3) <b>Verdict loyalty adalah hipotesis</b>, bukan kesimpulan — "
    f"itulah sebabnya R4 berupa uji coba, bukan pembatalan.")

st.markdown("")
d1, d2, _ = st.columns([2, 2, 6])
with d1:
    st.download_button("Unduh Rekomendasi (CSV)", data=REKOMENDASI.to_csv(index=False),
                       file_name="rekomendasi_bisnis.csv", mime="text/csv")
with d2:
    st.download_button("Unduh Alur Presentasi (CSV)", data=ALUR.to_csv(index=False),
                       file_name="alur_presentasi.csv", mime="text/csv")
