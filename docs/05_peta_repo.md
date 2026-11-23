# Peta Repo — dibaca oleh orang yang bukan analis

> **Untuk siapa dokumen ini.** Untuk siapa pun yang membuka repo ini dan bertanya:
> *"Ini isinya apa, dan file-nya nyambung ke mana?"*
> Tidak ada istilah teknis yang diasumsikan. Kalau kamu analis dan mencari detail
> metode, baca `02_bab1_memo.md` dan `04_lab_h2.md`.

---

## 1. Analogi: ini bukan lemari arsip, ini satu rantai produksi

Bayangkan repo ini seperti **pabrik tahu**, bukan seperti folder dokumen.

| Di pabrik | Di repo ini |
|---|---|
| Gudang kedelai | `data/` — bahan mentah (143 MB CSV) |
| Mesin & dapur | `gen/` — **14 skrip Python** (dulu 12) |
| Cetak biru & daftar periksa | `sql/` — definisi tabel + 10 uji kualitas |
| Meja saji berisi tahu jadi | `analysis/` — tabel & grafik hasil analisis |
| Ruang latihan menimbang | `lab/` — uji apakah alat ukur kita akurat |
| Papan menu untuk pembeli | `docs/` + `README.md` |

Yang membuat pabrik ini bisa dipercaya cuma satu hal: **panahnya selalu satu arah.**
Kedelai tidak lahir dari menu. Angka tidak lahir dari dokumen. Dokumen hanya **membaca** angka.

Jadi kalau ada yang bertanya *"angka 59,53% ini dari mana?"*, jawabannya bukan "dari memo",
tetapi:

> `analysis/retention_matrix.csv` → dibuat oleh `gen/bab1_analysis.py` → yang membaca `data/transactions.csv` → yang dibuat `gen/generate.py` dari seed `20251118`.

Rantai itu bisa ditelusuri mundur sampai ujung. Itulah inti seluruh repo ini.

---

## 2. Enam kamar

| Folder | Bahasa awam | Isinya | Boleh diedit tangan? |
|---|---|---|---|
| `data/` | **Gudang bahan** | 143 MB CSV mentah: nasabah, rekening, transaksi, produk, kanal | ❌ Tidak — dibuat mesin, dibangun ulang dari seed |
| `gen/` | **Dapur & mesin** | 12 skrip Python: pembuat data, pemeriksa, penganalisis, pembuat grafik & viewer | ✅ Ya — ini yang diedit |
| `sql/` | **Cetak biru & daftar periksa** | Definisi tabel, 10 uji kualitas, template uji promo | ✅ Ya |
| `analysis/` | **Meja saji** | 14 CSV + 1 HTML + 7 PNG hasil analisis Bab 1 & 2 | ❌ Tidak — selalu ditimpa skrip |
| `lab/` | **Ruang percobaan** | Bukti bahwa alat ukur kita akurat sebelum dipakai | ❌ Tidak — selalu ditimpa skrip |
| `docs/` | **Papan menu** | 6 dokumen yang dibaca manusia | ✅ Ya — tapi hanya boleh *membaca* angka |

Ditambah dua file di akar: `README.md` (papan nama + menu utama) dan `.gitignore`
(daftar "jangan dibawa pulang").

---

## 3. Alur: dari kedelai sampai menu

