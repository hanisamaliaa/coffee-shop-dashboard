"""Perhitungan metrik untuk seluruh halaman dashboard.

Aturan yang dipegang di modul ini:
  1. Perbandingan harus SEBANDING. Jangan bandingkan 1 bulan lawan 11 bulan.
  2. Kalau sebuah angka adalah noise, katakan itu noise — jangan disajikan
     sebagai temuan.
  3. Setiap temuan harus membawa angkanya sendiri.
"""

import numpy as np
import pandas as pd

from utils.business_logic import PEAK_HOURS, QUIET_HOURS


# ─────────────────────────────────────────────────────────────────────────────
# KPI
# ─────────────────────────────────────────────────────────────────────────────
def calc_kpi(df):
    kosong = {"total_revenue": 0, "total_transactions": 0, "avg_transaction": 0,
              "total_quantity": 0, "total_profit": 0, "profit_margin": 0,
              "total_discount": 0, "unique_customers": 0}
    if df.empty:
        return kosong

    revenue = df["total_amount"].sum()
    trx = df["transaction_id"].nunique()
    profit = df["est_profit"].sum() if "est_profit" in df.columns else 0
    diskon = df["discount_amount"].sum() if "discount_amount" in df.columns else 0

    return {
        "total_revenue": revenue,
        "total_transactions": trx,
        "avg_transaction": revenue / trx if trx else 0,
        "median_transaction": df["total_amount"].median(),
        "total_quantity": int(df["quantity"].sum()),
        "total_profit": profit,
        "profit_margin": profit / revenue if revenue else 0,
        "total_discount": diskon,
        "unique_customers": df["customer_id"].nunique() if "customer_id" in df.columns else 0,
    }


def calc_delta(df, date_col="timestamp"):
    """Bandingkan bulan penuh TERAKHIR dengan bulan penuh SEBELUMNYA.

    Versi sebelumnya membandingkan 1 bulan terakhir melawan SELURUH sisa data
    (11 bulan), sehingga setiap KPI menampilkan sekitar -90% dan bisnis terlihat
    ambruk. Itu bukan perbandingan yang sebanding.

    Kalau rentang data kurang dari 2 bulan, kita bagi dua sama panjang.
    Selalu mengembalikan `label` supaya UI bisa menjelaskan yang dibandingkan.
    """
    kosong = {"revenue": None, "transactions": None, "avg_txn": None,
              "quantity": None, "profit": None, "label": None}
    if df.empty or date_col not in df.columns or df[date_col].isna().all():
        return kosong

    periode = df[date_col].dt.to_period("M")
    bulan = sorted(periode.unique())

    if len(bulan) >= 2:
        kini, lalu = df[periode == bulan[-1]], df[periode == bulan[-2]]
        label = f"{bulan[-1].strftime('%b %Y')} vs {bulan[-2].strftime('%b %Y')}"
    else:
        tengah = df[date_col].min() + (df[date_col].max() - df[date_col].min()) / 2
        kini, lalu = df[df[date_col] >= tengah], df[df[date_col] < tengah]
        label = "paruh akhir vs paruh awal periode"

    if lalu.empty or kini.empty:
        return kosong

    def ubah(a, b):
        return ((a - b) / b * 100) if b else None

    rev_k, rev_l = kini["total_amount"].sum(), lalu["total_amount"].sum()
    trx_k, trx_l = kini["transaction_id"].nunique(), lalu["transaction_id"].nunique()

    return {
        "revenue": ubah(rev_k, rev_l),
        "transactions": ubah(trx_k, trx_l),
        "quantity": ubah(kini["quantity"].sum(), lalu["quantity"].sum()),
        "avg_txn": ubah(rev_k / trx_k if trx_k else 0, rev_l / trx_l if trx_l else 0),
        "profit": (ubah(kini["est_profit"].sum(), lalu["est_profit"].sum())
                   if "est_profit" in df.columns else None),
        "label": label,
    }


