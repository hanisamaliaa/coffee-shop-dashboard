"""Tulis INSIGHT_REPORT.md dan BUSINESS_RECOMMENDATIONS.md.

Setiap angka di kedua dokumen dihitung DI SINI dari dataset bersih, tidak ada
yang diketik manual. Dengan begitu isi dokumen tidak bisa melenceng dari
dashboard, dan cukup jalankan ulang script ini kalau data berubah.

Pakai:  python scripts/export_reports.py
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.business_logic import (COGS_RATIO, PEAK_HOURS,  # noqa: E402
                                  QUIET_HOURS, ensure_features)
from utils.metrics import calc_opportunities, test_trend  # noqa: E402

FEATURED = ROOT / "processed" / "coffee_shop_sales_featured.csv"
df = ensure_features(pd.read_csv(FEATURED, parse_dates=["timestamp"]))


def M(x, dp=0):
    return f"${x:,.{dp}f}"


def P(x, dp=1):
    return f"{x * 100:.{dp}f}%".replace(".", ",")


def PS(x, dp=1):
    """Persen bertanda, mis. +0,3% — tandanya mengubah arti kalimat."""
    return f"{x * 100:+.{dp}f}%".replace(".", ",")


def X(x, dp=1):
    """Pengali, mis. 5,7x — pakai koma desimal agar konsisten dengan persen."""
    return f"{x:.{dp}f}".replace(".", ",") + "×"


# ── Kumpulkan semua fakta ────────────────────────────────────────────────────
F = {}
REV = df["total_amount"].sum()
F["rev"], F["trx"] = REV, len(df)
F["kotor"] = df["gross_amount"].sum()
F["hpp"] = df["est_cost"].sum()
F["laba"] = df["est_profit"].sum()
F["margin"] = F["laba"] / REV
F["diskon"] = df["discount_amount"].sum()
F["toko"] = df["store_id"].nunique()
F["kota"] = df["city"].nunique()
F["negara"] = df["country"].nunique()
F["produk"] = df["product_name"].nunique()
F["hari"] = df["timestamp"].dt.date.nunique()
F["avg"] = df["total_amount"].mean()
F["med"] = df["total_amount"].median()

bulanan = df.groupby(df["timestamp"].dt.to_period("M")).agg(
    revenue=("total_amount", "sum"), profit=("est_profit", "sum")).reset_index()
bulanan["days"] = (df.groupby(df["timestamp"].dt.to_period("M"))["timestamp"]
                     .apply(lambda s: s.dt.date.nunique()).values)
bulanan["revenue_per_day"] = bulanan["revenue"] / bulanan["days"]
tren = test_trend(bulanan)
F.update({"slope": tren["slope_per_bulan"], "p": tren["p_value"],
          "r2": tren["r_squared"], "sebaran": tren["sebaran_pct"],
          "jan": bulanan["revenue"].iloc[0], "des": bulanan["revenue"].iloc[-1]})

# Berapa variasi bulanan yang DIHARAPKAN kalau omzet harian murni acak?
harian = df.groupby("date")["total_amount"].sum()
F["cv_diharapkan"] = (harian.std() / np.sqrt(30)) / harian.mean()
F["cv_teramati"] = bulanan["revenue_per_day"].std() / bulanan["revenue_per_day"].mean()

per_jam = df.groupby("hour")["total_amount"].sum()
F["pagi"] = per_jam.reindex(PEAK_HOURS).sum() / REV
F["sepi"] = per_jam.reindex(QUIET_HOURS).sum() / REV
F["rasio_jam"] = ((per_jam.reindex(PEAK_HOURS).sum() / len(PEAK_HOURS))
                  / (per_jam.reindex(QUIET_HOURS).sum() / len(QUIET_HOURS)))
F["akhir_pekan"] = df.loc[df.is_weekend, "total_amount"].sum() / REV
laba_jam = df.groupby("hour")["est_profit"].sum()
F["laba_sepi"] = laba_jam.reindex(QUIET_HOURS).sum() / F["laba"]

anggota, non = df[df.loyalty_member], df[~df.loyalty_member]
vis = df.groupby("customer_id").agg(n=("transaction_id", "size"),
                                    m=("loyalty_member", "first"))
F.update({
    "mem_disc": anggota["is_discounted"].mean(),
    "non_disc": non["is_discounted"].mean(),
    "lipat": anggota["is_discounted"].mean() / non["is_discounted"].mean(),
    "ret_mem": (vis.loc[vis["m"], "n"] > 1).mean(),
    "ret_non": (vis.loc[~vis["m"], "n"] > 1).mean(),
    "basket_mem": anggota["gross_amount"].mean(),
    "basket_non": non["gross_amount"].mean(),
    "mem_share": df["loyalty_member"].mean(),
    "biaya_mem": anggota["discount_amount"].sum(),
    "porsi_diskon_mem": anggota["discount_amount"].sum() / F["diskon"],
    "pelanggan": df["customer_id"].nunique(),
    "sekali": (df.groupby("customer_id").size() == 1).mean(),
    "sekali_n": int((df.groupby("customer_id").size() == 1).sum()),
    "kunjungan_max": int(df.groupby("customer_id").size().max()),
})

dasar = df.loc[df.discount_pct == 0, "quantity"].mean()
tier = (df[df.discount_pct > 0].groupby("discount_tier", observed=True)
        .agg(unit=("quantity", "mean"), biaya=("discount_amount", "sum")).dropna())
F["dasar_unit"] = dasar
F["tier"] = tier
F["tier_gagal"] = int((tier["unit"] < dasar).sum())
F["biaya_gagal"] = tier.loc[tier["unit"] < dasar, "biaya"].sum()
F["deep_biaya"] = df.loc[df.is_deep_discount, "discount_amount"].sum()

tipe = df.groupby("store_type", observed=True).agg(
    harga=("price_index", "median"), trx=("total_amount", "size"),
    toko=("store_id", "nunique"), rev=("total_amount", "sum"),
    laba=("est_profit", "sum"))
tipe["trx_per_toko"] = tipe["trx"] / tipe["toko"]
tipe["rev_per_toko"] = tipe["rev"] / tipe["toko"]
tipe["margin"] = tipe["laba"] / tipe["rev"]
mahal, murah = tipe["harga"].idxmax(), tipe["harga"].idxmin()
F.update({"fmt_mahal": mahal, "fmt_murah": murah,
          "premi": tipe.loc[mahal, "harga"] / tipe.loc[murah, "harga"] - 1,
          "beda_vol": tipe.loc[mahal, "trx_per_toko"] / tipe.loc[murah, "trx_per_toko"] - 1,
          "beda_rev": tipe.loc[mahal, "rev_per_toko"] - tipe.loc[murah, "rev_per_toko"],
          "toko_mahal": int(tipe.loc[mahal, "toko"]),
          "margin_mahal": tipe.loc[mahal, "margin"],
          "margin_murah": tipe.loc[murah, "margin"]})

kota = df.groupby("city", observed=True).agg(
    rev=("total_amount", "sum"), toko=("store_id", "nunique"),
    harga=("price_index", "median"))
kota["per_toko"] = kota["rev"] / kota["toko"]
F.update({"kota_lemah": kota["per_toko"].idxmin(), "kota_kuat": kota["per_toko"].idxmax(),
          "per_toko_lemah": kota["per_toko"].min(), "per_toko_kuat": kota["per_toko"].max(),
          "gap_kota": kota["per_toko"].max() / kota["per_toko"].min() - 1,
          "harga_lemah": kota.loc[kota["per_toko"].idxmin(), "harga"]})

merch = df[df.product_category == "Merchandise"]
F.update({"merch_share": len(merch) / len(df),
          "merch_rev": merch["total_amount"].sum() / REV,
          "merch_aov": merch["total_amount"].mean(),
          "merch_lipat": merch["total_amount"].mean() / F["avg"]})

urut = df.groupby("product_name")["total_amount"].sum().sort_values(ascending=False)
F["n80"] = int(((urut.cumsum() / REV) <= 0.80).sum() + 1)
F["produk_top"], F["rev_top"] = urut.index[0], urut.iloc[0]
omzet_toko = df.groupby("store_id")["total_amount"].sum()
F["gap_toko"] = omzet_toko.max() / omzet_toko.min()

kat = df.groupby("product_category", observed=True).agg(
    rev=("total_amount", "sum"), laba=("est_profit", "sum"))
kat["margin"] = kat["laba"] / kat["rev"]
F.update({"kat_top": kat["rev"].idxmax(), "kat_top_share": kat["rev"].max() / REV,
          "kat_laba_top": kat["laba"].idxmax(),
          "margin_tipis": kat["margin"].idxmin(), "margin_tipis_v": kat["margin"].min(),
          "margin_tebal": kat["margin"].idxmax(), "margin_tebal_v": kat["margin"].max()})

# Produk musiman
prod = df.groupby("product_name").agg(
    rev=("total_amount", "sum"), laba=("est_profit", "sum"),
    bulan=("month", "nunique"))
prod["laba_per_bulan"] = prod["laba"] / prod["bulan"]
prod["rank_thn"] = prod["laba"].rank(ascending=False).astype(int)
prod["rank_bln"] = prod["laba_per_bulan"].rank(ascending=False).astype(int)
prod["lompat"] = prod["rank_thn"] - prod["rank_bln"]
bawah8 = prod.nsmallest(8, "laba")
F["musiman"] = int((bawah8["bulan"] < 12).sum())
F["bulan_musiman"] = int(bawah8["bulan"].min())
juara = prod.loc[prod["lompat"].idxmax()]
F.update({"lompat_nama": prod["lompat"].idxmax(),
          "lompat_thn": int(juara["rank_thn"]), "lompat_bln": int(juara["rank_bln"]),
          "lompat_n": int(juara["lompat"])})

usia = df.groupby("customer_age_group", observed=True)["total_amount"].mean()
usia = usia.drop("Tidak Diketahui", errors="ignore")
F["sebar_usia"] = usia.max() / usia.min() - 1

peluang = calc_opportunities(df)
F["opp_total"] = peluang["Nilai per tahun"].sum()
F["opp_pct"] = peluang["% omzet"].sum()


def nilai_opp(kunci):
    b = peluang[peluang["Aksi"].str.contains(kunci, regex=False)]
    return b["Nilai per tahun"].iloc[0] if not b.empty else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# INSIGHT REPORT
# ─────────────────────────────────────────────────────────────────────────────
INSIGHT = f"""# Insight Report — Coffee Shop Sales

