#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BAB 1 — Kualitas CASA: retensi orang vs retensi uang.
Menghasilkan berkas di analysis/ (CSV + summary.json).
Dijalankan: uv run --with duckdb python gen/bab1_analysis.py
"""
import csv
import json
import os
from collections import defaultdict

import duckdb

DATA = "data"
OUT = "analysis"
os.makedirs(OUT, exist_ok=True)

con = duckdb.connect()
con.execute(f"CREATE VIEW txn  AS SELECT * FROM read_csv_auto('{DATA}/transactions.csv', header=true)")
con.execute(f"CREATE VIEW cust AS SELECT * FROM read_csv_auto('{DATA}/customers.csv', header=true)")
con.execute(f"CREATE VIEW acc  AS SELECT * FROM read_csv_auto('{DATA}/accounts.csv', header=true)")
con.execute(f"CREATE VIEW bal  AS SELECT * FROM read_csv_auto('{DATA}/account_monthly_balances.csv', header=true)")

BULAN = [f"2025-{i:02d}" for i in range(1, 13)]


def tulis(nama, header, rows):
    p = os.path.join(OUT, nama)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  -> {nama}: {len(rows)} baris")


# ============================================================
# 0. BASIS DATA
# ============================================================
info = {}
for cid, jd, ch, kyc in con.execute(
        "SELECT customer_id, CAST(join_date AS DATE), acquisition_channel, kyc_status FROM cust").fetchall():
    info[cid] = dict(join=jd, kohort=jd.strftime("%Y-%m"), channel=ch, kyc=kyc)

aktif = defaultdict(set)          # bulan -> set(customer_id)
for cid, m in con.execute("""
        SELECT DISTINCT t.customer_id, strftime(CAST(t.txn_date AS DATE), '%Y-%m')
        FROM txn t JOIN acc a USING (account_id)""").fetchall():
    aktif[m].add(cid)

saldo = defaultdict(dict)         # bulan -> cid -> saldo tabungan
for cid, m, v in con.execute("""
        SELECT a.customer_id, strftime(CAST(b.month_end_date AS DATE), '%Y-%m'),
               sum(b.closing_balance)
        FROM bal b JOIN acc a USING (account_id)
        WHERE a.account_type = 'SAVINGS'
        GROUP BY 1, 2""").fetchall():
    saldo[m][cid] = float(v)

kohort_cust = defaultdict(list)
for cid, d in info.items():
    kohort_cust[d["kohort"]].append(cid)


def k_index(kohort, bln):
    return (int(bln[:4]) - int(kohort[:4])) * 12 + int(bln[5:]) - int(kohort[5:])


# ============================================================
# 1. MATRIKS RETENSI (orang & uang)
# ============================================================
mat = []
for k in sorted(kohort_cust):
    if not k.startswith("2025"):
        continue
    ids = kohort_cust[k]
    n = len(ids)
    s0 = sum(saldo[k].get(c, 0.0) for c in ids)
    for bln in BULAN:
        ki = k_index(k, bln)
        if ki < 0:
            continue
        a = sum(1 for c in ids if c in aktif[bln])
        s = sum(saldo[bln].get(c, 0.0) for c in ids)
        mat.append([k, n, ki, a, round(a / n * 100, 2),
                    round(s / 1e9, 4), round(s / s0 * 100, 2) if s0 else 0.0])
tulis("retention_matrix.csv",
      ["kohort", "n_kohort", "bulan_ke", "aktif", "retensi_orang_pct",
       "saldo_miliar", "retensi_uang_pct"], mat)

# ============================================================
# 2. DEKOMPOSISI: efek orang vs efek saldo per orang
# ============================================================
dek = []
for k in sorted(kohort_cust):
    if not k.startswith("2025"):
        continue
    ids = kohort_cust[k]
    n = len(ids)
    s0 = sum(saldo[k].get(c, 0.0) for c in ids)
    for bln in BULAN:
        ki = k_index(k, bln)
        if ki < 0 or ki not in (5, 11):
            continue
        a = sum(1 for c in ids if c in aktif[bln])
        s = sum(saldo[bln].get(c, 0.0) for c in ids)
        if a == 0 or s0 == 0:
            continue
        orang = a / n
        per_orang = (s / a) / (s0 / n)
        dek.append([k, ki, n, a, round(orang * 100, 2),
                    round(per_orang * 100, 2), round(s / s0 * 100, 2),
                    round((s / s0 - 1) * 100, 2),
                    round((orang - 1) * 100, 2),
                    round(orang * (per_orang - 1) * 100, 2)])
tulis("retention_decomposition.csv",
      ["kohort", "bulan_ke", "n_kohort", "aktif", "retensi_orang_pct",
       "saldo_per_orang_pct", "retensi_uang_pct", "bocor_total_pp",
       "bocor_karena_orang_pp", "bocor_karena_saldo_pp"], dek)

# ============================================================
# 3. RETENSI PER KANAL AKUISISI (kohort 2025 dipool per bulan-ke)
# ============================================================
pool = defaultdict(lambda: [0, 0, 0.0, 0.0])   # (ch,ki) -> [n, aktif, saldo, saldo0]
for k in sorted(kohort_cust):
    if not k.startswith("2025"):
        continue
    ids = kohort_cust[k]
    n = len(ids)
    for ch in {info[c]["channel"] for c in ids}:
        sub = [c for c in ids if info[c]["channel"] == ch]
        s0 = sum(saldo[k].get(c, 0.0) for c in sub)
        for bln in BULAN:
            ki = k_index(k, bln)
            if ki < 0:
                continue
            key = (ch, ki)
            pool[key][0] += len(sub)
            pool[key][1] += sum(1 for c in sub if c in aktif[bln])
            pool[key][2] += sum(saldo[bln].get(c, 0.0) for c in sub)
            pool[key][3] += s0

kanal = []
for (ch, ki), (n, a, s, s0) in sorted(pool.items()):
    kanal.append([ch, ki, n, a, round(a / n * 100, 2),
                  round(s / n / 1e6, 3),
                  round(s / s0 * 100, 2) if s0 else 0.0])
tulis("retention_by_channel.csv",
      ["channel", "bulan_ke", "n", "aktif", "retensi_orang_pct",
       "saldo_rata2_juta", "retensi_uang_pct"], kanal)

# ============================================================
# 4. UANG TIDUR — saldo di rekening yang sudah tidak bergerak
# ============================================================
aktif_q4 = set()
for m in ["2025-10", "2025-11", "2025-12"]:
    aktif_q4 |= aktif[m]

dorm = []
total_des = 0.0
tot_dorm = 0.0
n_dorm = 0
for cid, d in info.items():
    v = saldo["2025-12"].get(cid, 0.0)
    total_des += v
    if v > 0 and cid not in aktif_q4:
        tot_dorm += v
        n_dorm += 1
for ch in sorted({d["channel"] for d in info.values()}):
    ids = [c for c, d in info.items() if d["channel"] == ch]
    v_all = sum(saldo["2025-12"].get(c, 0.0) for c in ids)
    v_d = sum(saldo["2025-12"].get(c, 0.0) for c in ids if c not in aktif_q4)
    n_d = sum(1 for c in ids if saldo["2025-12"].get(c, 0.0) > 0 and c not in aktif_q4)
    dorm.append([ch, len(ids), n_d, round(v_all / 1e9, 3), round(v_d / 1e9, 3),
                 round(v_d / v_all * 100, 2) if v_all else 0.0])
dorm.append(["TOTAL", len(info), n_dorm, round(total_des / 1e9, 3), round(tot_dorm / 1e9, 3),
             round(tot_dorm / total_des * 100, 2)])
tulis("dormant_money.csv",
      ["channel", "n_nasabah", "n_dorman", "saldo_des_miliar", "saldo_dorman_miliar",
       "pct_saldo_dorman"], dorm)

# ============================================================
# 5. JURANG PROMO — indeks saldo per bulan-ke, promo vs non-promo
# ============================================================
promo = defaultdict(lambda: [0, 0.0, 0.0])
for k in sorted(kohort_cust):
    if not k.startswith("2025"):
        continue
    ids = kohort_cust[k]
    for ch in {info[c]["channel"] for c in ids}:
        grp = "PROMO" if ch == "PROMO_CAMPAIGN" else "NON_PROMO"
        sub = [c for c in ids if info[c]["channel"] == ch]
        s0 = sum(saldo[k].get(c, 0.0) for c in sub)
        if s0 <= 0:
            continue
        for bln in BULAN:
            ki = k_index(k, bln)
            if ki < 0:
                continue
            s = sum(saldo[bln].get(c, 0.0) for c in sub)
            promo[(grp, ki)][0] += len(sub)
            promo[(grp, ki)][1] += s
            promo[(grp, ki)][2] += s0

cliff = []
for (grp, ki), (n, s, s0) in sorted(promo.items()):
    cliff.append([grp, ki, n, round(s / n / 1e6, 3), round(s / s0 * 100, 2)])
tulis("promo_cliff.csv", ["grup", "bulan_ke", "n", "saldo_rata2_juta", "indeks_saldo_pct"], cliff)

# ============================================================
# 6. CASA MENURUT VINTAGE (tahun bergabung)
# ============================================================
vint = defaultdict(lambda: [0, 0.0, 0])
for cid, d in info.items():
    y = d["join"].year
    vint[y][0] += 1
    vint[y][1] += saldo["2025-12"].get(cid, 0.0)
    if cid in aktif["2025-12"]:
        vint[y][2] += 1
vt = []
for y in sorted(vint):
    n, s, a = vint[y]
    vt.append([y, n, a, round(a / n * 100, 2), round(s / 1e9, 3),
               round(s / total_des * 100, 2)])
tulis("casa_by_vintage.csv",
      ["tahun_gabung", "n", "aktif_des", "pct_aktif", "saldo_miliar", "pct_casa"], vt)

# ============================================================
# 7. KEBOCORAN TAHAP AWAL vs TAHAP LANJUT (kohort 2025 dipool)
# ============================================================
pooled = defaultdict(lambda: [0, 0, 0.0, 0.0])   # ki -> n, aktif, saldo, saldo0
for k in sorted(kohort_cust):
    if not k.startswith("2025"):
        continue
    ids = kohort_cust[k]
    n = len(ids)
    s0 = sum(saldo[k].get(c, 0.0) for c in ids)
    for bln in BULAN:
        ki = k_index(k, bln)
        if ki < 0:
            continue
        p = pooled[ki]
        p[0] += n
        p[1] += sum(1 for c in ids if c in aktif[bln])
        p[2] += sum(saldo[bln].get(c, 0.0) for c in ids)
        p[3] += s0

kurva = []
for ki in sorted(pooled):
    n, a, s, s0 = pooled[ki]
    kurva.append([ki, n, round(a / n * 100, 2), round(s / s0 * 100, 2)])
tulis("pooled_curve.csv", ["bulan_ke", "n", "retensi_orang_pct", "retensi_uang_pct"], kurva)

u = {r[0]: r[3] for r in kurva}
o = {r[0]: r[2] for r in kurva}
tahap = [
    ["UANG", round(100 - u[2], 2), round(u[2] - u[11], 2), round(100 - u[11], 2),
     round((100 - u[2]) / (100 - u[11]) * 100, 1)],
    ["ORANG", round(100 - o[2], 2), round(o[2] - o[11], 2), round(100 - o[11], 2),
     round((100 - o[2]) / (100 - o[11]) * 100, 1)],
]
tulis("leak_staging.csv",
      ["metrik", "bocor_0_3bln_pp", "bocor_4_12bln_pp", "bocor_total_pp",
       "pct_bocor_di_awal"], tahap)

# ============================================================
# 8. JENDELA PROMO BUNGA 4% (1 Jul - 30 Sep 2025): deskriptif
#    CATATAN: dataset tidak memodelkan sensitivitas bunga. Seri ini
#    hanya menunjukkan apa yang terjadi, bukan efek kausal promo.
# ============================================================
promo_win = {"2025-07", "2025-08", "2025-09"}
tot_bulan = {b: sum(saldo[b].values()) for b in BULAN}
basis = tot_bulan["2025-01"]
jendela = []
for b in BULAN:
    jendela.append([b, round(tot_bulan[b] / 1e9, 3),
                    round(tot_bulan[b] / basis * 100, 2),
                    "YA" if b in promo_win else "TIDAK"])
tulis("promo_window.csv", ["bulan", "saldo_tabungan_miliar", "indeks_jan100", "dalam_promo"], jendela)

# ============================================================
# 9. KONSENTRASI SALDO (31 Des 2025, rekening tabungan)
# ============================================================
des = sorted(saldo["2025-12"].values(), reverse=True)
tot_des_tab = sum(des)
kons = []
for p in (0.01, 0.05, 0.10, 0.20, 0.50):
    k = max(1, int(round(len(des) * p)))
    kons.append([f"top {int(p * 100)}%", k, round(sum(des[:k]) / 1e9, 3),
                 round(sum(des[:k]) / tot_des_tab * 100, 2)])
tulis("balance_concentration.csv",
      ["segmen", "n_nasabah", "saldo_miliar", "pct_saldo"], kons)

# ============================================================
# RINGKASAN
# ============================================================
ring = {
    "casa_des_miliar": round(total_des / 1e9, 3),
    "n_dorman": n_dorm,
    "saldo_dorman_miliar": round(tot_dorm / 1e9, 3),
    "pct_dorman": round(tot_dorm / total_des * 100, 2),
    "retensi_2025_01_m12": {
        "orang_pct": next(r[4] for r in mat if r[0] == "2025-01" and r[2] == 11),
        "uang_pct": next(r[6] for r in mat if r[0] == "2025-01" and r[2] == 11),
    },
}
with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(ring, f, indent=2, ensure_ascii=False)
print(json.dumps(ring, indent=2, ensure_ascii=False))
