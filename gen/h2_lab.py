#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
H2 LAB — simulator: apakah alat uji promo memulihkan efek yang diketahui?

Mengapa ada berkas ini
----------------------
Pada dataset v1, H2 TIDAK DAPAT DIUJI: tarif promo tidak pernah dibayar ke
rekening, tidak ada penanda eksposur per nasabah, dan saldo tidak punya
mekanisme untuk merespons tarif. Kesimpulan "tidak ada efek" di sana adalah
konsekuensi desain, bukan temuan.

Di sini ketiga prasyarat dibangun, dan besarnya efek DITENTUKAN sendiri.
Karena kebenaran diketahui, alat ujinya bisa diuji: apakah ia menemukan
angka yang benar? Dan kalau gagal, apakah ia memberi tahu bahwa ia gagal?

Ini bukan klaim tentang SeaBank. Ini uji kelayakan alat sebelum dipakai.

Tiga prasyarat yang dibangun
----------------------------
1. Tarif promo benar-benar dibayar. Bunga tiap akun-bulan = saldo x tarif
   katalog x faktor realisasi 0,708 / 12 (0,708 dikalibrasi dari rasio
   terealisasi/katalog v1). Akun eligible menerima 4,00% x 0,708 = 2,83%
   selama Jul-Sep; akun kontrol tetap 3,50% x 0,708 = 2,48%.
2. Tabel eksposur level nasabah. Promo BERTINGKAT: eligible bila saldo
   30 Jun >= Rp2 juta. Desain "target = ALL" seperti katalog v1 tidak
   teridentifikasi karena tidak punya kelompok pembanding.
3. Elastisitas saldo terhadap tarif. Selama promo akun eligible menerima
   aliran dana luar f per bulan (fraksi saldo Juni). Setelah promo, fraksi
   h = 0,45 dari dana tambahan keluar sebagai hot money (60/25/15 di
   Okt/Nov/Des), sisanya menetap.

Dua dunia, satu alat
--------------------
DUNIA A ("asumsi terpenuhi"): saldo dasar = saldo Juni x indeks agregat x
goyangan yang menetap pada nasabah. Semua tumbuh dengan laju sama dari
level masing-masing, jadi tren sejajar di sekitar cutoff.

DUNIA B ("apa adanya"): saldo dasar = trajektori asli dataset v1, yang
sangat bergantung pada umur akun dan pola gaji. Tren TIDAK sejajar.

Alat ujinya sama pada kedua dunia. Perbandingannya menunjukkan dua hal:
apakah alat memulihkan efek saat syaratnya terpenuhi, dan apakah uji
placebo memberi peringatan saat syaratnya dilanggar.

Alat uji
--------
RD dengan DUA BAND BERSEBELAHAN di sekitar cutoff, bukan pencocokan 1:1:
kontrol = saldo Juni [c x (1-w), c), treated = [c, c x (1+w)).
Diuji pada w = 5% dan 10% (sensitivitas lebar band).

Efek = DiD pada total saldo kelompok, dalam log:
    [ln S_T(b) - ln S_T(a)] - [ln S_C(b) - ln S_C(a)]
    dikurangi versi jendela pra yang sama panjang.
Total kelompok dipakai karena derau saldo per nasabah di dataset ini
sangat besar (bisa berayun 10x antar bulan); total meredamnya. Galat baku
lewat bootstrap akun di dalam masing-masing band.

Jendela (semua 3 bulan):
  pra     Apr-Jun (indeks 3 -> 5)
  promo   Jun-Sep (indeks 5 -> 8)
  pasca   Sep-Des (indeks 8 -> 11)
  placebo Jan-Mar vs Apr-Jun

