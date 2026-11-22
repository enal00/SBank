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

# ---------------------------------------------------------------- grafik 4
# jembatan: dari Rp100 yang masuk, ke mana perginya
d = [r for r in baca("retention_decomposition.csv")
     if r["kohort"] == "2025-01" and r["bulan_ke"] == "11"][0]
sisa = float(d["retensi_uang_pct"])
hilang_orang = abs(float(d["bocor_karena_orang_pp"]))
hilang_saldo = abs(float(d["bocor_karena_saldo_pp"]))
ret_orang = float(d["retensi_orang_pct"])
total_hilang = hilang_orang + hilang_saldo

def rp(x):
    """Rupiah satu desimal dengan koma desimal (konvensi Indonesia)."""
    return f"Rp{x:.1f}".replace(".", ",")


fig, ax = plt.subplots(figsize=(9.4, 3.8))
ax.barh(0, sisa, height=0.44, color=BIRU, zorder=2)
ax.barh(0, hilang_orang, left=sisa, height=0.44, color=MERAH, zorder=2)
ax.barh(0, hilang_saldo, left=sisa + hilang_orang, height=0.44, color=ORANGE, zorder=2)
ax.axvline(ret_orang, color="#333333", ls=(0, (4, 3)), lw=1.5, zorder=3)
ax.text(ret_orang - 1.5, 0.30,
        f"retensi orang {ret_orang:.2f}%\n({ret_orang:.0f} dari 100 nasabah masih ada)".replace(".", ","),
        ha="right", va="bottom", fontsize=9, color="#333333", linespacing=1.35)
ax.text(sisa / 2, 0, rp(sisa), ha="center", va="center", color="white",
        fontsize=16, fontweight="bold", zorder=4)
ax.text(sisa / 2, -0.30, "masih ada", ha="center", va="top", color=BIRU,
        fontsize=10, fontweight="bold")
ax.text(sisa + hilang_orang / 2, 0, rp(hilang_orang), ha="center", va="center",
        color="white", fontsize=13, fontweight="bold", zorder=4)
ax.text(70.5, -0.30, "ikut nasabah pergi", ha="left", va="top",
        color=MERAH, fontsize=9.5)
ax.annotate(f"{rp(hilang_saldo)} · saldo menyusut",
            xy=(sisa + hilang_orang + hilang_saldo / 2, 0.24), xytext=(84, 0.62),
            ha="center", fontsize=9.5, color=ORANGE,
            arrowprops=dict(arrowstyle="-", color=ORANGE, lw=1.1))
ax.set_xlim(0, 101)
ax.set_ylim(-0.85, 0.85)
ax.set_yticks([])
ax.set_xlabel("Rupiah per Rp100 dana di bulan bergabung")
ax.set_title(f"Dari Rp100 dana nasabah baru, {rp(sisa)} masih ada di bulan ke-12\n"
             "(kohort Januari 2025, n=600)",
             fontsize=12.5, loc="left", pad=12)
ax.grid(axis="y", visible=False)
ax.spines[["top", "right", "left"]].set_visible(False)
fig.text(0.012, 0.015,
         f"Dari {rp(total_hilang)} yang hilang: {rp(hilang_orang)} ikut nasabah pergi, "
         f"{rp(hilang_saldo)} menguap dari saldo. Cek: 68,33% × 87,11% = 59,53%.",
         fontsize=8.2, color="#555555")
