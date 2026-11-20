# Memo Bab 1 — Kualitas CASA SeaBank Twin
### "Nasabahnya bertahan. Uangnya tidak."

| | |
|---|---|
| **Untuk** | Kepala Business Intelligence · Head of Retail Banking |
| **Dari** | Zainal Salim — Analytics |
| **Tanggal** | 19 November 2026 |
| **Subjek** | Retensi orang vs retensi uang pada angkatan nasabah 2025 |
| **Basis data** | `seabank_twin` — **data SINTETIS**, 24.000 nasabah, skala 1:1.000, dikalibrasi ke AR2025 |

> **Baca dulu.** Seluruh angka di memo ini berasal dari dataset sintetis yang saya bangun sendiri, bukan data SeaBank. Rasio dan arahnya dirancang menyerupai bank digital Indonesia dengan CASA 70,74%; nominal absolut hanya bermakna setelah dikali 1.000. Yang bisa dipertanggungjawabkan dari memo ini adalah **metode dan cara membacanya**, bukan klaim tentang SeaBank.

---

## Ringkasan eksekutif

1. Dari 100 nasabah yang bergabung Januari 2025, **68 orang masih bertahan** di bulan ke-12 — tetapi hanya **Rp60 dari Rp100** dana mereka yang masih ada. Selisih 8,8 poin ini adalah ukuran kerapuhan CASA yang tidak terlihat dari laporan retensi biasa.
2. **78% kebocoran uang disebabkan nasabah pergi, bukan karena saldo per nasabah menyusut.** Ini membalik hipotesis awal saya — saya perkirakan masalahnya "orang tinggal, uang pergi", dan datanya mengatakan sebaliknya.
3. Tetapi **bentuk waktunya berbeda**, dan di sinilah letak masalah sebenarnya: uang bocor paling deras di **bulan pertama** (−16,9 pp, 42% dari seluruh kebocoran setahun), sementara nasabah menguap **merata sepanjang tahun**. Dua penyakit, dua obat.
4. **Hipotesis "uang tidur" gugur.** 5.029 nasabah dorman (21%) hanya menyimpan Rp0,63 miliar — 2,17% dari DPK. Uang tidak mengendap di rekening pasif; uang itu benar-benar keluar.
5. **Kanal akuisisi tidak membedakan retensi orang (selisih cuma 3,5 pp), tapi membedakan retensi uang sebesar 15,4 pp.** Payroll paling sehat; Agent Mitra dan Promo Campaign paling bocor.

---

## 1. Cara mengukur: dua angka, bukan satu

Retensi biasa hanya menghitung orang. Saya mengukur dua hal sekaligus, dan keduanya diikat oleh satu identitas:

```
retensi uang = retensi orang  ×  saldo per nasabah (relatif)
```

Artinya, dana bisa hilang lewat dua pintu: **nasabah pergi** (pintu kiri) atau **nasabah tinggal tapi membawa uangnya keluar** (pintu kanan). Tanpa memisahkan keduanya, kedua penyakit ini terlihat sama di dashboard.

---

## 2. Temuan 1 — 68 orang, 60 rupiah

Angkatan Januari 2025 (n=600), diukur pada bulan ke-12:

| Metrik | Bulan 0 | Bulan 12 | Bocor |
|---|---:|---:|---:|
| Retensi orang | 100,0% | **68,33%** | −31,67 pp |
| Saldo per nasabah (indeks) | 100,0 | 87,11 | −12,89 |
| **Retensi uang** | 100,0% | **59,53%** | **−40,47 pp** |

Selisih 8,8 pp antara orang dan uang tampak kecil, tetapi konsekuensinya besar: nasabah yang masih bertahan pun **memegang 12,9% dana lebih sedikit** daripada saat mereka bergabung. Nasabah yang tinggal bukan nasabah yang sama dengan nasabah yang setia.

