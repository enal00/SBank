"""Hitung ulang konsentrasi saldo Desember 2025 dari ledger — pemeriksa independen.

Basis sama dengan gen/bab1_analysis.py: `closing_balance` rekening SAVINGS,
dijumlah per nasabah pada 31 Des 2025 (sumber: data/account_monthly_balances.csv).
Hasilnya harus identik dengan analysis/balance_concentration.csv; kalau tidak,
salah satu dari keduanya sudah basi.

Jalankan:  uv run --with duckdb python gen/verify_concentration.py
"""
import duckdb
import statistics

con = duckdb.connect()
con.execute("CREATE VIEW acc AS SELECT * FROM read_csv_auto('data/accounts.csv')")
con.execute("CREATE VIEW bal AS SELECT * FROM read_csv_auto('data/account_monthly_balances.csv')")

rows = con.execute("""
    SELECT a.customer_id, sum(b.closing_balance) AS saldo
    FROM bal b JOIN acc a USING (account_id)
    WHERE a.account_type = 'SAVINGS'
      AND strftime(CAST(b.month_end_date AS DATE), '%Y-%m') = '2025-12'
    GROUP BY 1
""").fetchall()

s = sorted((float(v) for _, v in rows), reverse=True)
n = len(s)
tot = sum(s)

print(f"nasabah dengan rekening tabungan Des-2025: {n:,}")
print(f"total saldo tabungan: Rp{tot/1e9:.3f} miliar")
for p in (0.01, 0.05, 0.10, 0.20, 0.50):
    k = max(1, int(round(n * p)))
    print(f"  top {int(p*100):>2}% ({k:>5,} org): Rp{sum(s[:k])/1e9:>6.3f} M = {100*sum(s[:k])/tot:>5.2f}%")
print(f"  median Rp{statistics.median(s):,.0f}")
print(f"  rata-rata Rp{tot/n:,.0f}")
print(f"  saldo < Rp100 ribu: {100*sum(1 for x in s if x < 100_000)/n:.1f}%")
print(f"  saldo = 0: {100*sum(1 for x in s if x == 0)/n:.1f}%")
