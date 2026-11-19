-- ============================================================================
-- 10_dq_tests.sql — Lapisan Kepercayaan (Bab 0)
-- Dialek: DuckDB (dijalankan lokal terhadap CSV di ../data)
-- Untuk BigQuery: ganti blok `WITH src AS (SELECT * FROM read_csv_auto(...))`
--                 dengan nama tabel `seabank_twin.<tabel>`; sisanya identik.
-- Setiap uji mengembalikan: kode, nama_uji, nilai, harapan, vonis
-- ============================================================================

-- ---------------------------------------------------------------------------
-- T01. Duplikat primary key transaksi
--      Kalau ledger punya transaction_id ganda, SUM(amount) akan overstate.
-- ---------------------------------------------------------------------------
SELECT 'T01' AS kode,
       'Duplikat transaction_id' AS uji,
       (SELECT count(*) - count(DISTINCT transaction_id) FROM txn) AS nilai,
       0 AS harapan,
       CASE WHEN (SELECT count(*) - count(DISTINCT transaction_id) FROM txn) = 0
            THEN 'LULUS' ELSE 'GAGAL' END AS vonis
-- ;;
-- ---------------------------------------------------------------------------
-- T02. Transaksi yatim: account_id tidak ada di master akun
--      Ini yang membuat total DPK tidak pernah rekonsiliasi dengan ledger.
-- ---------------------------------------------------------------------------
SELECT 'T02' AS kode,
       'Transaksi yatim (orphan account)' AS uji,
       (SELECT count(*) FROM txn t
        LEFT JOIN acc a USING (account_id)
        WHERE a.account_id IS NULL) AS nilai,
       0 AS harapan,
       CASE WHEN (SELECT count(*) FROM txn t
                  LEFT JOIN acc a USING (account_id)
                  WHERE a.account_id IS NULL) = 0
            THEN 'LULUS' ELSE 'GAGAL' END AS vonis
-- ;;
-- ---------------------------------------------------------------------------
-- T03. Rantai saldo: opening + kredit - debit harus = closing
--      Uji paling keras. Kalau ini gagal, semua analisis kohort tidak sah.
-- ---------------------------------------------------------------------------
SELECT 'T03' AS kode,
       'Rantai saldo akun-bulan' AS uji,
       (SELECT count(*) FROM bal
        WHERE abs(opening_balance + total_credit - total_debit - closing_balance) > 1) AS nilai,
       0 AS harapan,
       CASE WHEN (SELECT count(*) FROM bal
                  WHERE abs(opening_balance + total_credit - total_debit - closing_balance) > 1) = 0
            THEN 'LULUS' ELSE 'GAGAL' END AS vonis
-- ;;
-- ---------------------------------------------------------------------------
-- T04. Snapshot vs ledger: jumlah transaksi harus sama di dua sumber
--      Ketidakcocokan di sini = dua sumber kebenaran yang berbeda.
-- ---------------------------------------------------------------------------
SELECT 'T04' AS kode,
       'Snapshot vs ledger (txn_count)' AS uji,
       (SELECT count(*) FROM bal b
        LEFT JOIN (SELECT account_id,
                          date_trunc('month', txn_date) AS m,
                          count(*) AS n
                   FROM txn GROUP BY 1, 2) t
          ON b.account_id = t.account_id
         AND t.m = date_trunc('month', b.month_end_date)
        WHERE coalesce(t.n, 0) <> b.txn_count) AS nilai,
       0 AS harapan,
       'SELIDIKI' AS vonis
-- ;;
-- ---------------------------------------------------------------------------
-- T05. Dua definisi "nasabah aktif"
--      Field master last_txn_date tertinggal dari ledger. Kalau analis memakai
--      field master, jumlah nasabah aktif akan understated.
-- ---------------------------------------------------------------------------
WITH aktual AS (
    SELECT customer_id, max(txn_date) AS txn_terakhir
    FROM txn GROUP BY 1
)
SELECT 'T05' AS kode,
       'Nasabah aktif: master vs ledger' AS uji,
       (SELECT count(*) FROM cust c
        JOIN aktual a USING (customer_id)
        WHERE c.last_txn_date_master < a.txn_terakhir - INTERVAL 30 DAY) AS nilai,
       0 AS harapan,
       'SELIDIKI' AS vonis
