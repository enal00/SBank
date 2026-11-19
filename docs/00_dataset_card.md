# Kartu Dataset — SeaBank Digital Twin v1.1

## 1. Status dan peringatan

| Atribut | Nilai |
|---|---|
| Nama | SeaBank Digital Twin v1.1 |
| Jenis | **Data sintetis** — dibangkitkan secara programatis |
| Cakupan | 1 Januari – 31 Desember 2025 (riwayat akuisisi sejak 2019) |
| Skala | **1 : 1.000** terhadap bank sebenarnya |
| Seed | 20251118 (deterministik, dapat direproduksi) |
| Lisensi | Karya sendiri untuk portofolio; bebas dipakai ulang dengan atribusi |
| Data pribadi | **Tidak ada.** Semua nama, nomor, dan identitas fiktif |

**Dataset ini bukan data SeaBank.** Tidak ada satu baris pun yang berasal dari
sistem internal SeaBank, mitra, atau nasabah. Yang diambil dari dunia nyata hanya
**angka rasio publik** dan **struktur produk** — keduanya tersedia di laporan
tahunan dan situs resmi.

## 2. Cara membaca angka — arti kata "setara"

Ini bagian yang paling sering disalahbaca, jadi ditaruh paling depan.

Bank sebenarnya punya **±24 juta nasabah**. Dataset ini punya **24.000**. Kita
memakai **skala 1 : 1.000** karena 24 juta nasabah × 12 bulan = 288 juta baris
saldo — terlalu berat untuk dikomputasi tanpa menambah wawasan apa pun.

Aturannya cuma satu:

> **Angka absolut di dataset × 1.000 = nilai sesungguhnya di bank nyata.**
> **Angka persentase tidak berubah** — pembilang dan penyebut sama-sama dibagi
> 1.000, jadi rasionya identik.

| Yang tertulis di dataset | Setara di bank nyata |
|---|---:|
| 24.000 nasabah | 24.000.000 nasabah |
| 600 nasabah baru/bulan (2025) | 600.000 nasabah baru/bulan |
| 7.200 nasabah baru sepanjang 2025 | 7.200.000 |
| 16.800 nasabah awal 2025 | 16.800.000 |
| DPK Rp34,8 miliar | Rp34,8 triliun |
| CASA **70,74%** | CASA **70,74%** (sama, tidak dikali) |

**Dasar angka 600.000/bulan** — Laporan Tahunan SeaBank 2025 hlm. 35:
*"...dengan akuisisi rata-rata 600.000 nasabah baru setiap bulan, sehingga total
pengguna mencapai sekitar 24 juta nasabah pada akhir tahun 2025."*

Aritmetika silang: 600.000 × 12 = 7.200.000 nasabah baru → basis awal 2025
= 24.000.000 − 7.200.000 = **16.800.000**, yaitu 16.800 × 1.000 di dataset.

Konsekuensi praktis: **aman** menyimpulkan *"CASA terlalu rapuh"*; **tidak aman**
menyimpulkan *"kerugian Rp34,8 miliar"* tanpa dikali 1.000 lebih dulu.

## 3. Sumber lapis nyata (L1)

| Sumber | Dipakai untuk |
|---|---|
| Laporan Tahunan SeaBank 2025 | DPK, kredit, CASA, LDR, NPL, NIM, BOPO, CAR, laba, total aset |
| AR2025 hlm. 35 | Laju akuisisi 600.000 nasabah baru/bulan; total ±24 juta nasabah |
| Komposisi kredit AR2025 | Joint financing Rp25.913 M · Channeling Rp3.533 M · Langsung Rp2.653 M · Legacy Rp35 M |
| Situs resmi SeaBank | Suku bunga tabungan 3,50%; deposito 4,25/5,25/5,75/6,00% untuk 1/3/6/12 bulan |
| Publikasi industri (Dataindonesia, 17 Nov 2026) | Bench-marking 14 bank digital: kredit Rp171,89 T · DPK Rp207,81 T · LDR 82,71% |

## 4. Apa yang dikalibrasi dan apa yang tidak

**Dikalibrasi (dipaksa cocok persis):**
- Total DPK, total kredit, saldo tabungan (CASA), saldo deposito aktif
- Rasio CASA 70,74%, LDR 92,32%, NPL gross 1,82%
- Komposisi buku kredit per skema (joint financing / channeling / langsung / legacy)
- Jumlah nasabah 24.000 dan laju akuisisi 600/bulan pada 2025

**Tidak dikalibrasi (muncul dari proses generatif — ini bahan temuan):**
- Retensi kohort per bulan akuisisi
- Konsentrasi saldo (pangsa top 1/5/10/20%)
- Tingkat dormansi dan saldo dorman
- Distribusi NPL antar mitra dan dinamika bulanannya
- Elastisitas saldo terhadap perubahan suku bunga promo

Konsekuensinya penting: **temuan tentang retensi dan konsentrasi bukan asumsi yang
saya tanam**, melainkan hasil dari aturan perilaku sederhana yang dijalankan
konsisten. Aturan itu didokumentasikan di `gen/generate.py` bagian `ARCH` dan
bisa diperdebatkan secara terbuka.

## 5. Kurva akuisisi historis

Versi awal menyebar basis lama secara rata 2019–2024 sehingga menghasilkan kurva
**datar ±233 nasabah/bulan selama enam tahun** lalu melompat ke 600. Itu tidak wajar
dan akan langsung dipersoalkan pada analisis kohort.

