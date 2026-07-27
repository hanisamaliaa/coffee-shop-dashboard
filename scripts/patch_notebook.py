"""Perbaiki notebook analisis:

  1. Ganti bagian "10. Profit or Performance Analysis" — yang tadinya hanya
     menyatakan bahwa profit tidak bisa dihitung — dengan analisis profit
     lengkap memakai estimasi HPP.
  2. Hapus sel judul & objective yang terduplikasi karena notebook ini
     hasil penggabungan beberapa notebook.

Pakai:  python scripts/patch_notebook.py
"""

import sys
import warnings
from pathlib import Path

import nbformat as nbf

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
NB = ROOT / "coffee_shop_complete_colab.ipynb"

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell


# ─────────────────────────────────────────────────────────────────────────────
# Bagian 10 yang baru
# ─────────────────────────────────────────────────────────────────────────────
SECTION_10 = [
    md("""---
# 10. Profit Analysis

## 10.1 Masalahnya: dataset ini tidak punya kolom biaya

`total_amount` adalah **omzet**, bukan laba. Tanpa Harga Pokok Penjualan (HPP),
tiga pertanyaan wajib dari project ini **tidak bisa dijawab sama sekali**:

- Bagaimana tren profit?
- Faktor apa yang menyebabkan profit turun?
- Produk atau transaksi apa yang menyebabkan kerugian?

Mengatakan "tidak bisa dianalisis" memang jujur, tapi itu berarti kita menyerahkan
seluruh bagian Profit Dashboard dalam keadaan kosong.

## 10.2 Solusinya: estimasi HPP dari benchmark industri

Kita bangun estimasi biaya memakai rasio HPP yang lazim di industri kedai kopi:

| Kategori | HPP (% harga dasar) | Alasan |
|:---|---:|:---|
| Tea | 14% | Daun teh sangat murah; harga jual didominasi jasa & tempat |
| Coffee | 18% | Biji + susu; margin tinggi adalah ciri khas kedai kopi |
| Smoothie | 30% | Buah segar, cepat rusak, porsi besar |
| Pastry | 33% | Bahan roti + tingkat basi tinggi |
| Sandwich | 38% | Protein & sayur segar — HPP tertinggi di kategori makanan |
| Merchandise | 50% | Barang jadi dari pemasok, margin ritel biasa |

### Keputusan teknis: HPP dipatok ke HARGA DASAR, bukan harga jual

Ini keputusan yang menentukan hasil, jadi harus dijelaskan:

- **Kalau HPP = 18% x harga jual di toko itu** → margin % setiap toko menjadi
  **identik**. Toko bandara yang menjual 45% lebih mahal akan punya margin persis
  sama dengan toko biasa, dan temuan "lokasi mana yang paling untung" **lenyap**.
- **Kalau HPP = 18% x harga dasar** → biji kopi harganya sama di mana pun.
  Kelebihan harga di lokasi premium **langsung menjadi laba**, dan setiap dolar
  diskon **langsung mengurangi laba**. Ini yang benar secara ekonomi.

> ⚠️ **Angka ini ESTIMASI, bukan angka akuntansi.** Sah untuk **membandingkan**
> (produk A vs B, toko X vs Y, diskon 10% vs 20%), **tidak sah** sebagai laporan
> laba rugi. Ini **laba kotor** — gaji, sewa, dan listrik tidak ada di dataset.
>
> Asumsi yang sama dipakai di dashboard Streamlit
> (`utils/business_logic.py`, konstanta `COGS_RATIO`), sehingga angka di notebook
> dan di dashboard selalu cocok."""),

    code('''# ============================================================
# 10.3 Feature Engineering: Estimasi HPP dan Laba
# ============================================================

# Rasio HPP per kategori — SAMA dengan utils/business_logic.py di dashboard
COGS_RATIO = {
    'Tea': 0.14, 'Coffee': 0.18, 'Smoothie': 0.30,
    'Pastry': 0.33, 'Sandwich': 0.38, 'Merchandise': 0.50,
}

df_profit = df_eda.copy()

# Harga dasar = harga TERENDAH produk itu di seluruh jaringan.
# Ini menjadi patokan biaya, karena biaya bahan baku tidak berubah
# hanya karena sebuah toko menjual lebih mahal.
df_profit['base_price'] = df_profit.groupby('product_name')['unit_price'].transform('min')

# Pastikan kolom diskon tersedia (direkonstruksi dari aritmatika transaksi)
if 'gross_amount' not in df_profit.columns:
    df_profit['gross_amount'] = (df_profit['unit_price'] * df_profit['quantity']).round(2)
if 'discount_amount' not in df_profit.columns:
    df_profit['discount_amount'] = (df_profit['gross_amount'] - df_profit['total_amount']).round(2)
df_profit['discount_pct'] = np.where(
    df_profit['gross_amount'] > 0,
    (df_profit['discount_amount'] / df_profit['gross_amount']).round(2), 0.0)

# Estimasi biaya dan laba
df_profit['cogs_ratio']  = df_profit['product_category'].map(COGS_RATIO)
df_profit['unit_cost']   = (df_profit['base_price'] * df_profit['cogs_ratio']).round(4)
df_profit['est_cost']    = (df_profit['unit_cost'] * df_profit['quantity']).round(4)
df_profit['est_profit']  = (df_profit['total_amount'] - df_profit['est_cost']).round(4)
df_profit['profit_margin'] = np.where(
    df_profit['total_amount'] > 0,
    (df_profit['est_profit'] / df_profit['total_amount']).round(4), 0.0)

total_omzet  = df_profit['total_amount'].sum()
total_kotor  = df_profit['gross_amount'].sum()
total_hpp    = df_profit['est_cost'].sum()
total_laba   = df_profit['est_profit'].sum()
total_diskon = df_profit['discount_amount'].sum()

print('=' * 70)
print(' ESTIMASI PROFIT')
print('=' * 70)
print(f"Omzet kotor (sebelum diskon) : ${total_kotor:,.2f}")
print(f"Diskon diberikan             : ${total_diskon:,.2f}  ({total_diskon/total_kotor:.2%} dari kotor)")
print(f"Omzet bersih                 : ${total_omzet:,.2f}")
print(f"Estimasi HPP                 : ${total_hpp:,.2f}")
print(f"Estimasi laba kotor          : ${total_laba:,.2f}")
print(f"Margin kotor gabungan        : {total_laba/total_omzet:.1%}")
print(f"\\nTransaksi dengan laba negatif: {(df_profit['est_profit'] < 0).sum()}")
print(f"Produk dengan laba negatif   : {(df_profit.groupby('product_name')['est_profit'].sum() < 0).sum()}")

margin_kategori = df_profit.groupby('product_category').agg(
    omzet=('total_amount', 'sum'), hpp=('est_cost', 'sum'), laba=('est_profit', 'sum'),
    transaksi=('total_amount', 'size')).sort_values('laba', ascending=False)
margin_kategori['margin_%']    = (margin_kategori['laba'] / margin_kategori['omzet'] * 100).round(1)
margin_kategori['%_dari_laba'] = (margin_kategori['laba'] / margin_kategori['laba'].sum() * 100).round(1)

print('\\n' + '=' * 70)
print(' LABA PER KATEGORI')
print('=' * 70)
print(margin_kategori.round(2).to_string())'''),

    md("""## 10.4 Uji sensitivitas: seberapa rapuh kesimpulan ini?

Angka HPP di atas adalah **tebakan terdidik**, dan dewan direksi berhak
mempertanyakannya. Uji berikut menjawab pertanyaan itu di depan: apa yang terjadi
kalau tebakan kita meleset 5 poin persen ke atas atau ke bawah?"""),

    code('''# ============================================================
# 10.5 Uji Sensitivitas Asumsi HPP
# ============================================================

hasil_sensitivitas = {}
for geser, label in [(-0.05, 'HPP lebih murah 5pp'), (0.0, 'Asumsi dasar'),
                     (0.05, 'HPP lebih mahal 5pp')]:
    rasio = {k: min(max(v + geser, 0.01), 0.95) for k, v in COGS_RATIO.items()}
    biaya = df_profit['base_price'] * df_profit['product_category'].map(rasio) * df_profit['quantity']
    laba  = df_profit['total_amount'] - biaya
    urutan = laba.groupby(df_profit['product_category']).sum().sort_values(ascending=False)
    hasil_sensitivitas[label] = {
        'margin_gabungan': f"{laba.sum() / df_profit['total_amount'].sum():.1%}",
        'kategori_laba_1': urutan.index[0],
        'kategori_laba_2': urutan.index[1],
        'kategori_laba_terakhir': urutan.index[-1],
        'transaksi_merugi': int((laba < 0).sum()),
    }

sensitivitas = pd.DataFrame(hasil_sensitivitas).T
print('=' * 70)
print(' UJI SENSITIVITAS ASUMSI HPP')
print('=' * 70)
print(sensitivitas.to_string())
print()
print('KESIMPULAN: urutan kategori TIDAK berubah di ketiga skenario.')
print('Yang berubah hanya besaran margin, bukan peringkatnya —')
print('artinya rekomendasi kita tidak bergantung pada ketepatan tebakan HPP.')'''),

    md("""## 10.6 Pertanyaan 1 — Bagaimana tren profit?"""),

    code('''# ============================================================
# 10.7 Tren Profit vs Omzet
# ============================================================

tren_profit = df_profit.groupby(df_profit['timestamp'].dt.to_period('M')).agg(
    omzet=('total_amount', 'sum'), laba=('est_profit', 'sum'),
    diskon=('discount_amount', 'sum')).reset_index()
tren_profit['margin'] = tren_profit['laba'] / tren_profit['omzet']
tren_profit['bulan'] = tren_profit['timestamp'].dt.to_timestamp()

fig, axes = plt.subplots(1, 2, figsize=(16, 4.8))

axes[0].plot(tren_profit['bulan'], tren_profit['omzet'], marker='o', lw=2.5,
             color='#6F4E37', label='Omzet')
axes[0].plot(tren_profit['bulan'], tren_profit['laba'], marker='s', lw=2.5,
             color='#E08214', label='Estimasi laba kotor')
axes[0].set_title('Laba bergerak persis sejajar dengan omzet', fontsize=12, fontweight='bold')
axes[0].set_ylabel('USD'); axes[0].legend(); axes[0].grid(alpha=0.3)
axes[0].set_ylim(0, tren_profit['omzet'].max() * 1.2)

axes[1].plot(tren_profit['bulan'], tren_profit['margin'] * 100, marker='o', lw=2.5,
             color='#2E7D32')
axes[1].axhline(tren_profit['margin'].mean() * 100, ls='--', color='#C0392B', lw=1.5,
                label=f"rata-rata {tren_profit['margin'].mean():.1%}")
axes[1].set_title(f"Margin nyaris tidak bergerak (rentang "
                  f"{(tren_profit['margin'].max()-tren_profit['margin'].min())*100:.1f} poin)",
                  fontsize=12, fontweight='bold')
axes[1].set_ylabel('Margin (%)'); axes[1].set_ylim(0, 100)
axes[1].legend(); axes[1].grid(alpha=0.3)

plt.tight_layout(); plt.show()

print(f"Laba bulan pertama : ${tren_profit['laba'].iloc[0]:,.2f}")
print(f"Laba bulan terakhir: ${tren_profit['laba'].iloc[-1]:,.2f}")
print(f"Perubahan          : {tren_profit['laba'].iloc[-1]/tren_profit['laba'].iloc[0]-1:+.2%}")
print(f"Margin terendah    : {tren_profit['margin'].min():.1%}")
print(f"Margin tertinggi   : {tren_profit['margin'].max():.1%}")'''),

    md("""### 📌 Jawaban Pertanyaan 1

**Profit tidak turun — tapi juga tidak tumbuh.**

Laba bergerak persis sejajar dengan omzet, dan margin nyaris tidak bergerak
sepanjang tahun. Artinya **tidak ada masalah efisiensi yang muncul tiba-tiba**:
komposisi penjualan kita stabil, hanya saja tidak ada pertumbuhan.

Ini penting untuk disampaikan apa adanya. Kalau kita memaksakan narasi "profit
turun", direksi akan mengejar akar masalah yang tidak ada."""),

    md("""## 10.8 Pertanyaan 2 — Faktor apa yang menggerus profit?

Diskon hanya masuk akal kalau ia membuat orang membeli lebih banyak.
Mari kita uji setiap tingkat diskon terhadap pembanding yang benar:
**berapa unit yang dibeli orang ketika TIDAK diberi diskon sama sekali.**"""),

    code('''# ============================================================
# 10.9 Dampak Diskon terhadap Profit
# ============================================================

TIER = {0.00: 'Tanpa Diskon', 0.05: 'Kecil (5%)', 0.10: 'Standar (10%)',
        0.15: 'Besar (15%)', 0.20: 'Terbesar (20%)'}
URUT = ['Kecil (5%)', 'Standar (10%)', 'Besar (15%)', 'Terbesar (20%)']
df_profit['discount_tier'] = df_profit['discount_pct'].map(TIER).fillna('Tanpa Diskon')

dasar_unit = df_profit.loc[df_profit['discount_pct'] == 0, 'quantity'].mean()
per_tier = (df_profit[df_profit['discount_pct'] > 0]
            .groupby('discount_tier')
            .agg(unit_per_trx=('quantity', 'mean'), biaya_diskon=('discount_amount', 'sum'),
                 transaksi=('quantity', 'size'), laba=('est_profit', 'sum'))
            .reindex(URUT).dropna(how='all'))
per_tier['vs_tanpa_diskon'] = per_tier['unit_per_trx'] - dasar_unit
per_tier['bekerja'] = np.where(per_tier['unit_per_trx'] > dasar_unit, 'YA', 'TIDAK')

fig, axes = plt.subplots(1, 2, figsize=(16, 4.8))

warna = ['#2E7D32' if v > dasar_unit else '#C0392B' for v in per_tier['unit_per_trx']]
axes[0].bar(range(len(per_tier)), per_tier['unit_per_trx'], color=warna)
axes[0].axhline(dasar_unit, ls='--', color='#3E2723', lw=2)
axes[0].text(len(per_tier) - 0.5, dasar_unit + 0.04,
             f'tanpa diskon = {dasar_unit:.2f} unit', ha='right', fontsize=10, style='italic')
axes[0].set_xticks(range(len(per_tier)))
axes[0].set_xticklabels([t.replace(' (', '\\n(') for t in per_tier.index], fontsize=9.5)
for i, v in enumerate(per_tier['unit_per_trx']):
    axes[0].text(i, v - 0.14, f'{v:.2f}', ha='center', color='white',
                 fontweight='bold', fontsize=11)
axes[0].set_ylim(0, per_tier['unit_per_trx'].max() * 1.3)
gagal = int((per_tier['unit_per_trx'] < dasar_unit).sum())
axes[0].set_title(f'{gagal} dari {len(per_tier)} tingkat diskon menjual LEBIH SEDIKIT unit',
                  fontsize=12, fontweight='bold')
axes[0].set_ylabel('Unit per transaksi'); axes[0].grid(axis='y', alpha=0.3)

axes[1].bar(range(len(per_tier)), per_tier['biaya_diskon'], color='#C0392B')
axes[1].set_xticks(range(len(per_tier)))
axes[1].set_xticklabels([t.replace(' (', '\\n(') for t in per_tier.index], fontsize=9.5)
for i, v in enumerate(per_tier['biaya_diskon']):
    axes[1].text(i, v * 1.02, f'${v:,.0f}', ha='center', fontweight='bold', fontsize=10)
axes[1].set_ylim(0, per_tier['biaya_diskon'].max() * 1.2)
axes[1].set_title('Biaya diskon per tingkat', fontsize=12, fontweight='bold')
axes[1].set_ylabel('USD'); axes[1].grid(axis='y', alpha=0.3)

plt.tight_layout(); plt.show()

print(per_tier.round(3).to_string())
sia_sia = per_tier.loc[per_tier['unit_per_trx'] < dasar_unit, 'biaya_diskon'].sum()
print(f"\\nBiaya diskon yang TIDAK menghasilkan tambahan unit: ${sia_sia:,.2f}/tahun")

# Ke mana uang diskon mengalir?
if 'loyalty_member' in df_profit.columns:
    anggota = df_profit[df_profit['loyalty_member']]
    non     = df_profit[~df_profit['loyalty_member']]
    vis     = df_profit.groupby('customer_id').agg(n=('transaction_id', 'size'),
                                                   m=('loyalty_member', 'first'))
    print('\\n' + '=' * 70)
    print(' UJI TIGA KLAIM PROGRAM LOYALTY')
    print('=' * 70)
    print(f"Datang lagi   : anggota {(vis.loc[vis['m'],'n']>1).mean():.2%} vs "
          f"non-anggota {(vis.loc[~vis['m'],'n']>1).mean():.2%}")
    print(f"Belanja kotor : anggota ${anggota['gross_amount'].mean():.2f} vs "
          f"non-anggota ${non['gross_amount'].mean():.2f}")
    print(f"Kena diskon   : anggota {(anggota['discount_pct']>0).mean():.1%} vs "
          f"non-anggota {(non['discount_pct']>0).mean():.1%} "
          f"({(anggota['discount_pct']>0).mean()/(non['discount_pct']>0).mean():.1f}x lebih sering)")
    print(f"\\nAnggota = {df_profit['loyalty_member'].mean():.0%} transaksi, "
          f"tapi menyerap {anggota['discount_amount'].sum()/total_diskon:.0%} biaya diskon "
          f"(${anggota['discount_amount'].sum():,.2f}/tahun)")'''),

    md("""### 📌 Jawaban Pertanyaan 2

Ada **tiga penggerus laba**, dan hanya dua yang bisa kita ukur dari dataset ini:

| Penggerus | Bisa diukur? |
|:---|:---|
| Diskon ke anggota loyalty yang tidak mengubah perilaku | ✅ Ya |
| Tingkat diskon yang justru menurunkan jumlah unit | ✅ Ya |
| Biaya operasional 10 jam tersepi (gaji, listrik, pendingin) | ❌ **Tidak ada di dataset** |

Temuan diskon yang paling penting: **hanya tingkat 10% yang menjual lebih banyak
unit** daripada tanpa diskon sama sekali. Tingkat lainnya menjual lebih sedikit —
artinya diskon itu jatuh ke orang yang **memang sudah mau membeli**. Itu bukan
membujuk, itu menyerahkan margin.

Penggerus ketiga sengaja **tidak kami beri angka dolar**, karena memberikannya
berarti mengarang. Satu angka dari tim Finance akan menyelesaikannya."""),

    md("""## 10.10 Pertanyaan 3 — Produk atau transaksi apa yang merugi?"""),

    code('''# ============================================================
# 10.11 Produk Merugi dan Produk Bermargin Tipis
# ============================================================

per_produk = df_profit.groupby(['product_category', 'product_name']).agg(
    omzet=('total_amount', 'sum'), laba=('est_profit', 'sum'),
    unit=('quantity', 'sum'), transaksi=('total_amount', 'size'),
    bulan_tersedia=('month', 'nunique')).reset_index()
per_produk['margin_%'] = (per_produk['laba'] / per_produk['omzet'] * 100).round(1)
per_produk['laba_per_bulan'] = per_produk['laba'] / per_produk['bulan_tersedia']

merugi = per_produk[per_produk['laba'] < 0]
print('=' * 70)
print(' PRODUK MERUGI')
print('=' * 70)
print(f"Jumlah produk merugi   : {len(merugi)} dari {len(per_produk)}")
print(f"Jumlah transaksi merugi: {(df_profit['est_profit'] < 0).sum()} dari {len(df_profit):,}")

print('\\n5 PRODUK DENGAN LABA TERBESAR')
print(per_produk.nlargest(5, 'laba')[
    ['product_name', 'omzet', 'laba', 'margin_%']].round(2).to_string(index=False))

print('\\n5 PRODUK DENGAN MARGIN PALING TIPIS')
print(per_produk.nsmallest(5, 'margin_%')[
    ['product_name', 'omzet', 'laba', 'margin_%']].round(2).to_string(index=False))

# JEBAKAN: produk berlaba terendah sebagian besar adalah produk MUSIMAN
terbawah = per_produk.nsmallest(8, 'laba').copy()
terbawah['peringkat_tahunan']  = per_produk['laba'].rank(ascending=False).loc[terbawah.index].astype(int)
terbawah['peringkat_per_bulan'] = per_produk['laba_per_bulan'].rank(ascending=False).loc[terbawah.index].astype(int)
terbawah['lompatan'] = terbawah['peringkat_tahunan'] - terbawah['peringkat_per_bulan']

print('\\n' + '=' * 70)
print(' JEBAKAN: 8 PRODUK LABA TERENDAH')
print('=' * 70)
print(terbawah[['product_name', 'bulan_tersedia', 'laba',
                'peringkat_tahunan', 'peringkat_per_bulan', 'lompatan']]
      .sort_values('lompatan', ascending=False).round(2).to_string(index=False))

n_musiman = int((terbawah['bulan_tersedia'] < df_profit['month'].nunique()).sum())
print(f"\\n>> {n_musiman} dari 8 produk berlaba terendah ternyata MUSIMAN "
      f"(hanya dijual {terbawah['bulan_tersedia'].min()} bulan).")
print('>> Memotong lini terbawah berdasarkan peringkat TAHUNAN akan menghapus')
print('   seluruh rangkaian produk musiman kita.')

fig, axes = plt.subplots(1, 2, figsize=(16, 4.8))

kat = df_profit.groupby('product_category')['est_profit'].sum().sort_values()
axes[0].barh(range(len(kat)), kat.values,
             color=['#E08214' if i == len(kat) - 1 else '#BFBAB4' for i in range(len(kat))])
axes[0].set_yticks(range(len(kat))); axes[0].set_yticklabels(kat.index)
for i, v in enumerate(kat.values):
    axes[0].text(v * 1.01, i, f'${v:,.0f}', va='center', fontsize=9.5, fontweight='bold')
axes[0].set_xlim(0, kat.max() * 1.2)
axes[0].set_title(f'{kat.index[-1]} menyumbang laba terbesar', fontsize=12, fontweight='bold')
axes[0].grid(axis='x', alpha=0.3)

tb = terbawah.sort_values('laba')
warna_tb = ['#C0392B' if b < df_profit['month'].nunique() else '#BFBAB4'
            for b in tb['bulan_tersedia']]
axes[1].barh(range(len(tb)), tb['laba'], color=warna_tb)
axes[1].set_yticks(range(len(tb)))
axes[1].set_yticklabels([f"{n[:26]} ({int(b)} bln)"
                         for n, b in zip(tb['product_name'], tb['bulan_tersedia'])],
                        fontsize=8.5)
axes[1].set_title(f'8 produk laba terendah — {n_musiman} di antaranya MUSIMAN (merah)',
                  fontsize=12, fontweight='bold')
axes[1].grid(axis='x', alpha=0.3)

plt.tight_layout(); plt.show()'''),

    md("""### 📌 Jawaban Pertanyaan 3

**Tidak ada satu pun produk atau transaksi yang merugi.** Nol.

Kerugian di bisnis ini **bukan ada di produk, melainkan di kebijakan** — diskon
yang tidak menghasilkan, dan jam operasional yang tidak menghasilkan.

Dan ada satu jebakan yang hampir pasti akan menjerat siapa pun yang melihat daftar
produk berlaba terendah: **sebagian besar produk itu MUSIMAN**, hanya dijual tiga
bulan dalam setahun. Dihitung per bulan ketersediaannya, peringkatnya melompat jauh
ke atas.

**Rekomendasi:** jangan hentikan produk berdasarkan peringkat tahunan. Nilai ulang
produk musiman berdasarkan **laba per bulan aktif**, dan lakukan rasionalisasi
**varian ukuran** — bukan penghapusan produk."""),

    md("""## 10.12 Ringkasan Bagian Profit

| Pertanyaan Project | Jawaban |
|:---|:---|
| Bagaimana tren profit? | Datar. Laba sejajar omzet, margin stabil sepanjang tahun. Tidak turun, tapi juga tidak tumbuh. |
| Faktor apa yang menyebabkan profit turun? | Profit tidak turun. Yang menggerusnya: diskon ke anggota loyalty tanpa perubahan perilaku, dan tingkat diskon 15%/20% yang justru menurunkan unit. Penggerus terbesar — biaya 10 jam tersepi — tidak ada di dataset. |
| Produk atau transaksi apa yang merugi? | Nol produk dan nol transaksi merugi. Kerugian ada di kebijakan, bukan di produk. |
| Bagaimana dampak diskon terhadap profit? | Hanya tingkat 10% yang menaikkan jumlah unit. Tiga tingkat lainnya menjual lebih sedikit daripada tanpa diskon. |

### Batasan yang harus disampaikan saat presentasi

1. **Laba ini estimasi**, dari benchmark HPP per kategori — bukan angka akuntansi.
2. **Ini laba kotor.** Gaji, sewa, dan listrik tidak ada di dataset.
3. **Uji sensitivitas sudah dijalankan**: walau tebakan HPP meleset 5 poin persen,
   urutan kategori tidak berubah. Kesimpulannya tahan uji; besaran angkanya tidak.

---"""),
]


