# SeaBank Digital Twin — Portofolio Analitik

> **PERINGATAN KERAS — BACA SEBELUM APA PUN**
> Dataset dalam repo ini **SINTETIS**. Ini **bukan** data PT Bank SeaBank Indonesia,
> bukan data nasabah nyata, dan tidak diambil dari sistem mana pun.
> Yang **nyata** hanya dua hal: (1) rasio keuangan publik dari laporan tahunan 2025,
> dan (2) struktur produk yang dipublikasikan di situs resmi.
> Semua baris transaksi, nama, saldo, dan nasabah dibangkitkan secara programatis
> untuk **mereproduksi rasio publik tersebut pada skala 1/1000**.
> Tujuannya: melatih dan mendemonstrasikan penalaran analitik pada struktur bisnis
> yang menyerupai bank digital sungguhan — bukan mengklaim memiliki data internal.

---

## Masalah bisnis yang dijawab

Bank digital Indonesia tumbuh cepat, tapi pertumbuhan DPK bukan otomatis profit.
SeaBank FY2025: DPK naik 30,6%, kredit naik 18,2%, **LDR 92,32%**, **NIM 21,45%**,
tapi **BOPO 91,47%** — artinya bank sudah sangat efisien secara biaya, sehingga
ruang perbaikan profitabilitas berikutnya **tidak** datang dari memotong biaya.
Ia harus datang dari **kualitas komposisi neraca**: dana mana yang murah dan lengket,
kredit mana yang menghasilkan tapi menaikkan risiko.

Pertanyaan portofolio:

> **Di mana SeaBank harus menaruh rupiah berikutnya — menambah DPK murah,
> atau menambah kredit berimbal hasil tinggi — agar NIM terjaga tanpa
> menaikkan NPL di atas toleransi?**

Pertanyaan itu dipecah jadi tiga hipotesis yang bisa diuji pada dataset:

| # | Hipotesis | Metrik uji |
|---|---|---|
| H1 | CASA terlihat sehat di agregat, tapi rapuh karena terkonsentrasi & tidak lengket | konsentrasi saldo, retensi kohort |
| H2 | Sebagian DPK bersifat musiman/buru bunga — naik saat promo, pergi setelahnya | elastisitas saldo terhadap perubahan suku bunga |
| H3 | Pertumbuhan kredit digerakkan mitra berisiko tinggi yang NPL-nya memburuk lebih cepat | NPL per mitra vs laju pertumbuhan buku |

---

## Struktur repo

```
portfolio/
├── gen/
│   ├── generate.py        # generator dataset terkalibrasi (deterministik, seed 20251118)
│   └── verify.py          # verifikasi independen — membaca ulang CSV, hitung ulang rasio
├── sql/
│   ├── 00_schema_bigquery.sql   # DDL + view metrik resmi
│   └── 10_dq_tests.sql          # 10 uji kualitas data (lapisan kepercayaan)
├── docs/
│   ├── 00_dataset_card.md       # kartu dataset: sumber, kalibrasi, batasan, etika
│   └── 01_calibration_report.md # target publik vs hasil dataset, per metrik
└── data/                        # CSV sintetis hasil generate (disimpan via Git LFS)
```

## Cara menjalankan

```bash
cd gen
python3 generate.py     # ~90 detik, menulis 9 CSV ke ../data
python3 verify.py       # cetak ulang semua rasio dari CSV mentah
```

`generate.py` memakai seed tetap → hasil deterministik dan dapat diaudit ulang.

## Prinsip yang dipegang

1. **Rasio publik dikalibrasi persis.** CASA, LDR, NPL, dan total DPK/kredit cocok
   dengan laporan tahunan sampai satuan rupiah. Kalau tidak cocok, modelnya salah.
2. **Perilaku yang tidak diketahui publik dibiarkan muncul sendiri.** Retensi kohort,
   konsentrasi saldo, dan dormansi **tidak** ditanam sebagai angka target —
   mereka adalah *output* proses generatif, jadi layak disebut temuan.
3. **Anomali disuntik sengaja.** 0,36% duplikat dan 0,25% transaksi yatim dimasukkan
   agar lapisan uji kualitas data punya sesuatu yang nyata untuk ditemukan.
4. **Verifikasi tidak mempercayai generator.** `verify.py` membaca ulang file CSV
   dan menghitung ulang semuanya dari nol.