fig.tight_layout(rect=(0, 0.055, 1, 1))
fig.savefig(os.path.join(OUT, "g4_dekomposisi.png"), dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- grafik 5
# dua penyakit, dua bentuk waktu
k = baca("pooled_curve.csv")
xs_all = [int(r["bulan_ke"]) for r in k]
orang_all = [float(r["retensi_orang_pct"]) for r in k]
uang_all = [float(r["retensi_uang_pct"]) for r in k]
bulan = list(range(1, 12))
d_uang = [uang_all[i - 1] - uang_all[i] for i in bulan]
d_orang = [orang_all[i - 1] - orang_all[i] for i in bulan]
awal_uang = sum(d_uang[:3]) / sum(d_uang) * 100
awal_orang = sum(d_orang[:3]) / sum(d_orang) * 100

fig, ax = plt.subplots(figsize=(9.4, 4.8))
w = 0.4
ax.bar([b - w / 2 for b in bulan], d_uang, width=w, color=ORANGE, label="Uang yang hilang (pp)")
ax.bar([b + w / 2 for b in bulan], d_orang, width=w, color=BIRU, label="Nasabah yang pergi (pp)")
ax.axvspan(0.55, 3.45, color="#f2f2f2", zorder=0)
ax.text(2.0, max(d_uang) * 1.02, f"3 bulan pertama: {awal_uang:.1f}% dari kebocoran uang\ntapi hanya {awal_orang:.1f}% dari kebocoran orang",
        ha="center", va="bottom", fontsize=9.2, color="#333333", linespacing=1.35)
ax.annotate(f"{d_uang[0]:.1f} pp", (1 - w / 2, d_uang[0]), textcoords="offset points",
            xytext=(0, 4), ha="center", fontsize=9, color=ORANGE, fontweight="bold")
ax.set_xticks(bulan)
ax.set_xticklabels([f"M{i}" for i in bulan])
ax.set_xlabel("Bulan sejak bergabung")
ax.set_ylabel("Hilang dibanding bulan sebelumnya (pp)")
ax.set_ylim(0, max(d_uang) * 1.28)
ax.set_title("Uang bocor menumpuk di awal, nasabah menguap merata\n"
             "(kohort 2025, penurunan per bulan, dipool per bulan-ke)",
             fontsize=12.5, loc="left", pad=12)
ax.legend(frameon=False, fontsize=9.5, loc="upper right")
ax.grid(axis="x", visible=False)
ax.spines[["top", "right"]].set_visible(False)
fig.text(0.012, 0.015,
         "Batang = penurunan retensi dibanding bulan sebelumnya. Total kebocoran setahun: uang 40,47 pp, orang 31,67 pp.",
         fontsize=8.2, color="#555555")
fig.tight_layout(rect=(0, 0.055, 1, 1))
fig.savefig(os.path.join(OUT, "g5_bentuk_waktu.png"), dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- grafik 6
# hipotesis "uang tidur": banyak orang, sedikit uang
dm = baca("dormant_money.csv")
n_cust = sum(int(r["n_nasabah"]) for r in dm)
n_dor = sum(int(r["n_dorman"]) for r in dm)
sal_des = sum(float(r["saldo_des_miliar"]) for r in dm)
sal_dor = sum(float(r["saldo_dorman_miliar"]) for r in dm)
pct_orang = n_dor / n_cust * 100
pct_uang = sal_dor / sal_des * 100

fig, ax = plt.subplots(figsize=(9.4, 3.5))
ax.barh([1], [pct_orang], height=0.42, color=BIRU)
ax.barh([0], [pct_uang], height=0.42, color=ORANGE)
ax.text(pct_orang + 0.8, 1, f"{pct_orang:.2f}%  ·  {n_dor:,} dari {n_cust:,} nasabah".replace(",", "."),
        va="center", fontsize=10.5, color=BIRU, fontweight="bold")
ax.text(pct_uang + 0.8, 0, f"{pct_uang:.2f}%  ·  Rp{sal_dor:.3f} miliar dari Rp{sal_des:.1f} miliar".replace(",", "."),
        va="center", fontsize=10.5, color=ORANGE, fontweight="bold")
ax.set_yticks([1, 0])
ax.set_yticklabels(["Porsi nasabah dorman", "Porsi DPK yang tertinggal\ndi rekening mereka"], fontsize=10)
ax.set_xlim(0, 34)
ax.set_xlabel("Persentase (%)")
ax.set_title("Hipotesis \"uang tidur\" gugur: 1 dari 5 nasabah pasif, tapi hanya 1 dari 46 rupiah\n"
             "(kondisi 31 Desember 2025, seluruh 24.000 nasabah)",
             fontsize=12.5, loc="left", pad=12)
ax.grid(axis="y", visible=False)
ax.spines[["top", "right", "left"]].set_visible(False)
fig.text(0.012, 0.015,
         "\"Dorman\" = tidak ada transaksi dan saldo di bawah ambang aktif selama 90 hari terakhir.",
         fontsize=8.2, color="#555555")
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.savefig(os.path.join(OUT, "g6_dorman.png"), dpi=170)
plt.close(fig)

# ---------------------------------------------------------------- grafik 7
# konsentrasi: ada, tapi tidak setajam dugaan
import re
bc = baca("balance_concentration.csv")
label = [r["segmen"].title() for r in bc]
aktual = [float(r["pct_saldo"]) for r in bc]
merata = [float(int(re.sub(r"\D", "", r["segmen"]))) for r in bc]

fig, ax = plt.subplots(figsize=(9.4, 4.6))
xpos = range(len(label))
ax.bar([x - 0.19 for x in xpos], aktual, width=0.36, color=BIRU, label="Pangsa saldo sebenarnya")
ax.bar([x + 0.19 for x in xpos], merata, width=0.36, color="#c9d6e3",
       label="Kalau saldo terbagi rata")
for x, v in zip(xpos, aktual):
    ax.text(x - 0.19, v + 1.2, f"{v:.1f}%", ha="center", fontsize=9.5, color=BIRU, fontweight="bold")
ax.axhline(55, color=MERAH, ls=(0, (5, 3)), lw=1.4)
ax.text(len(label) - 0.45, 56.5, "dugaan awal: top 5% > 55%", ha="right", fontsize=9, color=MERAH)
ax.set_xticks(list(xpos))
ax.set_xticklabels(label, fontsize=10)
ax.set_ylabel("Pangsa saldo (%)")
ax.set_ylim(0, 72)
ax.set_title("Konsentrasi ada, tapi tidak setajam dugaan — hipotesis H1a ditolak\n"
             "(pangsa saldo per kelompok saldo terbesar, 31 Desember 2025)",
             fontsize=12.5, loc="left", pad=12)
ax.legend(frameon=False, fontsize=9.5, loc="upper left")
ax.grid(axis="x", visible=False)
ax.spines[["top", "right"]].set_visible(False)
fig.text(0.012, 0.015,
         "Bandingkan dengan garis \"merata\": tanpa konsentrasi, top 5% hanya memegang 5% saldo. Konsentrasi nyata (6,6×) tetap jauh di bawah ambang yang saya duga.",
         fontsize=8.2, color="#555555")
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(os.path.join(OUT, "g7_konsentrasi.png"), dpi=170)
plt.close(fig)

print("grafik selesai:", [f for f in sorted(os.listdir(OUT)) if f.endswith(".png")])