> **Peringatan interpretasi.** Payroll adalah satu-satunya kanal yang retensi uangnya (77,4%) *lebih tinggi* dari retensi orangnya (61,0%) di bulan ke-11 — artinya yang pergi justru nasabah bersaldo kecil. Di kanal itu, kehilangan nasabah tidak sama dengan kehilangan dana, dan **bonus akuisisi tidak boleh dihitung per kepala**.

---

## 3. Temuan 2 — Dari mana kebocoran itu datang

Dekomposisi eksak (komponen dijamin berjumlah tepat sama dengan total):

| Bulan ke- | Total bocor | Karena orang pergi | Karena saldo menyusut |
|---|---:|---:|---:|
| 5 | −33,54 pp | −21,33 (**63,6%**) | −12,21 (36,4%) |
| 12 | −40,47 pp | −31,67 (**78,3%**) | −8,81 (21,7%) |

**Kesimpulan yang membalik dugaan saya:** porsi "saldo menyusut" justru **mengecil** seiring waktu (36,4% → 21,7%), karena nasabah bersaldo kecil keluar lebih dulu sehingga rata-rata saldo penyintas pulih. Akar masalahnya bukan kedalaman saldo — **akar masalahnya adalah nasabah yang pergi.**

Rekomendasi yang salah kalau membaca angka ini setengah: "buat program agar saldo betah" (suku bunga khusus, cashback saldo). Obat itu menyasar 22% masalah.

---

## 4. Temuan 3 — Dua penyakit dengan bentuk waktu berbeda

Ini temuan paling operasional dari Bab 1. Kebocoran dipecah menurut tahap:

| | Bocor M0–M2 | Bocor M3–M12 | Total | Porsi di 3 bulan pertama |
|---|---:|---:|---:|---:|
| **Uang** | **25,47 pp** | 15,00 pp | 40,47 pp | **62,9%** |
| **Orang** | 13,41 pp | 18,26 pp | 31,67 pp | 42,3% |

Laju per bulan memperjelas:

| Bulan | Uang | Orang |
|---|---:|---:|
| M1 | **−16,92 pp** | −10,61 pp |
| M2 | −8,55 pp | −2,80 pp |
| M3 | −5,04 pp | −3,26 pp |

- **Bulan pertama adalah guncangan dana, bukan guncangan nasabah.** Uang turun 16,9 pp sementara orang hanya turun 10,6 pp. Pola ini khas saldo "titipan pembukaan": dana masuk untuk membuka rekening atau mengejar bonus, lalu ditarik kembali begitu syaratnya terpenuhi.
- **Setelah bulan ke-3, yang tersisa adalah erosi orang** — 18,3 pp tersebar rata 10 bulan, sementara dana hanya turun 15,0 pp.

**Implikasi:** program retensi yang dipasang di bulan ke-6 sudah terlambat untuk 63% masalah uang. Titik intervensi ada di **minggu ke-4 sampai ke-8**.

---

## 5. Temuan 4 — "Uang tidur" tidak terbukti

Saya menguji hipotesis populer: dana besar tertinggal di rekening nasabah pasif, tetap dibayar bunga 3,5%, tapi tidak produktif.

| | Nilai |
|---|---:|
| Nasabah dorman (Des 2025) | 5.029 dari 24.000 (**20,95%**) |
| Saldo yang tertinggal di rekening mereka | Rp0,629 miliar |
| Porsi terhadap total DPK | **2,17%** |

**Hipotesis ditolak.** Uang tidur bukan masalah material di buku ini. Konsekuensi: program reaktivasi bernilai rendah untuk menyelamatkan dana — nilainya ada pada **mengurangi jumlah nasabah dorman** (biaya layanan, kepatuhan, dan kanal cross-sell), bukan pada menyelamatkan rupiahnya.

> Catatan mutu data: uji T05 menemukan **15% nasabah** berstatus aktif di master tapi tidak bermutasi di ledger. Bila status master dipakai, angka dorman bisa berbeda ±15%. Angka 2,17% dihitung dari aktivitas ledger, bukan status.