```
   ┌──────────────────────────────────────────────────────────────┐
   │  LAPIS 0 — BAHAN                                             │
   │  gen/generate.py  ──(seed 20251118)──▶  data/*.csv  (143 MB) │
   │       ▲                                      │               │
   │       │ target dari laporan publik           │               │
   │  data/_calibration.json                      │               │
   └──────────────────────────────────────────────┼───────────────┘
                                                  │
   ┌──────────────────────────────────────────────▼───────────────┐
   │  LAPIS 1 — UJI KEPERCAYAAN (sebelum percaya angkanya)        │
   │  gen/verify.py   → docs/01_calibration_report.md             │
   │  gen/run_dq.py   → menjalankan sql/10_dq_tests.sql (T01–T10) │
   └──────────────────────────────────────────────┼───────────────┘
                                                  │ lolos 10 uji
   ┌──────────────────────────────────────────────▼───────────────┐
   │  LAPIS 2 — MENGOLAH                                          │
   │  gen/explore_bab1.py   (mencari cacat desain)                │
   │  gen/bab1_analysis.py  ──▶ analysis/*.csv + summary.json     │
   │  gen/bab1_charts.py    ──▶ analysis/g1…g7.png                │
   │  gen/bab2_rfm.py       ──▶ rfm_scored/segments + basket_*.csv │
   │  gen/build_rfm_viewer.py ─▶ analysis/rfm_viewer.html         │
   └──────────────────────────────────────────────┼───────────────┘
                                                  │
   ┌──────────────────────────────────────────────▼───────────────┐
   │  LAPIS 3 — MENGUJI ALAT UKURNYA SENDIRI                      │
   │  gen/h2_lab.py          ──▶ lab/*.csv + run.log              │
   │  gen/lab_h2_charts.py   ──▶ lab/g8_recovery.png              │
   │  gen/run_promo_probe.py ──▶ bukti sql/20_promo_effect.sql    │
   │                             benar-benar berjalan             │
   └──────────────────────────────────────────────┼───────────────┘
                                                  │
   ┌──────────────────────────────────────────────▼───────────────┐
   │  LAPIS 4 — BERCERITA (hanya membaca, tidak menghitung)       │
   │  docs/02_bab1_memo.md      ◀── analysis/*  + lab/*           │
   │  docs/04_lab_h2.md         ◀── lab/*                         │
   │  docs/03_kamus_istilah.md     (istilah, tanpa angka baru)    │
   │  docs/00_dataset_card.md      (asal-usul bahan)              │
   │  README.md                 ◀── semua di atas, versi 3 menit  │
   └──────────────────────────────────────────────────────────────┘
```

Perhatikan: **tidak ada panah yang mengarah ke atas.** Dokumen tidak pernah memberi makan skrip.
Itu bukan kebetulan — itu aturan (lihat §5).

---

## 4. File per file

### 4.1 `gen/` — dapur (15 mesin)

| File | Bahasa awam | Peran dalam rantai |
|---|---|---|
| `generate.py` (781 baris) | **Pabrik kedelai.** Membuat 24.000 nasabah sintetis dari nol; angka besar dipaksa cocok ke laporan tahunan SeaBank | Sumber semua bahan. Dijalankan sekali, hasilnya 143 MB |
| `verify.py` (97 baris) | **Juru timbang independen.** Tidak memakai satu variabel pun dari pabrik; membaca CSV lalu menghitung ulang dari nol | Kalau pabrik dan juru timbang berbeda, **juru timbang yang menang** |
| `run_dq.py` (84 baris) | **Petugas kebersihan.** Menjalankan 10 tes: ada yang kosong? ada yang dobel? ada tanggal mustahil? | Gerbang: kalau gagal, angka tidak boleh dikutip |
| `explore_bab1.py` (110 baris) | **Orang iseng yang membongkar.** Eksplorasi awal yang justru menemukan cacat desain data | Nenek moyang Bab 1 — dari sini ketahuan "retensi orang" dan "retensi uang" itu beda hal |
| `bab1_analysis.py` | **Koki utama Bab 1.** Mengubah transaksi menjadi tabel-tabel jadi | Menulis `analysis/retention_matrix.csv` dan kawan-kawan |
| `bab1_charts.py` | **Juru foto.** Mengubah tabel jadi gambar yang bisa dilihat mata | Menulis `analysis/g1…g7.png` |
| `run_promo_probe.py` (82 baris) | **Uji coba senjata.** Menembakkan template SQL promo ke data untuk membuktikan SQL-nya tidak error | Bukti bahwa `sql/20_promo_effect.sql` bukan hiasan |
| `h2_lab.py` (313 baris) | **Ruang latihan menembak.** Membuat dua dunia buatan yang jawabannya sudah diketahui, lalu mengecek apakah alat kita bisa menemukan jawaban itu | Menulis `lab/*.csv`. Hasil: bias +0,41 pp, slope 1,02 |
| `lab_h2_charts.py` | **Juru foto ruang latihan** | Menulis `lab/g8_recovery.png` |
| `bab2_rfm.py` (305 baris) | **Tukang sortir nasabah.** Menghitung ulang R/F/M dari 1.075.753 transaksi mentah, memberi skor 1–5 berbasis kuintil, lalu menempel label 9 segmen | Menulis `analysis/rfm_scored.csv`, `rfm_segments.csv`, `basket_categories.csv`, `basket_pairs.csv` |
| `build_rfm_viewer.py` (330 baris) | **Pencetak katalog interaktif.** Menanam seluruh 24.000 baris ke dalam satu file HTML supaya bisa dibuka tanpa Python | Menulis `analysis/rfm_viewer.html` |
| `bab3_credit.py` | **Koki utama Bab 3.** Mengolah portofolio kredit 13 mitra dan kredit langsung, menghitung ilusi NPL, konsentrasi risiko per tier, dan simulasi headroom alokasi kredit | Menulis `analysis/h3_*.csv` |
| `bab3_charts.py` | **Juru foto Bab 3.** Visualisasi ilusi rasio NPL, konsentrasi risiko per tier, dan headroom alokasi kredit | Menulis `analysis/g9_npl_dilemma.png`, `g10_tier_contribution.png`, `g11_headroom.png` |
| `audit_consistency.py` | **Pemeriksa sebelum berangkat.** Memastikan setiap file yang disebut di dokumen benar-benar ada, dan angka di dokumen cocok dengan CSV | Dijalankan sebelum setiap commit |
| `verify_concentration.py` | **Juru timbang kedua untuk konsentrasi.** Menghitung ulang pangsa saldo top 1/5/10/20% langsung dari ledger, tanpa memakai `bab1_analysis.py` | Harus identik dengan `analysis/balance_concentration.csv`; kalau beda, ada yang basi |