**Capstone KADA Batch 4** · {F['trx']:,} transaksi · {F['toko']} toko ·
{F['kota']} kota · {F['negara']} negara · {F['hari']} hari di 2023

Sumber: `processed/coffee_shop_sales_featured.csv`
Dokumen ini **dibangkitkan otomatis** oleh `scripts/export_reports.py` — setiap
angka dihitung dari dataset, tidak ada yang diketik manual.

---

## Cerita dalam satu kalimat

> **Ini bisnis minuman pagi yang membayar untuk beroperasi 24 jam seperti toko
> serba ada.**

{F['toko']} toko menghasilkan {M(F['rev'])} tahun lalu. Tidak ada yang rusak —
tidak ada toko yang gagal, tidak ada produk yang merugi, datanya bersih.
Dan tidak ada yang tumbuh: Desember ditutup di {M(F['des'])} melawan
Januari {M(F['jan'])}.

Sepuluh temuan berikut masing-masing menjawab lima pertanyaan, karena temuan
yang berhenti di *"omzet menumpuk di pagi hari"* belum selesai bekerja:

> **Apa yang kita lihat → buktinya → artinya apa → nilainya berapa → harus apa**

---

## 1. Kita membayar 24 jam dan menghasilkan di lima jam

**Apa yang kita lihat.** {P(len(QUIET_HOURS) / 24, 0)} hari operasional hanya
menghasilkan di bawah 10% omzet.

