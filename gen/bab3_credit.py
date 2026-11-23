#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bab 3 — kredit & risiko mitra.

Menjawab dua pertanyaan berurutan:
  H3  : apakah pertumbuhan kredit digerakkan mitra berisiko tinggi?
  H3b : apakah NPL terkonsentrasi di segmen mitra tertentu, dan berapa rupiah
        kredit yang bisa ditumbuhkan tanpa melewati toleransi NPL?

Jalankan: uv run --with duckdb python gen/bab3_credit.py
Keluaran: analysis/h3_*.csv
"""
from __future__ import annotations

import csv
import os

import duckdb

OUT = os.path.abspath("analysis")
os.makedirs(OUT, exist_ok=True)

# Ambang NPL yang diuji. 1,82% = NPL gross SeaBank FY2025 (laporan tahunan),
# 3,00% = selera risiko internal yang lazim dipakai bank digital,
# 5,00% = batas NPL gross yang dipakai sebagai acuan industri.
AMBANG = [("1,82% (level SeaBank FY2025)", 0.0182),
          ("3,00% (selera risiko internal)", 0.0300),
          ("5,00% (acuan industri)", 0.0500)]

BLN = "strftime(CAST(month AS DATE), '%Y-%m')"

con = duckdb.connect()
for t in ("loan_partners", "partner_monthly_performance", "direct_loans"):
    con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_csv_auto('data/{t}.csv')")


def tulis(nama: str, header: list[str], rows: list[list]) -> None:
    with open(os.path.join(OUT, nama), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  tulis {nama}: {len(rows)} baris")


# ============================================================
# 1. PORTOFOLIO BULANAN (13 mitra digabung)
# ============================================================
bulanan = con.execute(f"""
    SELECT {BLN} AS bulan,
           sum(disbursement), sum(outstanding_balance), sum(npl_balance),
           sum(dpd_30_balance), sum(active_borrowers)
    FROM partner_monthly_performance GROUP BY 1 ORDER BY 1
""").fetchall()
tulis("h3_portofolio_bulanan.csv",
      ["bulan", "disburse_juta", "outstanding_miliar", "npl_juta", "npl_pct", "dpd30_juta"],
      [[b, round(d / 1e6, 1), round(o / 1e9, 3), round(n / 1e6, 1),
        round(100 * n / o, 2), round(p / 1e6, 1)] for b, d, o, n, p, _ in bulanan])

pertama, terakhir = bulanan[0], bulanan[-1]
OUT0, NPL0 = terakhir[2] / 1e9, terakhir[3] / 1e9
print(f"\n  Des 2025: outstanding Rp{OUT0:.3f} M · NPL Rp{NPL0:.3f} M "
      f"({100*NPL0/OUT0:.2f}%)")
print(f"  NPL rupiah Jan→Des: {100*(terakhir[3]-pertama[3])/pertama[3]:+.1f}% "
      f"| outstanding: {100*(terakhir[2]-pertama[2])/pertama[2]:+.1f}% "
      f"| rasio: {100*pertama[3]/pertama[2]:.2f}% → {100*NPL0/OUT0:.2f}%")

# ============================================================
# 2. RINGKASAN PER TIER
# ============================================================
tier = con.execute(f"""
    WITH j AS (
        SELECT p.risk_tier AS tier,
               sum(m.disbursement)        FILTER (WHERE {BLN} = '2025-01') AS d_jan,
               sum(m.disbursement)        FILTER (WHERE {BLN} = '2025-12') AS d_des,
               sum(m.outstanding_balance) FILTER (WHERE {BLN} = '2025-12') AS outst,
               sum(m.npl_balance)         FILTER (WHERE {BLN} = '2025-12') AS npl
        FROM loan_partners p JOIN partner_monthly_performance m USING (partner_id)
        GROUP BY 1
    ) SELECT tier, d_jan, d_des, outst, npl FROM j ORDER BY tier
