#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Uji logika 20_promo_effect.sql (Q1-Q3) pada dataset sintetis, dialek DuckDB.
Tujuan: membuktikan template SQL-nya benar-benar jalan, bukan hiasan.
Hasil TIDAK boleh ditafsirkan sebagai efek kausal promo (lihat header .sql).
Jalankan: uv run --with duckdb python gen/run_promo_probe.py
"""
import duckdb

con = duckdb.connect()
con.execute("CREATE VIEW acc AS SELECT * FROM read_csv_auto('data/accounts.csv', header=true)")
con.execute("CREATE VIEW bal AS SELECT * FROM read_csv_auto('data/account_monthly_balances.csv', header=true)")
con.execute("CREATE VIEW rates AS SELECT * FROM read_csv_auto('data/product_rates.csv', header=true)")

# Q1 — jendela kampanye dibaca dari tabel tarif, bukan ditulis manual
q1 = """
SELECT product_code, CAST(effective_date AS DATE) mulai,
       COALESCE(CAST(end_date AS DATE), DATE '9999-12-31') selesai,
       rate_pa, is_promo,
       date_diff('day', CAST(effective_date AS DATE),
                 COALESCE(CAST(end_date AS DATE), CAST(effective_date AS DATE))) + 1 durasi_hari
FROM rates
WHERE product_code = 'SB_SAVINGS'
ORDER BY effective_date
"""
print("Q1 — jendela tarif:")
for r in con.execute(q1).fetchall():
    print("   ", r)

# Q2 — saldo bulanan per nasabah + fase
q2 = """
CREATE OR REPLACE TEMP TABLE saldo_fase AS
WITH promo AS (
  SELECT min(CAST(effective_date AS DATE)) mulai, max(CAST(end_date AS DATE)) selesai
  FROM rates WHERE product_code = 'SB_SAVINGS' AND is_promo = true
),
b AS (
  SELECT a.customer_id, date_trunc('month', CAST(b.month_end_date AS DATE)) bulan,
         sum(b.closing_balance) saldo
  FROM bal b JOIN acc a USING (account_id)
  WHERE a.account_type = 'SAVINGS'
  GROUP BY 1, 2
)
SELECT b.customer_id, b.bulan, b.saldo,
       CASE WHEN b.bulan <  date_trunc('month', promo.mulai)  THEN 'SEBELUM'
            WHEN b.bulan <= date_trunc('month', promo.selesai) THEN 'SELAMA'
            ELSE 'SESUDAH' END fase
FROM b CROSS JOIN promo
"""
con.execute(q2)
print("\nQ2 — baris saldo_fase:",
      con.execute("SELECT count(*), count(DISTINCT customer_id) FROM saldo_fase").fetchone())

# Q3 — apakah dana yang masuk saat promo bertahan sesudahnya?
q3 = """
WITH akhir_promo AS (
  SELECT customer_id, saldo AS saldo_akhir_promo
  FROM saldo_fase WHERE fase = 'SELAMA'
  QUALIFY row_number() OVER (PARTITION BY customer_id ORDER BY bulan DESC) = 1
),
pasca AS (
  SELECT customer_id, saldo AS saldo_pasca
  FROM saldo_fase WHERE fase = 'SESUDAH'
  QUALIFY row_number() OVER (PARTITION BY customer_id ORDER BY bulan ASC) = 1
)
SELECT count(*) n_nasabah,
       round(sum(akhir_promo.saldo_akhir_promo)/1e9, 3) dana_akhir_promo_miliar,
       round(sum(coalesce(pasca.saldo_pasca,0))/1e9, 3) dana_pasca_miliar,
       round(100.0 * sum(coalesce(pasca.saldo_pasca,0))
             / nullif(sum(akhir_promo.saldo_akhir_promo),0), 2) retensi_pasca_promo_pct,
       round(100.0 * sum(CASE WHEN coalesce(pasca.saldo_pasca,0) = 0 THEN 1 ELSE 0 END)
             / count(*), 2) pct_rekening_kosong_pasca
FROM akhir_promo LEFT JOIN pasca USING (customer_id)
"""
r = con.execute(q3).fetchone()
print("\nQ3 — retensi pasca-promo (DESKRIPTIF, bukan kausal):")
print(f"    n nasabah                     : {r[0]:,}")
print(f"    dana akhir promo              : Rp{r[1]:,.3f} miliar")
print(f"    dana 90 hari sesudahnya       : Rp{r[2]:,.3f} miliar")
print(f"    retensi pasca-promo           : {r[3]}%")
print(f"    rekening kosong pasca-promo   : {r[4]}%")