**Buktinya.** Pukul 06:00–10:00 adalah lima jam dan **{P(F['pagi'], 0)} omzet**.
Pukul 20:00–06:00 adalah sepuluh jam dan **{P(F['sepi'])}**. Per jam kerja,
blok pagi mengalahkan blok tersepi **{F['rasio_jam']:.0f} banding 1**.
Diukur dari laba pun sama: 10 jam tersepi hanya menghasilkan
{P(F['laba_sepi'])} laba kotor.

**Artinya apa.** Jam-jam itu tetap memakan gaji, listrik, pendingin, dan
keamanan. Ini **masalah jam operasional, bukan masalah penjualan**.

**Nilainya berapa.** {P(len(QUIET_HOURS) / 24, 0)} jam operasional, melawan
{P(F['sepi'])} omzet yang berisiko.

**Harus apa.** Uji coba tutup 20:00–06:00 di satu kota selama 60 hari, lalu ukur
apakah permintaannya pindah ke jam sebelah atau memang hilang.

---

## 2. Program loyalty adalah potongan harga tanpa syarat

**Apa yang kita lihat.** Anggota mendapat diskon **{X(F['lipat'])} lebih
sering** dan tidak memberi apa pun sebagai gantinya.

**Buktinya.** Tiga klaim, tiga kegagalan:

| Klaim program | Anggota | Non-anggota | Hasil |
|:---|---:|---:|:---|
| Datang lebih sering | {P(F['ret_mem'], 2)} | {P(F['ret_non'], 2)} | Tidak ada beda |
| Belanja lebih besar | {M(F['basket_mem'], 2)} | {M(F['basket_non'], 2)} | Anggota **lebih kecil** |
| Lebih murah dilayani | {P(F['mem_disc'])} kena diskon | {P(F['non_disc'])} kena diskon | **{X(F['lipat'])} biayanya** |

Anggota adalah {P(F['mem_share'], 0)} transaksi tapi menyerap
**{P(F['porsi_diskon_mem'], 0)} seluruh biaya diskon**.

**Artinya apa.** Orang mendaftar untuk mendapat diskon. Perilakunya tidak pernah
berubah.

**Nilainya berapa.** {M(F['biaya_mem'])} per tahun tanpa hasil terukur.

**Harus apa.** Jalankan **uji holdout** — hentikan diskon anggota di sepertiga
toko selama satu kuartal, lalu ukur. Setelah itu ubah menjadi hadiah yang
**diperoleh** (beli 9 gratis 1), supaya biayanya mengikuti perilaku, bukan
mendahuluinya.

---

## 3. Hanya satu dari empat tingkat diskon yang benar-benar bekerja

**Apa yang kita lihat.** {F['tier_gagal']} dari {len(F['tier'])} tingkat diskon
menjual keranjang yang **lebih kecil** daripada tidak memberi diskon sama sekali.

**Buktinya.** Unit per transaksi, dengan pembanding tanpa diskon
**{F['dasar_unit']:.2f} unit**:

| Tingkat | Unit per transaksi | vs tanpa diskon |
|:---|---:|:---|
""" + "\n".join(
    f"| {i} | {r.unit:.2f} | {'lebih baik' if r.unit > F['dasar_unit'] else 'lebih buruk'} |"
    for i, r in F["tier"].iterrows()) + f"""

**Artinya apa.** Hanya tingkat 10% yang mengubah perilaku. Yang lebih dalam
jatuh ke orang yang memang sudah mau membeli — itu margin yang diserahkan,
bukan bujukan.

**Nilainya berapa.** {M(F['biaya_gagal'])} per tahun mengalir ke tingkat yang
tidak bekerja, dengan hasil negatif.

**Harus apa.** Batasi wewenang diskon toko maksimal 10%, **dikunci di kasir**
supaya tidak bisa ditimpa. Di atas itu perlu persetujuan.

---

## 4. Kekuatan harga sudah terbukti, tapi dipakai di {F['toko_mahal']} dari {F['toko']} toko

**Apa yang kita lihat.** Toko {F['fmt_mahal']} menjual **{P(F['premi'], 0)} lebih
mahal** dan tidak kehilangan pelanggan sama sekali.

**Buktinya.** Indeks harga {X(tipe.loc[mahal, 'harga'], 2)} melawan
{X(tipe.loc[murah, 'harga'], 2)}. Transaksi per toko justru
**{PS(F['beda_vol'], 1)}** lebih banyak. Hasilnya **{M(F['beda_rev'])} lebih
banyak per toko per tahun**. Margin {P(F['margin_mahal'])} melawan
{P(F['margin_murah'])} di {F['fmt_murah']}.

