# Laporan Kalibrasi — Digital Twin v1.1

Semua angka di bawah **dihitung ulang oleh `gen/verify.py`**, yang membaca file CSV
mentah dan tidak memakai satu pun variabel dari generator. Kalau generator dan
verifikator tidak sepakat, yang dipercaya adalah verifikator.

## 1. Rasio publik vs dataset

| Metrik | AR SeaBank 2025 | Dataset | Selisih | Status |
|---|---:|---:|---:|---|
| Total DPK | Rp34.806.000.000.000 | Rp34.806.000.010.000 | +0,00003% | presisi |
| Tabungan (CASA) | Rp24.621.764.400.000 | Rp24.621.764.386.000 | −0,00006% | presisi |
| Deposito aktif | Rp10.184.235.600.000 | Rp10.184.235.624.000 | +0,0002% | presisi |
| Rasio CASA | 70,74% | 70,74% | 0,00 pp | presisi |
| Total kredit | Rp32.134.000.000.000 | Rp32.133.999.307.000 | −0,000002% | presisi |
| LDR | 92,32% | 92,32% | 0,00 pp | presisi |
| NPL gross | 1,82% | 1,82% | 0,00 pp | presisi |
| NPL mitra saja | — | 1,67% | — | turunan |

> Skala 1 : 1.000. Angka dataset dikali 1.000 agar sebanding dengan laporan tahunan.

## 2. Komposisi buku kredit

| Skema | AR2025 | Dataset | Porsi |
|---|---:|---:|---:|
| Joint financing (mitra) | Rp25.913 M | Rp25.913.000.000 | 80,6% |
| Channeling | Rp3.533 M | Rp3.533.000.000 | 11,0% |
| Pinjaman langsung | Rp2.653 M | Rp2.652.999.307 | 8,3% |
| Legacy (run-off) | Rp35 M | Rp35.000.000 | 0,1% |

Temuan struktural pertama sudah terlihat dari tabel ini saja: **91,6% kredit
SeaBank bukan diputuskan oleh SeaBank**. Bank menanggung risikonya di neraca,
tetapi seleksi debitur ada di tangan mitra. Itulah akar pertanyaan portofolio.

## 3. Integritas data

| Pemeriksaan | Hasil |
|---|---|
| Rantai saldo (opening + kredit − debit = closing) | **0 pelanggaran dari 288.000 akun-bulan** |
| Kelengkapan snapshot bulanan | 12/12 bulan, 24.000 akun per bulan |
| Akun dengan saldo sebelum tanggal bergabung | 0 (bulan pra-gabung diisi nol, bukan saldo) |
| Pinjaman yatim | 0 |
| Deposito dengan tanggal mustahil | 0 |

## 4. Kurva akuisisi (perbaikan v1.1)

Versi awal menyebar basis lama rata 2019–2024 → **kurva datar 233/bulan selama enam
tahun**. Itu artefak cara membagi, bukan perilaku bank. Versi 1.1 memakai kurva yang
mengikuti sejarah perusahaan.

| Tahun | Rata-rata/bulan | Min | Max | Setara bank nyata |
|---|---:|---:|---:|---:|
| 2019 | 10 | 8 | 12 | 10.000 |
| 2020 | 25 | 19 | 31 | 25.000 |
| 2021 | 150 | 115 | 185 | 150.000 |
| 2022 | 300 | 231 | 369 | 300.000 |
| 2023 | 400 | 308 | 492 | 400.000 |
| 2024 | 515 | 396 | 634 | 515.000 |
| 2025 | 600 | 562 | 640 | 600.000 |

Total 2019–2024 = 16.800 dan 2025 = 7.200, keduanya **tetap** — jadi kalibrasi rasio
tidak terganggu sama sekali. Diperiksa langsung dari `customers.csv` dengan DuckDB.

## 5. Uji kualitas data (Bab 0) — hasil eksekusi nyata

Dijalankan dengan DuckDB terhadap CSV: `uv run --with duckdb python gen/run_dq.py`

| Kode | Uji | Nilai | Vonis | Arti bisnis |
|---|---|---:|---|---|
| T01 | Duplikat `transaction_id` | 4.735 | **GAGAL** | `SUM(amount)` overstate −0,34% |
| T02 | Transaksi yatim (akun tak dikenal) | 3.464 | **GAGAL** | Total mutasi tidak rekonsiliasi dengan DPK |
| T03 | Rantai saldo akun-bulan | 0 | LULUS | Analisis kohort sah dipakai |
| T04 | Snapshot vs ledger (jumlah txn) | 7.954 | SELIDIKI | Dua sumber kebenaran berbeda |
| T05 | Nasabah aktif: master vs ledger | 3.649 | SELIDIKI | 15% nasabah salah kelas jika pakai field master |
| T06 | KYC REJECTED pegang akun aktif | 13 | **GAGAL** | Eksposur kepatuhan |
| T07 | Deposito jatuh tempo < buka | 0 | LULUS | — |
| T08 | Pinjaman yatim | 0 | LULUS | — |
| T09 | Snapshot tidak lengkap | 0 | LULUS | — |
| T10 | Rekonsiliasi rasio | CASA 70,74 / LDR 92,32 / NPL 1,82 | LULUS | Model setia ke AR2025 |

**Kenapa tiga uji sengaja gagal.** Ini keputusan desain, bukan kelalaian. Bank
sungguhan selalu punya duplikat, transaksi yatim, dan field master yang tertinggal.
Analis yang melaporkan "data bersih 100%" biasanya belum menguji, bukan sudah bersih.

**T05 adalah temuan manajerial, bukan cacat teknis.** Jika tim pelaporan memakai
`last_txn_date_master` sebagai definisi "aktif", hasilnya meleset 3.649 nasabah
(15%). Angka "nasabah aktif" yang naik ke dashboard bisa salah selama berbulan-bulan
tanpa ada yang sadar, karena tidak ada yang membandingkannya dengan ledger.

## 6. Yang tidak dikalibrasi (bahan temuan)

Angka ini **tidak** ditanam sebagai target. Ia muncul dari aturan perilaku di
`gen/generate.py` dan karena itu layak disebut temuan, bukan asumsi:

| Metrik | Hasil |
|---|---:|
| Pangsa saldo top 1% | 14,04% |
| Pangsa saldo top 5% | 32,97% |
| Pangsa saldo top 10% | 46,40% |
| Pangsa saldo top 20% | 63,36% |
| Saldo median | Rp654.834 |
| Saldo rata-rata | Rp1.205.276 |
| Akun dengan saldo < Rp100 ribu | 15,4% |

*Basis: `closing_balance` rekening SAVINGS per 31 Des 2025, dijumlah per nasabah (24.000 orang, total Rp28,93 miliar). Dapat dihitung ulang dengan `uv run --with duckdb python gen/verify_concentration.py`; hasilnya identik dengan `analysis/balance_concentration.csv`.*

Catatan jujur: konsentrasi 32,97% pada top 5% **lebih rendah** dari dugaan awal saya
(>55%). Saya tidak menyesuaikan parameter untuk memaksa angka yang lebih dramatis —
yang dilaporkan adalah apa yang keluar dari model. Untuk bank digital massal dengan
DPK per nasabah ~Rp1,2 juta, sebaran yang relatif rata justru masuk akal.

## 7. Reproduksi

```bash
cd gen && python3 generate.py    # ~90 detik
python3 verify.py                # rekalkulasi independen
cd .. && uv run --with duckdb python gen/run_dq.py
```
Seed tetap `20251118` → hasil identik setiap kali dijalankan.