""").fetchall()

tot_out = sum(r[3] for r in tier)
tot_npl = sum(r[4] for r in tier)
tot_delta = sum(r[2] - r[1] for r in tier)
tulis("h3_ringkasan_tier.csv",
      ["tier", "disburse_jan_juta", "disburse_des_juta", "tumbuh_pct",
       "outstanding_miliar", "npl_miliar", "npl_pct", "porsi_buku_pct",
       "porsi_npl_pct", "kenaikan_juta", "porsi_kenaikan_pct"],
      [[r[0], round(r[1] / 1e6, 1), round(r[2] / 1e6, 1),
        round(100 * (r[2] - r[1]) / r[1], 1), round(r[3] / 1e9, 3), round(r[4] / 1e9, 3),
        round(100 * r[4] / r[3], 2), round(100 * r[3] / tot_out, 1),
        round(100 * r[4] / tot_npl, 1), round((r[2] - r[1]) / 1e6, 1),
        round(100 * (r[2] - r[1]) / tot_delta, 1)] for r in tier])

# ============================================================
# 3. HEADROOM — berapa rupiah kredit baru sampai rasio menyentuh ambang
# ============================================================
# Rumus: (NPL0 + r_p*L) / (OUT0 + L) = T
#        -> L = (T*OUT0 - NPL0) / (r_p - T)      berlaku bila r_p > T
mitra = con.execute(f"""
    WITH d AS (
        SELECT p.partner_id, p.partner_name, p.risk_tier AS tier,
               sum(m.disbursement)        FILTER (WHERE {BLN} = '2025-01') AS d_jan,
               sum(m.disbursement)        FILTER (WHERE {BLN} = '2025-12') AS d_des,
               sum(m.outstanding_balance) FILTER (WHERE {BLN} = '2025-12') AS outst,
               sum(m.npl_balance)         FILTER (WHERE {BLN} = '2025-12') AS npl
        FROM loan_partners p JOIN partner_monthly_performance m USING (partner_id)
        GROUP BY 1, 2, 3
    ) SELECT * FROM d ORDER BY outst DESC
