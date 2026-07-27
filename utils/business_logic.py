"""Business logic — satu sumber kebenaran untuk semua fitur turunan.

Modul ini dipakai oleh:
  - scripts/build_processed.py  (membuat processed/*.csv)
  - seluruh halaman dashboard   (lewat utils/data_loader.py)
  - notebook analisis           (konstanta yang sama, disalin manual untuk Colab)

Kalau ada angka asumsi yang berubah, ubah DI SINI saja.
"""

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# 1. ASUMSI BIAYA  (fitur paling penting — dataset TIDAK punya kolom cost)
# ─────────────────────────────────────────────────────────────────────────────
#
# Dataset ini tidak menyediakan harga pokok penjualan (HPP). Tanpa HPP,
# `total_amount` hanyalah OMZET, bukan laba — sehingga semua pertanyaan tentang
# profit tidak bisa dijawab.
#
# Kita estimasi HPP memakai rasio yang lazim di industri kedai kopi:
#
#   Tea          14%  daun teh sangat murah; harga jual didominasi jasa & tempat
#   Coffee       18%  biji + susu; margin tinggi adalah ciri khas kedai kopi
#   Smoothie     30%  buah segar, cepat rusak, porsi besar
#   Pastry       33%  bahan roti + tingkat basi tinggi
#   Sandwich     38%  protein & sayur segar — HPP tertinggi di kategori makanan
#   Merchandise  50%  barang jadi dari pemasok, margin ritel biasa
#
COGS_RATIO = {
    "Tea": 0.14,
    "Coffee": 0.18,
    "Smoothie": 0.30,
    "Pastry": 0.33,
    "Sandwich": 0.38,
    "Merchandise": 0.50,
}

