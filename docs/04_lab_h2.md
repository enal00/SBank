# Bab 1b — Laboratorium H2: apakah alat uji promo saya layak dipercaya?

> **Ini bukan klaim tentang SeaBank.** Bab ini tidak memakai data SeaBank.
> Yang diuji di sini adalah **alat ukurnya**, bukan banknya.

Di [memo Bab 1 §7](02_bab1_memo.md#7-temuan-6--promo-bunga-4-tidak-dapat-dijawab-dan-ini-alasannya) saya menulis H2 **tidak dapat diuji**, dan saya memberi tiga bukti. Yang belum saya lakukan: membuktikan bahwa kalau datanya benar, **uji saya memang bisa menemukan jawabannya**. Menolak menjawab tanpa membuktikan bahwa alatnya mampu menjawab hanyalah cara lain menghindari pekerjaan.

Jadi saya bangun dunia buatan tempat kebenarannya **saya tentukan sendiri**, lalu saya suruh alat uji menebak. Kalau tebakannya tepat, alatnya layak dipakai pada data nyata. Kalau tebakannya meleset, alatnya masih rusak — dan lebih baik saya tahu sekarang.

---

## 1. Analogi timbangan

Bayangkan Anda membeli timbangan badan, lalu menimbang barang yang **sudah Anda ketahui beratnya** — karung 10 kg dari pabrik.

- Timbangan menunjukkan **10,0 kg** → timbangan layak dipakai menimbang barang lain.
- Timbangan menunjukkan **13 kg** untuk karung 10 kg → timbangan itu tidak boleh dipakai, dan sekarang Anda tahu ke mana-mana ia melebihkan.

Inilah yang saya lakukan pada uji promo. Data sintetis = karung berlabel. Efek promo = berat yang saya tentukan sendiri. Alat uji = timbangan. Tanpa langkah ini, angka "101,45% retensi" dari template SQL punya status yang sama dengan timbangan tanpa pernah dikalibrasi: terlihat meyakinkan, tidak diketahui benar atau tidak.

---

## 2. Tiga prasyarat yang dulu tidak ada

H2 tidak dapat diuji pada dataset v1 karena tiga hal **tidak ada secara desain**, bukan karena datanya kurang panjang. Di laboratorium ini ketiganya dibangun.

| # | Syarat | Di dataset v1 | Di laboratorium |
|---|---|---|---|
| 1 | Tarif promo benar-benar dibayar ke rekening | katalog 4,00%, terealisasi datar 2,47–2,50% | bunga tiap akun-bulan = saldo × tarif katalog × **0,708** / 12 |
| 2 | Penanda siapa yang terpapar kampanye | `target_segment = 'ALL'` (level kampanye) | tabel eksposur level nasabah, **1 baris per nasabah** |
| 3 | Saldo punya mekanisme merespons tarif | tidak ada | dana luar masuk selama promo, sebagian keluar setelahnya |

**Prasyarat 1 terverifikasi di dalam simulator.** Tarif yang benar-benar dibayar selama Jul–Sep adalah **2,832%** untuk akun eligible (= 4,00% × 0,708) dan **2,478%** untuk akun kontrol (= 3,50% × 0,708). Rasio terealisasi/katalog tetap 0,708 di setiap bulan — sama seperti yang diamati pada v1. Artinya: laboratorium ini **memperbaiki cara promo dibayar**, tanpa mengubah hubungan katalog-vs-realitasi yang sudah terbukti nyata.

**Prasyarat 2 — pembagian populasi:**

| Kelompok | Nasabah | Saldo 30 Jun 2025 |
|---|---:|---:|
| eligible (saldo ≥ Rp2 juta) | 3.032 | Rp13.777 miliar |
| kontrol (saldo < Rp2 juta) | 20.968 | Rp10.605 miliar |
| mature (saldo > 0 di Jan, Apr, Jun, Sep, Des) | 17.400 | — |

Promo dibuat **bertingkat** (hanya saldo ≥ Rp2 juta yang dapat), karena desain "target semua orang" seperti katalog v1 secara matematis tidak bisa diidentifikasi: kalau semua orang dapat promo, tidak ada yang bisa dipakai sebagai pembanding.

---

## 3. Alat uji: dua band bersebelahan, bukan pencocokan 1:1

**Versi pertama saya gagal, dan kegagalannya informatif.** Saya mencocokkan tiap akun eligible dengan satu akun kontrol yang saldo Juni-nya paling mirip (toleransi 2%). Hasilnya 99 pasangan — dan **semuanya jatuh ke satu akun kontrol yang sama**, karena saldo kontrol tertinggi adalah Rp1.999.172 sedangkan treated mulai Rp2.000.000. Kelompok "kontrol" saya sebenarnya satu orang. Uji placebo langsung meledak −12,5 pp. Pelajarannya: pencocokan 1:1 pada cutoff yang padat akan menumpuk di titik terdekat, dan Anda tidak akan tahu kecuali ada uji placebo.

Versi yang dipakai sekarang: **RD dua band bersebelahan**. Kelompok kontrol = saldo Juni [c × (1−w), c), kelompok treated = [c, c × (1+w)), dengan c = Rp2 juta. Diuji pada w = 5% dan 10% (sensitivitas lebar band).

| Band | Treated | Kontrol |
|---|---:|---:|
| ±5% | 192 akun · Rp0,392 M | 174 akun · Rp0,339 M |
| ±10% | 354 akun · Rp0,741 M | 375 akun · Rp0,710 M |

Efek dihitung sebagai **DiD pada total saldo kelompok dalam log**, dikurangi jendela pra yang sama panjang; galat baku lewat bootstrap akun di dalam band (400 ulangan). Total kelompok dipakai karena saldo per nasabah di dataset ini bisa berayun 10× antar bulan — total meredam derau itu.

Jendela: **pra** Apr→Jun · **promo** Jun→Sep · **pasca** Sep→Des · **placebo** Jan–Mar vs Apr–Jun.

---

## 4. Dua dunia, satu alat

| Dunia | Isi | Untuk apa |
|---|---|---|
| **A — asumsi terpenuhi** | saldo dasar = saldo Juni × indeks agregat × heterogenitas menetap. Semua tumbuh dengan laju sama dari level masing-masing → tren sejajar | apakah alat memulihkan efek saat syaratnya terpenuhi |
| **B — apa adanya** | saldo dasar = trajektori asli dataset v1, yang sangat bergantung umur akun dan pola gaji → tren tidak sejajar | apakah alat memberi tahu saat syaratnya dilanggar |

---

## 5. Hasil

### 5.1 Uji placebo — seharusnya nol

Placebo menghitung "efek" pada periode **sebelum** promo ada. Angka yang benar adalah nol; angka besar berarti kelompok pembanding saya tidak sebanding.

| Dunia | Band | Placebo | SE | t |
|---|---:|---:|---:|---:|
| A — asumsi terpenuhi | 5% | **+0,27 pp** | 0,20 | 1,3 |
| A — asumsi terpenuhi | 10% | **+0,19 pp** | 0,16 | 1,2 |
| B — trajektori v1 | 5% | **−4,45 pp** | 4,52 | −1,0 |
| B — trajektori v1 | 10% | **−2,04 pp** | 3,54 | −0,6 |

Di dunia A placebo ≈ 0 (0,27 pp, tidak berbeda dari nol). Di dunia B placebo menyimpang 4,45 pp — **tapi SE-nya 4,52 pp**, jadi secara statistik ia hanya bisa berteriak "ada yang tidak beres", bukan membuktikannya.

### 5.2 Uji pemulihan — estimator vs kebenaran

Efek yang saya tanam: aliran dana luar sebesar f per bulan selama 3 bulan promo, lalu 45% dari dana tambahan itu keluar pada Okt/Nov/Des. Kolom "asli" = efek sesungguhnya, "est" = tebakan alat (rata-rata 10 seed).

| f/bln | Dunia | Band | Promo asli | Promo est | Bias | Pasca asli | Pasca est |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0,2% | A | 5% | 0,54 pp | 0,89 pp | +0,35 | −0,27 pp | +0,06 pp |
| 1,0% | A | 5% | 2,67 pp | 3,06 pp | +0,39 | −1,32 pp | −1,01 pp |
| 4,0% | A | 5% | 10,27 pp | 10,79 pp | +0,52 | −4,97 pp | −4,72 pp |
| 0,2% | B | 5% | 0,64 pp | 3,98 pp | **+3,35** | −0,28 pp | +2,88 pp |
| 1,0% | B | 5% | 3,15 pp | 6,41 pp | **+3,27** | −1,37 pp | +1,81 pp |
| 4,0% | B | 5% | 12,03 pp | 15,02 pp | **+3,00** | −5,10 pp | −1,86 pp |

Ringkasan seluruh grid (5 level efek × 2 dunia × 2 band × 10 seed = 200 estimasi):

| Dunia | Band | Bias rata-rata | Slope | SE | **MDE (80%)** |
|---|---:|---:|---:|---:|---:|
| A | 5% | +0,41 pp | 1,017 | 0,249 | **0,70 pp** |
| A | 10% | +0,33 pp | 1,017 | 0,192 | **0,54 pp** |
| B | 5% | +3,22 pp | 0,969 | 5,304 | **14,85 pp** |
| B | 10% | +4,13 pp | 0,979 | 3,962 | **11,09 pp** |

Tiga hal yang saya baca dari tabel ini:

1. **Slope 1,02.** Ketika efeknya saya perbesar 20× (0,54 pp → 10,27 pp), tebakan alat naik 12× lipat lebih cepat (0,89 → 10,79). Alat ini **merespons perubahan efek dengan benar** — ia bukan konstanta hiasan.
2. **Bias datar +0,3 s.d. +0,4 pp**, tidak bergantung besarnya efek. Bias datar bisa dikurangi: **kurangi angka placebo** dari estimasi. Setelah dikoreksi, bias di dunia A turun ke ≈ 0,1–0,2 pp.
3. **MDE** = efek terkecil yang masih bisa dibedakan dari derau pada 80% daya. Di dunia A, 0,54–0,70 pp per bulan. **Di dunia B, 11–15 pp per bulan** — artinya pada data yang berperilaku seperti v1, efek promo yang realistis (1–4 pp) **tidak akan terdeteksi, bahkan kalau benar-benar ada**. Alat yang sama, data yang berbeda, kegunaan yang berbeda jauh.

### 5.3 Metrik naif vs DiD

| f/bln | Retensi naif Sep→Des | Des/Jun | DiD net |
|---:|---:|---:|---:|
| 1,0% | 107,8% | 120,2% | +1,56 pp |
| 4,0% | 103,9% | 125,1% | +5,52 pp |

Kolom pertama adalah metrik yang dipakai template uji H2 versi awal. Pada f = 4% — kasus paling ekstrem — metrik naif melaporkan **retensi 103,9%**: "tidak ada yang pergi, malah bertambah". Padahal pada saat yang sama 45% dana tambahan sudah keluar. Metrik naif tidak salah hitung; ia **tidak bisa membedakan pertumbuhan organik dari dana panas**, karena penyebutnya ikut membesar oleh dana yang akan pergi. DiD memisahkan keduanya: +5,52 pp yang bertahan, sisanya pergi.

---

## 6. Vonis

**Alatnya layak dipakai — dengan dua syarat yang harus ditulis di laporan.**

1. **Selalu laporkan placebo dan MDE, bukan hanya estimasi.** Tanpa placebo, bias +0,41 pp tidak terlihat. Tanpa MDE, angka "efek +2,1 pp" pada data volatil akan dibaca sebagai temuan padahal masih di dalam derau.
2. **Koreksi bias dengan placebo.** Estimasi bersih = estimasi − placebo. Di dunia A langkah ini memotong bias dari +0,41 menjadi ≈ +0,15 pp.

**Dan satu syarat yang harus dipenuhi SeaBank sebelum H2 bisa dijawab:**

| Yang dibutuhkan | Status di dataset v1 |
|---|---|
| tarif promo benar-benar dibayar ke rekening (bukan hanya di katalog) | **tidak ada** — terealisasi datar 2,47–2,50% |
| tabel eksposur level nasabah (siapa, kapan, campaign apa) | **tidak ada** — hanya `target_segment = 'ALL'` |
| stok dana yang bisa dilacak masuk dan keluar setelah promo | **tidak ada** — saldo tidak punya mekanisme merespons tarif |

Tanpa ketiganya, jawaban yang jujur atas H2 tetap **"tidak dapat diuji"**, dan itu bukan kekurangan analisis — itu temuan tentang data. Yang berubah setelah bab ini: saya sekarang bisa menunjukkan **berapa besar tenaga** yang dibutuhkan untuk mendeteksi efek itu (0,5–0,7 pp/bulan pada data bersih, 11–15 pp/bulan pada data seperti v1), bukan sekadar mengatakan "datanya kurang".

---

## 7. Batasan bab ini

1. **Semua angka di sini sintetis dan parametrik.** Kebenaran "asli" ditentukan oleh rumus saya (`bangun`), bukan oleh perilaku nasabah sungguhan.
2. **Bentuk responsnya saya pilih, tidak diestimasi.** Aliran masuk linear, 45% keluar dengan pola 60/25/15. Bank sungguhan bisa memberi pola lain — yang diuji adalah kemampuan alat mendeteksi, bukan bentuk kurvanya.
3. **Hanya satu cutoff (Rp2 juta) dan satu kampanye.** Ambang lain akan mengubah jumlah akun per band, dan itu mengubah MDE.
4. **Dunia A masih menyisakan bias +0,3 pp.** Penyebabnya pemilihan kelompok memakai saldo Juni yang juga jadi basis pertumbuhan (mean reversion). Saya laporkan apa adanya, bukan dihilangkan dengan penyesuaian yang tidak bisa dipertanggungjawabkan.
5. **Uji placebo di dunia B tidak cukup kuat untuk menjadi alarm.** |t| = 1,0. Ini pelajaran tersendiri: pada data bervolatilitas tinggi, diagnosis terbaik pun bisa bisu.

---

## 8. Cara menjalankan & artefak

```bash
uv run --with duckdb --with numpy python gen/h2_lab.py    # ~90 detik
```

| Berkas | Isi |
|---|---|
| `lab/exposure.csv` | tabel eksposur level nasabah (24.000 baris) — prasyarat 2 |
| `lab/interest_check.csv` | tarif katalog vs tarif dibayar per bulan, eligible & kontrol — prasyarat 1 |
| `lab/design_check.csv` | uji placebo 2 dunia × 2 band |
| `lab/recovery_grid.csv` | 200 estimasi mentah (5 level efek × 2 dunia × 2 band × 10 seed) |
| `lab/recovery_summary.csv` | ringkasan: bias, SD antar-seed, SE bootstrap |
| `lab/naive_vs_did.csv` | perbandingan metrik naif vs DiD |
| `lab/run.log` | keluaran lengkap apa adanya |