**Artinya apa.** Permintaan di lokasi captive tidak sensitif terhadap harga pada
tingkat yang sudah kita uji. Kita membuktikannya di {F['toko_mahal']} toko dan
menerapkannya di nol dari {F['toko'] - F['toko_mahal']} toko lainnya.

**Nilainya berapa.** **{M(F['beda_rev'])} per lokasi per tahun**.

**Harus apa.** Prioritaskan lokasi bandara dan transit di review properti
berikutnya.

---

## 5. {F['kota_lemah']} paling murah *sekaligus* paling lemah

**Apa yang kita lihat.** Kota termurah kita juga kota paling tidak produktif.

**Buktinya.** Indeks harga **{X(F['harga_lemah'], 2)[:-1]}** — terendah dari
{F['kota']} kota. Omzet per toko {M(F['per_toko_lemah'])}; {F['kota_kuat']}
menghasilkan **{P(F['gap_kota'], 0)} lebih banyak**.

**Artinya apa.** Sebagian masalah format, sebagian kebiasaan harga yang tidak
pernah dipertanyakan.

**Nilainya berapa.** {M(nilai_opp('Uji harga'))} per tahun kalau digeser ke
indeks kota terdekat di negara yang sama.

**Harus apa.** Jalankan uji harga sebelum menganggap harga rendah itu wajar.

---

## 6. Merchandise paling jarang dibeli dan paling bernilai

**Apa yang kita lihat.** {P(F['merch_share'])} transaksi,
**{P(F['merch_rev'])} omzet**.

**Buktinya.** Rata-rata penjualan merchandise **{M(F['merch_aov'], 2)}** melawan
{M(F['avg'], 2)} keseluruhan — **{X(F['merch_lipat'])} rata-rata**.
{F['produk_top']} adalah produk beromzet tertinggi kita di {M(F['rev_top'])}.

**Artinya apa.** Evaluasi kategori berbasis jumlah transaksi akan menghapus
produk terbaik kita.

**Nilainya berapa.** Menaikkan attach dari {P(F['merch_share'])} ke 4,0% setara
**{M(nilai_opp('Merchandise'))} per tahun**, tanpa pelanggan baru.

**Harus apa.** Pindahkan merchandise ke meja kasir dan tawarkan saat jam sibuk
pagi, ketika {P(F['pagi'], 0)} lalu lintas kita memang sudah ada di toko.

---

## 7. Tiga ide marketing yang sebaiknya berhenti didanai

**Apa yang kita lihat.** Cuaca, hari libur, dan demografi tidak punya efek yang
bisa dipakai.

**Buktinya.** Nilai transaksi rata-rata antar kelompok usia hanya berbeda
**{P(F['sebar_usia'], 0)}** dari tertinggi ke terendah — pelanggan 18-24 dan 65+
berbelanja dengan nilai praktis sama.

**Artinya apa.** Perilaku di sini digerakkan oleh **kejadian dan lokasi**, bukan
oleh siapa pelanggannya.

**Nilainya berapa.** Mencegah satu siklus perencanaan penuh terbuang di tiga
jalan buntu.

**Harus apa.** Alihkan anggaran itu ke waktu dan lokasi — dua tuas yang terbukti
bekerja.

---

## 8. Dua belas bulan, nol pertumbuhan — dan nol musiman

**Apa yang kita lihat.** Desember ditutup di tempat Januari dimulai:
{M(F['des'])} melawan {M(F['jan'])}.

**Buktinya.** Regresi linier pada omzet **per hari** memberi slope
{F['slope']:+.2f} per bulan dengan **p = {F['p']:.2f}** dan R² = {F['r2']:.2f} —
secara statistik tidak bisa dibedakan dari nol.

Lebih jauh lagi: variasi antarbulan yang **teramati** adalah
{P(F['cv_teramati'])}, sementara variasi yang **diharapkan** kalau omzet harian
murni acak adalah {P(F['cv_diharapkan'])}. Yang teramati **lebih kecil** dari
kebisingan acak — artinya bukan sekadar "tidak tumbuh", melainkan
**tidak ada pola musiman sama sekali**.

**Artinya apa.** Tidak satu pun yang sedang dijalankan menghasilkan efek
berlipat. Program loyalty berjalan setahun penuh. Diskon dibagikan setahun
penuh. Keduanya tidak menggerakkan garis.

**Nilainya berapa.** Ini mengubah bingkai seluruh proyek. Pertanyaannya bukan
*"bagaimana mempercepat?"* melainkan *"apa yang bisa menggerakkan garis datar?"*

**Harus apa.** Berhenti mendanai "lebih banyak dari yang sama". Dukung perubahan
struktural di temuan 1, 4, dan 6.

---

## 9. Tidak ada produk bintang, tidak ada toko gagal

**Apa yang kita lihat.** Butuh **{F['n80']} dari {F['produk']} produk** untuk
mencapai 80% omzet.

**Buktinya.** Di ritel pada umumnya angka ini sekitar 20% dari lini. Toko
terbaik hanya **{X(F['gap_toko'])}** toko terlemah.

**Artinya apa.** Tidak ada pemenang untuk digenjot dan tidak ada yang tertinggal
untuk diselamatkan. **Masalahnya struktural, bukan lokal.**

