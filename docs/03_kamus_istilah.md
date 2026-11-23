# Kamus Istilah Perbankan

Term di bawah ini muncul di seluruh portofolio ini. Dibuat sederhana (bukan definisi resmi bank sentral) agar mudah dipahami saat diskusi bisnis.

| Istilah | Kepanjangan / Istilah Resmi | Pengertian Sederhana | Mengapa Penting di Portofolio Ini |
|---|---|---|---|
| **CASA** | *Current Account & Savings Account* | Dana murah (rekening giro & tabungan). Bunga rendah, tetapi dananya **paling "lengket"** dan mudah dipakai bertransaksi harian. | **Bab 1:** Retensi CASA ternyata rapuh (59,53% di akhir tahun). Ini basis alokasi DPK berikutnya. |
| **LDR** | *Loan to Deposit Ratio* | Persentase DPK yang diputar menjadi kredit. Formula: $\text{Kredit} / \text{DPK}$. | **2025:** LDR SeaBank **92,32%** — artinya dana nyaris seluruhnya sudah diputar sebagai kredit. |
| **NIM** | *Net Interest Margin* | Pendapatan bunga bersih dibagi rata-rata aktiva produktif. Sederhananya: "margin keuntungan bunga bank". | **21,45%** (sangat tinggi untuk ukuran bank). Margin ini harus dijaga tanpa menaikkan NPL. |
| **BOPO** | *Biaya Operasional vs Pendapatan Operasional* | Rasio efisiensi biaya. Formula: biaya operasional dibagi pendapatan operasional. **Semakin kecil %, semakin efisien.** 100% = laba operasional nol; di atas 100% = rugi operasional. | **91,47%** (publik 2025). Peringkat 2 dari 5 pada matriks komponen rentabilitas (Lampiran 6 SE BI 13/24/DPNP/2011) — bukan "sudah sangat efisien". Margin laba operasional tinggal 8,53%, jadi tiap 1 pp BOPO yang dipotong menaikkan laba operasional ~11,7%. Ruang perbaikannya masih besar. |
| **NPL** | *Non-Performing Loan* | Persentase kredit macet (tunggakan >90 hari). | **1,82%** (publik 2025). Portofolio menjaga kredit baru agar NPL tidak melonjak di atas batas toleransi. |
| **DPK** | *Dana Pihak Ketiga* | Total simpanan masyarakat (Tabungan + Deposito + Giro). | Rp34,8 triliun (publik 2025); pada dataset sintetis skala 1:1.000 menjadi **Rp34,8 miliar**. |
| **Retensi** | *Retention Rate* | Daya tahan orang/uang di bank dari waktu ke waktu. | **Temuan Kunci Bab 1:** Retensi orang (**68,33%**) ≠ retensi uang (**59,53%**). Bocornya di uang, bukan di nasabah. |
| **Kohort** | *Cohort Analysis* | Kelompok nasabah yang bergabung di periode yang sama (misal: angkatan Jan 2025). | Perilaku retensi diukur per angkatan agar tidak terdistorsi oleh nasabah baru yang terus masuk. |
| **Dorman** | *Dormant Account* | Rekening pasif tanpa transaksi dalam jangka waktu tertentu. | **Hipotesis Gugur:** 20,95% dorman hanya menyimpan **2,17% DPK**. Dana tidak "tidur" di bank, dananya sudah keluar. |
| **Promo** | *Promotional Yield / Rate* | Kampanye imbal hasil khusus untuk menarik DPK baru. | **Spesifikasi SQL (`20_promo_effect.sql`):** Tempat menguji apakah promo menciptakan *money migration* atau dana bertahan. |
| **RFM** | *Recency, Frequency, Monetary* | Tiga pertanyaan tentang satu nasabah: kapan terakhir bertransaksi (R), seberapa sering (F), seberapa besar (M). Tiap jawaban diberi skor 1–5. | **Bab 2:** dasar pembentukan 9 segmen. Skor 5 = 20% teratas, sehingga sebaran selalu 20/20/20/20/20 dan tahan outlier. |
| **Juara** | *Champions* (segmen RFM) | Nasabah yang baru bertransaksi, sering, dan besar (R≥4, F≥4, M≥4). | **4.725 orang (19,7%)** menyumbang **42,1% uang masuk** dan memegang **43,4% DPK** (Rp10,58 miliar). |
| **Tidak boleh hilang** | *Can't Lose Them* (segmen RFM) | Dulu sering dan besar, sekarang mulai jarang (R≤2, F≥4, M≥4). | Hanya **167 orang (0,7%)**, tetapi median uang masuknya **Rp15,9 juta** — nilai per kepala tertinggi kedua setelah Juara. |
| **Lift** | *Association Lift* | Seberapa lebih sering dua kategori muncul bersamaan dibanding kalau keduanya benar-benar acak. 1,00 = tidak ada hubungan; di bawah 1,2 umumnya belum layak jadi dasar bundel. | **Bab 2:** seluruh 21 pasangan berada di **1,00–1,07** — tidak ada asosiasi yang bisa dipakai. |
| **Keranjang belanja** | *Market Basket Analysis* | Teknik mencari "barang yang sering dibeli bersamaan" untuk menyusun bundel atau cross-sell. | **Bab 2: vonis TIDAK DAPAT DISIMPULKAN.** Kategori merchant diundi acak oleh generator (tiket rata-rata nyaris identik Rp437–558 ribu), jadi tidak ada pola yang bisa ditemukan. |
| **LTV** | *Lifetime Value* | Perkiraan total nilai uang yang dibawa satu nasabah selama menjadi pelanggan. | **Bab 2 (estimasi 12 bulan):** eligible **Rp18,5 miliar** vs kontrol **Rp4,2 miliar**. Estimasi ini belum memasukkan bunga & kredit, jadi absolutnya perkiraan. |
| **Eligible promo** | *Promo Eligibility* | Penanda apakah nasabah memenuhi syarat ikut kampanye — di sini: saldo ≥ Rp2 juta. | **3.032 orang (12,6%)** memegang **56,5% DPK**; **1.579** di antaranya juga masuk segmen Juara (Rp7,01 miliar / 28,7% DPK). |

> **Catatan Pembaca:** Data di portofolio ini adalah **SINTETIS (skala 1:1.000)** yang dikalibrasi ke laporan tahunan publik FY2025. Istilah di atas digunakan untuk menyusun argumen bisnis perbankan yang riil.