""").fetchall()


def headroom(r_p: float, ambang: float) -> float | None:
    """Rupiah kredit baru (miliar) yang masih menjaga rasio <= ambang.

    None = tidak dibatasi NPL (menambah kredit justru menurunkan rasio).
    """
    if r_p <= ambang:
        return None
    anggaran = ambang * OUT0 - NPL0
    if anggaran <= 0:
        return 0.0
    return anggaran / (r_p - ambang)


def r3(x):
    return "" if x is None else round(x, 3)


baris_mitra = []
for pid, nama, tier_mitra, d_jan, d_des, outst, npl in mitra:
    r_p = npl / outst if outst else 0.0
    h = {a: headroom(r_p, v) for a, v in AMBANG}
    baris_mitra.append([
        pid, nama, tier_mitra,
        round(outst / 1e9, 3), round(npl / 1e9, 3), round(100 * r_p, 2),
        round(d_jan / 1e6, 1), round(d_des / 1e6, 1),
        round(100 * (d_des - d_jan) / d_jan, 1) if d_jan else "",
        r3(h[AMBANG[0][0]]), r3(h[AMBANG[1][0]]), r3(h[AMBANG[2][0]]),
        "TIDAK" if h[AMBANG[0][0]] is None else "YA",
    ])
tulis("h3_ringkasan_mitra.csv",
      ["partner_id", "partner_name", "tier", "outstanding_miliar", "npl_miliar",
       "npl_pct", "disburse_jan_juta", "disburse_des_juta", "tumbuh_pct",
       "headroom_182_miliar", "headroom_300_miliar", "headroom_500_miliar",
       "dibatasi_npl_182"], baris_mitra)

# Skenario gabungan: anggaran risiko dipakai pada mitra dengan (r_p - T) terkecil.
# Mitra yang rasio NPL-nya hanya 0,10 pp di atas ambang dikecualikan: penyebutnya
# nyaris nol sehingga headroom meledak dan tidak bermakna secara bisnis.
AMBANG_STABIL = 0.0010
skenario = []
for label, T in AMBANG:
    anggaran = T * OUT0 - NPL0
    di_atas = [(r[5] / 100 - T, r[0], r[1], r[5], r[3]) for r in baris_mitra
               if r[5] / 100 > T]
    stabil = sorted(k for k in di_atas if k[0] >= AMBANG_STABIL)
    if anggaran <= 0:
        skenario.append([label, round(anggaran * 1e3, 1), 0, "-", "", "",
                         "anggaran risiko habis: NPL sekarang sudah di atas ambang", len(di_atas)])
        continue
    if not stabil:
        skenario.append([label, round(anggaran * 1e3, 1), "", "-", "", "",
                         f"{len(di_atas)} mitra di atas ambang tetapi semuanya <0,10 pp di atasnya — "
                         "model tidak stabil; secara praktis NPL tidak mengikat", len(di_atas)])
        continue
    jarak, pid, nama, r_p, outst = stabil[0]
    L = anggaran / jarak
    skenario.append([label, round(anggaran * 1e3, 1), round(L, 3), f"{pid} {nama}",
                     r_p, round(100 * L / outst, 0),
                     f"seluruh anggaran risiko habis di mitra termurah (r_p - T = {100*jarak:.2f} pp)",
                     len(di_atas)])
tulis("h3_headroom_skenario.csv",
      ["ambang", "anggaran_risiko_juta", "total_headroom_miliar", "mitra_penerima",
       "npl_mitra_pct", "headroom_vs_buku_sekarang_pct", "catatan",
       "mitra_di_atas_ambang"], skenario)
print("\n  Skenario headroom:")
for s in skenario:
    print(f"    {s[0]:<32} anggaran Rp{s[1]:>8.1f} jt → headroom {s[2]} M ({s[3]})")

# ------------------------------------------------------------
# 3b. ALOKASI — anggaran risiko yang sama, cara membagi berbeda
# ------------------------------------------------------------
# Pertanyaan yang dijawab: kalau toleransi NPL 1,82% dipegang, apakah hasilnya
# berubah tergantung ke mitra mana kredit baru disalurkan? (jawab: ya, 3–4x)
T = AMBANG[0][1]
anggaran = T * OUT0 - NPL0
peta = {r[0]: {"tier": r[2], "outst": r[3], "r_p": r[5] / 100} for r in baris_mitra}


def evaluasi(alokasi: dict[str, float]) -> tuple[float, float, float]:
    """Kembalikan (tambahan_kredit_miliar, npl_baru_miliar, rasio_baru_pct)."""
    npl_baru = NPL0 + sum(L * peta[p]["r_p"] for p, L in alokasi.items())
    out_baru = OUT0 + sum(alokasi.values())
    return sum(alokasi.values()), npl_baru, 100 * npl_baru / out_baru


alokasi_rows = []

# (1) bauran sekarang: tambah kredit mengikuti komposisi A–D yang ada
skala = 0.10  # contoh: buku tumbuh 10% dengan bauran yang sama
a1 = {p: skala * v["outst"] for p, v in peta.items()}
L1, _, r1 = evaluasi(a1)
alokasi_rows.append(["bauran sekarang (A–D proporsional)", "1,82%", round(L1, 3),
                     round(r1, 2),
                     f"rasio bertahan {r1:.2f}% — di bawah ambang, jadi NPL tidak membatasi"])

# (2) merata ke setiap mitra yang berada di atas ambang
atas = {p: v for p, v in peta.items() if v["r_p"] > T and v["r_p"] - T >= AMBANG_STABIL}
if atas:
    per_mitra = anggaran / sum(v["r_p"] - T for v in atas.values())
    a2 = {p: per_mitra for p in atas}
    L2, _, r2 = evaluasi(a2)
    alokasi_rows.append(["merata ke semua mitra di atas ambang", "1,82%", round(L2, 3),
                         round(r2, 2), f"{len(atas)} mitra × Rp{per_mitra:.3f} M"])

# (3) proporsional ke buku tier C+D (menaikkan porsi segmen berisiko)
cd = {p: v for p, v in peta.items() if v["tier"] in ("C", "D") and v["r_p"] > T}
if cd:
    s = anggaran / sum(v["outst"] * (v["r_p"] - T) for v in cd.values())
    a3 = {p: s * v["outst"] for p, v in cd.items()}
    L3, _, r3s = evaluasi(a3)
    alokasi_rows.append(["proporsional ke buku tier C+D", "1,82%", round(L3, 3),
                         round(r3s, 2),
                         f"buku C+D tumbuh {100*L3/sum(v['outst'] for v in cd.values()):.0f}%"])

# (4) optimal tanpa batas: seluruh anggaran ke mitra dengan (r_p − T) terkecil
if atas:
    p_min = min(atas, key=lambda p: atas[p]["r_p"] - T)
    L4 = anggaran / (peta[p_min]["r_p"] - T)
    L4, _, r4 = evaluasi({p_min: L4})
    alokasi_rows.append([f"optimal tanpa batas (seluruhnya ke {p_min})", "1,82%", round(L4, 3),
                         round(r4, 2),
                         f"= {100*L4/peta[p_min]['outst']:.0f}% buku {p_min} — tidak realistis "
                         "sebagai kapasitas satu mitra"])

# (5) bertahap: urut dari risiko termurah, tiap mitra maksimal +100% bukunya
sisa, a5, rincian = anggaran, {}, []
for p in sorted(atas, key=lambda p: atas[p]["r_p"] - T):
    if sisa <= 0:
        break
    kapasitas = peta[p]["outst"]  # +100% buku sekarang
    L = min(kapasitas, sisa / (peta[p]["r_p"] - T))
    if L <= 0:
        continue
    a5[p] = L
    sisa -= L * (peta[p]["r_p"] - T)
    rincian.append(f"{p} +Rp{L:.2f} M")
L5, _, r5 = evaluasi(a5)
alokasi_rows.append(["bertahap, tiap mitra maks +100% buku", "1,82%", round(L5, 3),
                     round(r5, 2), " · ".join(rincian)])

tulis("h3_headroom_alokasi.csv",
      ["strategi", "ambang", "tambahan_kredit_miliar", "npl_hasil_pct", "catatan"],
      alokasi_rows)
print("\n  Alokasi pada ambang 1,82%:")
for r in alokasi_rows:
    print(f"    {r[0]:<45} Rp{r[2]:>7.3f} M → NPL {r[3]:.2f}%  | {r[4]}")

# ============================================================
# 4. KREDIT LANGSUNG (di luar mitra)
# ============================================================
langsung = con.execute("""
    SELECT product, count(*), sum(CAST(principal AS DOUBLE)), sum(CAST(outstanding AS DOUBLE)),
           sum(CAST(outstanding AS DOUBLE)) FILTER (WHERE CAST(dpd AS INTEGER) > 90),
           sum(CAST(outstanding AS DOUBLE)) FILTER (WHERE CAST(dpd AS INTEGER) BETWEEN 1 AND 90),
           avg(CAST(dpd AS DOUBLE))
    FROM direct_loans GROUP BY 1 ORDER BY 4 DESC
