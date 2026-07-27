# ☕ Coffee Shop Sales — Capstone Data Analysis

Capstone KADA Batch 4 · Analisis penjualan 20.000 transaksi, 45 toko, 9 kota, 4 negara, sepanjang 2023.

> **Kesimpulan utama:**
> **Ini bisnis minuman pagi yang membayar untuk beroperasi 24 jam seperti toko serba ada.**
>
> Perusahaan ini dikelola dengan baik — tidak ada toko yang gagal, tidak ada produk yang
> merugi, datanya bersih. Dan omzetnya tidak tumbuh sedikit pun selama dua belas bulan.

---

## Cara menjalankan

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

Kalau folder `processed/` masih kosong atau data mentah berubah, bangun ulang dulu:

```bash
python scripts/build_processed.py
```

Setelah mengubah grafik, jalankan pemeriksa ini:

```bash
python scripts/check_charts.py
```

Ia memeriksa 54 grafik di 9 halaman dan gagal kalau ada data yang terkirim
sebagai biner ke Plotly.js. Lihat bagian *Catatan kompatibilitas grafik* di bawah.

---

## Delapan halaman dashboard

| # | Halaman | Untuk | Pertanyaan yang dijawab |
|:--|:---|:---|:---|
| 1 | Executive Summary | Direksi | Apakah bisnis sehat, dan di mana keputusan terbesarnya? |
| 2 | Sales | Sales Director | Bagaimana tren penjualan? Kapan tertinggi dan terendah? |
| 3 | Product | Category Manager | Produk mana yang dipertahankan, didorong, dievaluasi? |
| 4 | Customer | Marketing | Siapa pelanggan utama? Apakah loyalty bekerja? |
| 5 | Region & Store | Regional Manager | Wilayah mana yang terbaik dan perlu perhatian? |
| 6 | Time & Operations | Operasional | Kapan permintaan datang? Kapan waktu terbaik promosi? |
| 7 | **Profit** | CFO | Dari mana laba datang? Bagaimana dampak diskon? |
| 8 | **Recommendations** | Semua | 12 rekomendasi + alur presentasi 10 menit |

Setiap halaman disusun sebagai **langkah bernomor**, dan **setiap grafik diakhiri kotak
"Apa artinya"** — grafik tanpa kesimpulan memaksa pembaca menebak sendiri.

---

## Temuan utama

| # | Temuan | Angka |
|:--|:---|:---|
| 1 | Omzet datar 12 bulan — bukan cuma tidak tumbuh, **tidak ada pola musiman sama sekali** | slope ≈ 0, p = 0,99, R² = 0,00 |
| 2 | 42% jam operasional hanya menghasilkan 9,7% omzet | per jam kerja, pagi menang 10 : 1 |
| 3 | Program loyalty gagal di ketiga klaimnya sendiri | 5,7× diskon, retensi sama, keranjang lebih kecil |
| 4 | Kekuatan harga sudah terbukti tapi hampir tidak dipakai | Airport +27% harga, +0,3% pelanggan, +$800/toko |
| 5 | Merchandise paling jarang dibeli tapi paling bernilai | 2,7% transaksi, 8,9% omzet, $22,71/penjualan |
| 6 | Kerugian ada di kebijakan, bukan di produk | 0 produk & 0 transaksi merugi |

**Peluang terukur: +5,9% omzet ($8.032/tahun)** dari empat aksi yang tidak tumpang tindih.
Peluang terbesar — menutup jam 20:00–06:00 — **sengaja tidak diberi angka dolar**, karena
biaya operasional tidak ada di dataset.

---

## Bagaimana profit dihitung (dan kenapa ini estimasi)

Dataset ini **tidak punya kolom biaya**, sehingga `total_amount` hanyalah omzet.
Tanpa HPP, seluruh bagian Profit Dashboard tidak bisa diisi.

Kami membangun estimasi HPP dari benchmark industri kedai kopi:

| Kategori | HPP | Kategori | HPP |
|:---|---:|:---|---:|
| Tea | 14% | Pastry | 33% |
| Coffee | 18% | Sandwich | 38% |
| Smoothie | 30% | Merchandise | 50% |

**HPP dipatok ke harga dasar produk** (harga terendah di jaringan), bukan ke harga jual di
toko tersebut. Kalau HPP dihitung sebagai persen dari harga jual, margin setiap toko menjadi
identik dan temuan soal harga lokasi lenyap. Biji kopi harganya sama di mana pun.

