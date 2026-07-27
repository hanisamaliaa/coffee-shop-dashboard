# Insight Report — Coffee Shop Sales

**Capstone KADA Batch 4** · 20,000 transaksi · 45 toko ·
9 kota · 4 negara · 365 hari di 2023

Sumber: `processed/coffee_shop_sales_featured.csv`
Dokumen ini **dibangkitkan otomatis** oleh `scripts/export_reports.py` — setiap
angka dihitung dari dataset, tidak ada yang diketik manual.

---

## Cerita dalam satu kalimat

> **Ini bisnis minuman pagi yang membayar untuk beroperasi 24 jam seperti toko
> serba ada.**

45 toko menghasilkan $137,009 tahun lalu. Tidak ada yang rusak —
tidak ada toko yang gagal, tidak ada produk yang merugi, datanya bersih.
Dan tidak ada yang tumbuh: Desember ditutup di $12,165 melawan
Januari $12,223.

Sepuluh temuan berikut masing-masing menjawab lima pertanyaan, karena temuan
yang berhenti di *"omzet menumpuk di pagi hari"* belum selesai bekerja:

> **Apa yang kita lihat → buktinya → artinya apa → nilainya berapa → harus apa**

---

## 1. Kita membayar 24 jam dan menghasilkan di lima jam

**Apa yang kita lihat.** 42% hari operasional hanya
menghasilkan di bawah 10% omzet.

**Buktinya.** Pukul 06:00–10:00 adalah lima jam dan **49% omzet**.
Pukul 20:00–06:00 adalah sepuluh jam dan **9,7%**. Per jam kerja,
blok pagi mengalahkan blok tersepi **10 banding 1**.
Diukur dari laba pun sama: 10 jam tersepi hanya menghasilkan
9,7% laba kotor.

**Artinya apa.** Jam-jam itu tetap memakan gaji, listrik, pendingin, dan
keamanan. Ini **masalah jam operasional, bukan masalah penjualan**.

**Nilainya berapa.** 42% jam operasional, melawan
9,7% omzet yang berisiko.

**Harus apa.** Uji coba tutup 20:00–06:00 di satu kota selama 60 hari, lalu ukur
apakah permintaannya pindah ke jam sebelah atau memang hilang.

---

## 2. Program loyalty adalah potongan harga tanpa syarat

**Apa yang kita lihat.** Anggota mendapat diskon **5,7× lebih
sering** dan tidak memberi apa pun sebagai gantinya.

**Buktinya.** Tiga klaim, tiga kegagalan:

| Klaim program | Anggota | Non-anggota | Hasil |
|:---|---:|---:|:---|
| Datang lebih sering | 3,01% | 3,06% | Tidak ada beda |
| Belanja lebih besar | $6.81 | $7.00 | Anggota **lebih kecil** |
| Lebih murah dilayani | 28,3% kena diskon | 5,0% kena diskon | **5,7× biayanya** |

Anggota adalah 29% transaksi tapi menyerap
**68% seluruh biaya diskon**.

**Artinya apa.** Orang mendaftar untuk mendapat diskon. Perilakunya tidak pernah
berubah.

**Nilainya berapa.** $1,254 per tahun tanpa hasil terukur.

**Harus apa.** Jalankan **uji holdout** — hentikan diskon anggota di sepertiga
toko selama satu kuartal, lalu ukur. Setelah itu ubah menjadi hadiah yang
**diperoleh** (beli 9 gratis 1), supaya biayanya mengikuti perilaku, bukan
mendahuluinya.

---

## 3. Hanya satu dari empat tingkat diskon yang benar-benar bekerja

**Apa yang kita lihat.** 3 dari 4 tingkat diskon
menjual keranjang yang **lebih kecil** daripada tidak memberi diskon sama sekali.

**Buktinya.** Unit per transaksi, dengan pembanding tanpa diskon
**1.71 unit**:

| Tingkat | Unit per transaksi | vs tanpa diskon |
|:---|---:|:---|
| Kecil (5%) | 1.62 | lebih buruk |
| Standar (10%) | 1.82 | lebih baik |
| Besar (15%) | 1.57 | lebih buruk |
| Terbesar (20%) | 1.66 | lebih buruk |

**Artinya apa.** Hanya tingkat 10% yang mengubah perilaku. Yang lebih dalam
jatuh ke orang yang memang sudah mau membeli — itu margin yang diserahkan,
bukan bujukan.

**Nilainya berapa.** $615 per tahun mengalir ke tingkat yang
tidak bekerja, dengan hasil negatif.

**Harus apa.** Batasi wewenang diskon toko maksimal 10%, **dikunci di kasir**
supaya tidak bisa ditimpa. Di atas itu perlu persetujuan.

---

## 4. Kekuatan harga sudah terbukti, tapi dipakai di 4 dari 45 toko

**Apa yang kita lihat.** Toko Airport menjual **27% lebih
mahal** dan tidak kehilangan pelanggan sama sekali.

**Buktinya.** Indeks harga 1,45× melawan
1,15×. Transaksi per toko justru
**+0,3%** lebih banyak. Hasilnya **$800 lebih
banyak per toko per tahun**. Margin 83,0% melawan
78,1% di Standalone.