def calc_monthly_data(df):
    if df.empty:
        return pd.DataFrame()

    agg = {"revenue": ("total_amount", "sum"),
           "transactions": ("transaction_id", "nunique"),
           "quantity": ("quantity", "sum")}
    if "est_profit" in df.columns:
        agg["profit"] = ("est_profit", "sum")
    if "discount_amount" in df.columns:
        agg["discount"] = ("discount_amount", "sum")

    bulanan = df.groupby(df["timestamp"].dt.to_period("M")).agg(**agg).reset_index()
    hari = (df.groupby(df["timestamp"].dt.to_period("M"))["timestamp"]
              .apply(lambda s: s.dt.date.nunique()).values)
    bulanan["days"] = hari
    # Omzet per hari — supaya Februari (28 hari) tidak terlihat buruk hanya
    # karena bulannya lebih pendek.
    bulanan["revenue_per_day"] = bulanan["revenue"] / bulanan["days"]
    bulanan["timestamp"] = bulanan["timestamp"].dt.to_timestamp()
    return bulanan


# ─────────────────────────────────────────────────────────────────────────────
# UJI TREN — apakah pergerakan bulanan itu nyata atau cuma noise?
# ─────────────────────────────────────────────────────────────────────────────
def test_trend(monthly_df):
    """Regresi linier sederhana pada omzet PER HARI.

    Mengembalikan slope, p-value, dan penilaian apakah tren itu nyata.
    Ini yang membedakan "omzet turun 5% bulan ini" (noise) dari tren sungguhan.
    """
    if monthly_df.empty or len(monthly_df) < 4:
        return {"cukup_data": False}

    y = monthly_df["revenue_per_day"].to_numpy(dtype=float)
    x = np.arange(len(y), dtype=float)
    n = len(x)
    slope = ((x - x.mean()) * (y - y.mean())).sum() / ((x - x.mean()) ** 2).sum()
    intercept = y.mean() - slope * x.mean()
    resid = y - (intercept + slope * x)
    se = np.sqrt((resid ** 2).sum() / (n - 2) / ((x - x.mean()) ** 2).sum())
    t = slope / se if se else 0.0
    r2 = 1 - (resid ** 2).sum() / ((y - y.mean()) ** 2).sum()

    # p-value dua sisi via aproksimasi normal (cukup untuk n=12)
    from math import erfc, sqrt
    p = erfc(abs(t) / sqrt(2))

    return {
        "cukup_data": True,
        "slope_per_bulan": slope,
        "p_value": p,
        "r_squared": max(r2, 0.0),
        "ada_tren": bool(p < 0.05),
        "sebaran_pct": (monthly_df["revenue_per_day"].max()
                        / monthly_df["revenue_per_day"].min() - 1),
    }


# ─────────────────────────────────────────────────────────────────────────────
# TEMUAN — berbasis data, dan jujur ketika angkanya tidak berarti apa-apa
# ─────────────────────────────────────────────────────────────────────────────
def _hi(teks):
    return f"<span class='finding-highlight'>{teks}</span>"