-- ;;
-- ---------------------------------------------------------------------------
-- T06. KYC ditolak tapi masih pegang akun aktif (risiko kepatuhan)
-- ---------------------------------------------------------------------------
SELECT 'T06' AS kode,
       'KYC REJECTED dengan akun aktif' AS uji,
       (SELECT count(*) FROM cust c
        JOIN acc a USING (customer_id)
        WHERE c.kyc_status = 'REJECTED' AND a.status = 'ACTIVE') AS nilai,
       0 AS harapan,
       CASE WHEN (SELECT count(*) FROM cust c
                  JOIN acc a USING (customer_id)
                  WHERE c.kyc_status = 'REJECTED' AND a.status = 'ACTIVE') = 0
            THEN 'LULUS' ELSE 'GAGAL' END AS vonis
-- ;;
-- ---------------------------------------------------------------------------
-- T07. Deposito dengan tanggal jatuh tempo sebelum tanggal buka (mustahil)
-- ---------------------------------------------------------------------------
SELECT 'T07' AS kode,
       'Deposito jatuh tempo < buka' AS uji,
       (SELECT count(*) FROM acc
        WHERE account_type = 'DEPOSITO' AND close_date IS NOT NULL
          AND close_date < open_date) AS nilai,
       0 AS harapan,
       'LULUS' AS vonis
-- ;;
-- ---------------------------------------------------------------------------
-- T08. Pinjaman yatim: customer_id tidak dikenal
-- ---------------------------------------------------------------------------
SELECT 'T08' AS kode,
       'Pinjaman yatim (orphan customer)' AS uji,
       (SELECT count(*) FROM loans l
        LEFT JOIN cust c USING (customer_id)
        WHERE c.customer_id IS NULL) AS nilai,
       0 AS harapan,
       CASE WHEN (SELECT count(*) FROM loans l
                  LEFT JOIN cust c USING (customer_id)
                  WHERE c.customer_id IS NULL) = 0
            THEN 'LULUS' ELSE 'GAGAL' END AS vonis
-- ;;
-- ---------------------------------------------------------------------------
-- T09. Kelengkapan snapshot: setiap bulan harus punya 24.000 akun tabungan
-- ---------------------------------------------------------------------------
SELECT 'T09' AS kode,
       'Bulan dengan snapshot tidak lengkap' AS uji,
       (SELECT count(*) FROM (
            SELECT month_end_date, count(*) AS n
            FROM bal GROUP BY 1 HAVING count(*) <> 24000)) AS nilai,
       0 AS harapan,
       CASE WHEN (SELECT count(*) FROM (
                      SELECT month_end_date FROM bal GROUP BY 1 HAVING count(*) <> 24000)) = 0
            THEN 'LULUS' ELSE 'GAGAL' END AS vonis
-- ;;
-- ---------------------------------------------------------------------------
-- T10. Rekonsiliasi rasio: hitung ulang CASA / LDR / NPL dari tabel mentah
--      dan bandingkan dengan angka publik. Toleransi 0,05 pp.
-- ---------------------------------------------------------------------------
WITH casa AS (
    SELECT sum(closing_balance) / 12.0 AS v
    FROM bal b JOIN acc a USING (account_id)
    WHERE a.account_type = 'SAVINGS'
),
depo AS (
    SELECT sum(principal) AS v FROM acc
    WHERE account_type = 'DEPOSITO' AND status = 'ACTIVE'
),
kredit AS (
    SELECT (SELECT sum(outstanding_balance) FROM perf
            WHERE date_trunc('month', month) = DATE '2025-12-01')
         + (SELECT sum(outstanding) FROM loans) AS v,
           (SELECT sum(npl_balance) FROM perf
            WHERE date_trunc('month', month) = DATE '2025-12-01')
         + (SELECT sum(outstanding) FROM loans WHERE dpd > 90) AS npl
)
SELECT 'T10' AS kode,
       'Rekonsiliasi rasio ke AR2025' AS uji,
       round(((SELECT v FROM casa) / ((SELECT v FROM casa) + (SELECT v FROM depo))) * 100, 2) AS casa_pct,
       round(((SELECT v FROM kredit) / ((SELECT v FROM casa) + (SELECT v FROM depo))) * 100, 2) AS ldr_pct,
       round(((SELECT npl FROM kredit) / (SELECT v FROM kredit)) * 100, 2) AS npl_pct
-- ;;