### 4.2 `sql/` — cetak biru (3 file)

| File | Bahasa awam | Kenapa ada |
|---|---|---|
| `00_schema_bigquery.sql` | **Cetak biru gedung.** Definisi kolom tiap tabel + *view* (tabel jadi yang siap dipakai) | Supaya analisis bisa dipindah ke BigQuery tanpa mengubah logika |
| `10_dq_tests.sql` | **Daftar periksa 10 poin** (T01–T10). Tiap tes mengembalikan vonis: lulus atau tidak | Dijalankan oleh `gen/run_dq.py` |
| `20_promo_effect.sql` | **Resep uji promo — berstatus TEMPLATE.** Ditulis lengkap, tetapi sengaja **tidak** dipakai untuk menyimpulkan | Kejujuran yang disengaja: alatnya siap, datanya belum ada |

### 4.3 `analysis/` — meja saji (**19 CSV** + 1 HTML + **10 PNG**)

| File | Isinya | Dikutip di |
|---|---|---|
| `retention_matrix.csv` | Tabel retensi **orang** dan retensi **uang** per bulan, per kohort | Memo §2, README §2 |
| `retention_decomposition.csv` | Kebocoran dipecah: berapa karena orang pergi, berapa karena saldo menyusut | Memo §3 |
| `retention_by_channel.csv` | Sama, tetapi dipisah per kanal akuisisi (payroll, promo, referral, …) | Memo §6 |
| `pooled_curve.csv` | Kurva gabungan semua kohort menjadi satu garis | Bahan grafik g1 |
| `leak_staging.csv` | Laju kebocoran per tahap bulan | Memo §4 |
| `dormant_money.csv` | "Uang tidur": nasabah dorman vs porsi DPK-nya | Memo §5 |
| `balance_concentration.csv` | Berapa persen saldo dikuasai top 5% nasabah | Memo §5, README §5 |
| `casa_by_vintage.csv` | CASA per angkatan masuk | Memo §2 |
| `summary.json` | **5 angka kunci** dalam satu file kecil | Rujukan cepat |
| `promo_rate_realized.csv` | Tarif promo yang **benar-benar dibayar** vs yang diiklankan | Memo §7, README §8 |
| `promo_window.csv` | Saldo di dalam vs di luar jendela promo | Memo §7 |
| `rfm_scored.csv` | **24.000 baris** — satu baris per nasabah: skor R/F/M (1–5), kode RFM, dan nama segmen | Memo §11, viewer |
| `rfm_segments.csv` | **9 baris** — agregat per segmen: jumlah nasabah, % nasabah, % uang masuk, median uang masuk, saldo Juni | Memo §11 |
| `basket_categories.csv` | **7 baris** — transaksi, nasabah-bulan, volume, dan tiket rata-rata per kategori merchant | Memo §12 |
| `basket_pairs.csv` | **21 baris** — pasangan kategori yang muncul bersamaan + nilai *lift* | Memo §12 |
| `rfm_viewer.html` | **Tabel interaktif 24.000 nasabah** — cari, filter segmen, urut kolom. Buka dengan klik dua kali, tanpa Python & tanpa internet | Memo §11, §13 |
| `h3_portofolio_bulanan.csv` | Portofolio kredit 13 mitra per bulan (12 baris) | Memo §14.1 |
| `h3_ringkasan_tier.csv` | Agregat per risk tier (4 baris) | Memo §14.1 |
| `h3_ringkasan_mitra.csv` | Mitra per baris: outstanding, npl, headroom | Memo §14.1 |
| `h3_headroom_skenario.csv` | 3 skenario headroom (1,82% / 3% / 5%) | Memo §15.1 |
| `h3_headroom_alokasi.csv` | 5 strategi alokasi headroom | Memo §15.1 |
| `h3_kredit_langsung.csv` | Kredit langsung per produk (3 baris) | Memo §16 |
| `h3_kualitas_data.csv` | 4 temuan kualitas data | Memo §16 |
| `h9_npl_dilemma.png` | Ilusi rasio NPL (outstanding +45,7% vs NPL +29,1% vs rasio turun 1,90→1,69%) | Memo §14.2 |
| `g10_tier_contribution.png` | Konsentrasi risiko per tier (Tier C+D = 21,2% buku, 47,7% NPL) | Memo §14.2 |
| `g11_headroom.png` | Alokasi headroom kredit baru pada ambang 1,82% | Memo §15.1 |
| `g1…g7.png` | 7 grafik Bab 1 tetap | Tersebar di memo §2–§6 & README |

