"""Eksplorasi cepat H3 — apakah data kredit cukup untuk menjawab pertanyaan Bab 3.

Bukan analisis final; hanya memeriksa bentuk data sebelum merancang bab.
"""
import duckdb

con = duckdb.connect()
for t in ("loan_partners", "partner_monthly_performance", "direct_loans",
          "ref_industry_benchmark", "accounts"):
    con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_csv_auto('data/{t}.csv')")

print("=" * 78)
print("A. MITRA KREDIT")
print("=" * 78)
for r in con.execute("""
    SELECT partner_id, partner_name, partner_type, scheme, risk_tier,
           onboard_date, revenue_share_pct
    FROM loan_partners ORDER BY risk_tier, partner_id
""").fetchall():
    print(f"  {r[0]:<6} {r[1][:26]:<26} {r[2][:14]:<14} {r[3][:12]:<12} tier={r[4]:<3} "
          f"onboard={r[5]} share={r[6]}%")

print()
print("=" * 78)
print("B. PORTOFOLIO PER BULAN (seluruh mitra)")
print("=" * 78)
print(f"  {'bulan':<8}{'disb (M)':>10}{'outst (M)':>11}{'npl (M)':>10}{'npl%':>8}{'dpd30 (M)':>11}{'borrower':>10}")
for r in con.execute("""
    SELECT strftime(CAST(month AS DATE), '%Y-%m') AS bln,
           round(sum(disbursement)/1e9, 2),
           round(sum(outstanding_balance)/1e9, 2),
           round(sum(npl_balance)/1e9, 2),
           round(100.0*sum(npl_balance)/nullif(sum(outstanding_balance),0), 2),
           round(sum(dpd_30_balance)/1e9, 2),
           sum(active_borrowers)
    FROM partner_monthly_performance GROUP BY 1 ORDER BY 1
""").fetchall():
    print(f"  {r[0]:<8}{r[1]:>10.2f}{r[2]:>11.2f}{r[3]:>10.2f}{r[4]:>8.2f}{r[5]:>11.2f}{r[6]:>10,}")

print()
print("=" * 78)
print("C. PER MITRA — Des 2025 (atau bulan terakhir) + pertumbuhan")
print("=" * 78)
print(f"  {'id':<6}{'tier':<5}{'outst (M)':>11}{'npl (M)':>10}{'npl%':>8}{'disb Jan':>10}{'disb Des':>10}{'tumb%':>8}")
rows = con.execute("""
    WITH des AS (
        SELECT p.partner_id, p.risk_tier,
               sum(m.outstanding_balance) FILTER (WHERE strftime(CAST(m.month AS DATE),'%Y-%m') = '2025-12') AS outst,
               sum(m.npl_balance)         FILTER (WHERE strftime(CAST(m.month AS DATE),'%Y-%m') = '2025-12') AS npl,
               sum(m.disbursement)        FILTER (WHERE strftime(CAST(m.month AS DATE),'%Y-%m') = '2025-01') AS d_jan,
               sum(m.disbursement)        FILTER (WHERE strftime(CAST(m.month AS DATE),'%Y-%m') = '2025-12') AS d_des
        FROM loan_partners p LEFT JOIN partner_monthly_performance m USING (partner_id)
        GROUP BY 1, 2
    )
    SELECT partner_id, risk_tier, round(outst/1e9,2), round(npl/1e9,2),
           round(100.0*npl/nullif(outst,0),2), round(d_jan/1e9,2), round(d_des/1e9,2),
           round(100.0*(d_des-nullif(d_jan,0))/nullif(d_jan,0),1)
    FROM des ORDER BY outst DESC
""").fetchall()
for r in rows:
    print(f"  {r[0]:<6}{r[1]:<5}{r[2]:>11.2f}{r[3]:>10.2f}{r[4]:>8.2f}"
          f"{r[5]:>10.2f}{r[6]:>10.2f}{r[7] if r[7] is not None else 0:>8.1f}")

print()
print("=" * 78)
print("D. DIRECT LOANS (2.000 pinjaman langsung ke nasabah)")
print("=" * 78)
for r in con.execute("""
    SELECT product, count(*), round(sum(principal)/1e9,2), round(sum(outstanding)/1e9,2),
           round(100.0*sum(outstanding) FILTER (WHERE status IN ('NPL','DEFAULT','DELINQUENT'))
                 /nullif(sum(outstanding),0),2) AS npl_pct,
           round(avg(dpd),1)
    FROM direct_loans GROUP BY 1 ORDER BY 3 DESC
""").fetchall():
    print(f"  {r[0]:<22} n={r[1]:>5,} principal=Rp{r[2]:>6.2f}M outst=Rp{r[3]:>6.2f}M "
          f"npl={r[4]:>5.2f}% avg_dpd={r[5]:>6.1f}")
print("  status:", con.execute(
    "SELECT status, count(*), round(sum(outstanding)/1e9,2) FROM direct_loans GROUP BY 1 ORDER BY 2 DESC"
).fetchall())
print("  dpd bucket:", con.execute("""
    SELECT CASE WHEN dpd = 0 THEN '0' WHEN dpd <= 30 THEN '1-30' WHEN dpd <= 90 THEN '31-90'
                WHEN dpd <= 180 THEN '91-180' ELSE '>180' END AS b,
           count(*), round(sum(outstanding)/1e9,2)
    FROM direct_loans GROUP BY 1 ORDER BY 1
""").fetchall())

print()
print("=" * 78)
print("E. TOLERANSI NPL — apa yang tersedia sebagai acuan")
print("=" * 78)
for r in con.execute("SELECT * FROM ref_industry_benchmark ORDER BY entity, metric").fetchall():
    print("  ", r)

print()
print("=" * 78)
print("F. APAKAH KREDIT MITRA MENYENTUH NASABAH KITA? (irisan dengan customers)")
print("=" * 78)
print(con.execute("""
    SELECT count(*) AS pinjaman_direct, count(DISTINCT customer_id) AS nasabah,
           count(DISTINCT customer_id) FILTER (WHERE customer_id IN (SELECT customer_id FROM accounts)) AS ada_rekening
    FROM direct_loans
""").fetchall())
print("  akun LOAN di accounts:", con.execute(
    "SELECT account_type, count(*), round(sum(principal)/1e9,2) FROM accounts GROUP BY 1 ORDER BY 2 DESC"
).fetchall())