---

## 6. Temuan 5 — Kanal membedakan uang, bukan orang

Pada bulan ke-5, dipecah per kanal akuisisi:

| Kanal | Retensi orang | Retensi uang | Selisih |
|---|---:|---:|---:|
| Payroll | 78,25% | **75,17%** | −3,08 pp |
| Referral | 81,00% | 69,13% | −11,87 pp |
| Organic | 78,35% | 66,00% | −12,35 pp |
| Shopee Ecosystem | 77,50% | 65,96% | −11,54 pp |
| Promo Campaign | 79,15% | 62,92% | −16,23 pp |
| Agent Mitra | 77,86% | **59,81%** | −18,05 pp |

- **Retensi orang hampir seragam:** 77,5%–81,0%, selisih hanya 3,5 pp — sebagian ada di dalam rentang galat sampling.
- **Retensi uang terbelah 15,4 pp.** Kanal yang sama-sama "berhasil" menurut KPI akuisisi punya kualitas dana yang sangat berbeda.
- **Payroll** unggul karena gaji masuk berulang — dana punya lantai struktural, tidak bergantung pada insentif.
- **Agent Mitra dan Promo Campaign** adalah kanal termahal untuk dipertahankan: nasabahnya bertahan, dananya tidak.

**Implikasi anggaran:** biaya akuisisi sebaiknya tidak dibandingkan per nasabah, tapi per **rupiah dana yang bertahan 5 bulan**. Dengan basis itu, satu nasabah Payroll setara 1,26 nasabah Agent Mitra.

---

## 7. Temuan 6 — Promo bunga 4%: **tidak dapat dijawab**, dan ini alasannya

Katalog promo mencatat kenaikan bunga tabungan 3,50% → 4,00% untuk 1 Juli–30 September 2025, lalu kembali 3,50% pada 1 Oktober.

Uji naifnya sudah saya jalankan (`gen/run_promo_probe.py`): dana akhir September **Rp26.483 miliar**, 90 hari setelah tarif kembali normal **Rp26.868 miliar** — "retensi pasca-promo" **101,45%**, nol pendarahan, bahkan tumbuh.

Angka itu nyata dan bisa diulang, tetapi **tidak membuktikan apa pun**. Tiga pemeriksaan menunjukkan mengapa.

### Bukti 1 — tarif promo tidak pernah sampai ke rekening

Kalau kampanye benar-benar berjalan, bunga yang dibayar harus naik ~14% pada Jul–Sep (4,00 / 3,50). Yang terjadi:

| Bulan | Tarif katalog | Tarif terealisasi | Selisih |
|---|---:|---:|---:|
| Jun | 3,50% | 2,48% | −1,02 pp |
| **Jul** | **4,00%** | **2,50%** | **−1,50 pp** |
| **Agu** | **4,00%** | **2,47%** | **−1,53 pp** |
| **Sep** | **4,00%** | **2,48%** | **−1,52 pp** |
| Okt | 3,50% | 2,42% | −1,08 pp |

Tarif terealisasi **datar 2,42–2,54% sepanjang 12 bulan**. Di luar jendela promo, rasio terealisasi-terhadap-katalog sangat stabil: **0,69–0,73** di setiap bulan (selisih ~1,0 pp, wajar karena pajak bunga dan saldo yang tidak penuh berbunga). Rasio itu **putus di bulan promo**: turun ke **0,62** karena tarif katalog naik sementara bunga yang benar-benar dibayar tidak bergerak. Selisih katalog-vs-realisasi melebar ≈0,5 pp selama tiga bulan — persis sebesar kenaikan yang tidak pernah dibayarkan.

**Nasabah tidak pernah menerima promo, sehingga tidak mungkin bereaksi terhadap promo.**

### Bukti 2 — tidak ada penanda siapa yang ikut kampanye