**Uji sensitivitas sudah dijalankan:** walau tebakan HPP meleset ±5 poin persen, urutan
kategori paling menguntungkan tidak berubah. Yang berubah hanya besaran angkanya.

> ⚠️ Ini **laba kotor estimasi** — gaji, sewa, dan listrik tidak ada di dataset.
> Sah untuk membandingkan, tidak sah sebagai laporan laba rugi.

Semua asumsi ada di satu tempat: [`utils/business_logic.py`](utils/business_logic.py),
konstanta `COGS_RATIO`. Notebook memakai angka yang sama.

---

## Yang tidak bisa dijawab proyek ini

Ditulis di depan, bukan disembunyikan di catatan kaki.

1. **Laba adalah estimasi**, bukan angka akuntansi.
2. **Retensi pelanggan tidak bisa diukur.** 97% dari 19.250 pelanggan hanya muncul sekali
   dalam setahun. CLV, churn, dan cohort **tidak dilaporkan** — bukan karena tidak dibuat,
   tapi karena angkanya tidak akan bertahan saat ditanya. Perlu konfirmasi tim IT apakah
   `customer_id` tersimpan lintas kunjungan.
3. **Biaya operasional tidak ada di dataset**, sehingga rekomendasi terbesar sengaja tidak
   diberi angka dolar.

---

## Struktur proyek

```text
coffee-shop-dashboard/
├── app.py                            Halaman utama — peta isi dashboard
├── INSIGHT_REPORT.md                 10 temuan tertulis (dibangkitkan dari data)
├── BUSINESS_RECOMMENDATIONS.md       12 rekomendasi + alur presentasi
├── .streamlit/config.toml            Tema dikunci LIGHT — jangan dihapus
├── pages/                            8 halaman dashboard
├── utils/
│   ├── business_logic.py             ⭐ Satu sumber kebenaran: asumsi HPP + fitur turunan
│   ├── metrics.py                    KPI, uji tren, temuan, rekomendasi, sizing peluang
│   ├── charts.py                     Perpustakaan grafik (satu grafik = satu pesan)
│   ├── styling.py                    CSS + komponen (langkah, "Apa artinya", caveat)
│   ├── data_loader.py                Pemuatan data + pemulihan urutan kategori
│   ├── filters.py                    Filter sidebar
│   └── formatting.py                 Format angka
├── scripts/
│   ├── build_processed.py            raw → clean → featured (dengan log & verifikasi)
│   ├── export_reports.py             Menulis kedua file .md di atas dari data
│   ├── patch_notebook.py             Menyisipkan bagian Profit ke notebook
│   └── sync_notebook_docs.py         Menyamakan dokumentasi notebook dgn folder
├── data/                             Data mentah
├── processed/                        Hasil cleaning + feature engineering + log
└── coffee_shop_complete_colab.ipynb  Notebook analisis lengkap
```

### Alur data

```text
data/coffee_shop_sales.csv                  20.000 x 20   (mentah)
        │
        ├─ scripts/build_processed.py  →  cleaning (0 baris dihapus)
        ▼
processed/coffee_shop_sales_clean.csv       20.000 x 21
        │
        ├─ business_logic.build_features()  →  35 fitur baru
        ▼
processed/coffee_shop_sales_featured.csv    20.000 x 56   ← dibaca dashboard
processed/cleaning_log.csv                  dokumentasi setiap perubahan
```

---

## Catatan cleaning

Nol baris dihapus. Setiap perubahan tercatat di `processed/cleaning_log.csv`.

Satu keputusan yang layak disorot: **cuaca dan suhu yang kosong dipulihkan dari kota-hari
yang sama**, bukan diisi modus/median. Cuaca adalah properti kota-hari — dari 3.265 pasangan
kota-hari, tidak ada satu pun yang punya dua kondisi cuaca berbeda. Artinya 974 dari 978
nilai yang hilang **masih ada di dalam dataset**, tinggal diambil. Mengisi dengan modus akan
menaikkan porsi "Rainy" dari 42,3% ke 45,2% dan membuat analisis cuaca menjadi bias.

Yang **sengaja tidak diubah**:

