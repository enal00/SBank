#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grafik Bab 3 — Kredit & Risiko Mitra.

Grafik yang dihasilkan:
  - g9_npl_dilemma.png        : Ilusi rasio NPL (NPL Rp naik +29,1%, rasio turun 1,90%→1,69%)
  - g10_tier_contribution.png  : Konsentrasi risiko (Tier C+D = 21,2% buku tapi 47,7% NPL)
  - g11_headroom.png           : Alokasi headroom kredit baru pada ambang NPL 1,82%

Jalankan: uv run --with matplotlib python gen/bab3_charts.py
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = os.path.abspath("analysis")
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.edgecolor": "#cccccc", "axes.labelcolor": "#333333",
    "xtick.color": "#555555", "ytick.color": "#555555",
    "axes.grid": True, "grid.color": "#eeeeee", "grid.linewidth": 0.8,
    "figure.facecolor": "white",
})
BIRU, ORANGE, ABU, MERAH, HIJAU = "#1f4e79", "#c55a11", "#777777", "#a61b1b", "#2e75b6"


def baca(nama: str) -> list[dict]:
    with open(os.path.join(OUT, nama), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- GRAFIK 9
# g9: Ilusi Rasio NPL — Outstanding naik +45.7%, NPL nominal naik +29.1%, rasio NPL % justru "turun"
b = baca("h3_portofolio_bulanan.csv")
bulan = [r["bulan"][5:] for r in b]  # '01', '02', ...
outst = [float(r["outstanding_miliar"]) for r in b]
npl_rp = [float(r["npl_juta"]) for r in b]
npl_pct = [float(r["npl_pct"]) for r in b]

fig, ax1 = plt.subplots(figsize=(9.5, 5))

color_out = BIRU
ax1.set_xlabel("Bulan (2025)")
ax1.set_ylabel("Outstanding Kredit Mitra (Rp Miliar)", color=color_out, fontweight="bold")
line1 = ax1.plot(bulan, outst, color=color_out, marker="o", lw=2.5, label="Outstanding (Rp Miliar)")
ax1.tick_params(axis="y", labelcolor=color_out)
ax1.set_ylim(18, 32)

ax2 = ax1.twinx()
color_npl = MERAH
ax2.set_ylabel("Rasio NPL Gross (%)", color=color_npl, fontweight="bold")
line2 = ax2.plot(bulan, npl_pct, color=color_npl, marker="s", lw=2.2, linestyle="--", label="Rasio NPL (%)")
ax2.tick_params(axis="y", labelcolor=color_npl)
ax2.set_ylim(1.5, 2.1)
ax2.grid(False)  # hindari grid ganda

# Annotations
ax1.annotate(f"Jan: Rp{outst[0]:.1f} M", (0, outst[0]), textcoords="offset points", xytext=(0, 10),
             ha="center", fontsize=9, color=color_out, fontweight="bold")
ax1.annotate(f"Des: Rp{outst[-1]:.1f} M (+45,7%)", (11, outst[-1]), textcoords="offset points", xytext=(-40, 12),
             fontsize=9, color=color_out, fontweight="bold")

ax2.annotate(f"Jan: {npl_pct[0]:.2f}%\n(Rp{npl_rp[0]:.1f} jt)", (0, npl_pct[0]), textcoords="offset points", xytext=(15, -10),
             fontsize=8.5, color=color_npl)
ax2.annotate(f"Des: {npl_pct[-1]:.2f}%\n(Rp{npl_rp[-1]:.1f} jt, +29,1%)", (11, npl_pct[-1]), textcoords="offset points", xytext=(-75, -25),
             fontsize=8.5, color=color_npl, fontweight="bold")

plt.title("Ilusi Rasio NPL: Rasio membaik (1,90% → 1,69%) padahal NPL nominal naik +29,1%\n(Pertumbuhan penyebut +45,7% menyamarkan pembengkakan kredit bermasalah)",
          fontsize=12, loc="left", pad=12)

fig.text(0.012, 0.015, "Catatan: NPL nominal naik dari Rp385,2 juta (Jan) menjadi Rp497,1 juta (Des). Rasio tampak membaik murni karena ekspansi outstanding.",
         fontsize=8, color="#777777")
fig.tight_layout(rect=(0, 0.035, 1, 1))
fig.savefig(os.path.join(OUT, "g9_npl_dilemma.png"), dpi=170)
plt.close(fig)


# ---------------------------------------------------------------- GRAFIK 10
# g10: Konsentrasi Risiko — Porsi Buku vs Porsi NPL per Risk Tier
t = baca("h3_ringkasan_tier.csv")
tiers = [f"Tier {r['tier']}" for r in t]
porsi_buku = [float(r["porsi_buku_pct"]) for r in t]
porsi_npl = [float(r["porsi_npl_pct"]) for r in t]
npl_pct_tier = [float(r["npl_pct"]) for r in t]

fig, ax = plt.subplots(figsize=(9, 5))
x_pos = list(range(len(tiers)))
width = 0.35

rects1 = ax.bar([p - width/2 for p in x_pos], porsi_buku, width, label="Porsi Buku Kredit (%)", color=BIRU)
rects2 = ax.bar([p + width/2 for p in x_pos], porsi_npl, width, label="Porsi Total NPL (%)", color=MERAH)

ax.set_ylabel("Persentase dari Total (%)")
ax.set_title("Konsentrasi Risiko: Tier C & D hanya 21,2% buku tapi menyumbang 47,7% NPL\n(Tier D memiliki rasio NPL 5,04% — telah menembus batas toleransi OJK 5,00%)",
             fontsize=12, loc="left", pad=12)
ax.set_xticks(x_pos)
ax.set_xticklabels([f"{t['tier']}\n(NPL: {npl_pct_tier[i]:.2f}%)" for i, t in enumerate(t)])
ax.legend(frameon=False, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)

for rect in rects1:
    h = rect.get_height()
    ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                textcoords="offset points", ha="center", va="bottom", fontsize=9, color=BIRU, fontweight="bold")

