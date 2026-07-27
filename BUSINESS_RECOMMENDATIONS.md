# Business Recommendations — Coffee Shop Sales

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
| **R1** | Uji coba tutup 20:00–06:00 di satu kota selama 60 hari | 10 jam = 9,7% omzet; pagi menang 10:1 per jam | 42% jam operasional | Operasional | Q1 | Rendah |
| **R2** | Susun jadwal staf mengikuti kurva permintaan | 49% omzet dalam 5 jam, bentuk sama di 7 hari | Satu template jadwal | Operasional | Q1 | Rendah |
| **R3** | Batasi wewenang diskon maksimal 10%, dikunci di kasir | 3 dari 4 tingkat menjual < 1.71 unit | $529/thn | Keuangan | Q1 | Rendah |
| **R4** | Uji holdout loyalty di ⅓ toko selama 1 kuartal | Anggota dapat diskon 5,7× lebih sering, retensi sama | Menjawab $1,254 | Marketing | Q1 | Rendah |
| **R5** | Ubah loyalty jadi hadiah yang diperoleh (beli 9 gratis 1) | Anggota belanja $0.19 lebih kecil | $1,124/thn | Marketing | Q2 | Sedang |
| **R6** | Pindahkan merchandise ke kasir, tawarkan saat peak pagi | 2,7% transaksi, 8,9% omzet, $22.71/jual | $5,950/thn | Ops Ritel | Q1 | Rendah |
| **R7** | Prioritaskan lokasi Airport & transit di review properti | Harga +27%, pelanggan +0,3%, $800/toko | $800/lokasi | Properti | Q2 | Tinggi |
| **R8** | Uji kenaikan harga di Manchester | Indeks 1,00 terendah; New York unggul 37%/toko | $428/thn | Pricing | Q2 | Rendah |
| **R9** | Hentikan penargetan cuaca, hari libur, dan demografi | Selisih nilai transaksi antar kelompok usia hanya 6% | Bebaskan anggaran segmen | Marketing | Q1 | Rendah |
| **R10** | **Jangan** jalankan program turnaround per toko | Toko terbaik hanya 1,9× terlemah dari 45 toko | Hindari usaha sia-sia | Regional | Q1 | Rendah |
| **R11** | Rasionalisasi varian ukuran, bukan hapus produk lambat | Butuh 27 dari 43 produk untuk 80% omzet | Penyederhanaan lini | Kategori | Q2 | Sedang |
| **R12** | Tanya IT: apakah `customer_id` tersimpan lintas kunjungan? | 97,0% pelanggan muncul sekali; terloyal cuma 5 kali | Buka semua analisis CLV | Data / IT | Q1 | Rendah |

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
| Naikkan penetrasi Merchandise ke 4% | $5,950 | 4,34% | 262 penjualan tambahan x $22.71 — kategorinya sudah ada |
| Restrukturisasi program loyalty | $1,124 | 0,82% | Diskon anggota tanpa perubahan perilaku yang terukur |
| Batasi diskon maksimal 10% | $529 | 0,39% | Tingkat 15% & 20% menjual lebih sedikit unit daripada tanpa diskon sama sekali |
| Uji harga di Manchester | $428 | 0,31% | Kota termurah di jaringan (indeks 1.00); London sudah berjalan di 1.03 di negara yang sama |
| **Total** | **$8,032** | **5,9%** | |

> ### Peluang terbesar tidak ada di tabel ini
>
> Menutup 20:00–06:00 menyentuh **42% jam operasional**
> melawan **9,7% omzet** dan 9,7% laba kotor.
> Nilainya lebih besar dari keempat aksi di atas digabung.
>
> Kami **sengaja tidak memberinya angka dolar**, karena biaya gaji, listrik, dan
> pendingin **tidak ada di dataset**. Memberikan angka di situ berarti mengarang.
> Satu angka dari tim Finance akan menyelesaikannya.

---

## Rincian tiap rekomendasi

### R1 · Uji coba tutup 20:00–06:00 di satu kota selama 60 hari
- **Bukti:** 10 jam dari 24 menghasilkan 9,7% omzet dan 9,7% laba kotor. Per jam kerja, pagi menang 10 banding 1. Pola ini identik di ketujuh hari, jadi bukan gejala akhir pekan.
- **Lakukan:** pilih satu kota dengan minimal tiga toko. Tutup semalam. Jangan ubah variabel lain.
- **Ukuran berhasil:** omzet bertahan ≥ 95% setelah 60 hari. Kalau pelanggan hanya bergeser ke 06:00–10:00, jam itu memang murni biaya.
- **Risiko:** lokasi transit mungkin punya nilai strategis semalam. Kecualikan toko bandara dari uji coba.

