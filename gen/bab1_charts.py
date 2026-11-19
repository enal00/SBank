#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grafik Bab 1. Jalankan: uv run --with matplotlib python gen/bab1_charts.py"""
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
BIRU, ORANGE, ABU, MERAH = "#1f4e79", "#c55a11", "#8c8c8c", "#a61b1b"


def baca(nama):
    with open(os.path.join(OUT, nama), encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- grafik 1
k = baca("pooled_curve.csv")
x = [int(r["bulan_ke"]) for r in k]
orang = [float(r["retensi_orang_pct"]) for r in k]
uang = [float(r["retensi_uang_pct"]) for r in k]

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(x, orang, marker="o", ms=5, lw=2.2, color=BIRU, mfc="white", mew=1.8,
        label="Retensi orang (% nasabah masih aktif)", zorder=3)
ax.plot(x, uang, marker="s", ms=5, lw=2.2, color=ORANGE, mfc="white", mew=1.8,
        label="Retensi uang (% saldo tersisa)", zorder=4)
ax.axvspan(-0.3, 2.3, color="#f4f4f4", zorder=0)
ax.text(1.0, 97, "3 bulan pertama (M0–M2)\n62,9% dari seluruh kebocoran\nuang tahun pertama terjadi di sini",
        ha="center", va="top", fontsize=9, color="#3d3d3d", linespacing=1.35)
ax.annotate(f"{uang[2]:.1f}%", (2, uang[2]), textcoords="offset points", xytext=(6, -16),
            fontsize=9.5, color=ORANGE, fontweight="bold")
ax.annotate(f"{uang[-1]:.1f}%", (11, uang[-1]), textcoords="offset points", xytext=(-24, -16),
            fontsize=9.5, color=ORANGE, fontweight="bold")
ax.annotate(f"{orang[-1]:.1f}%", (11, orang[-1]), textcoords="offset points", xytext=(-24, 10),
            fontsize=9.5, color=BIRU, fontweight="bold")
ax.set_xlim(-0.3, 11.4)
ax.set_ylim(40, 104)
ax.set_xlabel("Bulan sejak bergabung (M0 = bulan bergabung)")
ax.set_ylabel("Indeks (%)")
ax.set_title("Retensi uang jatuh lebih cepat daripada retensi orang\n(kohort nasabah baru 2025, dipool per bulan-ke)",
             fontsize=13, loc="left", pad=12)
ax.legend(frameon=False, loc="upper right", fontsize=9.5)
ax.spines[["top", "right"]].set_visible(False)
fig.text(0.012, 0.015, "Catatan: titik M11 hanya berasal dari kohort Januari 2025 (n=600); titik lain gabungan beberapa kohort.",
         fontsize=8, color="#777777")
fig.tight_layout(rect=(0, 0.035, 1, 1))
fig.savefig(os.path.join(OUT, "g1_kurva_retensi.png"), dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- grafik 2
c = baca("retention_by_channel.csv")
pilih = ["PAYROLL", "SHOPEE_ECOSYSTEM", "ORGANIC", "PROMO_CAMPAIGN", "REFERRAL", "AGENT_MITRA"]
warna = {"PAYROLL": BIRU, "SHOPEE_ECOSYSTEM": "#2e75b6", "ORGANIC": "#7f9fbf",
         "PROMO_CAMPAIGN": ORANGE, "REFERRAL": "#c9a227", "AGENT_MITRA": ABU}
fig, ax = plt.subplots(figsize=(9, 5))
for ch in pilih:
    baris = sorted([r for r in c if r["channel"] == ch], key=lambda r: int(r["bulan_ke"]))
    xs = [int(r["bulan_ke"]) for r in baris]
    ys = [float(r["retensi_uang_pct"]) for r in baris]
    ax.plot(xs, ys, marker="o", ms=4, lw=2, color=warna[ch], label=ch.replace("_", " ").title())
ax.set_xlim(-0.3, 11.6)
ax.set_ylim(40, 104)
ax.set_xticks(range(12))
ax.set_xlabel("Bulan sejak bergabung")
ax.set_ylabel("Retensi uang (%)")
ax.set_title("Kanal mana yang uangnya betah?\n(retensi saldo per kanal akuisisi, kohort 2025, dipool per bulan-ke)",
             fontsize=13, loc="left", pad=12)
ax.legend(frameon=False, fontsize=9, loc="lower left", ncol=2)
ax.spines[["top", "right"]].set_visible(False)
fig.text(0.012, 0.015,
         "Titik M11 hanya dari kohort Januari 2025 (n kecil per kanal); titik lain gabungan beberapa kohort.",
         fontsize=8, color="#555555")
fig.tight_layout(rect=(0, 0.035, 1, 1))
fig.savefig(os.path.join(OUT, "g2_kanal.png"), dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- grafik 3
m5 = [r for r in c if r["bulan_ke"] == "5"]
m5.sort(key=lambda r: float(r["retensi_uang_pct"]), reverse=True)
nama = [r["channel"].replace("_", " ").title() for r in m5]
ro = [float(r["retensi_orang_pct"]) for r in m5]
ru = [float(r["retensi_uang_pct"]) for r in m5]
nn = [int(r["n"]) for r in m5]

fig, ax = plt.subplots(figsize=(9, 4.8))
for i, (a, b) in enumerate(zip(ro, ru)):
    ax.plot([b, a], [i, i], color="#d0d0d0", lw=3.2, zorder=1, solid_capstyle="round")
    ax.scatter(b, i, s=110, color=BIRU, zorder=4, edgecolor="white", linewidth=1.2)
    ax.scatter(a, i, s=110, color="#9dc3e6", zorder=3, edgecolor="white", linewidth=1.2)
    ax.text(90, i, f"−{a - b:.0f} pp", va="center", ha="right", fontsize=9.5,
            color=MERAH, fontweight="bold")
ax.scatter([], [], s=110, color="#9dc3e6", label="Retensi orang (% nasabah aktif)")
ax.scatter([], [], s=110, color=BIRU, label="Retensi uang (% saldo tersisa)")
ax.set_yticks(range(len(nama)))
ax.set_yticklabels(nama, fontsize=10)
ax.invert_yaxis()
ax.set_xlim(52, 91)
ax.set_xlabel("Retensi pada bulan ke-5 setelah bergabung (%)")
ax.set_title("Retensi orang hampir seragam — retensi uang terbelah 15 poin\n"
             "(kohort 2025; Payroll paling betah, Agent Mitra paling bocor)",
             fontsize=12.5, loc="left", pad=12)
ax.legend(frameon=False, fontsize=9.5, loc="upper center",
          bbox_to_anchor=(0.5, -0.16), ncol=2)
ax.grid(axis="y", visible=False)
ax.spines[["top", "right", "left"]].set_visible(False)
fig.text(0.012, 0.015,
         "n pada bulan ke-5: Payroll 285 · Referral 500 · Organic 1.238 · Shopee 1.200 · Promo 355 · Agent Mitra 560. "
         "Selisih di bawah 3 pp berada dalam rentang galat sampling.",
         fontsize=8.2, color="#555555")
fig.tight_layout(rect=(0, 0.10, 1, 1))
fig.savefig(os.path.join(OUT, "g3_orang_vs_uang.png"), dpi=170)
plt.close(fig)

print("grafik selesai:", [f for f in os.listdir(OUT) if f.endswith(".png")])