for rect in rects2:
    h = rect.get_height()
    ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h), xytext=(0, 3),
                textcoords="offset points", ha="center", va="bottom", fontsize=9, color=MERAH, fontweight="bold")

fig.text(0.012, 0.015, "Catatan: Tier A (Rp13,15 M outst, NPL 0,81%) | Tier B (Rp10,09 M outst, NPL 1,53%) | Tier C (Rp5,02 M outst, NPL 3,50%) | Tier D (Rp1,23 M outst, NPL 5,04%).",
         fontsize=8, color="#777777")
fig.tight_layout(rect=(0, 0.035, 1, 1))
fig.savefig(os.path.join(OUT, "g10_tier_contribution.png"), dpi=170)
plt.close(fig)


# ---------------------------------------------------------------- GRAFIK 11
# g11: Headroom Kredit Baru pada Ambang NPL 1,82% berdasarkan Strategi Alokasi
a = baca("h3_headroom_alokasi.csv")
# Filter strategi yang relevan untuk visualisasi perbandingan
strategi_names = [
    "Proporsional C+D\n(Fokus Mitra Berisiko)",
    "Merata ke Mitra\ndi atas Ambang",
    "Bauran Sekarang\n(A–D Proporsional)",
    "Bertahap\n(Maks +100% Buku)"
]
vals = [1.992, 2.108, 2.948, 3.006]  # dalam Miliar
catatan_npl = ["NPL 1.82%", "NPL 1.82%", "NPL 1.69%", "NPL 1.82%"]
colors = [ORANGE, ABU, BIRU, HIJAU]

fig, ax = plt.subplots(figsize=(9, 4.8))
bars = ax.barh(strategi_names, vals, color=colors, height=0.55)

ax.set_xlabel("Kapasitas Tambahan Kredit Baru (Rp Miliar)")
ax.set_title("Kapasitas Kredit Baru (Headroom) pada Ambang NPL 1,82%\n(Strategi bertahap menghasilkan +Rp3,01 M kredit baru tanpa menembus ambang NPL SeaBank)",
             fontsize=12, loc="left", pad=12)
ax.set_xlim(0, 3.6)
ax.spines[["top", "right"]].set_visible(False)

for bar, val, cat in zip(bars, vals, catatan_npl):
    w = bar.get_width()
    ax.annotate(f"Rp{val:.3f} M  ({cat})", xy=(w, bar.get_y() + bar.get_height() / 2),
                xytext=(8, 0), textcoords="offset points", ha="left", va="center",
                fontsize=9.5, fontweight="bold", color="#333333")

fig.text(0.012, 0.015, "Catatan: Anggaran risiko NPL tersisa Rp39,4 juta pada ambang 1,82%. Strategi bertahap mengalokasikan kredit ke P010, P004, dan P006 hingga batas kapasitas 100% buku.",
         fontsize=8, color="#777777")
fig.tight_layout(rect=(0, 0.035, 1, 1))
fig.savefig(os.path.join(OUT, "g11_headroom.png"), dpi=170)
plt.close(fig)

print("  tulis g9_npl_dilemma.png, g10_tier_contribution.png, g11_headroom.png")