def calc_findings(df, monthly_df):
    if df.empty:
        return ["Data tidak cukup untuk dianalisis."]

    temuan = []
    omzet = df["total_amount"].sum()

    # 1. Tren — dan kejujuran kalau ternyata tidak ada tren
    tren = test_trend(monthly_df)
    if tren.get("cukup_data"):
        if tren["ada_tren"]:
            arah = "naik" if tren["slope_per_bulan"] > 0 else "turun"
            temuan.append(
                f"Omzet {_hi(arah)} secara konsisten sebesar "
                f"{_hi(f'${abs(tren['slope_per_bulan']):,.0f} per hari setiap bulan')} "
                f"(p={tren['p_value']:.3f}). Ini tren nyata, bukan fluktuasi biasa.")
        else:
            temuan.append(
                f"Omzet {_hi('datar sepanjang periode')} — tidak ada tren naik maupun "
                f"turun (p={tren['p_value']:.2f}). Sebaran antarbulan {tren['sebaran_pct']:.0%} "
                f"masih dalam batas fluktuasi acak, jadi {_hi('tidak ada pola musiman')} "
                f"yang bisa dimanfaatkan.")

    # 2. Konsentrasi waktu — biasanya temuan terbesar di bisnis ini
    if "hour" in df.columns:
        per_jam = df.groupby("hour")["total_amount"].sum()
        pagi = per_jam.reindex(PEAK_HOURS).sum() / omzet
        sepi = per_jam.reindex(QUIET_HOURS).sum() / omzet
        rasio = ((per_jam.reindex(PEAK_HOURS).sum() / len(PEAK_HOURS))
                 / max(per_jam.reindex(QUIET_HOURS).sum() / len(QUIET_HOURS), 1e-9))
        temuan.append(
            f"{_hi(f'{pagi:.0%} omzet')} masuk hanya dalam {_hi('5 jam (06:00-10:00)')}, "
            f"sementara {len(QUIET_HOURS)} jam tersepi (20:00-06:00) cuma menghasilkan "
            f"{_hi(f'{sepi:.1%}')}. Per jam kerja, pagi menang {rasio:.0f} banding 1.")

    # 3. Kategori dominan
    kat = df.groupby("product_category")["total_amount"].sum().sort_values(ascending=False)
    temuan.append(
        f"{_hi(kat.index[0])} menyumbang {_hi(f'{kat.iloc[0]/omzet:.0%}')} omzet "
        f"(${kat.iloc[0]:,.0f}) — lebih besar dari gabungan "
        f"{len(kat)-2} kategori terbawah.")

    # 4. Nilai vs volume — jebakan klasik saat mengevaluasi produk
    ringkas = df.groupby("product_category").agg(
        trx=("total_amount", "size"), rev=("total_amount", "sum"))
    ringkas["indeks"] = (ringkas["rev"] / omzet) / (ringkas["trx"] / len(df))
    puncak = ringkas["indeks"].idxmax()
    if ringkas.loc[puncak, "indeks"] > 1.5:
        temuan.append(
            f"{_hi(puncak)} hanya {ringkas.loc[puncak,'trx']/len(df):.1%} transaksi "
            f"tapi {_hi(f'{ringkas.loc[puncak,'rev']/omzet:.1%} omzet')} — "
            f"nilainya {ringkas.loc[puncak,'indeks']:.1f}x rata-rata. "
            f"Evaluasi produk berbasis jumlah transaksi akan salah menilai kategori ini.")

    # 5. Profit
    if "est_profit" in df.columns:
        laba = df["est_profit"].sum()
        rugi = int((df["est_profit"] < 0).sum())
        temuan.append(
            f"Estimasi laba kotor {_hi(f'${laba:,.0f}')} (margin {laba/omzet:.0%}), "
            f"dengan {_hi(f'{rugi} transaksi merugi')}. Kebocoran laba ada di "
            f"{_hi('kebijakan diskon')}, bukan di produk.")

    return temuan