**Artinya apa.** Permintaan di lokasi captive tidak sensitif terhadap harga pada
tingkat yang sudah kita uji. Kita membuktikannya di 4 toko dan
menerapkannya di nol dari 41 toko lainnya.

**Nilainya berapa.** **$800 per lokasi per tahun**.

**Harus apa.** Prioritaskan lokasi bandara dan transit di review properti
berikutnya.

---

## 5. Manchester paling murah *sekaligus* paling lemah

**Apa yang kita lihat.** Kota termurah kita juga kota paling tidak produktif.

**Buktinya.** Indeks harga **1,00** — terendah dari
9 kota. Omzet per toko $2,447; New York
menghasilkan **37% lebih banyak**.

**Artinya apa.** Sebagian masalah format, sebagian kebiasaan harga yang tidak
pernah dipertanyakan.

**Nilainya berapa.** $428 per tahun kalau digeser ke
indeks kota terdekat di negara yang sama.

**Harus apa.** Jalankan uji harga sebelum menganggap harga rendah itu wajar.

---

## 6. Merchandise paling jarang dibeli dan paling bernilai

**Apa yang kita lihat.** 2,7% transaksi,
**8,9% omzet**.

**Buktinya.** Rata-rata penjualan merchandise **$22.71** melawan
$6.85 keseluruhan — **3,3× rata-rata**.
Tote Bag adalah produk beromzet tertinggi kita di $7,021.

**Artinya apa.** Evaluasi kategori berbasis jumlah transaksi akan menghapus
produk terbaik kita.

**Nilainya berapa.** Menaikkan attach dari 2,7% ke 4,0% setara
**$5,950 per tahun**, tanpa pelanggan baru.

**Harus apa.** Pindahkan merchandise ke meja kasir dan tawarkan saat jam sibuk
pagi, ketika 49% lalu lintas kita memang sudah ada di toko.

---

## 7. Tiga ide marketing yang sebaiknya berhenti didanai

**Apa yang kita lihat.** Cuaca, hari libur, dan demografi tidak punya efek yang
bisa dipakai.

**Buktinya.** Nilai transaksi rata-rata antar kelompok usia hanya berbeda
**6%** dari tertinggi ke terendah — pelanggan 18-24 dan 65+
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
$12,165 melawan $12,223.

**Buktinya.** Regresi linier pada omzet **per hari** memberi slope
-0.02 per bulan dengan **p = 0.99** dan R² = 0.00 —
secara statistik tidak bisa dibedakan dari nol.

Lebih jauh lagi: variasi antarbulan yang **teramati** adalah
4,2%, sementara variasi yang **diharapkan** kalau omzet harian
murni acak adalah 5,2%. Yang teramati **lebih kecil** dari
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

**Apa yang kita lihat.** Butuh **27 dari 43 produk** untuk
mencapai 80% omzet.

**Buktinya.** Di ritel pada umumnya angka ini sekitar 20% dari lini. Toko
terbaik hanya **1,9×** toko terlemah.

**Artinya apa.** Tidak ada pemenang untuk digenjot dan tidak ada yang tertinggal
untuk diselamatkan. **Masalahnya struktural, bukan lokal.**

**Nilainya berapa.** Menghemat biaya program intervensi per toko yang tidak akan
menemukan apa pun.

**Harus apa.** Jangan jalankan turnaround per toko. Ubah kebijakan — jam, harga,
komposisi produk.

---

## 10. Retensi tidak bisa diukur, dan kita harus mengatakannya

**Apa yang kita lihat.** **97,0%** pelanggan muncul tepat sekali dalam
setahun penuh.

**Buktinya.** 19,250 pelanggan untuk 20,000 transaksi.
18,664 datang sekali. Pelanggan paling setia di seluruh perusahaan
datang **5 kali**.

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

**6 dari 8 produk berlaba terendah adalah produk MUSIMAN**, hanya
dijual 3 bulan dalam setahun. Contoh paling tajam:
**Large Pumpkin Spice Latte** berada di peringkat **38 dari
43** secara tahunan, tapi peringkat **1 dari
43** kalau dihitung per bulan ketersediaannya — melompat
37 posisi.

Memotong lini terbawah berdasarkan peringkat tahunan akan **menghapus seluruh
rangkaian musiman kita**, termasuk salah satu produk berkinerja terbaik per
bulan aktifnya.

---

## Yang tidak kami klaim

| Batasan | Kenapa penting |
|:---|:---|
| **Laba adalah estimasi** | Dataset tidak punya kolom biaya. Margin memakai benchmark HPP per kategori dan bersifat **kotor** — gaji, sewa, listrik tidak termasuk. Sah untuk membandingkan, tidak sah sebagai laporan laba rugi. |
| **Retensi tidak terukur** | 97,0% pelanggan sekali datang. Tidak ada CLV, churn, atau cohort yang aman dari data ini. |
| **Verdict loyalty adalah hipotesis** | Satu tahun tidak bisa melihat efek merek atau pelanggan yang akan pergi. Karena itu rekomendasinya uji coba, bukan pembatalan. |
| **Biaya jam operasional tidak ada** | Temuan terbesar di laporan ini sengaja **tidak diberi angka**. Finance punya angkanya; belum ada yang memintanya. |

---

*Coffee Shop Sales Analytics · Capstone KADA Batch 4*
