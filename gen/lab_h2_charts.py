#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grafik laboratorium H2 (Bab 1b).

Jalankan: uv run --with matplotlib python gen/lab_h2_charts.py
Masukan:  lab/recovery_summary.csv (dari gen/h2_lab.py)
Keluaran: lab/g8_recovery.png
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LAB = os.path.abspath("lab")
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.edgecolor": "#cccccc", "axes.labelcolor": "#333333",
    "xtick.color": "#555555", "ytick.color": "#555555",
    "axes.grid": True, "grid.color": "#eeeeee", "grid.linewidth": 0.8,
    "figure.facecolor": "white",
})
BIRU, MERAH, ABU = "#1f4e79", "#a61b1b", "#8c8c8c"

with open(os.path.join(LAB, "recovery_summary.csv"), encoding="utf-8") as f:
    rows = list(csv.DictReader(f))


def fnum(r, k):
    return float(r[k])


dunia_label = {"A_paralel": "A", "B_trajektori_v1": "B"}
warna = {"A_paralel": BIRU, "B_trajektori_v1": MERAH}
penanda = {"0.05": "o", "0.1": "s"}

# ------------------------------------------------------------------ panel 1
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.4, 8.2),
                               gridspec_kw={"height_ratios": [1.25, 1]})

maks = 0.0
for dunia in dunia_label:
    for band in ("0.05", "0.1"):
        sel = [r for r in rows if r["dunia"] == dunia and r["band"] == band]
        x = [fnum(r, "promo_asli_pp") for r in sel]
        y = [fnum(r, "promo_est_pp") for r in sel]
        e = [fnum(r, "promo_se_boot_pp") for r in sel]
        maks = max(maks, max(x), max(y))
        ax1.errorbar(x, y, yerr=e, fmt=penanda[band], ms=6, lw=1.2, capsize=3,
                     color=warna[dunia], mfc="white", mew=1.6, alpha=0.95,
                     label=f"{'A' if dunia == 'A_paralel' else 'B'} · band {'5%' if band == '0.05' else '10%'}")

batas = maks * 1.06
ax1.plot([0, batas], [0, batas], color="#555555", lw=1.3, ls=(0, (4, 3)), zorder=1)
ax1.text(batas * 0.72, batas * 0.76, "estimasi = kebenaran", fontsize=9, color="#555555", rotation=34)
ax1.set_xlim(0, batas)
ax1.set_ylim(-2, batas)
ax1.axhline(0, color="#bbbbbb", lw=1)
ax1.set_xlabel("Efek sebenarnya yang saya tanam sendiri (pp)")
ax1.set_ylabel("Efek yang ditebak alat uji (pp)")
ax1.set_title("Uji pemulihan: apakah alat menebak efek yang saya tanam?\n"
              "(200 estimasi = 5 tingkat efek × 2 dunia × 2 band × 10 seed; batang = SE bootstrap 400)",
              fontsize=12.5, loc="left", pad=12)
ax1.legend(frameon=False, fontsize=8.8, loc="upper left", ncol=2)
ax1.spines[["top", "right"]].set_visible(False)
ax1.text(0.015, 0.03, "Dunia A menempel garis identitas → tebakan jujur.\nDunia B melebar dan meleset → alat hanya jujur kalau\nasumsi tren paralel benar.",
         transform=ax1.transAxes, fontsize=8.8, color="#333333", va="bottom",
         linespacing=1.4,
         bbox=dict(boxstyle="round,pad=0.45", fc="#f7f7f7", ec="#dddddd"))

# ------------------------------------------------------------------ panel 2
fs = sorted({fnum(r, "f_per_bulan") for r in rows})
for dunia in dunia_label:
    for band in ("0.05", "0.1"):
        sel = {fnum(r, "f_per_bulan"): r for r in rows
               if r["dunia"] == dunia and r["band"] == band}
        y = [fnum(sel[f], "bias_pp") for f in fs]
        ax2.plot([f * 100 for f in fs], y, marker=penanda[band], ms=5, lw=1.8,
                 color=warna[dunia], ls="-" if band == "0.05" else "--",
                 label=f"{'A' if dunia == 'A_paralel' else 'B'} · band {'5%' if band == '0.05' else '10%'}")

ax2.axhline(0, color="#777777", lw=1.2)
ax2.set_xlabel("Besar efek yang ditanam (pp per bulan)")
ax2.set_ylabel("Bias = tebakan − kebenaran (pp)")
ax2.set_title("Bias tidak hilang saat efek diperbesar — tapi efeknya tetap terbaca\n"
              "Dunia A: bias ≈ +0,3 s.d. +0,4 pp (kecil, stabil) · Dunia B: +3 s.d. +4 pp (besar)",
              fontsize=12, loc="left", pad=12)
ax2.legend(frameon=False, fontsize=8.8, loc="center right")
ax2.spines[["top", "right"]].set_visible(False)

fig.text(0.012, 0.012,
         "Sumber: lab/recovery_summary.csv. Bias dan SE dilaporkan bersama — vonis \"layak dipakai\" hanya berlaku untuk Dunia A.",
         fontsize=8.2, color="#555555")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(os.path.join(LAB, "g8_recovery.png"), dpi=170)
plt.close(fig)
print("grafik lab selesai: lab/g8_recovery.png")