### 4.4 `lab/` — ruang percobaan (6 CSV + 1 PNG + 1 log)

| File | Bahasa awam |
|---|---|
| `exposure.csv` (24.001 baris) | **Daftar hadir kampanye.** Siapa ikut kampanye, kapan, layak atau tidak, saldo Juni berapa |
| `design_check.csv` | Cek apakah pembagian grup (band) sudah benar |
| `interest_check.csv` | Cek apakah bunga yang dibayar sesuai tarif |
| `recovery_grid.csv` | 200 percobaan estimasi (*grid*) |
| `recovery_summary.csv` | Ringkasan bias, slope, dan placebo per dunia & band — **ini yang membuktikan alatnya akurat** |
| `naive_vs_did.csv` | Perbandingan metode naif vs DiD (selisih-dalam-selisih) |
| `run.log` | Catatan apa yang terjadi saat lab dijalankan |
| `g8_recovery.png` | Gambar: estimasi vs kebenaran (garis 45°) |

### 4.5 `docs/` — papan menu (6 dokumen)

| File | Bahasa awam | Dibaca oleh |
|---|---|---|
| `00_dataset_card.md` | **Kartu identitas bahan.** Dari mana, sintetis atau asli, skala berapa, seed berapa, boleh dipakai untuk apa | Siapa pun yang mau mengutip datanya |
| `01_calibration_report.md` | **Rapor kecocokan.** Target laporan publik vs hasil dataset, selisih per metrik | Verifikator / interviewer skeptis |
| `02_bab1_memo.md` | **Memo utama.** 13 bagian: 6 temuan, BOPO, rekomendasi, batasan, lalu RFM, market basket, LTV | Interviewer (10 menit) |
| `03_kamus_istilah.md` | **Kamus bahasa awam.** CASA, LDR, NIM, BOPO, NPL, DPK tanpa jargon | Orang non-bank |
| `04_lab_h2.md` | **Laporan lab.** Apakah alat uji promo layak dipercaya — beserta vonisnya | Interviewer teknis (5 menit) |
| `05_peta_repo.md` | **Dokumen ini.** Peta seluruh isi repo | Orang baru pertama kali membuka repo |