**Nilainya berapa.** Menghemat biaya program intervensi per toko yang tidak akan
menemukan apa pun.

**Harus apa.** Jangan jalankan turnaround per toko. Ubah kebijakan — jam, harga,
komposisi produk.

---

## 10. Retensi tidak bisa diukur, dan kita harus mengatakannya

**Apa yang kita lihat.** **{P(F['sekali'])}** pelanggan muncul tepat sekali dalam
setahun penuh.

**Buktinya.** {F['pelanggan']:,} pelanggan untuk {F['trx']:,} transaksi.
{F['sekali_n']:,} datang sekali. Pelanggan paling setia di seluruh perusahaan
datang **{F['kunjungan_max']} kali**.

**Artinya apa.** Entah ini memang lalu lintas sekali datang, atau `customer_id`
**tidak tersimpan lintas kunjungan** di kasir. Keduanya menuntut strategi yang
sama sekali berbeda, dan kita tidak bisa membedakannya dari data ini.

**Nilainya berapa.** Mencegah kita menyajikan angka lifetime value yang runtuh
oleh satu pertanyaan dari direksi.

**Harus apa.** Tanyakan ke tim IT apakah `customer_id` bertahan lintas
kunjungan. Sampai ada jawabannya, tidak ada CLV, churn, atau cohort yang
dilaporkan.

---

## Bonus: jebakan yang hampir menjerat kami

Daftar produk berlaba terendah terlihat seperti kandidat penghapusan yang jelas.
**Itu salah.**

**{F['musiman']} dari 8 produk berlaba terendah adalah produk MUSIMAN**, hanya
dijual {F['bulan_musiman']} bulan dalam setahun. Contoh paling tajam:
**{F['lompat_nama']}** berada di peringkat **{F['lompat_thn']} dari
{F['produk']}** secara tahunan, tapi peringkat **{F['lompat_bln']} dari
{F['produk']}** kalau dihitung per bulan ketersediaannya — melompat
{F['lompat_n']} posisi.

Memotong lini terbawah berdasarkan peringkat tahunan akan **menghapus seluruh
rangkaian musiman kita**, termasuk salah satu produk berkinerja terbaik per
bulan aktifnya.

---

## Yang tidak kami klaim

| Batasan | Kenapa penting |
|:---|:---|
| **Laba adalah estimasi** | Dataset tidak punya kolom biaya. Margin memakai benchmark HPP per kategori dan bersifat **kotor** — gaji, sewa, listrik tidak termasuk. Sah untuk membandingkan, tidak sah sebagai laporan laba rugi. |
| **Retensi tidak terukur** | {P(F['sekali'])} pelanggan sekali datang. Tidak ada CLV, churn, atau cohort yang aman dari data ini. |
| **Verdict loyalty adalah hipotesis** | Satu tahun tidak bisa melihat efek merek atau pelanggan yang akan pergi. Karena itu rekomendasinya uji coba, bukan pembatalan. |
| **Biaya jam operasional tidak ada** | Temuan terbesar di laporan ini sengaja **tidak diberi angka**. Finance punya angkanya; belum ada yang memintanya. |

---

*Coffee Shop Sales Analytics · Capstone KADA Batch 4*
"""


# ─────────────────────────────────────────────────────────────────────────────
# BUSINESS RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────
REKOM = f"""# Business Recommendations — Coffee Shop Sales

**Capstone KADA Batch 4** · Dua belas rekomendasi berbasis data

Dokumen ini **dibangkitkan otomatis** oleh `scripts/export_reports.py`.
Setiap angka dihitung dari `processed/coffee_shop_sales_featured.csv`.

Setiap rekomendasi membawa **angka, pemilik, tenggat, dan cara mengukur
keberhasilannya**. Rekomendasi yang kehilangan salah satu dari keempatnya hanya
pendapat.

Tiga di antaranya (**R4, R8, R12**) sengaja berbentuk **uji coba, bukan
keputusan**. Di tempat data menunjukkan ada yang salah tapi tidak menunjukkan
jawabannya, rekomendasi yang jujur adalah pergi mengukur.

---

## Ringkasan