Dijalankan: uv run --with duckdb --with numpy python gen/h2_lab.py
"""
import csv
import os

import duckdb
import numpy as np

DATA, OUT = "data", "lab"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- parameter
CUTOFF = 2_000_000
BAND_W = (0.05, 0.10)                   # lebar band relatif, diuji dua-duanya
FAKTOR_REALISASI = 0.708                # dari rasio terealisasi/katalog v1
TARIF_DASAR, TARIF_PROMO = 3.50, 4.00
PROMO_MONTHS = (6, 7, 8)
POST_MONTHS = (9, 10, 11)
HOT_SPLIT = (0.60, 0.25, 0.15)
HOT_SHARE = 0.45
GRID_F = (0.002, 0.005, 0.010, 0.020, 0.040)
SEEDS = tuple(range(10))
BULAN = [f"2025-{i:02d}" for i in range(1, 13)]

# ---------------------------------------------------------------- baca data
con = duckdb.connect()
con.execute(f"CREATE VIEW bal AS SELECT * FROM read_csv_auto('{DATA}/account_monthly_balances.csv', header=true)")
con.execute(f"CREATE VIEW acc AS SELECT * FROM read_csv_auto('{DATA}/accounts.csv', header=true)")

ids = sorted(r[0] for r in con.execute(
    "SELECT DISTINCT customer_id FROM acc WHERE account_type = 'SAVINGS'").fetchall())
pos = {c: i for i, c in enumerate(ids)}
n = len(ids)

B0 = np.zeros((n, 12))
for cid, m, v in con.execute("""
        SELECT a.customer_id, CAST(strftime(CAST(b.month_end_date AS DATE), '%m') AS INT),
               sum(b.closing_balance)
        FROM bal b JOIN acc a USING (account_id)
        WHERE a.account_type = 'SAVINGS'
        GROUP BY 1, 2""").fetchall():
    B0[pos[cid], int(m) - 1] = float(v)

saldo_jun = B0[:, 5]
eligible = (saldo_jun >= CUTOFF).astype(int)

# ---------------------------------------------------------------- 1. eksposur
print("=== 1. EKSPOSUR (prasyarat 2) ===")
print(f"  eligible (saldo Jun >= Rp{CUTOFF:,.0f}) : {int(eligible.sum()):,} nasabah, "
      f"Rp{saldo_jun[eligible == 1].sum()/1e9:.3f} miliar")
print(f"  kontrol (saldo Jun <  Rp{CUTOFF:,.0f}) : {int(n - eligible.sum()):,} nasabah, "
      f"Rp{saldo_jun[eligible == 0].sum()/1e9:.3f} miliar")

with open(os.path.join(OUT, "exposure.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["customer_id", "campaign_id", "exposure_date", "eligible", "saldo_jun_idr"])
    for i in range(n):
        w.writerow([ids[i], "CMP001", "2025-07-01", int(eligible[i]),
                    round(float(saldo_jun[i]), 2)])

# ---------------------------------------------------------------- 2. dua dunia
indeks = B0.sum(axis=0) / B0.sum(axis=0)[0]
w_rel = indeks / indeks[5]

rng0 = np.random.default_rng(20251118)
efek_nasabah = rng0.normal(0, 0.10, n)
goyang = rng0.normal(0, 0.01, (n, 12))
BLAB = np.maximum(saldo_jun[:, None] * w_rel[None, :] * np.exp(efek_nasabah[:, None] + goyang), 0.0)

hidup = np.all(B0[:, [0, 3, 5, 8, 11]] > 0, axis=1)
print(f"  nasabah mature (saldo > 0 di Jan, Apr, Jun, Sep, Des): {int(hidup.sum()):,}")

DUNIA = {"A_paralel": BLAB, "B_trajektori_v1": B0}

band_mask = {}
for bw in BAND_W:
    mt = hidup & (saldo_jun >= CUTOFF) & (saldo_jun < CUTOFF * (1 + bw))
    mc = hidup & (saldo_jun >= CUTOFF * (1 - bw)) & (saldo_jun < CUTOFF)
    band_mask[bw] = (np.where(mt)[0], np.where(mc)[0])
    print(f"  band +/-{bw*100:.0f}%: treated {len(band_mask[bw][0]):,} akun "
          f"(Rp{saldo_jun[band_mask[bw][0]].sum()/1e9:.3f} M) | kontrol "
          f"{len(band_mask[bw][1]):,} akun (Rp{saldo_jun[band_mask[bw][1]].sum()/1e9:.3f} M)")


def bangun(f, seed, dasar):
    """Stok dana masuk menumpuk selama promo, lalu sebagian keluar setelahnya."""
    rng = np.random.default_rng(seed)
    mult = rng.lognormal(0.0, 0.6, n)
    mult /= mult.mean()
    per_bulan = dasar[:, 5] * f * mult
    inc = np.zeros((n, 12))
    stock = np.zeros(n)
    for m in PROMO_MONTHS:
        stock = stock + per_bulan
        inc[:, m] = stock
    sisa = stock.copy()
    for k, m in enumerate(POST_MONTHS):
        sisa = sisa - stock * HOT_SHARE * HOT_SPLIT[k]
        inc[:, m] = sisa
    return np.maximum(dasar + inc * eligible[:, None], 0.0)


# ---------------------------------------------------------------- 3. bunga
panel_kanonik = bangun(0.010, 0, BLAB)


def bunga_bulan(panel):
    hasil = []
    for m in range(12):
        tarif_el = TARIF_PROMO if m in PROMO_MONTHS else TARIF_DASAR
        b_el = panel[eligible == 1, m].sum() * tarif_el / 100 * FAKTOR_REALISASI / 12
        b_ct = panel[eligible == 0, m].sum() * TARIF_DASAR / 100 * FAKTOR_REALISASI / 12
        hasil.append((float(b_el), float(b_ct)))
    return hasil


bunga = bunga_bulan(panel_kanonik)

print("\n=== 2. PRASYARAT 1 — apakah tarif promo benar-benar dibayar? ===")
print(f"{'bulan':<9}{'katalog':>9}{'real.el':>10}{'rasio':>7}{'real.ktr':>10}{'rasio':>7}")
rows_rate = []
for m in range(12):
    kat = TARIF_PROMO if m in PROMO_MONTHS else TARIF_DASAR
    s_el = panel_kanonik[eligible == 1, m].sum()
    s_ct = panel_kanonik[eligible == 0, m].sum()
    r_el = bunga[m][0] / s_el * 1200
    r_ct = bunga[m][1] / s_ct * 1200
    rows_rate.append([BULAN[m], "YA" if m in PROMO_MONTHS else "TIDAK", f"{kat:.2f}",
                      round(bunga[m][0], 0), round(bunga[m][1], 0),
                      round(r_el, 3), round(r_el / kat, 3),
                      round(r_ct, 3), round(r_ct / TARIF_DASAR, 3)])
    print(f"{BULAN[m]:<9}{kat:>8.2f}%{r_el:>9.3f}%{r_el/kat:>7.2f}{r_ct:>9.3f}%{r_ct/TARIF_DASAR:>7.2f}")
with open(os.path.join(OUT, "interest_check.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["bulan", "dalam_promo", "tarif_katalog_pa_pct", "bunga_eligible_idr",
                "bunga_kontrol_idr", "tarif_terealisasi_eligible_pa_pct", "rasio_eligible",
                "tarif_terealisasi_kontrol_pa_pct", "rasio_kontrol"])
    w.writerows(rows_rate)

# ---------------------------------------------------------------- 4. estimator
def ln_total(panel, idx):
    return np.log(panel[idx].sum(axis=0))


def efek(panel, bw, target, dasar_a, dasar_b, pra=(3, 5)):
    """DiD log total: jendela dasar_a->dasar_b, dibersihkan jendela pra."""
    it, ic = band_mask[bw]
    lt, lc = ln_total(panel, it), ln_total(panel, ic)
    return float(((lt[dasar_b] - lt[dasar_a]) - (lc[dasar_b] - lc[dasar_a]))
                 - ((lt[pra[1]] - lt[pra[0]]) - (lc[pra[1]] - lc[pra[0]])))


def efek_boot(panel, bw, a, b, B=400, seed=0):
    rng = np.random.default_rng(seed)
    it, ic = band_mask[bw]
    T, C = panel[it], panel[ic]
    vals = np.empty(B)
    for k in range(B):
        lt = np.log(T[rng.integers(0, len(it), len(it))].sum(axis=0))
        lc = np.log(C[rng.integers(0, len(ic), len(ic))].sum(axis=0))
        vals[k] = ((lt[b] - lt[a]) - (lc[b] - lc[a])) \
            - ((lt[5] - lt[3]) - (lc[5] - lc[3]))
    return float(vals.std(ddof=1))


# ---------------------------------------------------------------- 5. validity
print("\n=== 3. UJI PLACEBO (Jan-Mar vs Apr-Jun) — seharusnya ~0 ===")
print(f"{'dunia':<20}{'band':>6}{'placebo pp':>12}{'SE pp':>9}{'t':>7}")
rows_valid = []
for nama, dasar in DUNIA.items():
    for bw in BAND_W:
        e = efek(dasar, bw, None, 0, 2)
        se = efek_boot(dasar, bw, 0, 2)
        print(f"{nama:<20}{bw*100:>5.0f}%{100*e:>11.3f}{100*se:>9.3f}{(e/se if se else 0):>7.1f}")
        rows_valid.append([nama, bw, round(100 * e, 3), round(100 * se, 3)])
with open(os.path.join(OUT, "design_check.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["dunia", "band", "placebo_pp", "se_pp"])
    w.writerows(rows_valid)

# ---------------------------------------------------------------- 6. recovery
print("\n=== 4. UJI PEMULIHAN — estimator vs kebenaran yang diketahui ===")
print(f"{'efek/bln':>9}{'dunia':>17}{'band':>6}{'promo asli':>11}{'promo est':>10}{'bias':>8}{'SE':>7}{'t':>6}"
      f"{'pasca asli':>11}{'pasca est':>10}{'bias':>8}")
grid, ring = [], []
for f in GRID_F:
    for nama, dasar in DUNIA.items():
        lt_b = np.log(dasar[eligible == 1].sum(axis=0))
        for seed in SEEDS:
            P = bangun(f, seed, dasar)
            lt_p = np.log(P[eligible == 1].sum(axis=0))
            tr_pr = 100 * ((lt_p[8] - lt_p[5]) - (lt_b[8] - lt_b[5]))
            tr_po = 100 * ((lt_p[11] - lt_p[8]) - (lt_b[11] - lt_b[8]))
            for bw in BAND_W:
                e_pr = 100 * efek(P, bw, None, 5, 8)
                e_po = 100 * efek(P, bw, None, 8, 11)
                grid.append([f, nama, bw, seed, round(tr_pr, 3), round(e_pr, 3),
                             round(tr_po, 3), round(e_po, 3)])
with open(os.path.join(OUT, "recovery_grid.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["f_per_bulan", "dunia", "band", "seed", "promo_asli_pp", "promo_est_pp",
                "pasca_asli_pp", "pasca_est_pp"])
    w.writerows(grid)

for f in GRID_F:
    for nama, dasar in DUNIA.items():
        for bw in BAND_W:
            rows = [r for r in grid if r[0] == f and r[1] == nama and r[2] == bw]
            pr = np.array([r[5] for r in rows]); po = np.array([r[7] for r in rows])
            t_pr, t_po = rows[0][4], rows[0][6]
            P0 = bangun(f, 0, dasar)
            se_pr = 100 * efek_boot(P0, bw, 5, 8)
            se_po = 100 * efek_boot(P0, bw, 8, 11)
            print(f"{f*100:>8.1f}%{nama:>17}{bw*100:>5.0f}%{t_pr:>11.2f}{pr.mean():>10.2f}"
                  f"{pr.mean()-t_pr:>8.2f}{se_pr:>7.3f}{(pr.mean()/se_pr if se_pr else 0):>6.1f}"
                  f"{t_po:>11.2f}{po.mean():>10.2f}{po.mean()-t_po:>8.2f}")
            ring.append([f, nama, bw, round(t_pr, 3), round(float(pr.mean()), 3),
                         round(float(pr.std(ddof=1)), 4), round(float(pr.mean() - t_pr), 3),
                         round(t_po, 3), round(float(po.mean()), 3),
                         round(float(po.std(ddof=1)), 4), round(se_pr, 4), round(se_po, 4)])
with open(os.path.join(OUT, "recovery_summary.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["f_per_bulan", "dunia", "band", "promo_asli_pp", "promo_est_pp",
                "promo_sd_antar_seed", "bias_pp", "pasca_asli_pp", "pasca_est_pp",
                "pasca_sd_antar_seed", "promo_se_boot_pp", "pasca_se_boot_pp"])
    w.writerows(ring)

# ---------------------------------------------------------------- 7. naif
print("\n=== 5. METRIK NAIF vs DiD (dunia A, band 5%) ===")
naif = []
for f in (0.010, 0.040):
    for seed in SEEDS[:3]:
        P = bangun(f, seed, BLAB)
        T = P[eligible == 1]
        s_jun, s_sep, s_des = T[:, 5].sum(), T[:, 8].sum(), T[:, 11].sum()
        it, ic = band_mask[0.05]
        lt, lc = ln_total(P, it), ln_total(P, ic)
        e_nt = 100 * ((lt[11] - lt[5]) - (lc[11] - lc[5]))
        naif.append([f, seed, round(s_des / s_sep * 100, 2), round(s_des / s_jun * 100, 2),
                     round(e_nt, 3)])
        print(f"  f={f*100:.1f}% seed={seed}  retensi naif Sep->Des = {s_des/s_sep*100:6.2f}%  "
              f"Des/Jun = {s_des/s_jun*100:6.2f}%   DiD net = {e_nt:+6.2f} pp")
with open(os.path.join(OUT, "naive_vs_did.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["f_per_bulan", "seed", "retensi_naif_sep_des_pct", "des_vs_jun_pct", "did_net_pp"])
    w.writerows(naif)

print("\nSelesai -> lab/: exposure.csv, interest_check.csv, design_check.csv, "
      "recovery_grid.csv, recovery_summary.csv, naive_vs_did.csv")
