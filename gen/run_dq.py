#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Menjalankan sql/10_dq_tests.sql terhadap CSV lokal memakai DuckDB."""

import os
import re
import sys

import duckdb

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, ".."))
DATA = os.path.join(ROOT, "data").replace("\\", "/")
SQLF = os.path.join(ROOT, "sql", "10_dq_tests.sql")

con = duckdb.connect()

VIEWS = {
    "txn": "transactions.csv",
    "bal": "account_monthly_balances.csv",
    "cust": "customers.csv",
    "loans": "direct_loans.csv",
    "perf": "partner_monthly_performance.csv",
}
for view, f in VIEWS.items():
    con.execute(
        f"CREATE OR REPLACE VIEW {view} AS "
        f"SELECT * FROM read_csv_auto('{DATA}/{f}', header=true)"
    )

# accounts.csv punya kolom kosong (close_date/term_months/principal untuk tabungan)
# -> DuckDB menyimpulkan VARCHAR. Normalisasi tipenya di sini supaya file .sql
#    tetap portabel ke BigQuery (di BQ tipenya sudah benar sejak DDL).
con.execute(
    f"""CREATE OR REPLACE VIEW acc AS
        SELECT account_id                                AS account_id,
               customer_id                               AS customer_id,
               account_type                              AS account_type,
               CAST(open_date AS DATE)                   AS open_date,
               TRY_CAST(close_date AS DATE)              AS close_date,
               status                                    AS status,
               TRY_CAST(term_months AS INTEGER)          AS term_months,
               CAST(interest_rate_pa AS DOUBLE)          AS interest_rate_pa,
               TRY_CAST(principal AS DOUBLE)             AS principal
        FROM read_csv_auto('{DATA}/accounts.csv', header=true)"""
)

raw = open(SQLF, encoding="utf-8").read()
# buang komentar baris agar pemisahan bersih
stmts = [s.strip() for s in raw.split("-- ;;") if s.strip()]
stmts = [re.sub(r"^\s*--.*$", "", s, flags=re.M) or s for s in stmts]

print(f"{'KODE':<5} {'UJI':<38} {'NILAI':>12}  VONIS")
print("-" * 78)
gagal = 0
for s in stmts:
    # ambil komentar judul dari blok asli
    try:
        rel = con.execute(s)
        cols = [d[0] for d in rel.description]
        rows = rel.fetchall()
    except Exception as e:  # noqa: BLE001
        print(f"{'ERR':<5} query gagal: {e}")
        gagal += 1
        continue
    for r in rows:
        d = dict(zip(cols, r))
        kode = d.get("kode", "?")
        uji = str(d.get("uji", ""))[:38]
        vonis = d.get("vonis", "")
        if "nilai" in d:
            nilai = f"{d['nilai']:,}" if isinstance(d["nilai"], int) else str(d["nilai"])
            harap = d.get("harapan")
            if vonis in ("GAGAL",):
                gagal += 1
                vonis = f"GAGAL (harap {harap})"
            print(f"{kode:<5} {uji:<38} {nilai:>12}  {vonis}")
        else:
            print(f"{kode:<5} {uji:<38} {'':>12}  "
                  f"CASA={d.get('casa_pct')}% LDR={d.get('ldr_pct')}% NPL={d.get('npl_pct')}%")

print("-" * 78)
print(f"Total uji: {len(stmts)} | Gagal keras: {gagal}")
sys.exit(0)