`customers.csv` punya 14 kolom — `customer_id`, `join_date`, `acquisition_channel`, `city`, `province`, `age`, `gender`, `occupation`, `monthly_income_band`, `is_first_time_bank_user`, `kyc_status`, dan seterusnya — **tidak satu pun menandai eksposur kampanye**. `promo_campaigns.csv` hanya level kampanye (4 baris: kode, tanggal, anggaran), bukan level nasabah. Tanpa grup pembanding tidak ada *treatment* dan *control*; yang ada hanya dua deret waktu.

### Bukti 3 — tidak ada patahan di Oktober

| Periode | Pertumbuhan (saldo akhir bulan) | Pertumbuhan (saldo rata-rata) |
|---|---:|---:|
| Jun → Sep (selama promo) | +8,6% | +9,1% |
| Sep → Des (setelah promo berakhir) | +9,2% | +8,1% |

Pertumbuhannya praktis sama sebelum dan sesudah jendela promo — dan **arah selisihnya berbalik** tergantung ukuran yang dipakai (akhir bulan vs rata-rata). Perbedaan sekecil itu, dengan tanda yang bisa dibalik oleh pilihan kolom, adalah tanda **tidak ada sinyal** — bukan efek yang kecil. Yang pasti: Sep→Des **tidak negatif**. Kalau dana itu "uang sewaan", ia seharusnya rontok begitu tarif kembali ke 3,50%. Saldo hanya mengikuti tren waktu — tidak ada tarif di dalam persamaannya.

### Yang hilang, dan apa artinya

Tiga hal tidak ada di dataset ini, dan tanpa ketiganya H2 tidak terdefinisi:

| # | Kebutuhan | Status |
|---|---|---|
| 1 | Tarif promo diterapkan ke `INTEREST_CREDIT` | ❌ terealisasi datar, katalog 4,00% tidak dibayar |
| 2 | Tabel eksposur level nasabah `(customer_id, campaign_id, exposure_date, eligible_flag)` | ❌ tidak ada |
| 3 | Elastisitas saldo terhadap tarif | ❌ saldo hanya fungsi waktu |

Dengan ketiganya, ujinya menjadi tiga hal yang bisa dipertanggungjawabkan: **DiD** (Δsaldo promo − Δsaldo non-promo, sebelum vs sesudah Juli), **uji cliff** (penurunan khusus grup promo pada Oktober), dan **elastisitas** (rupiah dana masuk per 1 bps kenaikan tarif).

> Hasil nol di sini adalah **konsekuensi desain, bukan temuan.** Menyimpulkan "promo tidak bekerja" dari data ini sama salahnya dengan menyimpulkan "promo bekerja" dari angka 101,45%. SQL untuk data nyata sudah siap di `sql/20_promo_effect.sql`.

**Catatan perbaikan:** tabel `promo_cliff.csv` yang sempat ada di `analysis/` sudah **dihapus**. Tabel itu menamai grup "PROMO" padahal yang dipakai adalah *kanal akuisisi* `PROMO_CAMPAIGN`, bukan eksposur tarif; dan `n`-nya menurun bukan murni karena churn melainkan karena kohort muda belum punya tenor panjang. Karena tidak layak disebut kurva retensi, ia tidak dipertahankan.

---

## 8. Rekomendasi

Diurutkan menurut rasio dampak terhadap usaha. Nominal adalah **ilustrasi setara** (×1.000), bukan proyeksi.

| # | Tindakan | Sasaran | Dampak terukur |
|---|---|---|---|
| 1 | **Perbaiki 8 minggu pertama:** transaksi wajib dalam 7 hari, setoran rutin terjadwal, cek "dana masih di sini?" pada hari ke-30 dan ke-60 | Guncangan M1 (−16,9 pp) | Tiap 1 pp retensi uang tahun-1 pada satu angkatan ≈ Rp126 miliar setara. Menutup setengah guncangan M1 ≈ **Rp1,0 triliun per angkatan** |
| 2 | **Ubah KPI akuisisi dari "jumlah nasabah" ke "dana bertahan 5 bulan"**, dan turunkan alokasi Agent Mitra/Promo kecuali kualitas dananya terbukti | Sebaran 15,4 pp antar kanal | Memindahkan 10% anggaran akuisisi ke kanal berkinerja teratas menaikkan retensi uang portofolio ~1,5 pp tanpa menambah belanja |
| 3 | **Program reaktivasi hanya untuk kepatuhan & cross-sell**, bukan penyelamatan dana | 5.029 dorman (21%) | Nilai dana yang diselamatkan kecil (2,17% DPK) — jangan alokasikan anggaran besar di sini |

