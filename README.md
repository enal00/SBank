# SeaBank Digital Twin
### Portofolio analitik: membangun bukti dari pertanyaan bisnis, bukan dari ketersediaan data

> **Data di repo ini SINTETIS.** Bukan data PT Bank SeaBank Indonesia, bukan nasabah nyata,
> tidak diambil dari sistem mana pun. Yang **nyata** hanya dua: rasio keuangan publik dari
> laporan tahunan 2025, dan struktur produk yang dipublikasikan. Semua transaksi, nama, saldo,
> dan nasabah dibangkitkan secara programatis untuk mereproduksi rasio publik itu pada skala
> **1:1.000** (24.000 nasabah). Tujuannya: mendemonstrasikan penalaran analitik pada struktur
> bisnis yang menyerupai bank digital sungguhan — bukan mengklaim memiliki data internal.
> Batasan lengkap ada di [§7](#7-batasan-yang-tidak-saya-sembunyikan).

---

## 1. Masalah bisnis

Bank digital Indonesia tumbuh cepat, tetapi pertumbuhan DPK bukan otomatis profit.

| Metrik publik FY2025 | Nilai | Artinya |
|---|---:|---|
| DPK | +30,6% | mesin pertumbuhan menyala |
| Kredit | +18,2% | kredit tumbuh lebih lambat dari dana |
| LDR | 92,32% | dana nyaris seluruhnya sudah diputar |
| NIM | 21,45% | spread sangat lebar untuk ukuran bank |
| **BOPO** | **91,47%** | peringkat 2 dari 5 — masih 3,5–8,5 pp dari "sangat sehat" |

BOPO 91,47% **bukan** tanda efisiensi sudah mentok. Margin laba operasionalnya hanya 8,53% dari pendapatan operasional, sehingga **setiap 1 pp penurunan BOPO = +11,7% laba operasional**; memotong biaya 10% melipatgandakannya (+107%). Ini pengungkit terbesar yang tersedia — tetapi rincian beban tidak ada di dataset ini, jadi pertanyaan yang bisa saya jawab dengan data adalah **komposisi neraca**, bukan pemangkasan biaya. Argumennya soal lingkup data, bukan klaim bahwa biaya sudah mentok. Perhitungan lengkap: [memo §8](docs/02_bab1_memo.md#8-konteks-yang-sering-salah-dibaca-bopo-9147).

> **Sumber ambang.** Pita peringkat: matriks penetapan peringkat komponen rentabilitas (BOPO), **Lampiran 6 SE BI 13/24/DPNP/2011** (83–88% peringkat 1 · 89–93% peringkat 2 · 94–96% peringkat 3 · 97–100% peringkat 4 · >100% peringkat 5). Ambang "sehat" < 93,52% berasal dari **SE BI 6/23/DPNP (31 Mei 2004)** — rujukan yang lebih tua. Dua catatan presisi: (a) "peringkat 2 dari 5" merujuk pada **sel BOPO** dalam matriks itu, **bukan** peringkat kesehatan bank secara keseluruhan (yang bersifat komposit RGEC); (b) sejak **RGEC (SEOJK 14/SEOJK.03/2017)** BOPO tidak lagi berpita angka tetap, sehingga pita di atas dipakai sebagai *benchmark praktik*, bukan aturan berlaku.

> **Pertanyaan Bisnis:**
> Di mana menaruh rupiah berikutnya — menambah DPK murah, atau menambah kredit berimbal hasil tinggi — agar NIM terjaga tanpa menaikkan NPL di atas toleransi?

Pertanyaan itu terlalu besar untuk dijawab sekaligus, jadi dipecah menjadi empat bab yang masing-masing punya deliverable sendiri.

---

## 2. Temuan Bab 1 — CASA terlihat sehat, ternyata rapuh

Angkatan nasabah Januari 2025 (n=600), diukur pada bulan ke-12:

| Metrik | Bulan 0 | Bulan 12 | Bocor |
|---|---:|---:|---:|
| Retensi orang | 100,0% | **68,33%** | −31,67 pp |
| Saldo per nasabah (indeks) | 100,0 | 87,11 | −12,89 |
| **Retensi uang** | 100,0% | **59,53%** | **−40,47 pp** |

**Dari 100 nasabah: 68 orang masih ada, tetapi hanya Rp60 dari Rp100 dananya.** Retensi biasa — yang hanya menghitung kepala — akan melaporkan "68%, masih wajar" dan menutup berkas.

Lima temuan yang tidak terlihat dari KPI agregat:

| # | Temuan | Angka |
|---|---|---|
| 1 | **Kebocoran uang 78,3% disebabkan nasabah pergi**, hanya 21,7% karena saldo menyusut | dekomposisi bulan ke-12: −31,67 pp vs −8,81 pp |
| 2 | **Uang bocor deras di bulan pertama**, orang bocor merata sepanjang tahun | M1: uang −16,92 pp vs orang −10,61 pp; 62,9% kebocoran uang terjadi di 3 bulan pertama |
| 3 | **Hipotesis "uang tidur" gugur** — dana tidak mengendap, dana keluar | 5.029 dorman (20,95%) hanya menyimpan **2,17%** DPK |
| 4 | **Kanal membedakan uang, bukan orang** | retensi orang seragam 77,5–81,0% (3,5 pp), retensi uang terbelah **15,4 pp** (Payroll 75,2% vs Agent Mitra 59,8%) |
| 5 | **Konsentrasi saldo tidak terbukti** | top 5% memegang 32,97%, bukan >55% seperti dugaan awal |

Detail lengkap, tabel angka, dan rekomendasi anggaran: **[`docs/02_bab1_memo.md`](docs/02_bab1_memo.md)**

![Kurva retensi orang vs uang](analysis/g1_kurva_retensi.png)

---

## 3. Status hipotesis

| # | Hipotesis | Vonis | Dasar |
|---|---|---|---|
| H1a | CASA rapuh karena **terkonsentrasi** di segelintir nasabah | **DITOLAK** | top 5% = 32,97% saldo; top 20% = 63,36% |
| H1b | CASA rapuh karena **tidak lengket** | **TERBUKTI** | retensi uang 12 bulan = 59,53% |
| H2 | Sebagian DPK buru bunga — naik saat promo, pergi setelahnya | **TIDAK DAPAT DIUJI** | tarif promo 4,00% tidak pernah dibayar (terealisasi datar 2,48%), tidak ada penanda eksposur per nasabah, tidak ada patahan di Oktober — lihat [memo §7](docs/02_bab1_memo.md#7-temuan-6--promo-bunga-4-tidak-dapat-dijawab-dan-ini-alasannya) dan [`analysis/promo_rate_realized.csv`](analysis/promo_rate_realized.csv). **Alat ujinya sudah lulus kalibrasi** di [lab H2](docs/04_lab_h2.md): bias +0,41 pp, slope 1,02, placebo ≈ 0 |
| H3 | Pertumbuhan kredit digerakkan mitra berisiko tinggi | **BELUM** | dijadwalkan Bab 3 |

Menolak menjawab satu hipotesis lebih berharga daripada memaksakan jawaban. H2 gagal di tiga titik sekaligus: **tarif promo 4,00% tidak pernah diterapkan ke bunga yang benar-benar dibayar** (terealisasi tetap 2,47–2,50% selama Jul–Sep), **tidak ada penanda siapa yang terpapar kampanye**, dan **saldo tidak punya mekanisme untuk merespons tarif**. Ujinya tetap bisa dijalankan — dan sudah dijalankan. Hasil 101,45% itu hanya mengukur "tidak ada yang terjadi", bukan "promo berhasil".

---

## 4. Peta progres

| Bab | Isi | Deliverable | Status |
|---|---|---|---|
| **0** | Fondasi & kepercayaan data | skema BigQuery, generator terkalibrasi, verifikasi independen, 10 uji kualitas data | **selesai** |
| **1** | Kualitas CASA — retensi orang vs uang | memo 2 halaman, 10 tabel, 3 grafik, 2 berkas SQL | **selesai** |
| **1b** | Laboratorium H2 — kalibrasi alat uji promo | simulator 2 dunia, 200 estimasi pemulihan, MDE, uji placebo | **selesai** |
| 2 | Segmentasi & nilai nasabah | RFM perilaku, nilai seumur, segmentasi yang bisa dieksekusi | berikutnya |
| 3 | Kredit & risiko mitra | NPL per mitra, konsentrasi risiko, kualitas agunan | — |
| 4 | Sintesis | jawaban atas pertanyaan portofolio: alokasi rupiah berikutnya | — |

---

## 5. Struktur repo

```
portfolio/
├── gen/
│   ├── generate.py          # generator terkalibrasi (deterministik, seed 20251118)
│   ├── verify.py            # verifikasi independen — baca ulang CSV, hitung ulang dari nol
│   ├── run_dq.py            # menjalankan 10 uji kualitas data
│   ├── explore_bab1.py      # eksplorasi kohort (skrip yang membongkar cacat desain)
│   ├── bab1_analysis.py     # analisis Bab 1 — menulis 10 tabel ke analysis/
│   ├── bab1_charts.py       # 3 grafik Bab 1
│   ├── run_promo_probe.py   # menjalankan Q1–Q3 template uji promo
│   └── h2_lab.py            # laboratorium H2 — 3 prasyarat, 2 dunia, 200 estimasi
├── sql/
│   ├── 00_schema_bigquery.sql   # DDL + view metrik resmi
│   ├── 10_dq_tests.sql          # 10 uji kualitas data (T01–T10)
│   └── 20_promo_effect.sql      # spesifikasi uji efek kampanye bunga (template)
├── docs/
│   ├── 00_dataset_card.md       # kartu dataset: sumber, kalibrasi, batasan, etika (v1.1)
│   ├── 01_calibration_report.md # target publik vs hasil dataset, per metrik (v1.1)
│   ├── 02_bab1_memo.md          # memo Bab 1 — temuan & rekomendasi
│   ├── 03_kamus_istilah.md      # glosarium bahasa awam
│   └── 04_lab_h2.md             # laporan laboratorium H2 — vonis atas alatnya
├── analysis/                    # keluaran Bab 1: 10 CSV + 3 PNG + summary.json
├── lab/                         # keluaran laboratorium: 6 CSV + run.log
└── data/                        # TIDAK di-commit: 143 MB, dibangun ulang dari seed
```

**Kenapa `data/` tidak disimpan.** Yang berharga dari dataset sintetis adalah **resepnya**, bukan hasilnya. `gen/generate.py` dengan seed tetap menghasilkan 143 MB identik dalam ~90 detik. Menyimpannya di repo berarti mengunggah 143 MB yang bisa dibangun ulang kapan saja — dan setiap kali model dikalibrasi ulang, 143 MB baru menumpuk lagi. Yang tetap disimpan: `data/_calibration.json` (3 KB) sebagai bukti target vs hasil, dan seluruh `analysis/` sebagai keluaran yang benar-benar dipakai di memo.

---

## 6. Cara menjalankan

```bash
# 0. Repo ini TIDAK memuat data. Langkah 1 wajib, bukan opsional.
#    Clone bersih ≈ 1 MB; setelah langkah 1 menjadi ≈ 145 MB.

# 1. Bangun ulang dataset dari nol lalu verifikasi (≈90 detik)
uv run python gen/generate.py
uv run python gen/verify.py

# 2. Kepercayaan data: 10 uji kualitas
uv run --with duckdb python gen/run_dq.py

# 3. Bab 1: tabel + grafik
uv run --with duckdb     python gen/bab1_analysis.py
uv run --with matplotlib python gen/bab1_charts.py

# 4. Uji promo (template)
uv run --with duckdb python gen/run_promo_probe.py

# 5. Laboratorium H2 — kalibrasi alat uji (≈90 detik)
uv run --with duckdb --with numpy python gen/h2_lab.py
```

Seed tetap → hasil deterministik dan dapat diaudit ulang.

---

## 7. Batasan yang tidak saya sembunyikan

1. **Sintetis, skala 1:1.000.** Rasio persen bertahan terhadap penskalaan; nominal rupiah absolut hanya bermakna setelah dikali 1.000. Aman menyimpulkan "CASA rapuh"; tidak aman menyimpulkan "kerugian Rp34,8 miliar" tanpa konversi.
2. **Perilaku adalah asumsi, bukan estimasi.** Parameter churn, reaktivasi, dan residual dana (`ARCH` di `gen/generate.py`) saya pilih sendiri. Temuan Bab 1 menunjukkan **metode ini mampu mendeteksi pola tersebut**, bukan bahwa SeaBank mengalaminya.
3. **Horizon 12 bulan.** Retensi tahun ke-2 dan nilai seumur nasabah belum terukur.
4. **Uji kualitas data T01, T02, T06 sengaja gagal** — duplikat, transaksi yatim, nasabah KYC-ditolak yang tetap punya akun aktif. Analisis berjalan di atas data yang tidak bersih, seperti di bank sungguhan. T05 menemukan **15% nasabah** berbeda status antara master dan ledger.
5. **Tidak ada klaim kausal.** Semua pernyataan adalah asosiasi dan dekomposisi aritmetika, kecuali disebut eksplisit.
6. **Katalog tarif ≠ tarif yang dibayar.** Promo 4,00% (Jul–Sep 2025) tercatat di `product_rates.csv` tetapi tidak pernah diterapkan ke transaksi bunga; tarif terealisasi datar 2,4–2,5% sepanjang tahun. Konsekuensinya H2 tidak dapat diuji pada dataset versi ini — buktinya di [`analysis/promo_rate_realized.csv`](analysis/promo_rate_realized.csv) dan memo §7.

---

## 8. Prinsip kerja

1. **Rasio publik dikalibrasi presisi.** CASA 70,74% · LDR 92,32% · NPL 1,82% · DPK Rp34.806.000.010.000 · kredit Rp32.133.999.307.000 — cocok dengan laporan tahunan sampai satuan rupiah. Kalau tidak cocok, modelnya yang salah.
2. **Perilaku yang tidak diketahui publik dibiarkan muncul sendiri.** Retensi, konsentrasi, dan dormansi adalah *output* proses generatif — bukan angka target. Karena itu layak disebut temuan; kalau saya menyetelnya agar dramatis, itu bukan temuan lagi.
3. **Anomali disuntik sengaja.** Duplikat dan transaksi yatim dimasukkan agar lapisan uji kualitas data punya sesuatu yang nyata untuk ditemukan.
4. **Verifikasi tidak mempercayai generator.** `verify.py` membaca ulang CSV dan menghitung ulang semuanya dari nol.
5. **Hipotesis yang gagal dilaporkan sebagai gagal.** Konsentrasi saldo, uang tidur, dan efek promo semuanya berakhir "tidak terbukti" — dan itu ditulis di depan, bukan disembunyikan.

> **Bagi pembaca yang punya 3 menit:** baca memo Bab 1, lihat dua grafik (`g1`, `g3`), lalu lompat ke §7. Kalau batasannya jujur, angkanya biasanya juga.

---

---_Lisensi: kode MIT. Data sintetis, bebas dipakai dengan atribusi._
