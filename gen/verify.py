import csv, os, collections, math

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def rows(f):
    with open(os.path.join(D, f), encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


# 1. DPK & CASA ratio dihitung ulang dari tabel mentah
acc_type = {}
dep = {}
for a in rows("accounts.csv"):
    acc_type[a["account_id"]] = a["account_type"]
    if a["account_type"] == "DEPOSITO" and a["status"] == "ACTIVE":
        dep[a["account_id"]] = float(a["principal"])

monthly = collections.defaultdict(float)
for b in rows("account_monthly_balances.csv"):
    if acc_type.get(b["account_id"]) == "SAVINGS":
        monthly[b["month_end_date"]] += float(b["closing_balance"])

casa = sum(monthly.values()) / len(monthly)
depo = sum(dep.values())
print("== DPK / CASA ==")
print(f"SAVINGS avg  : {casa:,.0f}")
print(f"DEPOSITO act : {depo:,.0f}")
print(f"DPK avg      : {casa + depo:,.0f}   (target 34,806,000,000)")
print(f"CASA RATIO   : {casa / (casa + depo) * 100:.2f}%   (target 70.74)")

# 2. LDR + NPL
out12 = npl12 = 0.0
for r in rows("partner_monthly_performance.csv"):
    if r["month"].startswith("2025-12"):
        out12 += float(r["outstanding_balance"])
        npl12 += float(r["npl_balance"])

dol = dnp = 0.0
for l in rows("direct_loans.csv"):
    o = float(l["outstanding"])
    dol += o
    if int(l["dpd"]) > 90:
        dnp += o

print("\n== KREDIT / LDR / NPL ==")
print(f"LOANS total  : {out12 + dol:,.0f}   (target 32,134,000,000)")
print(f"LDR          : {(out12 + dol) / (casa + depo) * 100:.2f}%   (target 92.32)")
print(f"NPL GROSS    : {(npl12 + dnp) / (out12 + dol) * 100:.2f}%   (target 1.82)")

# 3. Integritas rantai saldo per akun-bulan
bad = n = 0
for b in rows("account_monthly_balances.csv"):
    n += 1
    op, cl = float(b["opening_balance"]), float(b["closing_balance"])
    cr, dr = float(b["total_credit"]), float(b["total_debit"])
    if abs(op + cr - dr - cl) > 1.0:
        bad += 1
print("\n== INTEGRITAS ==")
print(f"BALANCE CHAIN: {bad:,} dari {n:,} akun-bulan tidak balance ({bad / n * 100:.3f}%)")

# 4. Anomali transaksi
ids = collections.Counter()
orphans = tot = 0
for t in rows("transactions.csv"):
    tot += 1
    ids[t["transaction_id"]] += 1
    if t["account_id"] not in acc_type:
        orphans += 1
dups = sum(c - 1 for c in ids.values() if c > 1)
print(f"TXN total    : {tot:,}")
print(f"ORPHAN txn   : {orphans:,} ({orphans / tot * 100:.2f}%)")
print(f"DUPLICATE id : {dups:,} ({dups / tot * 100:.2f}%)")

# 5. Konsentrasi saldo 31 Des
dec = {}
for b in rows("account_monthly_balances.csv"):
    if b["month_end_date"].startswith("2025-12") and acc_type.get(b["account_id"]) == "SAVINGS":
        dec[b["account_id"]] = float(b["closing_balance"])
v = sorted(dec.values(), reverse=True)
N = len(v)
S = sum(v)


def share(p):
    k = math.ceil(N * p)
    return sum(v[:k]) / S * 100


print("\n== KONSENTRASI SALDO (31 Des 2025) ==")
print(f"TOP 1%  : {share(0.01):5.1f}%")
print(f"TOP 5%  : {share(0.05):5.1f}%")
print(f"TOP 10% : {share(0.10):5.1f}%")
print(f"TOP 20% : {share(0.20):5.1f}%")
print(f"MEDIAN  : Rp{int(v[N // 2]):,}")
print(f"MEAN    : Rp{int(S / N):,}")
print(f"AKUN dgn saldo < Rp100rb: {sum(1 for x in v if x < 100000) / N * 100:.1f}%")