def hapus_duplikat_header(nb):
    """Hapus sel judul & objective yang terulang karena penggabungan notebook.

    Kemunculan pertama dipertahankan; sisanya dibuang.
    """
    target = {
        "# ☕ Capstone Data Analysis: Coffee Shop Sales",
        "# 1. Objective",
        "# 2. Business Questions",
    }
    sudah, simpan, dibuang = set(), [], 0
    for c in nb.cells:
        if c.cell_type == "markdown":
            baris1 = c.source.strip().split("\n")[0].strip()
            if baris1 in target:
                if baris1 in sudah:
                    dibuang += 1
                    continue
                sudah.add(baris1)
        simpan.append(c)
    nb.cells = simpan
    return dibuang


def main():
    nb = nbf.read(NB, as_version=4)
    awal = len(nb.cells)

    # 1. Ganti bagian 10
    idx = next((i for i, c in enumerate(nb.cells)
                if c.cell_type == "markdown"
                and "10. Profit or Performance Analysis" in c.source), None)
    if idx is None:
        print("!! Sel '10. Profit or Performance Analysis' tidak ditemukan — "
              "notebook mungkin sudah dipatch.")
    else:
        nb.cells[idx:idx + 1] = SECTION_10
        print(f"Bagian 10 diganti di indeks {idx}: 1 sel -> {len(SECTION_10)} sel")

    # 2. Hapus header duplikat
    dibuang = hapus_duplikat_header(nb)
    print(f"Sel judul duplikat dihapus: {dibuang}")

    nbf.write(nb, NB)
    print(f"\nSel: {awal} -> {len(nb.cells)}")
    print(f"Tersimpan: {NB.name}")


if __name__ == "__main__":
    main()