### R2 · Susun jadwal staf mengikuti kurva permintaan
- **Bukti:** 49% omzet dalam lima jam, bentuk kurva sama setiap hari, akhir pekan hanya versi lebih tinggi (37% omzet dari 29% hari).
- **Lakukan:** satu template jadwal untuk tujuh hari. Sabtu–Minggu tambah orang, bukan tambah jam buka.
- **Ukuran berhasil:** antrean pukul 08:00 turun; jam kerja per dolar omzet turun.

### R3 · Batasi wewenang diskon maksimal 10%
- **Bukti:** tanpa diskon pelanggan membeli 1.71 unit. 3 dari 4 tingkat diskon berada di bawah angka itu.
- **Lakukan:** kunci batasnya di sistem kasir, bukan di dokumen kebijakan.
- **Ukuran berhasil:** nol transaksi di atas 10% tanpa persetujuan; unit per transaksi bertahan di 1.71.
- **Nilai:** $529/tahun.

### R4 · Uji holdout loyalty *(uji coba, bukan keputusan)*
- **Bukti:** anggota dapat diskon 5,7× lebih sering, tidak datang lebih sering (3,01% vs 3,06%), dan belanja lebih kecil sebelum diskon.
- **Lakukan:** hentikan diskon anggota di sepertiga toko yang dipilih acak selama satu kuartal.
- **Ukuran berhasil:** omzet dan frekuensi kunjungan uji vs kontrol. Ini menjawab pertanyaan senilai $1,254 dengan biaya satu kuartal data.
- **Kenapa uji coba:** satu tahun tidak bisa melihat efek merek atau pelanggan yang akan pergi. Membatalkan program hanya dengan bukti ini adalah tindakan berlebihan.

### R5 · Ubah loyalty jadi hadiah yang diperoleh
- **Bukti:** program sekarang membayar sebelum perilakunya terjadi. Anggota belanja $0.19 lebih kecil per keranjang.
- **Lakukan:** beli 9 gratis 1 — hadiah datang setelah kunjungan kesembilan, jadi biaya mengikuti perilaku.
- **Ukuran berhasil:** biaya per anggota turun; tingkat kunjungan kedua naik di atas 3,0%.
- **Urutan:** jalankan R4 dulu. R5 adalah tindak lanjut dari jawabannya.

### R6 · Merchandise ke meja kasir
- **Bukti:** 2,7% transaksi, 8,9% omzet, $22.71 per penjualan — 3,3× rata-rata. Tote Bag adalah produk beromzet tertinggi kita.
- **Lakukan:** penempatan di kasir plus penawaran saat peak 06:00–10:00, ketika 49% lalu lintas memang sudah ada.
- **Ukuran berhasil:** attach merchandise mencapai 4,0% transaksi.
- **Nilai:** $5,950/tahun — peluang terukur terbesar di laporan ini.

### R7 · Prioritaskan lokasi Airport dan transit
- **Bukti:** Airport menjual 27% lebih mahal dan melayani +0,3% pelanggan. $3,726 per toko melawan $2,926.
- **Lakukan:** condongkan review properti berikutnya ke lokasi dengan audiens captive.
- **Ukuran berhasil:** dua pembukaan berikutnya format transit dan mencapai indeks harga 1,45×.
- **Peringatan:** hanya 4 toko yang mendukung temuan ini. Sinyalnya kuat tapi sampelnya kecil — perlakukan pembukaan berikutnya sebagai konfirmasi. Perlu diingat juga biaya sewa bandara biasanya jauh lebih tinggi, dan itu tidak ada di dataset.

### R8 · Uji harga di Manchester *(uji coba, bukan keputusan)*
- **Bukti:** indeks harga 1,00, terendah dari 9 kota, dan omzet per toko paling rendah ($2,447 vs $3,358).
- **Lakukan:** naikkan sebagian produk 3% menuju indeks kota terdekat di negara yang sama, tahan satu kuartal.
- **Ukuran berhasil:** volume bertahan dalam 2%.
- **Nilai:** $428/tahun kalau bertahan.

### R9 · Hentikan penargetan cuaca, hari libur, dan demografi
- **Bukti:** nilai transaksi rata-rata antar kelompok usia hanya berbeda 6% dari tertinggi ke terendah.
- **Lakukan:** alokasikan ulang ke kampanye berbasis waktu dan lokasi.
- **Ukuran berhasil:** anggaran benar-benar berpindah, bukan diam-diam dipertahankan.