""").fetchall()
tl_out = sum(r[3] for r in langsung)
tl_npl = sum(r[4] for r in langsung)
tulis("h3_kredit_langsung.csv",
      ["produk", "jumlah_pinjaman", "principal_miliar", "outstanding_miliar",
       "npl_pct", "dalam_perhatian_pct", "dpd_rata2", "porsi_outstanding_pct"],
      [[r[0], r[1], round(r[2] / 1e9, 3), round(r[3] / 1e9, 3),
        round(100 * r[4] / r[3], 2), round(100 * r[5] / r[3], 2),
        round(r[6], 1), round(100 * r[3] / tl_out, 1)]
       for r in langsung])
print(f"\n  Kredit langsung: outstanding Rp{tl_out/1e9:.3f} M · NPL (DPD>90) {100*tl_npl/tl_out:.2f}%")
print(f"  Kredit mitra + langsung = Rp{(tot_out + tl_out)/1e9:.3f} M")
print(f"  NPL gabungan = Rp{(tot_npl + tl_npl)/1e9:.3f} M / Rp{(tot_out + tl_out)/1e9:.3f} M "
      f"= {100*(tot_npl + tl_npl)/(tot_out + tl_out):.2f}%  (SeaBank FY2025: 1,82%)")

tulis("h3_kredit_langsung_status.csv",
      ["status", "jumlah_pinjaman", "outstanding_miliar"],
      [[r[0], r[1], round(r[2] / 1e9, 3)] for r in con.execute("""
          SELECT status, count(*), sum(CAST(outstanding AS DOUBLE))
          FROM direct_loans GROUP BY 1 ORDER BY 3 DESC
      """).fetchall()])

# ============================================================
# 5. KUALITAS DATA — yang harus ditulis jujur sebelum angka ini dikutip
# ============================================================
dep = con.execute("""
    SELECT count(*), sum(CAST(principal AS DOUBLE))
    FROM read_csv_auto('data/accounts.csv') WHERE account_type = 'DEPOSITO'
""").fetchone()
ab = con.execute("""
    SELECT min(active_borrowers), max(active_borrowers), count(DISTINCT active_borrowers)
    FROM partner_monthly_performance
""").fetchone()
rs = con.execute("SELECT min(revenue_share_pct), max(revenue_share_pct) FROM loan_partners").fetchone()
tulis("h3_kualitas_data.csv", ["temuan", "angka", "konsekuensi"], [
    ["Rekening DEPOSITO tanpa saldo bulanan di account_monthly_balances",
     f"{dep[0]:,} akun · principal Rp{dep[1]/1e9:.3f} M".replace(",", "."),
     "DPK ledger hanya tabungan Rp28,93 M → LDR ledger 111%, mustahil dengan CAR 23,29%. "
     "LDR tidak dipakai dari ledger; acuan memakai laporan tahunan 92,32%."],
    ["active_borrowers bergerak acak (tidak sejalan dengan portofolio)",
     f"{ab[0]:,}–{ab[1]:,} peminjam, {ab[2]} nilai berbeda".replace(",", "."),
     "Tidak dipakai untuk tiket rata-rata atau produktivitas mitra."],
    ["revenue_share_pct bernilai 0,56–0,75 tanpa satuan yang jelas",
     f"{rs[0]}–{rs[1]}",
     "Kalau persen, mustahil untuk skema bagi hasil; kalau pecahan (56–75%), masuk akal. "
     "Karena ambigu, analisis risk-adjusted return tidak dibangun di atas kolom ini."],
    ["npl_ratio di file mitra adalah salinan npl_balance/outstanding_balance",
     "konsisten 100%",
     "Dihitung ulang dari komponen mentah; tidak ada kontradiksi."],
])
print("\n  Kualitas data:")
for r in csv.DictReader(open(os.path.join(OUT, "h3_kualitas_data.csv"), encoding="utf-8")):
    print(f"    - {r['temuan']}: {r['angka']}")