**Yang saya sarankan untuk *tidak* dilakukan:** menambah anggaran akuisisi. Dengan retensi uang 59,5%, setiap Rp100 akuisisi hanya menyisakan Rp60 dana setelah setahun; menambah volume hanya memperbesar kebocoran.

---

## 9. Batasan yang harus dibaca sebelum mengutip angka ini

1. **Data sintetis.** Perilaku churn, reaktivasi, dan residual dana adalah parameter yang saya pilih sendiri (`ARCH` di `gen/generate.py`), bukan hasil estimasi dari data primer. Temuan menunjukkan **bahwa metode ini mampu mendeteksi pola tersebut** — bukan bahwa SeaBank mengalaminya.
2. **Satu sampel bibit.** Angka bulan ke-11 hanya berasal dari satu angkatan (n=600); titik lain gabungan beberapa angkatan. Perbedaan di bawah 3 pp tidak dapat ditafsirkan.
3. **Horizon hanya 12 bulan, dan tidak semua angkatan teramati penuh.** Angkatan Januari 2025 punya 12 titik; angkatan Juli 2025 baru 6 titik. Retensi tahun ke-2 dan nilai seumur nasabah belum dapat diukur sama sekali.
4. **Uji kualitas data T01, T02, T06 sengaja gagal** (duplikat, transaksi yatim, KYC ditolak namun punya akun aktif). Analisis ini berjalan di atas data yang tidak bersih — seperti di bank sungguhan.
5. **Tidak ada klaim kausal.** Semua pernyataan di memo ini adalah asosiasi dan dekomposisi aritmetika, kecuali bila disebut eksplisit.

---

## Lampiran — cara menjalankan ulang

```bash
uv run --with duckdb      python gen/bab1_analysis.py   # 10 tabel di analysis/
uv run --with matplotlib  python gen/bab1_charts.py     # 3 grafik di analysis/
```

| Berkas | Isi |
|---|---|
| `analysis/pooled_curve.csv` | kurva retensi orang & uang per bulan-ke |
| `analysis/retention_matrix.csv` | matriks retensi per kohort × tenor |
| `analysis/leak_staging.csv` | pemecahan kebocoran awal vs lanjut |
| `analysis/retention_decomposition.csv` | dekomposisi eksak orang vs saldo |
| `analysis/retention_by_channel.csv` | retensi per kanal, 12 titik |
| `analysis/dormant_money.csv` | uang tidur per kanal |
| `analysis/casa_by_vintage.csv` | DPK menurut tahun bergabung |
| `analysis/balance_concentration.csv` | pangsa saldo per desil teratas (uji hipotesis konsentrasi) |
| `analysis/promo_window.csv` | seri bulanan di sekitar jendela promo |
| `analysis/promo_rate_realized.csv` | tarif katalog vs tarif yang benar-benar dibayar, per bulan (Bukti 1 di §7) |
| `analysis/g1_kurva_retensi.png` | kurva kembar retensi orang vs uang |
| `analysis/g2_kanal.png` | retensi uang per kanal |
| `analysis/g3_orang_vs_uang.png` | selisih orang vs uang per kanal (bulan ke-5) |
| `sql/20_promo_effect.sql` | spesifikasi uji kampanye bunga (template, perlu data eksposur) |
| `gen/run_promo_probe.py` | menjalankan Q1–Q3 template itu — bukti ia dieksekusi, bukan hiasan |
