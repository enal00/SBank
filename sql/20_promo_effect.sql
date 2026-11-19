-- =====================================================================
--  20_promo_effect.sql — Uji efek kampanye bunga terhadap dana
-- =====================================================================
--  STATUS: TEMPLATE. Tidak dapat dijalankan pada `seabank_twin` karena
--  dua kolom kunci tidak ada di dataset sintetis, dan saya menolak
--  memalsukan hasilnya. Berkas ini adalah spesifikasi uji yang siap
--  dipakai begitu data nyata tersedia.
--
--  YANG KURANG DARI DATASET SAAT INI
--  1. `campaign_exposure` — tabel penanda nasabah mana yang terekspos
--     kampanye apa, sejak kapan. Tanpa ini, tidak ada kelompok pembanding:
--     semua nasabah "terekspos" kampanye bunga 4% karena kampanye itu
--     berlaku untuk seluruh basis (target_segment = 'ALL').
--  2. Variasi tarif yang cukup. Bunga tabungan hanya berubah sekali
--     (3,50% -> 4,00% -> 3,50%). Dengan satu kejadian, efek kampanye
--     tidak dapat dipisahkan dari tren musiman dan pertumbuhan basis.
--
--  DESAIN UJI YANG DIBUTUHKAN (bukan sekadar "bulan promo naik atau tidak")
--  - Kelompok perlakuan : nasabah dengan saldo > 0 sebelum 1 Jul 2025.
--  - Kelompok pembanding: nasabah baru yang bergabung SETELAH 1 Okt 2025
--    (tidak pernah merasakan tarif 4%) — memisahkan efek kampanye dari
--    efek kematangan rekening.
--  - Ukuran             : (a) pertumbuhan saldo selama jendela,
--                         (b) porsi dana yang bertahan 90 hari setelah
--                             tarif kembali normal  <- ini yang menentukan
--                             "uang sewaan" atau "uang pelanggan".
--  - Metrik kunci       : RETENSI PASCA-PROMO, bukan lonjakan saat promo.
--    Lonjakan saat promo tanpa retensi pasca-promo = biaya bunga tanpa hasil.
--
--  Dialek: BigQuery (standar). Untuk DuckDB, ganti DATE_TRUNC(x, MONTH)
--  menjadi date_trunc('month', x) dan SAFE_DIVIDE menjadi pembagian biasa.
-- =====================================================================


-- ;; ------------------------------------------------------------------
-- Q1. Jendela kampanye, diambil dari tabel tarif (bukan ditulis manual,
--     supaya kalau tarif berubah, uji ikut berubah).
-- ---------------------------------------------------------------------
WITH tarif AS (
  SELECT product_code, effective_date, end_date, rate_pa, is_promo
  FROM `seabank_twin.product_rates`
  WHERE product_code = 'SB_SAVINGS'
)
SELECT
  product_code,
  effective_date                         AS mulai,
  COALESCE(end_date, DATE '9999-12-31')  AS selesai,
  rate_pa,
  is_promo,
  DATE_DIFF(COALESCE(end_date, effective_date), effective_date, DAY) + 1 AS durasi_hari
FROM tarif
ORDER BY effective_date;


-- ;; ------------------------------------------------------------------
-- Q2. Saldo bulanan per nasabah, dirata-kan ke akhir bulan, dengan
--     penanda fase: SEBELUM / SELAMA / SESUDAH jendela promo.
--     Q2 ini yang dipakai Q3 dan Q4.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TEMP TABLE saldo_fase AS
WITH promo AS (
  SELECT MIN(effective_date) AS mulai, MAX(end_date) AS selesai
  FROM `seabank_twin.product_rates`
  WHERE product_code = 'SB_SAVINGS' AND is_promo = TRUE
),
bal AS (
  SELECT
    a.customer_id,
    DATE_TRUNC(b.month_end_date, MONTH) AS bulan,
    SUM(b.closing_balance)              AS saldo
  FROM `seabank_twin.account_monthly_balances` b
  JOIN `seabank_twin.accounts` a USING (account_id)
  WHERE a.account_type = 'SAVINGS'
  GROUP BY 1, 2
)
SELECT
  bal.customer_id,
  bal.bulan,
  bal.saldo,
  CASE
    WHEN bal.bulan <  DATE_TRUNC(promo.mulai,   MONTH) THEN 'SEBELUM'
    WHEN bal.bulan <= DATE_TRUNC(promo.selesai, MONTH) THEN 'SELAMA'
    ELSE 'SESUDAH'
  END AS fase
FROM bal CROSS JOIN promo;


-- ;; ------------------------------------------------------------------
-- Q3. Uji utama: apakah dana yang masuk saat promo BERTAHAN sesudahnya?
--     Per nasabah: saldo di akhir promo vs saldo 90 hari setelahnya.
--     retensi_pasca_promo < 100% berarti sebagian dana pergi begitu
--     tarif kembali normal  -> indikasi "uang sewaan".
-- ---------------------------------------------------------------------
WITH akhir_promo AS (
  SELECT customer_id, saldo AS saldo_akhir_promo
  FROM saldo_fase
  WHERE fase = 'SELAMA'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY bulan DESC) = 1
),
pasca AS (
  SELECT customer_id, saldo AS saldo_pasca
  FROM saldo_fase
  WHERE fase = 'SESUDAH'
  QUALIFY ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY bulan ASC) = 1
)
SELECT
  COUNT(*)                                                       AS n_nasabah,
  SUM(akhir_promo.saldo_akhir_promo) / 1e9                       AS dana_akhir_promo_miliar,
  SUM(COALESCE(pasca.saldo_pasca, 0)) / 1e9                      AS dana_pasca_miliar,
  ROUND(100.0 * SAFE_DIVIDE(SUM(COALESCE(pasca.saldo_pasca, 0)),
                            SUM(akhir_promo.saldo_akhir_promo)), 2) AS retensi_pasca_promo_pct,
  ROUND(SUM(CASE WHEN COALESCE(pasca.saldo_pasca, 0) = 0 THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 2)                                           AS pct_rekening_kosong_pasca
FROM akhir_promo
LEFT JOIN pasca USING (customer_id);


-- ;; ------------------------------------------------------------------
-- Q4. Uji pembanding: kelompok perlakuan vs kelompok tidak terekspos.
--     Butuh tabel `campaign_exposure`. Struktur minimal:
--       campaign_exposure(customer_id STRING, campaign_id STRING,
--                         exposed_at DATE)
--     Jika tabel itu belum ada, Q4 TIDAK boleh dijalankan — hasilnya
--     akan menyesatkan karena tidak ada kelompok pembanding.
-- ---------------------------------------------------------------------
-- WITH perlakuan AS (
--   SELECT customer_id, MIN(exposed_at) AS t0
--   FROM `seabank_twin.campaign_exposure`
--   WHERE campaign_id = 'CMP001'
--   GROUP BY 1
-- ),
-- pembanding AS (
--   SELECT c.customer_id
--   FROM `seabank_twin.customers` c
--   WHERE c.join_date > DATE '2025-10-01'          -- tidak pernah kena tarif 4%
--     AND c.customer_id NOT IN (SELECT customer_id FROM perlakuan)
-- )
-- SELECT 'PERLAKUAN' AS grup, ... UNION ALL
-- SELECT 'PEMBANDING' AS grup, ...
-- (bentuk lengkap menyusul setelah tabel eksposur tersedia)