### R10 · Jangan jalankan program turnaround per toko
- **Bukti:** toko terbaik hanya 1,9× toko terlemah. Untuk jaringan 45 toko, itu luar biasa merata.
- **Lakukan:** arahkan usaha intervensi ke kebijakan — jam, harga, komposisi — bukan ke masing-masing lokasi.
- **Ukuran berhasil:** tidak ada rencana perbaikan per toko yang dibuka tahun ini.
- **Catatan:** ini rekomendasi untuk **tidak** membelanjakan. Ia masuk daftar justru karena naluri pertama biasanya adalah memeringkat toko lalu menindak yang terbawah.

### R11 · Rasionalisasi ukuran, jangan hapus produk lambat
- **Bukti:** 27 dari 43 produk dibutuhkan untuk 80% omzet — tidak ada ekor panjang untuk dipotong. Yang lebih penting: **6 dari 8 produk berlaba terendah adalah produk musiman**. Large Pumpkin Spice Latte berperingkat 38 dari 43 secara tahunan, tapi **1 dari 43 per bulan ketersediaannya**.
- **Lakukan:** tinjau varian ukuran dari produk yang sama. Nilai produk musiman berdasarkan laba per bulan aktif.
- **Ukuran berhasil:** jumlah SKU turun dengan omzet bertahan; tidak ada lini musiman yang dipotong berdasarkan peringkat tahunan.
- **Kenapa ini penting:** rekomendasi yang paling kelihatan jelas di sini — hapus 8 produk terbawah — adalah **salah**, dan kami hanya menangkapnya setelah menormalisasi berapa lama tiap produk tersedia.

### R12 · Tanyakan ke IT soal `customer_id`
- **Bukti:** 97,0% pelanggan muncul sekali; yang terloyal cuma 5 kali.
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
$1,254 layak ditunggu satu kuartal untuk dijawab dengan bukti.

**"Produk mana yang sebaiknya dihentikan?"**
Tidak ada, berdasarkan bukti ini. Butuh 27 dari 43 produk
untuk mencapai 80% omzet, jadi tidak ada ekor panjang untuk dipotong. Dan
6 dari 8 produk yang terlihat paling lambat sebenarnya **musiman** —
diperingkat per bulan ketersediaannya, posisinya jauh berbeda.
Rasionalisasi ukuran, bukan penghapusan produk.

---

## Alur presentasi 10 menit

> **Kalimat yang mengikat seluruh presentasi:**
> Ini bisnis minuman pagi yang membayar untuk beroperasi 24 jam seperti toko
> serba ada.

| # | Bagian | Durasi | Yang disampaikan |
|:--|:---|:--|:---|
| 1 | **Situation** | 1,5 mnt | 45 toko di 9 kota, 20,000 transaksi, $137,009, satu tahun penuh. Bisnis ini dikelola dengan baik: tidak ada toko gagal, data bersih, nol duplikat. |
| 2 | **Problem** | 1,5 mnt | Dua belas bulan, nol pertumbuhan (p = 0.99). Loyalty berjalan setahun. Diskon dibagikan setahun. Keduanya tidak menggerakkan garis. |
| 3 | **Evidence** | 3 mnt | 49% omzet dalam 5 jam. Loyalty gagal di ketiga klaimnya. Airport +27% lebih mahal tanpa kehilangan pelanggan. Merchandise 2,7% transaksi tapi 8,9% omzet. |
| 4 | **Insight** | 1,5 mnt | Kita membayar operasi 24 jam untuk kurva permintaan 5 jam, mendanai diskon yang tidak mengubah apa pun, dan hampir tidak memakai dua tuas yang terbukti bekerja. |
| 5 | **Recommendation** | 2 mnt | Dua belas aksi, sembilan bisa mulai kuartal ini, lima tanpa anggaran. Tiga di antaranya uji coba. |
| 6 | **Business Impact** | 0,5 mnt | +5,9% omzet ($8,032/tahun) dari empat aksi terukur, ditambah satu keputusan jam operasional yang nilainya lebih besar dari keempatnya digabung. |

**Kalimat penutup:**

> Setiap aksi di daftar ini layak dikerjakan. Tidak satu pun senilai menjawab
> satu pertanyaan: **berapa biaya membuka pintu dari pukul 20:00 sampai 06:00?**
> Finance punya angka itu. Belum ada yang memintanya.

---

*Coffee Shop Sales Analytics · Capstone KADA Batch 4*