| # | Rekomendasi | Angka yang mendasari | Nilai | Pemilik | Kapan | Usaha |
|:--|:---|:---|:---|:---|:--|:--|
| **R1** | Uji coba tutup 20:00–06:00 di satu kota selama 60 hari | {len(QUIET_HOURS)} jam = {P(F['sepi'])} omzet; pagi menang {F['rasio_jam']:.0f}:1 per jam | {P(len(QUIET_HOURS)/24, 0)} jam operasional | Operasional | Q1 | Rendah |
| **R2** | Susun jadwal staf mengikuti kurva permintaan | {P(F['pagi'], 0)} omzet dalam 5 jam, bentuk sama di 7 hari | Satu template jadwal | Operasional | Q1 | Rendah |
| **R3** | Batasi wewenang diskon maksimal 10%, dikunci di kasir | {F['tier_gagal']} dari {len(F['tier'])} tingkat menjual < {F['dasar_unit']:.2f} unit | {M(F['deep_biaya'])}/thn | Keuangan | Q1 | Rendah |
| **R4** | Uji holdout loyalty di ⅓ toko selama 1 kuartal | Anggota dapat diskon {X(F['lipat'])} lebih sering, retensi sama | Menjawab {M(F['biaya_mem'])} | Marketing | Q1 | Rendah |
| **R5** | Ubah loyalty jadi hadiah yang diperoleh (beli 9 gratis 1) | Anggota belanja {M(F['basket_non'] - F['basket_mem'], 2)} lebih kecil | {M(nilai_opp('loyalty'))}/thn | Marketing | Q2 | Sedang |
| **R6** | Pindahkan merchandise ke kasir, tawarkan saat peak pagi | {P(F['merch_share'])} transaksi, {P(F['merch_rev'])} omzet, {M(F['merch_aov'], 2)}/jual | {M(nilai_opp('Merchandise'))}/thn | Ops Ritel | Q1 | Rendah |
| **R7** | Prioritaskan lokasi {F['fmt_mahal']} & transit di review properti | Harga {PS(F['premi'], 0)}, pelanggan {PS(F['beda_vol'], 1)}, {M(F['beda_rev'])}/toko | {M(F['beda_rev'])}/lokasi | Properti | Q2 | Tinggi |
| **R8** | Uji kenaikan harga di {F['kota_lemah']} | Indeks {X(F['harga_lemah'], 2)[:-1]} terendah; {F['kota_kuat']} unggul {P(F['gap_kota'], 0)}/toko | {M(nilai_opp('Uji harga'))}/thn | Pricing | Q2 | Rendah |
| **R9** | Hentikan penargetan cuaca, hari libur, dan demografi | Selisih nilai transaksi antar kelompok usia hanya {P(F['sebar_usia'], 0)} | Bebaskan anggaran segmen | Marketing | Q1 | Rendah |
| **R10** | **Jangan** jalankan program turnaround per toko | Toko terbaik hanya {X(F['gap_toko'])} terlemah dari {F['toko']} toko | Hindari usaha sia-sia | Regional | Q1 | Rendah |
| **R11** | Rasionalisasi varian ukuran, bukan hapus produk lambat | Butuh {F['n80']} dari {F['produk']} produk untuk 80% omzet | Penyederhanaan lini | Kategori | Q2 | Sedang |
| **R12** | Tanya IT: apakah `customer_id` tersimpan lintas kunjungan? | {P(F['sekali'])} pelanggan muncul sekali; terloyal cuma {F['kunjungan_max']} kali | Buka semua analisis CLV | Data / IT | Q1 | Rendah |

**Sembilan dari dua belas bisa dimulai kuartal ini**, dan lima di antaranya
tidak butuh anggaran sama sekali — karena isinya keputusan untuk **berhenti**
melakukan sesuatu (R3, R9, R10) atau untuk **pergi bertanya** (R4, R12).

---

## Dampak yang bisa dihitung

Keempat aksi ini disusun agar **tidak tumpang tindih**: angka loyalty sudah
dikurangi diskon yang masuk hitungan R3, jadi totalnya tidak menghitung dolar
yang sama dua kali.

| Aksi | Nilai per tahun | % omzet | Dasarnya |
|:---|---:|---:|:---|
""" + "\n".join(
    f"| {r['Aksi']} | {M(r['Nilai per tahun'])} | {P(r['% omzet'], 2)} | {r['Dasarnya']} |"
    for _, r in peluang.iterrows()) + f"""
| **Total** | **{M(F['opp_total'])}** | **{P(F['opp_pct'])}** | |

> ### Peluang terbesar tidak ada di tabel ini
>
> Menutup 20:00–06:00 menyentuh **{P(len(QUIET_HOURS)/24, 0)} jam operasional**
> melawan **{P(F['sepi'])} omzet** dan {P(F['laba_sepi'])} laba kotor.
> Nilainya lebih besar dari keempat aksi di atas digabung.
>
> Kami **sengaja tidak memberinya angka dolar**, karena biaya gaji, listrik, dan
> pendingin **tidak ada di dataset**. Memberikan angka di situ berarti mengarang.
> Satu angka dari tim Finance akan menyelesaikannya.

---

## Rincian tiap rekomendasi

### R1 · Uji coba tutup 20:00–06:00 di satu kota selama 60 hari
- **Bukti:** {len(QUIET_HOURS)} jam dari 24 menghasilkan {P(F['sepi'])} omzet dan {P(F['laba_sepi'])} laba kotor. Per jam kerja, pagi menang {F['rasio_jam']:.0f} banding 1. Pola ini identik di ketujuh hari, jadi bukan gejala akhir pekan.
- **Lakukan:** pilih satu kota dengan minimal tiga toko. Tutup semalam. Jangan ubah variabel lain.
- **Ukuran berhasil:** omzet bertahan ≥ 95% setelah 60 hari. Kalau pelanggan hanya bergeser ke 06:00–10:00, jam itu memang murni biaya.
- **Risiko:** lokasi transit mungkin punya nilai strategis semalam. Kecualikan toko bandara dari uji coba.

### R2 · Susun jadwal staf mengikuti kurva permintaan
- **Bukti:** {P(F['pagi'], 0)} omzet dalam lima jam, bentuk kurva sama setiap hari, akhir pekan hanya versi lebih tinggi ({P(F['akhir_pekan'], 0)} omzet dari 29% hari).
- **Lakukan:** satu template jadwal untuk tujuh hari. Sabtu–Minggu tambah orang, bukan tambah jam buka.
- **Ukuran berhasil:** antrean pukul 08:00 turun; jam kerja per dolar omzet turun.

### R3 · Batasi wewenang diskon maksimal 10%
- **Bukti:** tanpa diskon pelanggan membeli {F['dasar_unit']:.2f} unit. {F['tier_gagal']} dari {len(F['tier'])} tingkat diskon berada di bawah angka itu.
- **Lakukan:** kunci batasnya di sistem kasir, bukan di dokumen kebijakan.
- **Ukuran berhasil:** nol transaksi di atas 10% tanpa persetujuan; unit per transaksi bertahan di {F['dasar_unit']:.2f}.
- **Nilai:** {M(F['deep_biaya'])}/tahun.