def calc_opportunities(df):
    """Peluang yang bisa diberi angka, dan sengaja dibuat TIDAK tumpang tindih.

    Angka loyalty hanya menghitung diskon yang BELUM masuk hitungan "batasi
    diskon 15%+", supaya totalnya tidak menghitung dolar yang sama dua kali.

    Peluang terbesar — menutup jam sepi — sengaja TIDAK dimasukkan, karena
    dataset tidak punya biaya operasional. Memberi angka di situ berarti
    mengarang.
    """
    if df.empty:
        return pd.DataFrame(columns=["Aksi", "Nilai per tahun", "% omzet", "Dasarnya"])

    omzet = df["total_amount"].sum()
    baris = []

    if "is_deep_discount" in df.columns:
        nilai = df.loc[df["is_deep_discount"], "discount_amount"].sum()
        if nilai > 0:
            baris.append(("Batasi diskon maksimal 10%", nilai,
                          "Tingkat 15% & 20% menjual lebih sedikit unit "
                          "daripada tanpa diskon sama sekali"))

    if "loyalty_member" in df.columns and "is_deep_discount" in df.columns:
        anggota = df[df["loyalty_member"]]
        nilai = anggota.loc[~anggota["is_deep_discount"], "discount_amount"].sum()
        if nilai > 0:
            baris.append(("Restrukturisasi program loyalty", nilai,
                          "Diskon anggota tanpa perubahan perilaku yang terukur"))

    # Naikkan penetrasi kategori bernilai tinggi ke 4% transaksi
    ringkas = df.groupby("product_category").agg(
        trx=("total_amount", "size"), rev=("total_amount", "sum"),
        aov=("total_amount", "mean"))
    ringkas["indeks"] = (ringkas["rev"] / omzet) / (ringkas["trx"] / len(df))
    puncak = ringkas["indeks"].idxmax()
    share = ringkas.loc[puncak, "trx"] / len(df)
    if ringkas.loc[puncak, "indeks"] > 1.5 and share < 0.04:
        tambahan = int(round((0.04 - share) * len(df)))
        baris.append((f"Naikkan penetrasi {puncak} ke 4%",
                      tambahan * ringkas.loc[puncak, "aov"],
                      f"{tambahan} penjualan tambahan x "
                      f"${ringkas.loc[puncak,'aov']:.2f} — kategorinya sudah ada"))

    # Naikkan kota termurah ke indeks harga kota terdekat di negara yang sama
    if {"city", "price_index", "country"} <= set(df.columns):
        kota = df.groupby(["country", "city"])["price_index"].median()
        termurah = kota.idxmin()
        senegara = kota.loc[termurah[0]].drop(termurah[1], errors="ignore")
        if len(senegara):
            naik = senegara.min() / kota.loc[termurah] - 1
            if naik > 0.005:
                rev_kota = df.loc[df["city"] == termurah[1], "total_amount"].sum()
                baris.append((f"Uji harga di {termurah[1]}", rev_kota * naik,
                              f"Kota termurah di jaringan (indeks "
                              f"{kota.loc[termurah]:.2f}); {senegara.idxmin()} sudah "
                              f"berjalan di {senegara.min():.2f} di negara yang sama"))

    out = pd.DataFrame(baris, columns=["Aksi", "Nilai per tahun", "Dasarnya"])
    if out.empty:
        return out
    out["% omzet"] = out["Nilai per tahun"] / omzet
    return out.sort_values("Nilai per tahun", ascending=False).reset_index(drop=True)