- **Harga berbeda untuk produk yang sama** — setiap kombinasi kota+tipe toko punya tepat
  satu harga, jadi ini kebijakan harga per lokasi, bukan data kotor. Menyeragamkannya akan
  menghapus temuan terbaik di seluruh analisis.
- **Outlier 6,7% (IQR)** — median 4 unit per transaksi, artinya pesanan rombongan.
  Membuangnya akan menghapus 23,1% omzet perusahaan.

---

## Hosting — supaya bisa dibuka orang lain

Rekomendasi: **Streamlit Community Cloud**. Gratis, link permanen, dan laptop
tidak perlu menyala. Repo ini sudah siap deploy — `processed/*.csv` ikut
di-commit, jadi server tidak perlu memproses ulang data.

**Langkah:**

1. Commit dan push semua perubahan ke GitHub (branch `main`).
2. Buka [share.streamlit.io](https://share.streamlit.io) → *Sign in with GitHub*.
3. *New app* → pilih repo `coffee-shop-dashboard`, branch `main`,
   main file path `app.py`.
4. *Deploy*. Build pertama sekitar 2–4 menit.

Hasilnya berupa URL permanen seperti
`https://coffee-shop-dashboard.streamlit.app` yang bisa langsung dibagikan ke
dosen atau dicantumkan di slide presentasi. Setiap `git push` berikutnya akan
otomatis men-deploy ulang.

**Yang sudah disiapkan untuk deploy:**

| File | Fungsi |
|:---|:---|
| `requirements.txt` | Hanya 4 paket dashboard — build cepat |
| `requirements-notebook.txt` | Dependensi notebook, sengaja dipisah |
| `.python-version` | Pin Python 3.12 |
| `.streamlit/config.toml` | Tema terkunci — wajib ikut ter-commit |
| `processed/*.csv` | Data siap pakai, tidak perlu diproses di server |

**Alternatif lain**

| Cara | Cocok untuk | Catatan |
|:---|:---|:---|
| **Streamlit Cloud** | Presentasi & penilaian | Gratis, link permanen, laptop boleh mati |
| **ngrok** | Demo cepat saat latihan | URL berubah tiap restart, laptop harus menyala dan terhubung internet |
| **Hugging Face Spaces** | Alternatif kalau Streamlit Cloud bermasalah | Gratis, perlu menambah `Dockerfile` atau `app_file` di README Space |

> **Kenapa bukan ngrok untuk presentasi?** URL tunnel gratis berubah setiap kali
> proses di-restart, dan link mati begitu laptop ditutup. Untuk demo langsung
> saat latihan ngrok memang praktis, tapi untuk link yang dikumpulkan ke dosen
> risikonya terlalu besar.

---

## Catatan kompatibilitas grafik

Ada satu jebakan yang perlu diketahui siapa pun yang mengubah `utils/charts.py`.

**plotly (Python) ≥ 6.0** menyerialisasi array numpy dan Series pandas menjadi
`{"dtype": "f8", "bdata": "<base64>"}`. **Plotly.js versi lama** — termasuk yang
dibundel Streamlit 1.31 — belum mengenal format itu.

Yang berbahaya: **tidak ada pesan error sama sekali**. Grafiknya tetap tampil,
tapi Plotly.js diam-diam menggambar **indeks (0, 1, 2, …)** sebagai ganti
nilainya. Gejalanya: garis omzet rata di nol, garis persentase naik lurus 0→11,
heatmap kosong.

Karena versi Streamlit di tiap mesin bisa berbeda, kode ini **tidak
mengandalkan upgrade**. Semua data grafik dikonversi ke list Python biasa lewat
`_v()` dan `_v2()` di `utils/charts.py`.

> **Kalau menambah grafik baru:** bungkus setiap `x`, `y`, dan `z` dengan `_v()`
> (1 dimensi) atau `_v2()` (2 dimensi), lalu jalankan
> `python scripts/check_charts.py`.

Aturan yang sama berlaku untuk tema: **jangan hapus `.streamlit/config.toml`**.
Tanpa file itu Streamlit mengikuti dark mode OS pengguna, sementara CSS
dashboard memakai palet terang — label filter di sidebar akan hilang sama
sekali (kontras 1,02:1).

---

## Tech stack

Python · Streamlit · Pandas · NumPy · Plotly · Matplotlib (notebook)