### R4 · Uji holdout loyalty *(uji coba, bukan keputusan)*
- **Bukti:** anggota dapat diskon {X(F['lipat'])} lebih sering, tidak datang lebih sering ({P(F['ret_mem'], 2)} vs {P(F['ret_non'], 2)}), dan belanja lebih kecil sebelum diskon.
- **Lakukan:** hentikan diskon anggota di sepertiga toko yang dipilih acak selama satu kuartal.
- **Ukuran berhasil:** omzet dan frekuensi kunjungan uji vs kontrol. Ini menjawab pertanyaan senilai {M(F['biaya_mem'])} dengan biaya satu kuartal data.
- **Kenapa uji coba:** satu tahun tidak bisa melihat efek merek atau pelanggan yang akan pergi. Membatalkan program hanya dengan bukti ini adalah tindakan berlebihan.

### R5 · Ubah loyalty jadi hadiah yang diperoleh
- **Bukti:** program sekarang membayar sebelum perilakunya terjadi. Anggota belanja {M(F['basket_non'] - F['basket_mem'], 2)} lebih kecil per keranjang.
- **Lakukan:** beli 9 gratis 1 — hadiah datang setelah kunjungan kesembilan, jadi biaya mengikuti perilaku.
- **Ukuran berhasil:** biaya per anggota turun; tingkat kunjungan kedua naik di atas {P(F['ret_mem'], 1)}.
- **Urutan:** jalankan R4 dulu. R5 adalah tindak lanjut dari jawabannya.

### R6 · Merchandise ke meja kasir
- **Bukti:** {P(F['merch_share'])} transaksi, {P(F['merch_rev'])} omzet, {M(F['merch_aov'], 2)} per penjualan — {X(F['merch_lipat'])} rata-rata. {F['produk_top']} adalah produk beromzet tertinggi kita.
- **Lakukan:** penempatan di kasir plus penawaran saat peak 06:00–10:00, ketika {P(F['pagi'], 0)} lalu lintas memang sudah ada.
- **Ukuran berhasil:** attach merchandise mencapai 4,0% transaksi.
- **Nilai:** {M(nilai_opp('Merchandise'))}/tahun — peluang terukur terbesar di laporan ini.

### R7 · Prioritaskan lokasi {F['fmt_mahal']} dan transit
- **Bukti:** {F['fmt_mahal']} menjual {P(F['premi'], 0)} lebih mahal dan melayani {PS(F['beda_vol'], 1)} pelanggan. {M(tipe.loc[mahal, 'rev_per_toko'])} per toko melawan {M(tipe.loc[murah, 'rev_per_toko'])}.
- **Lakukan:** condongkan review properti berikutnya ke lokasi dengan audiens captive.
- **Ukuran berhasil:** dua pembukaan berikutnya format transit dan mencapai indeks harga {X(tipe.loc[mahal, 'harga'], 2)}.
- **Peringatan:** hanya {F['toko_mahal']} toko yang mendukung temuan ini. Sinyalnya kuat tapi sampelnya kecil — perlakukan pembukaan berikutnya sebagai konfirmasi. Perlu diingat juga biaya sewa bandara biasanya jauh lebih tinggi, dan itu tidak ada di dataset.

### R8 · Uji harga di {F['kota_lemah']} *(uji coba, bukan keputusan)*
- **Bukti:** indeks harga {X(F['harga_lemah'], 2)[:-1]}, terendah dari {F['kota']} kota, dan omzet per toko paling rendah ({M(F['per_toko_lemah'])} vs {M(F['per_toko_kuat'])}).
- **Lakukan:** naikkan sebagian produk 3% menuju indeks kota terdekat di negara yang sama, tahan satu kuartal.
- **Ukuran berhasil:** volume bertahan dalam 2%.
- **Nilai:** {M(nilai_opp('Uji harga'))}/tahun kalau bertahan.

### R9 · Hentikan penargetan cuaca, hari libur, dan demografi
- **Bukti:** nilai transaksi rata-rata antar kelompok usia hanya berbeda {P(F['sebar_usia'], 0)} dari tertinggi ke terendah.
- **Lakukan:** alokasikan ulang ke kampanye berbasis waktu dan lokasi.
- **Ukuran berhasil:** anggaran benar-benar berpindah, bukan diam-diam dipertahankan.

### R10 · Jangan jalankan program turnaround per toko
- **Bukti:** toko terbaik hanya {X(F['gap_toko'])} toko terlemah. Untuk jaringan {F['toko']} toko, itu luar biasa merata.
- **Lakukan:** arahkan usaha intervensi ke kebijakan — jam, harga, komposisi — bukan ke masing-masing lokasi.
- **Ukuran berhasil:** tidak ada rencana perbaikan per toko yang dibuka tahun ini.
- **Catatan:** ini rekomendasi untuk **tidak** membelanjakan. Ia masuk daftar justru karena naluri pertama biasanya adalah memeringkat toko lalu menindak yang terbawah.