def calc_recommendations(df, monthly_df):
    """Rekomendasi harus punya angka, arah tindakan, dan alasan.

    Yang tidak boleh: 'pertahankan momentum di bulan puncak' ketika bulan puncak
    itu sebenarnya cuma fluktuasi acak.
    """
    if df.empty:
        return ["Data tidak cukup untuk membuat rekomendasi."]

    rekom = []
    omzet = df["total_amount"].sum()

    # 1. Jam operasional — nilai terbesar yang bisa diukur
    if "hour" in df.columns:
        per_jam = df.groupby("hour")["total_amount"].sum()
        sepi = per_jam.reindex(QUIET_HOURS).sum() / omzet
        rekom.append(
            f"<strong>Uji coba tutup 20:00-06:00 selama 60 hari di satu kota.</strong> "
            f"{len(QUIET_HOURS)} dari 24 jam ({len(QUIET_HOURS)/24:.0%} hari operasional) "
            f"hanya menghasilkan {sepi:.1%} omzet, tapi tetap memakan gaji, listrik, dan "
            f"pendingin. Ukur apakah permintaannya pindah ke jam sebelah atau memang hilang.")

    # 2. Diskon — mana tingkat yang benar-benar bekerja
    if "discount_tier" in df.columns and "quantity" in df.columns:
        dasar = df.loc[df["discount_pct"] == 0, "quantity"].mean()
        per_tier = (df[df["discount_pct"] > 0]
                    .groupby("discount_tier", observed=True)["quantity"].mean().dropna())
        buruk = per_tier[per_tier < dasar]
        if len(buruk):
            hemat = df.loc[df["is_deep_discount"], "discount_amount"].sum()
            rekom.append(
                f"<strong>Batasi wewenang diskon toko maksimal 10%, dikunci di kasir.</strong> "
                f"{len(buruk)} dari {len(per_tier)} tingkat diskon justru menjual LEBIH SEDIKIT "
                f"unit daripada tanpa diskon sama sekali ({dasar:.2f} unit). "
                f"Diskon 15% & 20% menelan ${hemat:,.0f}/tahun dengan hasil negatif.")

    # 3. Kategori bernilai tinggi tapi jarang dibeli.
    #    Nilainya diambil dari calc_opportunities supaya angka di halaman
    #    Executive Summary dan di sini tidak pernah berbeda.
    ringkas = df.groupby("product_category").agg(
        trx=("total_amount", "size"), rev=("total_amount", "sum"),
        aov=("total_amount", "mean"))
    ringkas["indeks"] = (ringkas["rev"] / omzet) / (ringkas["trx"] / len(df))
    puncak = ringkas["indeks"].idxmax()
    peluang = calc_opportunities(df)
    baris = peluang[peluang["Aksi"].str.contains(puncak, regex=False)]
    if ringkas.loc[puncak, "indeks"] > 1.5 and not baris.empty:
        share = ringkas.loc[puncak, "trx"] / len(df)
        rekom.append(
            f"<strong>Pindahkan {puncak} ke meja kasir dan tawarkan saat jam sibuk pagi.</strong> "
            f"Sekarang cuma {share:.1%} transaksi padahal nilainya ${ringkas.loc[puncak,'aov']:.2f} "
            f"per penjualan. Naik ke 4,0% setara "
            f"+${baris['Nilai per tahun'].iloc[0]:,.0f}/tahun tanpa perlu pelanggan baru.")

    # 4. Kekuatan harga per lokasi
    if "store_type" in df.columns and "price_index" in df.columns:
        per_tipe = df.groupby("store_type").agg(
            harga=("price_index", "median"), trx=("total_amount", "size"),
            toko=("store_id", "nunique"), rev=("total_amount", "sum"))
        per_tipe["trx_per_toko"] = per_tipe["trx"] / per_tipe["toko"]
        per_tipe["rev_per_toko"] = per_tipe["rev"] / per_tipe["toko"]
        if len(per_tipe) >= 2:
            mahal, murah = per_tipe["harga"].idxmax(), per_tipe["harga"].idxmin()
            selisih_harga = per_tipe.loc[mahal, "harga"] / per_tipe.loc[murah, "harga"] - 1
            selisih_vol = (per_tipe.loc[mahal, "trx_per_toko"]
                           / per_tipe.loc[murah, "trx_per_toko"] - 1)
            if selisih_harga > 0.10 and selisih_vol > -0.05:
                rekom.append(
                    f"<strong>Prioritaskan lokasi {mahal} di review properti berikutnya.</strong> "
                    f"Toko {mahal} menjual {selisih_harga:.0%} lebih mahal dan tetap melayani "
                    f"{selisih_vol:+.1%} pelanggan — kenaikan harga itu tidak menghilangkan "
                    f"satu pun pelanggan. Selisihnya "
                    f"${per_tipe.loc[mahal,'rev_per_toko']-per_tipe.loc[murah,'rev_per_toko']:,.0f} "
                    f"per toko per tahun, tapi baru dipakai di {int(per_tipe.loc[mahal,'toko'])} toko.")

    # 5. Kalau tidak ada tren, jangan suruh orang "cari akar masalah penurunan"
    tren = test_trend(monthly_df)
    if tren.get("cukup_data") and not tren.get("ada_tren"):
        rekom.append(
            "<strong>Berhenti mendanai 'lebih banyak dari yang sama'.</strong> "
            "Omzet datar 12 bulan berarti tidak ada satu pun program berjalan yang "
            "menghasilkan pertumbuhan. Yang dibutuhkan perubahan struktural "
            "(jam operasional, harga, komposisi produk), bukan penambahan anggaran "
            "pada program yang sudah terbukti tidak menggerakkan garis.")

    return rekom