### 4.6 Akar repo

| File | Bahasa awam |
|---|---|
| `README.md` | **Papan nama restoran.** 9 bagian: masalah bisnis → temuan → status hipotesis → peta progres → struktur → cara jalankan → batasan → batasan promo → prinsip kerja |
| `.gitignore` | **Daftar "jangan dibawa pulang".** Intinya: `data/*` dikecualikan (143 MB), kecuali `data/_calibration.json` (3 KB) |

---

## 5. Tiga aturan yang membuat repo ini layak dipercaya

**Aturan 1 — Resep disimpan, hasil tidak.**
`data/` tidak masuk git. Yang disimpan adalah `gen/generate.py` + seed `20251118`.
Artinya siapa pun bisa membangun ulang 143 MB **identik** dalam ~90 detik. Ini juga
jawaban untuk pertanyaan *"kok repo-nya cuma sekitar 1 MB?"* — karena 143 MB itu bisa
dilahirkan kembali kapan saja.

**Aturan 2 — Yang memeriksa lebih tinggi daripada yang membuat.**
`gen/verify.py` sengaja tidak memakai satu pun variabel dari `generate.py`; ia membaca
CSV mentah dan menghitung ulang. Kalau keduanya berselisih, yang dipercaya adalah
verifikator. Prinsip yang sama dipakai di lab: `h2_lab.py` membuat dua dunia yang
jawabannya sudah diketahui, lalu memeriksa apakah alat kita bisa menemukan jawaban itu.

**Aturan 3 — Angka mengalir naik, dokumen tidak pernah mengalir turun.**
`data/` → `gen/` → `analysis/` → `docs/` → `README.md`. Kalau suatu hari memo dan CSV
berbeda, CSV yang benar. Ini yang mencegah penyakit paling umum di portofolio: angka
yang "diarang" di dokumen lalu dipaksa masuk ke grafik.

---

## 6. Kalau kamu cuma punya 3 menit

Urutan baca yang disarankan:

1. **`README.md` §1** — masalah bisnisnya apa (bukan datasetnya apa)
2. **`README.md` §2** — satu tabel 5 temuan + 2 gambar
3. **`analysis/g4_dekomposisi.png`** — satu gambar yang menjelaskan seluruh Bab 1
   (dari Rp100 dana: Rp59,5 masih ada, Rp31,7 ikut nasabah pergi, Rp8,8 menguap dari saldo)
4. **`docs/02_bab1_memo.md` §10** — batasan. Ini yang membedakan analis yang matang:
   ia tahu di mana angkanya tidak boleh dipakai
5. **`docs/04_lab_h2.md` §5** — bukti bahwa ia menguji alat ukurnya sendiri

Kalau punya 10 menit, tambahkan: memo §7 (promo tidak dapat diuji), §8 (BOPO), dan
`docs/01_calibration_report.md`.

---

## 7. Cara membangun ulang seluruh rantai dari nol

```bash
# 0. Repo ini tidak memuat data. Langkah 1 wajib, bukan opsional.
# 1. Bangun ulang dataset dari seed lalu verifikasi (~90 detik)
uv run --with duckdb python gen/generate.py
uv run python gen/verify.py

# 2. Kepercayaan data: 10 uji kualitas
uv run --with duckdb python gen/run_dq.py

# 3. Bab 1: tabel + grafik
uv run --with duckdb python gen/bab1_analysis.py
uv run --with matplotlib python gen/bab1_charts.py

# 4. Uji promo (template) — bukti SQL-nya jalan
uv run --with duckdb python gen/run_promo_probe.py

# 5. Laboratorium H2 — kalibrasi alat uji (~90 detik)
uv run --with duckdb python gen/h2_lab.py
uv run --with matplotlib python gen/lab_h2_charts.py
```

Kalau setelah langkah 1–5 semua angka di `docs/` masih cocok dengan `analysis/`,
berarti rantainya utuh: tidak ada angka di dokumen yang tidak bisa dilacak ke CSV.