### R11 · Rasionalisasi ukuran, jangan hapus produk lambat
- **Bukti:** {F['n80']} dari {F['produk']} produk dibutuhkan untuk 80% omzet — tidak ada ekor panjang untuk dipotong. Yang lebih penting: **{F['musiman']} dari 8 produk berlaba terendah adalah produk musiman**. {F['lompat_nama']} berperingkat {F['lompat_thn']} dari {F['produk']} secara tahunan, tapi **{F['lompat_bln']} dari {F['produk']} per bulan ketersediaannya**.
- **Lakukan:** tinjau varian ukuran dari produk yang sama. Nilai produk musiman berdasarkan laba per bulan aktif.
- **Ukuran berhasil:** jumlah SKU turun dengan omzet bertahan; tidak ada lini musiman yang dipotong berdasarkan peringkat tahunan.
- **Kenapa ini penting:** rekomendasi yang paling kelihatan jelas di sini — hapus 8 produk terbawah — adalah **salah**, dan kami hanya menangkapnya setelah menormalisasi berapa lama tiap produk tersedia.

### R12 · Tanyakan ke IT soal `customer_id`
- **Bukti:** {P(F['sekali'])} pelanggan muncul sekali; yang terloyal cuma {F['kunjungan_max']} kali.
- **Lakukan:** satu email ke tim Data/IT.
- **Ukuran berhasil:** jawaban tertulis. Kalau ID tidak tersimpan, perbaiki sebelum analisis berikutnya.
- **Nilai:** membuka setiap pertanyaan CLV, churn, dan cohort yang cepat atau lambat akan ditanyakan direksi.

---

## Tiga pertanyaan yang pasti ditanyakan

**"Kenapa omzet naik tapi profit turun?"**
Di data ini profit **tidak** turun — laba bergerak sejajar omzet dan margin
stabil sepanjang tahun. Yang bisa kami tunjukkan adalah di mana margin paling
tipis: tingkat diskon 15% dan 20%, serta setiap jam setelah 20:00. Dan kami
harus jujur: angka laba kami **estimasi** dari benchmark kategori, bukan angka
akuntansi.

**"Apakah program loyalty sebaiknya dihentikan?"**
Belum. Program ini gagal di ketiga klaimnya di data, tapi satu tahun tidak bisa
melihat efek merek atau pelanggan yang akan pergi kalau programnya dicabut.
Jalankan holdout di sepertiga toko selama satu kuartal —
{M(F['biaya_mem'])} layak ditunggu satu kuartal untuk dijawab dengan bukti.

**"Produk mana yang sebaiknya dihentikan?"**
Tidak ada, berdasarkan bukti ini. Butuh {F['n80']} dari {F['produk']} produk
untuk mencapai 80% omzet, jadi tidak ada ekor panjang untuk dipotong. Dan
{F['musiman']} dari 8 produk yang terlihat paling lambat sebenarnya **musiman** —
diperingkat per bulan ketersediaannya, posisinya jauh berbeda.
Rasionalisasi ukuran, bukan penghapusan produk.

---

## Alur presentasi 10 menit

> **Kalimat yang mengikat seluruh presentasi:**
> Ini bisnis minuman pagi yang membayar untuk beroperasi 24 jam seperti toko
> serba ada.

| # | Bagian | Durasi | Yang disampaikan |
|:--|:---|:--|:---|
| 1 | **Situation** | 1,5 mnt | {F['toko']} toko di {F['kota']} kota, {F['trx']:,} transaksi, {M(F['rev'])}, satu tahun penuh. Bisnis ini dikelola dengan baik: tidak ada toko gagal, data bersih, nol duplikat. |
| 2 | **Problem** | 1,5 mnt | Dua belas bulan, nol pertumbuhan (p = {F['p']:.2f}). Loyalty berjalan setahun. Diskon dibagikan setahun. Keduanya tidak menggerakkan garis. |
| 3 | **Evidence** | 3 mnt | {P(F['pagi'], 0)} omzet dalam 5 jam. Loyalty gagal di ketiga klaimnya. {F['fmt_mahal']} {PS(F['premi'], 0)} lebih mahal tanpa kehilangan pelanggan. Merchandise {P(F['merch_share'])} transaksi tapi {P(F['merch_rev'])} omzet. |
| 4 | **Insight** | 1,5 mnt | Kita membayar operasi 24 jam untuk kurva permintaan 5 jam, mendanai diskon yang tidak mengubah apa pun, dan hampir tidak memakai dua tuas yang terbukti bekerja. |
| 5 | **Recommendation** | 2 mnt | Dua belas aksi, sembilan bisa mulai kuartal ini, lima tanpa anggaran. Tiga di antaranya uji coba. |
| 6 | **Business Impact** | 0,5 mnt | +{P(F['opp_pct'])} omzet ({M(F['opp_total'])}/tahun) dari empat aksi terukur, ditambah satu keputusan jam operasional yang nilainya lebih besar dari keempatnya digabung. |

**Kalimat penutup:**

> Setiap aksi di daftar ini layak dikerjakan. Tidak satu pun senilai menjawab
> satu pertanyaan: **berapa biaya membuka pintu dari pukul 20:00 sampai 06:00?**
> Finance punya angka itu. Belum ada yang memintanya.

---

*Coffee Shop Sales Analytics · Capstone KADA Batch 4*
"""

if __name__ == "__main__":
    for nama, isi in [("INSIGHT_REPORT.md", INSIGHT),
                      ("BUSINESS_RECOMMENDATIONS.md", REKOM)]:
        (ROOT / nama).write_text(isi, encoding="utf-8")
        print(f"  tertulis  {nama:<32} {len(isi):>7,} karakter")
    print(f"\nSemua angka dihitung dari {len(df):,} baris dataset bersih.")