# HPP dipatok ke HARGA DASAR produk (harga terendah produk itu di seluruh
# jaringan), BUKAN ke harga jual di toko tersebut.
#
# Alasannya menentukan:
#   - Kalau HPP = 18% x harga jual toko  -> margin % setiap toko jadi IDENTIK.
#     Toko bandara yang menjual 45% lebih mahal akan punya margin % yang sama
#     persis dengan toko biasa, dan temuan "lokasi mana yang paling untung"
#     lenyap begitu saja.
#   - Kalau HPP = 18% x harga dasar      -> biji kopi harganya sama di mana pun.
#     Kelebihan harga di bandara langsung menjadi laba, dan setiap dolar diskon
#     langsung mengurangi laba. Ini yang benar secara ekonomi.
#
# ⚠️  Angka ini ESTIMASI, bukan angka akuntansi. Sah untuk MEMBANDINGKAN
#     (produk A vs B, toko X vs Y, diskon 10% vs 20%), tidak sah sebagai laporan
#     laba rugi. Ini LABA KOTOR — gaji, sewa, dan listrik tidak ada di dataset.
COST_BASIS = "harga dasar produk (harga terendah di seluruh jaringan)"
PROFIT_DISCLAIMER = (
    "Laba adalah ESTIMASI, bukan angka akuntansi. Dataset ini tidak punya kolom "
    "biaya, sehingga HPP diperkirakan dari benchmark industri per kategori dan "
    "dipatok ke harga dasar produk. Angka ini LABA KOTOR — gaji, sewa, dan "
    "listrik tidak termasuk."
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. BLOK WAKTU OPERASIONAL
# ─────────────────────────────────────────────────────────────────────────────
DAYPARTS = [
    (0, 5, "Dini Hari (00-05)"),
    (6, 10, "Puncak Pagi (06-10)"),
    (11, 13, "Siang (11-13)"),
    (14, 16, "Sore (14-16)"),
    (17, 19, "Petang (17-19)"),
    (20, 23, "Malam (20-23)"),
]
DAYPART_LABELS = [d[2] for d in DAYPARTS]
DAYPART_HOURS = {d[2]: d[1] - d[0] + 1 for d in DAYPARTS}

PEAK_HOURS = list(range(6, 11))                       # 06:00-10:00
QUIET_HOURS = list(range(0, 6)) + list(range(20, 24))  # 20:00-06:00

DISCOUNT_TIERS = {
    0.00: "Tanpa Diskon",
    0.05: "Kecil (5%)",
    0.10: "Standar (10%)",
    0.15: "Besar (15%)",
    0.20: "Terbesar (20%)",
}
DISCOUNT_TIER_ORDER = ["Tanpa Diskon", "Kecil (5%)", "Standar (10%)",
                       "Besar (15%)", "Terbesar (20%)"]

# Nama hari & bulan dalam Bahasa Indonesia — seluruh dashboard berbahasa
# Indonesia, jadi sumbu grafiknya juga harus terbaca oleh semua orang.
DAY_NAMES = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
               "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
WEEKEND_DAYS = {"Sabtu", "Minggu"}

# Belahan bumi selatan — Juli di Sydney itu musim DINGIN, bukan panas.
SOUTHERN_COUNTRIES = {"AUS"}
_SEASON_NORTH = {12: "Dingin", 1: "Dingin", 2: "Dingin", 3: "Semi", 4: "Semi",
                 5: "Semi", 6: "Panas", 7: "Panas", 8: "Panas", 9: "Gugur",
                 10: "Gugur", 11: "Gugur"}
_FLIP = {"Dingin": "Panas", "Semi": "Gugur", "Panas": "Dingin", "Gugur": "Semi"}
_SEASON_SOUTH = {m: _FLIP[s] for m, s in _SEASON_NORTH.items()}
SEASON_ORDER = ["Dingin", "Semi", "Panas", "Gugur"]


# ─────────────────────────────────────────────────────────────────────────────
# 3. FUNGSI FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────
def add_discount_features(df):
    """Rekonstruksi besaran diskon dari aritmatika transaksi.

    Dataset hanya menyediakan flag True/False. Tapi karena
    `total_amount = unit_price x quantity x (1 - diskon)` berlaku 100%,
    besaran diskonnya bisa dihitung balik dan ternyata jatuh rapi ke
    empat tingkat: 5%, 10%, 15%, 20%.
    """
    df = df.copy()
    df["gross_amount"] = (df["unit_price"] * df["quantity"]).round(2)
    df["discount_amount"] = (df["gross_amount"] - df["total_amount"]).round(2)
    df["discount_pct"] = np.where(
        df["gross_amount"] > 0,
        (df["discount_amount"] / df["gross_amount"]).round(2), 0.0)
    df["discount_tier"] = pd.Categorical(
        df["discount_pct"].map(DISCOUNT_TIERS).fillna("Tanpa Diskon"),
        categories=DISCOUNT_TIER_ORDER, ordered=True)
    df["is_discounted"] = df["discount_pct"] > 0
    df["is_deep_discount"] = df["discount_pct"] >= 0.15
    return df


def add_price_features(df):
    """price_index = harga di toko ini dibanding harga TERMURAH produk yang sama.

    Nilai 1,00 berarti toko itu menjual dengan harga terendah se-jaringan.
    Variasi harga ini BUKAN data kotor — setiap kombinasi kota+tipe toko punya
    tepat satu harga per produk, jadi ini kebijakan harga per lokasi.
    """
    df = df.copy()
    base = df.groupby("product_name")["unit_price"].transform("min")
    df["base_price"] = base.round(2)
    df["price_index"] = (df["unit_price"] / base).round(3)
    return df


def add_profit_features(df):
    """Estimasi HPP dan laba kotor. Lihat catatan COGS_RATIO di atas."""
    df = df.copy()
    if "base_price" not in df.columns:
        df = add_price_features(df)
    ratio = df["product_category"].map(COGS_RATIO)
    if ratio.isna().any():
        hilang = sorted(df.loc[ratio.isna(), "product_category"].unique())
        raise ValueError(f"Kategori tanpa asumsi HPP: {hilang}. Tambahkan ke COGS_RATIO.")

    df["cogs_ratio"] = ratio
    df["unit_cost"] = (df["base_price"] * ratio).round(4)
    df["est_cost"] = (df["unit_cost"] * df["quantity"]).round(4)
    df["est_profit"] = (df["total_amount"] - df["est_cost"]).round(4)
    df["profit_margin"] = np.where(
        df["total_amount"] > 0,
        (df["est_profit"] / df["total_amount"]).round(4), 0.0)
    # Laba yang HILANG karena diskon — inti pertanyaan "dampak diskon ke profit"
    df["profit_lost_to_discount"] = df["discount_amount"].round(4) \
        if "discount_amount" in df.columns else 0.0
    return df


def add_time_features(df):
    """Pecahan waktu + daypart + musim yang sadar belahan bumi."""
    df = df.copy()
    ts = pd.to_datetime(df["timestamp"])
    df["timestamp"] = ts
    df["date"] = ts.dt.date
    df["hour"] = ts.dt.hour
    df["month"] = ts.dt.month
    df["month_name"] = pd.Categorical(
        (ts.dt.month - 1).map(dict(enumerate(MONTH_NAMES))),
        categories=MONTH_NAMES, ordered=True)
    df["day_of_week"] = ts.dt.dayofweek
    df["day_name"] = pd.Categorical(
        ts.dt.dayofweek.map(dict(enumerate(DAY_NAMES))),
        categories=DAY_NAMES, ordered=True)
    df["quarter"] = ts.dt.quarter
    df["quarter_label"] = "Q" + ts.dt.quarter.astype(str)
    df["is_weekend"] = ts.dt.dayofweek >= 5

    df["daypart"] = pd.Categorical(
        pd.cut(df["hour"], bins=[-1, 5, 10, 13, 16, 19, 23], labels=DAYPART_LABELS),
        categories=DAYPART_LABELS, ordered=True)
    # Jumlah jam tiap blok. Tanpa ini kita membandingkan blok 6 jam dengan blok
    # 3 jam seolah setara.
    df["daypart_hours"] = df["daypart"].map(DAYPART_HOURS).astype(float)

    df["is_peak_hour"] = df["hour"].isin(PEAK_HOURS)
    df["is_quiet_hour"] = df["hour"].isin(QUIET_HOURS)

    df["season"] = pd.Categorical(
        np.where(df["country"].isin(SOUTHERN_COUNTRIES),
                 df["month"].map(_SEASON_SOUTH), df["month"].map(_SEASON_NORTH)),
        categories=SEASON_ORDER, ordered=True)
    return df


def add_product_features(df):
    df = df.copy()
    df["product_size"] = pd.Categorical(
        df["product_name"].str.extract(r"^(Small|Medium|Large)")[0]
          .fillna("Regular")
          .map({"Small": "Kecil", "Medium": "Sedang",
                "Large": "Besar", "Regular": "Reguler"}),
        categories=["Kecil", "Sedang", "Besar", "Reguler"], ordered=True)
    df["is_beverage"] = df["product_category"].isin(["Coffee", "Tea", "Smoothie"])
    df["is_merchandise"] = df["product_category"] == "Merchandise"
    return df


def add_customer_features(df):
    df = df.copy()
    df["customer_visits"] = df.groupby("customer_id")["transaction_id"].transform("size")
    df["is_repeat_customer"] = df["customer_visits"] > 1
    df["value_segment"] = pd.Categorical(
        pd.qcut(df["total_amount"], 4,
                labels=["Rendah", "Menengah", "Tinggi", "Premium"]),
        categories=["Rendah", "Menengah", "Tinggi", "Premium"], ordered=True)
    df["basket_size"] = pd.Categorical(
        pd.cut(df["quantity"], bins=[0, 1, 3, 6, np.inf],
               labels=["Small (1)", "Medium (2-3)", "Large (4-6)", "Bulk (7+)"]),
        categories=["Small (1)", "Medium (2-3)", "Large (4-6)", "Bulk (7+)"],
        ordered=True)
    return df


def build_features(df):
    """Jalankan seluruh feature engineering. Urutan penting: harga -> diskon -> profit."""
    df = add_price_features(df)
    df = add_discount_features(df)
    df = add_profit_features(df)
    df = add_time_features(df)
    df = add_product_features(df)
    df = add_customer_features(df)
    return df


# Urutan kategori. CSV tidak menyimpan dtype, jadi setelah `read_csv` semua
# kolom ini kembali menjadi teks biasa dan groupby akan mengurutkannya secara
# ALFABETIS — hari jadi Fri, Mon, Sat, Sun...; tier diskon jadi Besar, Kecil,
# Standar, Terbesar. Urutan harus dipulihkan setiap kali data dimuat.
CATEGORY_ORDERS = {
    "month_name": MONTH_NAMES,
    "day_name": DAY_NAMES,
    "daypart": DAYPART_LABELS,
    "discount_tier": DISCOUNT_TIER_ORDER,
    "season": SEASON_ORDER,
    "product_size": ["Kecil", "Sedang", "Besar", "Reguler"],
    "value_segment": ["Rendah", "Menengah", "Tinggi", "Premium"],
    "basket_size": ["Small (1)", "Medium (2-3)", "Large (4-6)", "Bulk (7+)"],
    "quarter_label": ["Q1", "Q2", "Q3", "Q4"],
}


def restore_categoricals(df):
    """Kembalikan urutan kategori yang hilang setelah CSV dibaca."""
    df = df.copy()
    for kol, urutan in CATEGORY_ORDERS.items():
        if kol in df.columns:
            hadir = [n for n in urutan if n in set(df[kol].dropna().unique())]
            if hadir:
                df[kol] = pd.Categorical(df[kol], categories=hadir, ordered=True)
    return df


def ensure_features(df):
    """Idempoten: tambahkan hanya fitur yang belum ada.

    Dipakai data_loader supaya dashboard tetap jalan walau CSV yang dimuat
    adalah versi lama tanpa kolom profit.
    """
    if "price_index" not in df.columns:
        df = add_price_features(df)
    if "discount_pct" not in df.columns:
        df = add_discount_features(df)
    if "est_profit" not in df.columns:
        df = add_profit_features(df)
    if "daypart" not in df.columns:
        df = add_time_features(df)
    if "product_size" not in df.columns:
        df = add_product_features(df)
    if "customer_visits" not in df.columns:
        df = add_customer_features(df)
    return restore_categoricals(df)
