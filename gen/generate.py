#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SeaBank Digital Twin v1.0 — Generator Dataset
==============================================
Membangun dataset sintetis TERKALIBRASI yang mereproduksi rasio publik
PT Bank SeaBank Indonesia FY2025 pada skala 1/1000.

ATURAN KALIBRASI (penting, jujur):
  - Rasio yang DIKETAHUI publik  -> dikalibrasi agar cocok persis (CASA, LDR, NPL,
    komposisi kredit, jumlah DPK).
  - Perilaku yang TIDAK diketahui -> dibiarkan MUNCUL dari proses generatif
    (retensi kohort, konsentrasi saldo, dormansi). Ini yang akan jadi TEMUAN,
    bukan asumsi.

Output: ../data/*.csv  +  ../data/_calibration.json
Jalankan: python3 generate.py
"""

import csv
import json
import math
import os
import random
from datetime import date, timedelta

random.seed(20251118)

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.abspath(os.path.join(BASE, "..", "data"))
os.makedirs(DATA, exist_ok=True)

# ============================================================================
# 0. TARGET KALIBRASI — nilai publik AR2025 dibagi 1000
# ============================================================================
T_DPK        = 34_806_000_000      # Rp34.806 miliar / 1000
T_CASA_RATIO = 0.7074
T_CASA       = int(T_DPK * T_CASA_RATIO)     # ~24,6 miliar
T_DEPOSITO   = T_DPK - T_CASA

T_LOANS      = 32_134_000_000      # Rp32.134 miliar / 1000
T_JF         = 25_913_000_000
T_CHANNELING = 3_533_000_000
T_LEGACY     = 35_000_000
T_DIRECT     = T_LOANS - T_JF - T_CHANNELING - T_LEGACY

T_NPL_RATIO  = 0.0182
T_NPL        = int(T_LOANS * T_NPL_RATIO)     # ~585 juta

N_CUST       = 24_000
N_NEW_2025   = 7_200               # 600/bulan x 12
N_EXIST      = N_CUST - N_NEW_2025

MONTH_ENDS = [date(2025, m, 1) + timedelta(days=31) for m in range(1, 13)]
MONTH_ENDS = [(date(2025, m, 1).replace(day=1)) for m in range(1, 13)]
# akhir bulan yang benar
MONTH_ENDS = []
for m in range(1, 13):
    nxt = date(2026, 1, 1) if m == 12 else date(2025, m + 1, 1)
    MONTH_ENDS.append(nxt - timedelta(days=1))

# ============================================================================
# 1. REFERENSI GEOGRAFI & DEMOGRAFI
# ============================================================================
CITIES = [
    ("DKI Jakarta", "Jakarta", 0.17),
    ("Jawa Barat", "Bandung", 0.14),
    ("Jawa Timur", "Surabaya", 0.13),
    ("Jawa Tengah", "Semarang", 0.10),
    ("Banten", "Tangerang", 0.09),
    ("Sumatera Utara", "Medan", 0.07),
    ("Sulawesi Selatan", "Makassar", 0.05),
    ("Riau", "Pekanbaru", 0.04),
    ("Lampung", "Bandar Lampung", 0.04),
    ("Kalimantan Timur", "Balikpapan", 0.04),
    ("Bali", "Denpasar", 0.04),
    ("Sumatera Selatan", "Palembang", 0.04),
    ("DI Yogyakarta", "Yogyakarta", 0.03),
    ("Nusa Tenggara Barat", "Mataram", 0.02),
]
_city_w = [c[2] for c in CITIES]
_city_s = sum(_city_w)
_city_w = [w / _city_s for w in _city_w]

CHANNELS = ["ORGANIC", "SHOPEE_ECOSYSTEM", "REFERRAL", "AGENT_MITRA", "PAYROLL", "PROMO_CAMPAIGN"]
CH_W = [0.30, 0.30, 0.12, 0.13, 0.07, 0.08]

OCCUPATIONS = ["Karyawan swasta", "Wirausaha", "Pedagang online", "ASN/TNI/Polri",
               "Freelancer", "Mahasiswa", "Ibu rumah tangga", "Driver online", "Lainnya"]
OCC_W = [0.28, 0.16, 0.14, 0.07, 0.10, 0.08, 0.09, 0.05, 0.03]

INCOME_BANDS = ["<3jt", "3-5jt", "5-10jt", "10-20jt", ">20jt"]
INCOME_W = [0.34, 0.26, 0.24, 0.12, 0.04]

# Arketipe perilaku TERSEMBUNYI (tidak masuk dataset — analisis harus menemukannya)
ARCH = {
    # growth: faktor bulanan; sigma: lebar distribusi kekayaan; boost/taper: perilaku nasabah baru
    # churn: peluang berhenti bertransaksi tiap bulan; react: peluang kembali aktif;
    # residual: porsi saldo yang ditinggal saat berhenti (-> jadi "uang tidur")
    "A": dict(growth=1.022, sigma=1.25, boost=-0.30, taper=1.6, turnover=0.55, ntxn=6,
              churn=0.008, react=0.09, residual=0.12, share=0.0),
    "B": dict(growth=1.004, sigma=0.78, boost=0.00, taper=1.0, turnover=1.10, ntxn=7,
              churn=0.020, react=0.07, residual=0.07, share=0.0),
    "C": dict(growth=0.955, sigma=0.95, boost=0.95, taper=1.1, turnover=1.90, ntxn=4,
              churn=0.085, react=0.03, residual=0.04, share=0.0),
    "D": dict(growth=0.975, sigma=0.45, boost=0.40, taper=2.0, turnover=0.25, ntxn=1,
              churn=0.050, react=0.05, residual=0.18, share=0.0),
}


def build_activity():
    """Matriks aktif/dorman per nasabah per bulan (Markov: churn & reaktivasi)."""
    act = []
    for i, c in enumerate(customers):
        a = ARCH[savings_arch[i]]
        jd = c["join_date"]
        baru = (jd.year == 2025)
        join_m = jd.month if baru else 1
        row = [False] * 12
        if baru:
            hidup = False
        else:
            # nasabah lama masuk 2025 dalam kondisi stasioner: sebagian sudah dorman
            p_dorm = a["churn"] / (a["churn"] + a["react"])
            hidup = random.random() > p_dorm
        for mi in range(1, 13):
            if mi < join_m:
                continue
            if baru and mi == join_m:
                hidup = True                     # bulan pertama pasti bertransaksi
            if hidup:
                row[mi - 1] = True
                # kegagalan aktivasi bulan pertama jauh lebih tinggi
                h = a["churn"] * (2.5 if (baru and mi == join_m) else 1.0)
                if random.random() < h:
                    hidup = False
            else:
                if random.random() < a["react"]:
                    hidup = True
                    row[mi - 1] = True
        act.append(row)
    return act

QRIS_CATS = ["F&B", "RETAIL", "TRANSPORT", "TELCO", "UTILITY", "E-COMMERCE", "LAINNYA"]
QRIS_W = [0.34, 0.24, 0.12, 0.07, 0.08, 0.12, 0.03]


def wchoice(items, weights, rnd=random):
    return rnd.choices(items, weights=weights, k=1)[0]


def rid(prefix, n, width):
    return f"{prefix}{n:0{width}d}"


def write_csv(name, header, rows):
    path = os.path.join(DATA, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        cnt = 0
        for r in rows:
            w.writerow(r)
            cnt += 1
    print(f"  -> {name}: {cnt:,} baris, {os.path.getsize(path)/1e6:.1f} MB")
    return cnt


# ============================================================================
# 2. CUSTOMERS
# ============================================================================
print("[1/8] Customers ...")
customers = []
savings_arch = []   # arketipe per nasabah (indeks = idx savings)

# --- Kurva akuisisi historis (mengikuti sejarah perusahaan) ----------------
# 2019-2020: bank kecil pra-akuisisi. 2021: titik belok (rebranding SeaBank).
# 2022-2024: ekspansi ekosistem Shopee. 2025: 600/bulan sesuai AR2025 hlm. 35.
# Sebelumnya basis lama disebar rata -> kurva datar 233/bulan 6 tahun, tidak wajar.
ACQ_RAMP = [
    (2019,   120),
    (2020,   300),
    (2021, 1_800),
    (2022, 3_600),
    (2023, 4_800),
    (2024, 6_180),
]
assert sum(y for _, y in ACQ_RAMP) == N_EXIST, (
    f"ACQ_RAMP berjumlah {sum(y for _, y in ACQ_RAMP)}, harus = N_EXIST {N_EXIST}"
)


def _alloc(total, weights):
    """Bagi `total` (int) ke n bagian; jumlahnya TEPAT total."""
    s = sum(weights)
    raw = [total * w / s for w in weights]
    out = [int(x) for x in raw]
    sisa = total - sum(out)
    order = sorted(range(len(raw)), key=lambda k: raw[k] - out[k], reverse=True)
    for k in order[:sisa]:
        out[k] += 1
    return out


_acq_pool = []
for _y, _tot in ACQ_RAMP:
    # di dalam satu tahun pun trennya menanjak, bukan rata
    _w = [1.0 + 0.6 * (m - 1) / 11 for m in range(1, 13)]
    for _m, _n in zip(range(1, 13), _alloc(_tot, _w)):
        _acq_pool.extend([(_y, _m)] * _n)
assert len(_acq_pool) == N_EXIST
random.shuffle(_acq_pool)
print(f"    kurva akuisisi: {len(_acq_pool)} nasabah basis lama + {N_NEW_2025} baru 2025")

for i in range(N_CUST):
    cid = rid("C", i + 1, 6)
    if i < N_EXIST:
        _y, _m = _acq_pool[i]
        jd = date(_y, _m, random.randint(1, 28))
        arch = wchoice(["A", "B", "C", "D"], [0.30, 0.35, 0.15, 0.20])
        tenure = max(1, (date(2025, 1, 1) - jd).days // 30)
    else:
        m = random.randint(1, 12)
        jd = date(2025, m, 1)
        if m == 12:
            jd = date(2025, 12, random.randint(1, 20))
        else:
            jd = date(2025, m, random.randint(1, 27))
        arch = wchoice(["A", "B", "C", "D"], [0.15, 0.28, 0.32, 0.25])
        tenure = 0

    prov, city, _ = wchoice(CITIES, _city_w)
    ch = wchoice(CHANNELS, CH_W)
    age = max(17, min(72, int(random.gauss(31, 8))))
    gender = wchoice(["M", "F"], [0.52, 0.48])
    occ = wchoice(OCCUPATIONS, OCC_W)
    inc = wchoice(INCOME_BANDS, INCOME_W)
    first_time = random.random() < 0.30
    kyc = wchoice(["VERIFIED", "PENDING", "REJECTED"], [0.955, 0.038, 0.007])
    customers.append(dict(
        customer_id=cid, join_date=jd, tenure_months_at_2025=tenure,
        acquisition_channel=ch, city=city, province=prov, age=age, gender=gender,
        occupation=occ, monthly_income_band=inc, is_first_time_bank_user=first_time,
        kyc_status=kyc,
    ))
    savings_arch.append(arch)

# ============================================================================
# 3. SHAPES SALDO TABUNGAN -> kalibrasi tepat ke T_CASA
# ============================================================================
print("[2/8] Bentuk trajektori saldo & kalibrasi CASA ...")


ACTIVITY = build_activity()


def build_shapes():
    shapes = []
    for i, c in enumerate(customers):
        a = ARCH[savings_arch[i]]
        w0 = random.lognormvariate(0.0, a["sigma"])
        jd = c["join_date"]
        join_m = None
        if jd.year == 2025:
            join_m = jd.month
        row = [0.0] * 12
        # nasabah lama yang sudah dorman sebelum 2025 tetap menyisakan saldo kecil
        resid = w0 * a["residual"] if join_m is None else 0.0
        for mi in range(1, 13):
            if join_m is not None and mi < join_m:
                row[mi - 1] = 0.0
                continue
            t = 0 if join_m is None else (mi - join_m)
            if not ACTIVITY[i][mi - 1]:
                # sedang dorman: saldo beku di sisa saldo terakhir
                row[mi - 1] = resid
                continue
            v = w0 * (a["growth"] ** t)
            if join_m is not None:
                v *= (1.0 + a["boost"] * math.exp(-t / a["taper"]))
            v *= random.lognormvariate(0.0, 0.16)
            v = max(v, 0.0)
            akhir = (mi == 12) or (not ACTIVITY[i][mi])
            if akhir and mi < 12:
                # bulan terakhir sebelum pergi: tarik dana, sisakan residual
                v *= a["residual"]
            row[mi - 1] = v
            resid = v
        shapes.append(row)
    return shapes


shapes = build_shapes()
total_shape = sum(sum(r) for r in shapes)
# tiap akun punya 12 angka; total_shape = jumlah saldo 12 bulan.
# agar RATA-RATA bulanan agregat = T_CASA, total 12 bulan harus = 12 x T_CASA
K = (T_CASA * 12.0) / total_shape if total_shape > 0 else 1.0

# terapkan skala -> saldo akhir bulan persis T_CASA (dalam rata-rata 12 bulan)
bal = [[round(v * K) for v in r] for r in shapes]

# qc: CASA = rata-rata saldo akhir bulan
casa_avg = sum(sum(r) for r in bal) / 12.0
calib = {
    "target_casa": T_CASA,
    "actual_casa_avg": round(casa_avg),
    "casa_gap_pct": round((casa_avg / T_CASA - 1) * 100, 4),
}

# ============================================================================
# 4. ACCOUNTS (SAVINGS + DEPOSITO)
# ============================================================================
print("[3/8] Accounts ...")
accounts = []
acc_idx_savings = []
n_acc = 0
for i, c in enumerate(customers):
    n_acc += 1
    aid = rid("ACC", n_acc, 7)
    acc_idx_savings.append(n_acc - 1)
    od = c["join_date"]
    last_bal = bal[i][11]
    status = "ACTIVE"
    if not ACTIVITY[i][11]:
        status = "DORMANT"
    elif last_bal < 120_000 and random.random() < 0.55:
        status = "DORMANT"
    if c["kyc_status"] == "REJECTED":
        status = "CLOSED"
    accounts.append(dict(
        account_id=aid, customer_id=c["customer_id"], account_type="SAVINGS",
        open_date=od, close_date=None, status=status, term_months=None,
        interest_rate_pa=3.50, principal=None,
    ))

# --- deposito: ~3.600 akun, total tepat T_DEPOSITO ---
N_DEP = 3_600
dep_terms = [1, 3, 6, 12]
dep_term_w = [0.16, 0.34, 0.30, 0.20]
dep_rate = {1: 4.25, 3: 5.25, 6: 5.75, 12: 6.00}
AS_OF = date(2025, 12, 31)

dep_contracts = []
for j in range(N_DEP):
    cust = customers[random.randrange(N_CUST)]
    term = wchoice(dep_terms, dep_term_w)
    principal = random.lognormvariate(0.0, 1.15)
    # bank yang tumbuh 30%: mayoritas deposito ditempatkan pada H2 2025,
    # supaya outstanding 31 Des mencerminkan buku yang benar-benar hidup
    if random.random() < 0.80:
        od = date(2025, random.randint(7, 12), random.randint(1, 27))
    else:
        od = date(2025, random.randint(1, 6), random.randint(1, 27))
    mat = od + timedelta(days=int(term * 30.4))
    status = "MATURED" if mat <= AS_OF else "ACTIVE"
    dep_contracts.append([cust, term, principal, od, mat, status])

# KALIBRASI: total pokok yang MASIH AKTIF per 31 Des = T_DEPOSITO
active_raw = sum(c[2] for c in dep_contracts if c[5] == "ACTIVE")
dep_scale = T_DEPOSITO / active_raw if active_raw else 1.0

for cust, term, principal, od, mat, status in dep_contracts:
    n_acc += 1
    aid = rid("ACC", n_acc, 7)
    p = round(principal * dep_scale)
    accounts.append(dict(
        account_id=aid, customer_id=cust["customer_id"], account_type="DEPOSITO",
        open_date=od, close_date=mat if status == "MATURED" else None, status=status,
        term_months=term, interest_rate_pa=dep_rate[term], principal=p,
    ))

# ============================================================================
# 5. TRANSACTIONS + MONTHLY BALANCES  (streaming)
# ============================================================================
print("[4/8] Transactions (streaming) ...")

TXN_H = ["transaction_id", "account_id", "customer_id", "txn_date", "txn_ts",
         "txn_type", "direction", "amount", "balance_after", "channel",
         "merchant_category", "is_counterparty_missing"]

tpath = os.path.join(DATA, "transactions.csv")
txn_f = open(tpath, "w", newline="", encoding="utf-8")
txn_w = csv.writer(txn_f)
txn_w.writerow(TXN_H)

bal_rows = []
txn_seq = 0
anom = dict(dup=0, orphan=0, zero=0, drift=0)
DEP_ACCTS = [a for a in accounts if a["account_type"] == "DEPOSITO"]


def emit(acc, cust, d, txn_type, direction, amount, balance_after, channel, cat,
         counterparty_missing=False):
    global txn_seq
    txn_seq += 1
    tid = rid("TXN", txn_seq, 12)
    amt = int(amount)
    if amt <= 0:
        amt = 1
    ts = f"{d.isoformat()} 00:00:00+07"
    hh = random.randint(0, 23)
    mm = random.randint(0, 59)
    ts = f"{d.isoformat()} {hh:02d}:{mm:02d}:{random.randint(0,59):02d}+07"
    accid = acc["account_id"]
    # --- injeksi anomali terkendali (untuk data quality test Bab 0) ---
    r = random.random()
    miss = counterparty_missing
    if r < 0.0025:
        accid = "ACC9999%03d" % random.randint(0, 999)   # orphan
        anom["orphan"] += 1
    txn_w.writerow([tid, accid, cust["customer_id"], d.isoformat(), ts, txn_type,
                    direction, amt, int(balance_after), channel, cat, miss])
    # duplikat: txn_id sama, timestamp beda 2 menit
    if random.random() < 0.0035:
        txn_w.writerow([tid, accid, cust["customer_id"], d.isoformat(), ts, txn_type,
                        direction, amt, int(balance_after), channel, cat, miss])
        anom["dup"] += 1
    return amt


def split_amount(total, n):
    """Bagi `total` menjadi n bagian bulat positif yang jumlahnya TEPAT total."""
    total = int(total)
    if total <= 0:
        return []
    n = max(1, min(int(n), total))
    parts = []
    rem = total
    for k in range(n - 1):
        left = n - k - 1
        a = int(total * random.uniform(0.08, 0.45))
        a = max(1, min(a, rem - left))
        parts.append(a)
        rem -= a
    parts.append(rem)
    return parts


CHAIN_BAD = 0

for i, c in enumerate(customers):
    a = ARCH[savings_arch[i]]
    acc = accounts[acc_idx_savings[i]]
    jd = c["join_date"]
    join_m = jd.month if jd.year == 2025 else 0
    prev = int(bal[i][0] / (a["growth"] ** 1)) if join_m == 0 else 0
    if join_m == 0 and not ACTIVITY[i][0]:
        prev = int(bal[i][0])      # dorman sejak awal: saldo beku, tanpa transaksi

    for mi in range(1, 13):
        d_end = MONTH_ENDS[mi - 1]
        if join_m and mi < join_m:
            bal_rows.append([acc["account_id"], d_end.isoformat(), 0, 0, 0, 0, 0, 0])
            continue

        if not ACTIVITY[i][mi - 1]:
            # dorman: tidak ada transaksi, saldo beku
            bal_rows.append([acc["account_id"], d_end.isoformat(), int(prev), int(prev),
                             int(prev), 0, 0, 0])
            continue

        opening = prev
        closing = bal[i][mi - 1]           # target kalibrasi, dipakai APA ADANYA
        net = closing - opening
        spend = int(opening * a["turnover"])
        # pisahkan arus bruto agar NETTO tepat = net, keduanya non-negatif
        if net >= 0:
            inflow, outflow = spend + net, spend
        else:
            inflow, outflow = spend, spend - net
        inflow, outflow = int(inflow), int(outflow)

        # bunga masuk SEBAGAI BAGIAN dari kredit, bukan tambahan (agar netto tetap tepat)
        ia = 0
        if closing > 500_000 and random.random() < 0.75:
            cand = int(closing * 0.035 / 12)
            if cand >= 100 and inflow - cand >= 0:
                ia = cand
        inflow_main = inflow - ia

        n_cr = min(3, max(1, a["ntxn"] // 3 + random.randint(0, 1))) if inflow_main > 0 else 0
        n_dr = min(5, max(1, a["ntxn"] - n_cr + random.randint(-1, 1))) if outflow > 0 else 0

        rows_m = []
        balrun = opening
        tc = td = 0

        # ---- kredit ----
        for k_, amt in enumerate(split_amount(inflow_main, n_cr)):
            if k_ == 0:
                if c["acquisition_channel"] == "PAYROLL" or savings_arch[i] == "A":
                    ttype, chan = "SALARY_IN", "TRANSFER"
                else:
                    ttype, chan = "TRANSFER_IN", "TRANSFER"
            else:
                ttype, chan = random.choice([("TRANSFER_IN", "TRANSFER"),
                                             ("EWALLET_TOPUP", "APP")])
            balrun += amt
            rows_m.append((ttype, "CR", amt, balrun, chan, "LAINNYA"))
            tc += amt

        if ia > 0:
            balrun += ia
            rows_m.append(("INTEREST_CREDIT", "CR", ia, balrun, "APP", "LAINNYA"))
            tc += ia

        # ---- debit ----
        for k_, amt in enumerate(split_amount(outflow, n_dr)):
            if k_ == 0 and random.random() < 0.5:
                ttype, chan, cat = "CASH_WITHDRAW", "ATM", "LAINNYA"
            elif random.random() < 0.72:
                ttype, chan, cat = "QRIS_PAYMENT", "QRIS", wchoice(QRIS_CATS, QRIS_W)
            elif random.random() < 0.6:
                ttype, chan, cat = "BILL_PAYMENT", "APP", wchoice(["TELCO", "UTILITY"], [0.6, 0.4])
            else:
                ttype, chan, cat = "TRANSFER_OUT", "TRANSFER", "LAINNYA"
            balrun -= amt
            rows_m.append((ttype, "DR", amt, balrun, chan, cat))
            td += amt

        # tanggal menaik dalam bulan agar balance_after masuk akal sebagai deret waktu
        nm = len(rows_m)
        for k in range(nm):
            day = d_end - timedelta(days=27 - (k * 27 // max(nm, 1)))
            tt, dr, amt, ba, ch, cat = rows_m[k]
            emit(acc, c, day, tt, dr, amt, max(ba, 0), ch, cat)

        if abs(opening + tc - td - closing) > 0:
            CHAIN_BAD += 1

        bal_rows.append([acc["account_id"], d_end.isoformat(), int(opening), int(closing),
                         int((opening + closing) / 2), tc, td, len(rows_m)])
        prev = closing

print(f"     cek rantai saldo internal: {CHAIN_BAD} pelanggaran")

# ---- transaksi deposito (placement & maturity) ----
for dep in DEP_ACCTS:
    cust = next(c for c in customers if c["customer_id"] == dep["customer_id"])
    p = dep["principal"]
    emit(dep, cust, dep["open_date"], "DEPOSITO_PLACEMENT", "DR", p, 0, "APP", "LAINNYA")
    if dep["status"] == "MATURED":
        r = dep["interest_rate_pa"] / 100.0
        gross = int(p * (1 + r * dep["term_months"] / 12))
        emit(dep, cust, dep["close_date"], "DEPOSITO_MATURITY", "CR", gross, 0, "APP", "LAINNYA")

txn_f.close()
print(f"  -> transactions.csv: {txn_seq + anom['dup']:,} baris, {os.path.getsize(tpath)/1e6:.1f} MB")
print(f"     anomali disuntik: duplikat={anom['dup']:,} orphan={anom['orphan']:,}")

write_csv("account_monthly_balances.csv",
          ["account_id", "month_end_date", "opening_balance", "closing_balance",
           "avg_balance", "total_credit", "total_debit", "txn_count"], bal_rows)

# ============================================================================
# 6. LOAN PARTNERS + PERFORMANCE
# ============================================================================
print("[5/8] Loan partners ...")
PARTNER_DEF = [
    # (nama, tipe, skema, tier, porsi_buku, npl_dasar, growth_bulanan)
    ("Multifinance Alfa",   "MULTIFINANCE", "JOINT_FINANCING", "A", 0.245, 0.0085, 0.030),
    ("Multifinance Bravo",  "MULTIFINANCE", "JOINT_FINANCING", "A", 0.190, 0.0110, 0.028),
    ("Multifinance Charlie","MULTIFINANCE", "JOINT_FINANCING", "B", 0.145, 0.0195, 0.041),
    ("Multifinance Delta",  "MULTIFINANCE", "JOINT_FINANCING", "C", 0.085, 0.0385, 0.055),
    ("Multifinance Echo",   "MULTIFINANCE", "JOINT_FINANCING", "B", 0.100, 0.0150, 0.022),
    ("P2P Foxtrot",         "P2P",          "JOINT_FINANCING", "C", 0.075, 0.0465, 0.062),
    ("P2P Golf",            "P2P",          "JOINT_FINANCING", "B", 0.065, 0.0210, 0.035),
    ("P2P Hotel",           "P2P",          "JOINT_FINANCING", "D", 0.045, 0.0580, 0.048),
    ("Koperasi India",      "KOPERASI",     "CHANNELING", "B", 0.150, 0.0140, 0.038),
    ("Koperasi Juliett",    "KOPERASI",     "CHANNELING", "C", 0.120, 0.0270, 0.045),
    ("Bank Kilo",           "BANK",         "CHANNELING", "A", 0.230, 0.0065, 0.020),
    ("Bank Lima",           "BANK",         "CHANNELING", "B", 0.150, 0.0130, 0.026),
    ("Legacy Portfolio",    "LEGACY",       "LEGACY",     "A", 1.000, 0.0000, 0.000),
]

# PENTING: porsi dinormalisasi DI DALAM masing-masing skema, bukan lintas skema.
# Kalau lintas skema, total buku jadi jauh di bawah T_JF/T_CHANNELING.
_scheme_sum = {}
for (n, t, s, tr, po, npl, g) in PARTNER_DEF:
    _scheme_sum[s] = _scheme_sum.get(s, 0.0) + po
PARTNER_DEF = [(n, t, s, tr, po / _scheme_sum[s], npl, g)
               for (n, t, s, tr, po, npl, g) in PARTNER_DEF]
assert abs(sum(p[4] for p in PARTNER_DEF if p[2] == "JOINT_FINANCING") - 1.0) < 1e-9

partners, perf_rows = [], []
for idx, (nm, tp, sch, tier, share, base_npl, g) in enumerate(PARTNER_DEF, start=1):
    pid = rid("P", idx, 3)
    onboard = date(random.randint(2020, 2023), random.randint(1, 12), random.randint(1, 27))
    partners.append([pid, nm, tp, sch, tier, onboard.isoformat(),
                     round(random.uniform(0.55, 0.75), 3)])

# alokasi buku: setiap skema punya targetnya sendiri
sch_total = {"JOINT_FINANCING": T_JF, "CHANNELING": T_CHANNELING, "LEGACY": T_LEGACY}
for m_i in range(12):
    month_end = MONTH_ENDS[m_i]
    for idx, (nm, tp, sch, tier, share, base_npl, g) in enumerate(PARTNER_DEF, start=1):
        pid = rid("P", idx, 3)
        total_sch = sch_total[sch]
        # outstanding bulan-12 = porsi x total skema; sebelumnya tumbuh ke belakang
        out_12 = total_sch * share
        out = out_12 / ((1 + g) ** (11 - m_i))
        # deteriorasi vintage: makin cepat tumbuh, makin naik NPL-nya
        growth_idx = (1 + g) ** (11 - m_i)
        npl_r = base_npl * (0.62 + 0.38 * growth_idx)
        npl_b = out * npl_r
        perf_rows.append([pid, month_end.isoformat(), int(out * 1.0 / 12 * (1 + g)),
                          int(out), int(npl_b), int(out * npl_r * 1.9),
                          round(npl_r, 6), int(random.randint(8_000, 45_000) * share * 12)])

# --- kalibrasi NPL dilakukan SETELAH direct loan dihitung (lihat di bawah) ---
def rescale_partner_npl(npl_target):
    """Skala npl_balance semua bulan agar total NPL Desember = npl_target."""
    des = [r for r in perf_rows if r[1].startswith("2025-12")]
    cur = sum(r[4] for r in des)
    k = (npl_target / cur) if cur else 1.0
    for r in perf_rows:
        r[4] = int(r[4] * k)
        r[5] = int(r[5] * k)
    for r in perf_rows:
        r[6] = round(r[4] / r[3], 6) if r[3] > 0 else 0.0
    return k

# ============================================================================
# 7. DIRECT LOANS
# ============================================================================
print("[6/8] Direct loans ...")
N_DIRECT = 2_000
raw = []
for j in range(N_DIRECT):
    cust = customers[random.randrange(N_CUST)]
    prod = wchoice(["PINJAM", "PAYROLL", "KTA"], [0.45, 0.30, 0.25])
    pr0 = random.lognormvariate(0, 0.85)
    dd = date(2025, random.randint(1, 11), random.randint(1, 27))
    term = wchoice([6, 12, 18, 24], [0.35, 0.40, 0.15, 0.10])
    rate = round(random.uniform(18.0, 29.5), 2)
    months_paid = max(0, (date(2025, 12, 31) - dd).days // 30)
    frac = min(1.0, months_paid / term)
    dpd = wchoice([0, 0, 0, 0, 0, 0, 0, 5, 12, 25, 45, 75, 95, 120],
                  [0.30, 0.15, 0.12, 0.08, 0.06, 0.05, 0.03, 0.05, 0.04, 0.04,
                   0.03, 0.02, 0.02, 0.01])
    raw.append([cust, prod, pr0, dd, term, rate, frac, dpd])

# KALIBRASI pada OUTSTANDING (bukan pokok) supaya total buku pinjaman tepat
out0 = sum(r[2] * (1 - r[6]) for r in raw)
o_scale = T_DIRECT / out0
dl = []
for j, (cust, prod, pr0, dd, term, rate, frac, dpd) in enumerate(raw):
    pr = round(pr0 * o_scale)
    out = int(pr * (1 - frac))
    status = "CURRENT" if dpd == 0 else ("DPD30" if dpd <= 30 else ("DPD90" if dpd <= 90 else "DEFAULT"))
    dl.append([rid("LN", j + 1, 7), cust["customer_id"], prod, pr, dd.isoformat(),
               term, rate, out, dpd, status])

direct_out = sum(r[7] for r in dl)
direct_npl = sum(r[7] for r in dl if r[8] > 90)

write_csv("direct_loans.csv",
          ["loan_id", "customer_id", "product", "principal", "disbursed_date",
           "term_months", "interest_rate_pa", "outstanding", "dpd", "status"], dl)

# NPL grup = 1,82% dari TOTAL kredit; mitra menyerap sisanya setelah NPL langsung
partner_npl_target = max(T_NPL - direct_npl, 0)
k_npl = rescale_partner_npl(partner_npl_target)

write_csv("loan_partners.csv",
          ["partner_id", "partner_name", "partner_type", "scheme", "risk_tier",
           "onboard_date", "revenue_share_pct"], partners)
write_csv("partner_monthly_performance.csv",
          ["partner_id", "month", "disbursement", "outstanding_balance", "npl_balance",
           "dpd_30_balance", "npl_ratio", "active_borrowers"], perf_rows)

# ============================================================================
# 8. RATES, PROMO, INDUSTRY REFERENCE
# ============================================================================
print("[7/8] Rates, promo, benchmark ...")
rates = [
    ["SB_SAVINGS", "2025-01-01", "2025-06-30", 3.50, 0, False, "Bunga tabungan dasar"],
    ["SB_SAVINGS", "2025-07-01", "2025-09-30", 4.00, 0, True, "Promo bunga tabungan H2"],
    ["SB_SAVINGS", "2025-10-01", None, 3.50, 0, False, "Kembali ke bunga dasar"],
    ["SB_DEP_1M", "2025-01-01", None, 4.25, 1_000_000, False, "Deposito 1 bulan"],
    ["SB_DEP_3M", "2025-01-01", None, 5.25, 1_000_000, False, "Deposito 3 bulan"],
    ["SB_DEP_6M", "2025-01-01", None, 5.75, 1_000_000, False, "Deposito 6 bulan"],
    ["SB_DEP_12M", "2025-01-01", None, 6.00, 1_000_000, False, "Deposito 12 bulan"],
]
write_csv("product_rates.csv",
          ["product_code", "effective_date", "end_date", "rate_pa", "min_balance",
           "is_promo", "notes"], rates)

promos = [
    ["CMP001", "Bunga Tabungan 4% (H2)", "SB_SAVINGS", "2025-07-01", "2025-09-30", 50, "ALL", 4_500_000_000],
    ["CMP002", "Cashback QRIS Ramadan", "SB_SAVINGS", "2025-03-01", "2025-04-30", 0, "NEW_USER", 1_200_000_000],
    ["CMP003", "Bonus Deposito 12 Bulan", "SB_DEP_12M", "2025-05-01", "2025-07-31", 75, "HIGH_BALANCE", 2_000_000_000],
    ["CMP004", "Referral Shopee Ecosystem", "SB_SAVINGS", "2025-01-01", "2025-12-31", 0, "SHOPEE_USER", 3_000_000_000],
]
write_csv("promo_campaigns.csv",
          ["campaign_id", "campaign_name", "product_code", "start_date", "end_date",
           "bonus_rate_bps", "target_segment", "budget_idr"], promos)

ref = [
    ["SEABANK", "FY2025", "loans_idr_bn", 32134.0, "AR SeaBank 2025 p.38", "2026-04-30"],
    ["SEABANK", "FY2025", "dpk_idr_bn", 34806.0, "AR SeaBank 2025 p.38", "2026-04-30"],
    ["SEABANK", "FY2025", "ldr_pct", 92.32, "AR SeaBank 2025", "2026-04-30"],
    ["SEABANK", "FY2025", "casa_pct", 70.74, "AR SeaBank 2025 p.38", "2026-04-30"],
    ["SEABANK", "FY2025", "npl_gross_pct", 1.82, "AR SeaBank 2025", "2026-04-30"],
    ["SEABANK", "FY2025", "nim_pct", 21.45, "AR SeaBank 2025 p.120", "2026-04-30"],
    ["SEABANK", "FY2025", "bopo_pct", 91.47, "AR SeaBank 2025 p.120", "2026-04-30"],
    ["SEABANK", "FY2025", "car_pct", 23.29, "AR SeaBank 2025 p.120", "2026-04-30"],
    ["SEABANK", "FY2025", "net_profit_idr_bn", 678.4, "AR SeaBank 2025 p.38", "2026-04-30"],
    ["SEABANK", "FY2025", "assets_idr_bn", 44439.0, "AR SeaBank 2025 p.38", "2026-04-30"],
    ["INDUSTRY_14_DIGITAL_BANKS", "Q3_2026", "loans_idr_bn", 171890.0, "Dataindonesia 2026-11-17", "2026-11-17"],
    ["INDUSTRY_14_DIGITAL_BANKS", "Q3_2026", "dpk_idr_bn", 207810.0, "Dataindonesia 2026-11-17", "2026-11-17"],
    ["INDUSTRY_14_DIGITAL_BANKS", "Q3_2026", "ldr_pct", 82.71, "Dataindonesia 2026-11-17", "2026-11-17"],
]
write_csv("ref_industry_benchmark.csv",
          ["entity", "period", "metric", "value", "source", "source_date"], ref)

# ============================================================================
# 9. CUSTOMERS CSV (last_txn_date_master sengaja lagging -> sumber DQ test)
# ============================================================================
print("[8/8] Customers & kalibrasi akhir ...")
cust_rows = []
for i, c in enumerate(customers):
    # field master lagging: 6% nasabah punya last_txn_date yang tidak match
    ltd = None
    if c["join_date"] <= date(2025, 12, 31):
        ltd = MONTH_ENDS[11] - timedelta(days=random.randint(0, 40))
        if random.random() < 0.06:
            ltd = ltd - timedelta(days=random.randint(60, 200))
    cust_rows.append([
        c["customer_id"], c["join_date"].isoformat(), c["tenure_months_at_2025"],
        c["acquisition_channel"], c["city"], c["province"], c["age"], c["gender"],
        c["occupation"], c["monthly_income_band"], str(c["is_first_time_bank_user"]).lower(),
        c["kyc_status"], ltd.isoformat() if ltd else "",
        c["join_date"].isoformat() + " 00:00:00+07",
    ])
write_csv("customers.csv",
          ["customer_id", "join_date", "tenure_months_at_2025", "acquisition_channel",
           "city", "province", "age", "gender", "occupation", "monthly_income_band",
           "is_first_time_bank_user", "kyc_status", "last_txn_date_master", "created_at"],
          cust_rows)

write_csv("accounts.csv",
          ["account_id", "customer_id", "account_type", "open_date", "close_date",
           "status", "term_months", "interest_rate_pa", "principal"],
          [[a["account_id"], a["customer_id"], a["account_type"], a["open_date"].isoformat(),
            a["close_date"].isoformat() if a["close_date"] else "", a["status"],
            a["term_months"] if a["term_months"] else "", a["interest_rate_pa"],
            a["principal"] if a["principal"] else ""] for a in accounts])

# ---- ringkasan kalibrasi ----
total_pf_des = sum(r[3] for r in perf_rows if r[1].startswith("2025-12"))
npl_des = sum(r[4] for r in perf_rows if r[1].startswith("2025-12"))
direct_out = sum(r[7] for r in dl)
direct_npl = sum(r[7] for r in dl if r[8] > 90)
dep_bal = sum(a["principal"] for a in accounts if a["account_type"] == "DEPOSITO" and a["status"] == "ACTIVE")

calib.update({
    "target_ldr_pct": 92.32,
    "actual_ldr_pct": round((total_pf_des + direct_out) / T_DPK * 100, 2),
    "target_npl_pct": 1.82,
    "actual_npl_pct": round((npl_des + direct_npl) / (total_pf_des + direct_out) * 100, 2),
    "partner_npl_pct": round(npl_des / total_pf_des * 100, 2) if total_pf_des else None,
    "target_loans": T_LOANS,
    "actual_loans": total_pf_des + direct_out,
    "target_dpk": T_DPK,
    "actual_dpk_avg": round(casa_avg) + dep_bal,
    "actual_casa_ratio_pct": round(casa_avg / (casa_avg + dep_bal) * 100, 2),
    "npl_rescale_factor": round(k_npl, 4),
    "rows": {"customers": N_CUST, "accounts": len(accounts), "transactions": txn_seq + anom["dup"],
             "balances": len(bal_rows), "partners": len(partners)},
    "anomalies": anom,
    "notes": "NPL headline = (NPL mitra + NPL pinjaman langsung) / total kredit. "
             "CASA dihitung atas rata-rata saldo tabungan vs total DPK rata-rata.",
})
with open(os.path.join(DATA, "_calibration.json"), "w", encoding="utf-8") as f:
    json.dump(calib, f, indent=2, ensure_ascii=False)

print("\n=== KALIBRASI ===")
for k, v in calib.items():
    print(f"  {k}: {v}")
print("\nSelesai.")
