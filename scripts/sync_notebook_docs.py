"""Sinkronkan dokumentasi dashboard di dalam notebook dengan kondisi nyata.

Notebook masih mendeskripsikan dashboard versi lama: 6 halaman dan 3 modul
utils. Sekarang ada 8 halaman dan 7 modul. Script ini membaca struktur folder
yang SEBENARNYA lalu menulis ulang dua sel dokumentasi itu, sehingga tidak
perlu diperbarui manual setiap kali ada halaman baru.

Pakai:  python scripts/sync_notebook_docs.py
"""

import warnings
from pathlib import Path

import nbformat as nbf

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "coffee_shop_complete_colab.ipynb"

# Deskripsi tiap halaman — dipetakan dari nama file yang ada di pages/
DESKRIPSI = {
    "1_Executive_Summary": ("Direksi", "Kondisi bisnis, uji tren, peluang terukur",
                            "Line chart, donut, hourly bar, ranked bar"),
    "2_Sales": ("Sales Director", "Tren omzet, pola mingguan, kontributor",
                "Line chart, ranked bar, heatmap"),
    "3_Product": ("Category Manager", "Terlaris, laba, jebakan produk musiman",
                  "Ranked bar, kurva Pareto, tabel keputusan"),
    "4_Customer": ("Marketing", "Batas pengukuran pelanggan, uji program loyalty",
                   "Bar log-scale, grouped bar, ranked bar"),
    "5_Region_Store": ("Regional Manager", "Normalisasi per toko, harga vs volume",
                       "Ranked bar, dual axis, heatmap"),
    "6_Time_Performance": ("Operasional", "Kurva harian, normalisasi per jam, musiman",
                           "Hourly bar, heatmap, dual axis"),
    "7_Profit": ("CFO", "Estimasi HPP, dampak diskon, laba per jam",
                 "Waterfall, threshold bar, hourly bar"),
    "8_Recommendations": ("Semua", "12 rekomendasi, alur presentasi, Q&A",
                          "Tabel, ranked bar"),
}


def bangun_arsitektur():
    pages = sorted(p.stem for p in (ROOT / "pages").glob("*.py")
                   if not p.stem.startswith("__"))
    utils = sorted(p.name for p in (ROOT / "utils").glob("*.py")
                   if not p.name.startswith("__"))
    scripts = sorted(p.name for p in (ROOT / "scripts").glob("*.py"))

    ket_utils = {
        "business_logic.py": "Asumsi HPP + seluruh fitur turunan (satu sumber kebenaran)",
        "metrics.py": "KPI, uji tren, temuan, rekomendasi, sizing peluang",
        "charts.py": "Perpustakaan grafik (satu grafik = satu pesan)",
        "styling.py": "CSS + komponen langkah / \"Apa artinya\" / caveat",
        "data_loader.py": "Load data + pemulihan urutan kategori",
        "filters.py": "Filter sidebar",
        "formatting.py": "Format angka, mata uang, tanggal",
    }
    ket_scripts = {
        "build_processed.py": "raw -> clean -> featured (dengan log & verifikasi)",
        "patch_notebook.py": "Menyisipkan bagian Profit ke notebook ini",
        "sync_notebook_docs.py": "Menyinkronkan sel dokumentasi ini",
    }

    baris_pages = "\n".join(
        f"│   ├── {p}.py{' ' * max(1, 32 - len(p) - 3)}# {DESKRIPSI.get(p, ('', '', ''))[1]}"
        for p in pages)
    baris_utils = "\n".join(
        f"│   ├── {u}{' ' * max(1, 32 - len(u))}# {ket_utils.get(u, '')}"
        for u in utils)
    baris_scripts = "\n".join(
        f"    ├── {s}{' ' * max(1, 32 - len(s))}# {ket_scripts.get(s, '')}"
        for s in scripts)

    return f"""---

### Arsitektur Dashboard

> Sel ini dibangkitkan otomatis oleh `scripts/sync_notebook_docs.py` dari isi
> folder yang sebenarnya, supaya tidak pernah lagi tertinggal dari kode.

```
coffee-shop-dashboard/
│
├── app.py                          # Halaman utama — peta isi dashboard
├── requirements.txt
├── .streamlit/config.toml          # Tema dikunci LIGHT (lihat catatan di bawah)
│
├── data/coffee_shop_sales.csv      # Data mentah
├── processed/
│   ├── coffee_shop_sales_clean.csv       # Setelah cleaning
│   ├── coffee_shop_sales_featured.csv    # + 35 fitur turunan  <- dibaca dashboard
│   ├── cleaning_log.csv                  # Dokumentasi tiap perubahan
│   └── eda/                              # Tabel agregasi hasil EDA
│
├── pages/                          # {len(pages)} halaman
{baris_pages}
│
├── utils/                          # {len(utils)} modul
{baris_utils}
│
└── scripts/
{baris_scripts}
```

**Catatan tema.** `.streamlit/config.toml` mengunci `base = "light"`. Tanpa itu,
Streamlit mengikuti setelan dark mode OS pengguna, sementara seluruh CSS
dashboard memakai palet terang — akibatnya teks bawaan Streamlit menjadi putih
di atas kartu putih (kontras 1,02:1) dan label filter di sidebar hilang total."""


def bangun_daftar_halaman():
    pages = sorted(p.stem for p in (ROOT / "pages").glob("*.py")
                   if not p.stem.startswith("__"))
    baris = "\n".join(
        f"| {p.split('_')[0]} | **{p.split('_', 1)[1].replace('_', ' ')}** | "
        f"{DESKRIPSI.get(p, ('-', '-', '-'))[0]} | "
        f"{DESKRIPSI.get(p, ('-', '-', '-'))[1]} | "
        f"{DESKRIPSI.get(p, ('-', '-', '-'))[2]} |"
        for p in pages)

    return f"""---

### Daftar Halaman

| # | Halaman | Untuk | Fokus Analisis | Visualisasi Utama |
|---|---------|-------|----------------|-------------------|
{baris}

Setiap halaman disusun sebagai **langkah bernomor**, dan setiap grafik diakhiri
kotak **"Apa artinya"**. Aturannya: grafik tanpa kesimpulan tertulis tidak boleh
masuk dashboard, karena memaksa pembaca menebak sendiri tindakan apa yang harus
diambil.

Halaman **7 (Profit)** dan **8 (Recommendations)** menutup dua syarat yang
sebelumnya belum terpenuhi: Profit Dashboard dan minimal 10 rekomendasi berbasis
data."""


def main():
    nb = nbf.read(NB, as_version=4)
    diubah = 0

    for c in nb.cells:
        if c.cell_type != "markdown":
            continue
        if "### Arsitektur Dashboard" in c.source:
            c.source = bangun_arsitektur()
            diubah += 1
            print("  Sel 'Arsitektur Dashboard' diperbarui")
        elif "### Daftar Halaman" in c.source:
            c.source = bangun_daftar_halaman()
            diubah += 1
            print("  Sel 'Daftar Halaman' diperbarui")

    if diubah:
        nbf.write(nb, NB)
        print(f"\n{diubah} sel disinkronkan. Tersimpan: {NB.name}")
    else:
        print("Tidak ada sel dokumentasi yang cocok — mungkin sudah diubah manual.")


if __name__ == "__main__":
    main()