Versi 1.1 memakai kurva yang mengikuti sejarah perusahaan: kecil pra-akuisisi,
berbelok saat rebranding SeaBank, lalu menanjak bersama ekosistem.

| Tahun | Nasabah baru/bulan (dataset) | Setara bank nyata | Alasan |
|---|---:|---:|---|
| 2019 | 10 | 10.000 | bank kecil pra-akuisisi |
| 2020 | 25 | 25.000 | awal integrasi |
| 2021 | 150 | 150.000 | **titik belok** — rebranding SeaBank |
| 2022 | 300 | 300.000 | ekspansi ekosistem |
| 2023 | 400 | 400.000 | |
| 2024 | 515 | 515.000 | |
| 2025 | 600 | 600.000 | sesuai AR2025 ✓ |

Total 2019–2024 tetap **16.800** dan 2025 tetap **7.200** — jadi seluruh rasio
(CASA, LDR, NPL) tidak bergeser. Yang berubah hanya *bentuk* pertumbuhannya.

## 6. Skema tabel

| Tabel | Baris | Isi |
|---|---|---|
| `customers` | 24.000 | Master nasabah: tanggal gabung, kanal akuisisi, demografi, KYC |
| `accounts` | 27.600 | 24.000 tabungan + 3.600 deposito |
| `transactions` | 1.379.585 | Ledger transaksi (kredit, debit, bunga, QRIS, ATM, deposito) |
| `account_monthly_balances` | 288.000 | Saldo akhir bulan per akun (24.000 × 12) |
| `loan_partners` | 13 | Mitra pembiayaan + portofolio legacy |
| `partner_monthly_performance` | 156 | Outstanding, NPL, DPD per mitra per bulan |
| `direct_loans` | 2.000 | Pinjaman langsung ke nasabah (Pinjam/Payroll/KTA) |
| `product_rates` | 7 | Riwayat suku bunga produk |
| `promo_campaigns` | 4 | Kampanye promo (bunga, cashback, referral) |
| `ref_industry_benchmark` | 13 | Jangkar eksternal: rasio SeaBank & industri |

## 7. Cacat data yang sengaja ditanam

Bank sungguhan tidak pernah punya data bersih. Tiga cacat ditanam agar pipeline
wajib menanganinya — sekaligus agar analis yang mengklaim "data saya bersih 100%"
langsung ketahuan belum memeriksa.

| Cacat | Jumlah | Dampak jika diabaikan |
|---|---:|---|
| `transaction_id` duplikat | 4.735 (0,34%) | `SUM(amount)` overstate |
| Transaksi dengan `account_id` tak dikenal | 3.464 (0,25%) | total mutasi tak rekonsiliasi dengan DPK |
| Nasabah KYC REJECTED masih pegang akun aktif | 13 | eksposur kepatuhan |

Uji lengkap ada di `sql/10_dq_tests.sql`, dijalankan lewat `gen/run_dq.py`.

## 8. Batasan yang harus diakui di depan pewawancara

1. **Distribusi tidak nyata.** Bentuk sebaran saldo mengikuti lognormal dengan
   parameter pilihan sendiri (`sigma` 0,45–1,25 per arketipe). Bank sungguhan punya
   ekor yang lebih berat dan segmentasi komersial yang tidak dimodelkan.
2. **Tidak ada giro.** SeaBank ritel praktis hanya tabungan; giro korporat diabaikan
   dan dilipat ke tabungan. CASA karena itu sedikit di atas kenyataan.
3. **Buku kredit disederhanakan.** Pencatatan joint financing sebenarnya
   *on-balance sheet* sebagian dan *off-balance* sebagian; di sini seluruhnya
   diperlakukan on-balance mengikuti angka AR.
4. **Tidak ada makro.** Tidak ada guncangan suku bunga BI, resesi, atau kompetisi
   harga antarbank. Perilaku hanya bereaksi terhadap promo internal.
5. **Nasabah tidak pernah mati.** Tidak ada penutupan akun permanen; hanya dormansi.
6. **NPL tidak *vintage*-murni.** Deteriorasi NPL dimodelkan sebagai fungsi laju
   pertumbuhan buku, bukan kohort pencairan sesungguhnya.
7. **Kurva akuisisi 2019–2024 adalah rekonstruksi, bukan angka resmi per tahun.**
   AR2025 hanya menyebut rata-rata 600.000/bulan untuk 2025. Bentuk kurva tahun-tahun
   sebelumnya adalah inferensi dari sejarah perusahaan, bukan kutipan laporan.

## 9. Etika dan penggunaan

- **Jangan** menyebut dataset ini sebagai data SeaBank dalam lamaran, wawancara,
  atau publikasi. Sebut sebagai **"model tiruan terkalibrasi"** — itu justru
  menunjukkan kemampuan yang lebih tinggi: mampu membangun dunia yang konsisten
  dengan angka publik, bukan sekadar mengunduh CSV.
- **Jangan** memakai nama mitra di dataset ini untuk menuduh perusahaan nyata.
  Semua nama mitra memakai alfabet NATO (Multifinance Alfa, P2P Foxtrot, dst.)
  justru agar jelas fiktif.
- Cara menyebutkan yang benar di CV:

  > "Membangun *digital twin* data bank (24.000 nasabah / setara 24 juta,
  > 1,38 juta transaksi) terkalibrasi ke rasio publik SeaBank FY2025 hingga
  > selisih <0,01%, untuk menguji hipotesis kualitas pertumbuhan DPK dan risiko
  > kredit mitra."
