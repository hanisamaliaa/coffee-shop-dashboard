"""Bangun ulang processed/*.csv dari data mentah.

Pakai:  python scripts/build_processed.py

Alur: raw -> clean -> featured. Setiap langkah dicatat, tidak ada baris yang
dihapus diam-diam, dan total omzet diverifikasi tidak berubah di akhir.
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from utils.business_logic import build_features, COGS_RATIO  # noqa: E402

RAW = ROOT / "data" / "coffee_shop_sales.csv"
OUT = ROOT / "processed"
OUT.mkdir(exist_ok=True)

LOG = []


def catat(langkah, kolom, tindakan, jumlah, alasan):
    LOG.append({"langkah": langkah, "kolom": kolom, "tindakan": tindakan,
                "baris_terdampak": jumlah, "alasan": alasan})
    print(f"  [{langkah}] {kolom:<20} {tindakan:<42} {jumlah:>6,} baris")


def clean(df_raw):
    """Pembersihan. Nol baris dihapus — semua diperbaiki di tempat."""
    df = df_raw.copy()
    print("\nCLEANING")

    # 1. Tipe data
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    catat(1, "timestamp", "object -> datetime64", len(df),
          "tanpa datetime tidak bisa buat fitur waktu")

    # 2. Cuaca & suhu: PULIHKAN dari kota-hari yang sama.
    #
    #    Cuaca adalah properti kota-hari, bukan properti transaksi: dari 3.265
    #    pasangan kota-hari, tidak ada satu pun yang punya dua kondisi cuaca
    #    berbeda. Jadi nilai yang hilang masih ADA di dataset — tinggal diambil.
    #
    #    Mengisi dengan modus/median akan MENGARANG data: 978 baris jadi
    #    "Rainy" menaikkan porsi Rainy dari 42,3% ke 45,2% dan membuat analisis
    #    cuaca apa pun jadi bias.
    tanggal = df["timestamp"].dt.date
    idx = pd.MultiIndex.from_arrays([df["city"], tanggal])

    peta_cuaca = (df.dropna(subset=["weather_condition"])
                    .assign(_d=tanggal[df["weather_condition"].notna()])
                    .drop_duplicates(["city", "_d"])
                    .set_index(["city", "_d"])["weather_condition"])
    peta_suhu = (df.dropna(subset=["temperature_c"])
                   .assign(_d=tanggal[df["temperature_c"].notna()])
                   .groupby(["city", "_d"])["temperature_c"].median())

    n_cuaca, n_suhu = int(df["weather_condition"].isna().sum()), int(df["temperature_c"].isna().sum())
    df["weather_condition"] = df["weather_condition"].fillna(
        pd.Series(idx.map(peta_cuaca), index=df.index))
    df["temperature_c"] = df["temperature_c"].fillna(
        pd.Series(idx.map(peta_suhu), index=df.index))
    catat(2, "weather_condition", "diisi dari kota-hari yang sama",
          n_cuaca - int(df["weather_condition"].isna().sum()),
          "cuaca = properti kota-hari, nilai asli ada di dataset")
    catat(2, "temperature_c", "diisi dari median kota-hari yang sama",
          n_suhu - int(df["temperature_c"].isna().sum()),
          "suhu = properti kota-hari, nilai asli ada di dataset")

    sisa_c, sisa_s = int(df["weather_condition"].isna().sum()), int(df["temperature_c"].isna().sum())
    if sisa_c:
        df["weather_condition"] = df["weather_condition"].fillna("Tidak Tercatat")
        catat(2, "weather_condition", "sisanya -> 'Tidak Tercatat'", sisa_c,
              "jujur bilang tidak tahu, daripada mengarang")
    if sisa_s:
        df["temperature_c"] = df["temperature_c"].fillna(
            df.groupby([df["city"], df["timestamp"].dt.month])["temperature_c"]
              .transform("median"))
        catat(2, "temperature_c", "sisanya -> median kota-bulan", sisa_s,
              "perkiraan terdekat yang masih masuk akal secara geografis")

    # 3. holiday_name: kosong BUKAN data hilang — memang hari biasa
    n_libur = int(df["holiday_name"].notna().sum())
    df["is_holiday"] = df["holiday_name"].notna()
    df["holiday_name"] = df["holiday_name"].fillna("Bukan Hari Libur")
    catat(3, "holiday_name", "NaN -> 'Bukan Hari Libur' + flag is_holiday",
          len(df) - n_libur, "kosong = hari itu memang bukan hari libur")

    # 4. Demografi. 'Prefer not to say' TIDAK digabung: itu jawaban yang
    #    diberikan pelanggan, berbeda dari data yang tidak tercatat.
    for kol in ["customer_age_group", "customer_gender"]:
        n = int(df[kol].isna().sum())
        df[kol] = df[kol].fillna("Tidak Diketahui")
        catat(4, kol, "NaN -> 'Tidak Diketahui'", n,
              "kategori sendiri, tidak digabung dgn 'Prefer not to say'")

    # Yang SENGAJA tidak diubah:
    #   - harga berbeda per produk  -> kebijakan harga per lokasi, bukan error
    #   - outlier 6,7% (IQR)        -> median 4 unit = pesanan rombongan;
    #                                   membuangnya menghapus 23,1% omzet
    #   - customer_id 97% sekali    -> ditandai, tapi tidak diutak-atik
    return df


def main():
    df_raw = pd.read_csv(RAW)
    print(f"Raw: {df_raw.shape[0]:,} baris x {df_raw.shape[1]} kolom")

    df_clean = clean(df_raw)
    df_clean.to_csv(OUT / "coffee_shop_sales_clean.csv", index=False)

    print("\nFEATURE ENGINEERING")
    df = build_features(df_clean)
    baru = [c for c in df.columns if c not in df_clean.columns]
    print(f"  {len(baru)} fitur baru: {', '.join(baru)}")

    # Verifikasi keras — kalau ada yang gagal, build berhenti.
    assert len(df) == len(df_raw), "jumlah baris berubah!"
    assert abs(df["total_amount"].sum() - df_raw["total_amount"].sum()) < 0.01, "omzet berubah!"
    assert df["transaction_id"].is_unique, "transaction_id tidak unik!"
    assert df.drop(columns=["date"]).isna().sum().sum() == 0, "masih ada nilai kosong!"
    assert (df["est_profit"] < 0).sum() == 0, "ada laba negatif — cek asumsi HPP!"

    df.to_csv(OUT / "coffee_shop_sales_featured.csv", index=False)
    pd.DataFrame(LOG).to_csv(OUT / "cleaning_log.csv", index=False)

    omzet, laba = df["total_amount"].sum(), df["est_profit"].sum()
    print(f"\nHASIL")
    print(f"  Baris x kolom      : {df.shape[0]:,} x {df.shape[1]}")
    print(f"  Total omzet        : ${omzet:,.2f}  (tidak berubah dari raw)")
    print(f"  Estimasi HPP       : ${df['est_cost'].sum():,.2f}")
    print(f"  Estimasi laba kotor: ${laba:,.2f}  (margin {laba/omzet:.1%})")
    print(f"  Total diskon       : ${df['discount_amount'].sum():,.2f}")
    print(f"\n  Asumsi HPP: " + ", ".join(f"{k} {v:.0%}" for k, v in COGS_RATIO.items()))
    print(f"\n  Tersimpan ke processed/: clean, featured, cleaning_log")


if __name__ == "__main__":
    main()
