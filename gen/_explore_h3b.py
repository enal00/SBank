"""Eksplorasi H3 tahap 2 — angka yang akan jadi tulang punggung Bab 3."""
import duckdb

con = duckdb.connect()
for t in ("loan_partners", "partner_monthly_performance", "direct_loans",
          "accounts", "account_monthly_balances", "ref_industry_benchmark"):
    con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_csv_auto('data/{t}.csv')")

M = "strftime(CAST(month AS DATE), '%Y-%m')"

print("=" * 78)
print("1. PER TIER — Des 2025 vs Jan 2025")
print("=" * 78)
rows = con.execute(f"""
    WITH j AS (
        SELECT p.risk_tier,
               sum(m.disbursement)        FILTER (WHERE {M} = '2025-01') AS d_jan,
               sum(m.disbursement)        FILTER (WHERE {M} = '2025-12') AS d_des,
               sum(m.outstanding_balance) FILTER (WHERE {M} = '2025-12') AS outst,
               sum(m.npl_balance)         FILTER (WHERE {M} = '2025-12') AS npl
        FROM loan_partners p JOIN partner_monthly_performance m USING (partner_id)
        GROUP BY 1
    )
    SELECT risk_tier, round(d_jan/1e6,1) d_jan_M, round(d_des/1e6,1) d_des_M,
           round(100.0*(d_des-d_jan)/d_jan,1) growth_pct,
           round(outst/1e9,3) outst_M, round(npl/1e9,3) npl_M,
           round(100.0*npl/nullif(outst,0),2) npl_pct
    FROM j ORDER BY risk_tier
""").fetchall()
tot_out = sum(r[4] for r in rows)
tot_npl = sum(r[5] for r in rows)
tot_djan = sum(r[1] for r in rows)
tot_ddes = sum(r[2] for r in rows)
print(f"  {'tier':<5}{'disb Jan':>10}{'disb Des':>10}{'tumb%':>8}{'outst':>10}{'npl':>8}{'npl%':>8}{'%buku':>8}{'%npl':>7}")
for r in rows:
    print(f"  {r[0]:<5}{r[1]:>10.1f}{r[2]:>10.1f}{r[3]:>8.1f}{r[4]:>10.3f}{r[5]:>8.3f}{r[6]:>8.2f}"
          f"{100*r[4]/tot_out:>8.1f}{100*r[5]/tot_npl:>7.1f}")
print(f"  {'TOTAL':<5}{tot_djan:>10.1f}{tot_ddes:>10.1f}{100*(tot_ddes-tot_djan)/tot_djan:>8.1f}"
      f"{tot_out:>10.3f}{tot_npl:>8.3f}{100*tot_npl/tot_out:>8.2f}{100:>8.1f}{100:>7.1f}")

print()
print("=" * 78)
print("2. DEKOMPOSISI PERTUMBUHAN: siapa menyumbang kenaikan disburse Jan→Des")
print("=" * 78)
delta = {r[0]: r[2] - r[1] for r in rows}
tot_delta = sum(delta.values())
for t, v in delta.items():
    print(f"  tier {t}: +Rp{v:.1f} juta = {100*v/tot_delta:.1f}% dari total kenaikan (+Rp{tot_delta:.1f} juta)")

print()
print("=" * 78)
print("3. JEBAKAN RASIO: NPL rupiah naik, NPL persen turun")
print("=" * 78)
for r in con.execute(f"""
    SELECT {M} AS bln, round(sum(npl_balance)/1e6,1), round(sum(outstanding_balance)/1e9,3),
           round(100.0*sum(npl_balance)/sum(outstanding_balance),2)
    FROM partner_monthly_performance WHERE {M} IN ('2025-01','2025-06','2025-12') GROUP BY 1 ORDER BY 1
""").fetchall():
    print(f"  {r[0]}: NPL Rp{r[1]:.1f} juta · outstanding Rp{r[2]:.3f} M · rasio {r[3]:.2f}%")

print()
print("=" * 78)
print("4. HEADROOM — berapa rupiah kredit baru sampai NPL menyentuh ambang T")
print("=" * 78)
print("  Rumus: (NPL0 + r_p*L) / (OUT0 + L) = T  ->  L = (T*OUT0 - NPL0) / (r_p - T)")
print("  Berlaku hanya bila r_p > T; kalau r_p < T, menambah kredit justru menurunkan rasio.")
for T in (0.05, 0.0182):
    print(f"\n  Ambang T = {T*100:.2f}%  (outstanding Rp{tot_out:.3f} M, NPL Rp{tot_npl:.3f} M)")
    for pid, tier, r_p, outst in con.execute(f"""
        SELECT p.partner_id, p.risk_tier,
               100.0*sum(m.npl_balance)/sum(m.outstanding_balance) AS r_p,
               sum(m.outstanding_balance)/1e9
        FROM loan_partners p JOIN partner_monthly_performance m USING (partner_id)
        WHERE {M} = '2025-12' GROUP BY 1,2 ORDER BY r_p DESC
    """).fetchall():
        rp = r_p / 100
        if rp <= T:
            print(f"    {pid} tier {tier}: NPL {r_p:4.2f}% < ambang -> tidak dibatasi NPL (malah menurunkan rasio)")
        else:
            L = (T * tot_out - tot_npl) / (rp - T)
            print(f"    {pid} tier {tier}: NPL {r_p:4.2f}% > ambang -> maks Rp{max(L,0):.3f} M kredit baru "
                  f"({max(L,0)/outst:.0f}% dari buku sekarang)" if L > 0 else
                  f"    {pid} tier {tier}: NPL {r_p:4.2f}% -> sudah melewati ambang, headroom 0")

print()
print("=" * 78)
print("5. APA YANG SEBENARNYA MENGIKAT: LDR, bukan NPL")
print("=" * 78)
acc = con.execute("SELECT account_type, count(*), round(sum(principal)/1e9,3) FROM accounts GROUP BY 1 ORDER BY 3 DESC").fetchall()
print("  jenis rekening:", acc)
dpk = con.execute(f"""
    SELECT strftime(CAST(month_end_date AS DATE),'%Y-%m') AS bln,
           round(sum(closing_balance)/1e9,3)
    FROM account_monthly_balances
    WHERE strftime(CAST(month_end_date AS DATE),'%Y-%m') = '2025-12'
    GROUP BY 1
""").fetchall()
print("  total saldo semua rekening Des:", dpk)
kredit = con.execute("""
    SELECT round(sum(outstanding)/1e9,3) FROM direct_loans
""").fetchone()[0]
print(f"  kredit mitra Rp{tot_out:.3f} M + kredit langsung Rp{kredit:.3f} M = Rp{tot_out+kredit:.3f} M")
print(f"  LDR dataset (Des): {100*(tot_out+kredit)/dpk[0][1]:.2f}%  |  SeaBank FY2025: 92,32%")
