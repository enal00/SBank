#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Eksplorasi awal Bab 1 — retensi orang vs retensi uang."""
import duckdb
from collections import defaultdict

con = duckdb.connect()
D = "data"
con.execute(f"CREATE VIEW txn  AS SELECT * FROM read_csv_auto('{D}/transactions.csv', header=true)")
con.execute(f"CREATE VIEW cust AS SELECT * FROM read_csv_auto('{D}/customers.csv', header=true)")
con.execute(f"CREATE VIEW acc  AS SELECT * FROM read_csv_auto('{D}/accounts.csv', header=true)")
con.execute(f"CREATE VIEW bal  AS SELECT * FROM read_csv_auto('{D}/account_monthly_balances.csv', header=true)")

# ---- kohort = bulan bergabung -------------------------------------------
rows = con.execute("""
    SELECT customer_id,
           strftime(CAST(join_date AS DATE), '%Y-%m') AS kohort
    FROM cust
""").fetchall()
kohort = dict(rows)
base = defaultdict(int)
for _, k in rows:
    base[k] += 1

# ---- aktivitas: nasabah bertransaksi di bulan tertentu -------------------
act = defaultdict(set)
for cid, m in con.execute("""
    SELECT DISTINCT t.customer_id, strftime(CAST(t.txn_date AS DATE), '%Y-%m')
    FROM txn t JOIN acc a USING (account_id)
""").fetchall():
    act[m].add(cid)

# ---- saldo akhir bulan per nasabah --------------------------------------
balm = defaultdict(dict)   # bln -> cid -> saldo
for cid, m, v in con.execute("""
    SELECT a.customer_id, strftime(CAST(b.month_end_date AS DATE), '%Y-%m'),
           sum(b.closing_balance)
    FROM bal b JOIN acc a USING (account_id)
    WHERE a.account_type = 'SAVINGS'
    GROUP BY 1, 2
""").fetchall():
    balm[m][cid] = v

BULAN = [f"2025-{i:02d}" for i in range(1, 13)]


def idx(bln):
    return int(bln[5:7]) - 1


print("=" * 78)
print("A. RETENSI ORANG — % nasabah kohort yang masih bertransaksi")
print("=" * 78)
print("kohort   n    " + "".join(f"{'M'+str(i+1):>6}" for i in range(12)))
ret_people = {}
for k in [b for b in BULAN if base[b] > 0]:
    ids = [c for c, kk in kohort.items() if kk == k]
    n = len(ids)
    line = f"{k} {n:>4}  "
    for i, bln in enumerate(BULAN):
        if bln < k:
            line += f"{'':>6}"
            continue
        a = sum(1 for c in ids if c in act[bln])
        pct = a / n * 100
        ret_people[(k, i)] = pct
        line += f"{pct:>6.1f}"
    print(line)

print()
print("=" * 78)
print("B. RETENSI UANG — % saldo kohort yang tersisa (relatif bulan pertama)")
print("=" * 78)
print("kohort   n    " + "".join(f"{'M'+str(i+1):>6}" for i in range(12)))
ret_money = {}
for k in [b for b in BULAN if base[b] > 0]:
    ids = [c for c, kk in kohort.items() if kk == k]
    n = len(ids)
    first = k
    # saldo rata-rata per nasabah di bulan pertama
    b0 = sum(balm[first].get(c, 0) for c in ids) / n
    line = f"{k} {n:>4}  "
    for i, bln in enumerate(BULAN):
        if bln < k:
            line += f"{'':>6}"
            continue
        b = sum(balm[bln].get(c, 0) for c in ids) / n
        pct = (b / b0 * 100) if b0 else 0
        ret_money[(k, i)] = pct
        line += f"{pct:>6.1f}"
    print(line)
print("  (angka = % saldo rata-rata per nasabah dibanding bulan pertama kohort)")

print()
print("=" * 78)
print("C. KOHORT 2025-01 DI TITIK 12 BULAN (M12 = Desember 2025)")
print("=" * 78)
print(f"  retensi orang : {ret_people[('2025-01', 11)]:.1f}%")
print(f"  retensi uang  : {ret_money[('2025-01', 11)]:.1f}%")

print()
print("=" * 78)
print("D. KOHORT LAMA (pra-2025) — 16.800 nasabah")
print("=" * 78)
old = [c for c, k in kohort.items() if k < "2025-01"]
print(f"  n = {len(old):,}")
for bln in ["2025-01", "2025-06", "2025-12"]:
    a = sum(1 for c in old if c in act[bln])
    print(f"  {bln}: aktif {a:>6,} ({a/len(old)*100:5.1f}%)  "
          f"saldo Rp{sum(balm[bln].get(c,0) for c in old)/1e9:8.2f} M")
