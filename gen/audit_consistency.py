"""Pemeriksa konsistensi repo sebelum commit / sebelum pindah bab.

Tiga pemeriksaan:
  1. Setiap file yang disebut di markdown benar-benar ada.
  2. Angka kunci di dokumen cocok dengan CSV sumbernya (bukan hasil ketik tangan).
  3. Tidak ada rujukan ke file yang sudah dihapus.

Jalankan:  uv run python gen/audit_consistency.py
Keluar dengan kode 1 kalau ada yang GAGAL, supaya bisa dipakai sebagai gerbang.
"""
from __future__ import annotations

import csv
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

fails: list[str] = []
warns: list[str] = []


def ok(label: str) -> None:
    print(f"  OK    {label}")


def fail(label: str, detail: str = "") -> None:
    fails.append(f"{label} {detail}".strip())
    print(f"  GAGAL {label} {detail}".rstrip())


def warn(label: str, detail: str = "") -> None:
    warns.append(f"{label} {detail}".strip())
    print(f"  WARN  {label} {detail}".rstrip())


def md_text() -> dict[str, str]:
    out = {}
    for p in glob.glob("*.md") + glob.glob("docs/*.md"):
        out[p.replace(os.sep, "/")] = open(p, encoding="utf-8").read()
    return out


DOCS = md_text()
ALL_MD = "\n".join(DOCS.values())

# ─────────────────────────── 1. rujukan file ───────────────────────────
print("\n[1] Rujukan file di markdown")
refs: set[str] = set()
for path, txt in DOCS.items():
    base = os.path.dirname(path)
    for m in re.finditer(r"`([A-Za-z0-9_\-/]+\.(?:csv|py|sql|md|png|html|json))`", txt):
        p = m.group(1)
        if p.split("/")[0] in ("data", "analysis", "lab", "gen", "sql", "docs"):
            refs.add(p)
    for m in re.finditer(r"\]\(([^)\s]+\.(?:csv|py|sql|md|png|html))\)", txt):
        p = os.path.normpath(os.path.join(base, m.group(1))).replace(os.sep, "/")
        refs.add(p)

for p in sorted(refs):
    if os.path.exists(p):
        continue
    # data/ memang tidak di-commit — hanya peringatan
    (warn if p.startswith("data/") else fail)(f"rujukan hilang: {p}")
print(f"  {len(refs)} rujukan diperiksa")

# ─────────────────────────── 2. angka vs CSV ───────────────────────────
print("\n[2] Angka dokumen vs CSV sumber")


def must_contain(doc: str, needle: str, label: str) -> None:
    (ok if needle in DOCS.get(doc, "") else fail)(f"{label}: '{needle}' di {doc}")


# 2a. RFM — 9 segmen, jumlah nasabah harus 24.000
seg_rows = list(csv.DictReader(open("analysis/rfm_segments.csv", encoding="utf-8")))
seg = {r["segment"]: r for r in seg_rows}
total_n = sum(int(r["customers"]) for r in seg_rows)
(ok if total_n == 24_000 else fail)(f"total nasabah 9 segmen = {total_n:,}")
for name, expected_n in [("Juara", "4.725"), ("Tidak boleh hilang", "167"), ("Tanpa transaksi 2025", "2.429")]:
    n = f"{int(seg[name]['customers']):,}".replace(",", ".")
    (ok if n == expected_n else fail)(f"nasabah {name} = {n} (diharap {expected_n})")
    must_contain("docs/02_bab1_memo.md", n, f"nasabah {name} muncul di memo")

# 2b. top 10% pangsa uang masuk = 47,6%
scored = list(csv.DictReader(open("analysis/rfm_scored.csv", encoding="utf-8")))
mon = sorted((float(r["monetary"]) for r in scored), reverse=True)
tot_mon = sum(mon)
share10 = 100 * sum(mon[: len(mon) // 10]) / tot_mon
(ok if f"{share10:.1f}" == "47.6" else fail)(f"top 10% pangsa uang masuk = {share10:.1f}%")
must_contain("docs/02_bab1_memo.md", "47,6%", "pangsa top 10% muncul di memo")

# 2c. keranjang belanja — volume per kategori
cat = {r["merchant_category"]: r for r in csv.DictReader(open("analysis/basket_categories.csv", encoding="utf-8"))}
vol_total = sum(int(r["total_amount_idr"]) for r in cat.values())
(ok if f"{vol_total/1e9:.1f}" == "551.4" else fail)(f"total volume kategori = Rp{vol_total/1e9:.1f} miliar")
for k, expected in [("LAINNYA", "363,4"), ("F&B", "53,4"), ("E-COMMERCE", "18,4")]:
    v = f"{int(cat[k]['total_amount_idr'])/1e9:.1f}".replace(".", ",")
    (ok if v == expected else fail)(f"volume {k} = Rp{v} miliar (diharap {expected})")
    must_contain("docs/02_bab1_memo.md", f"Rp{v} miliar", f"volume {k} muncul di memo")

pairs = list(csv.DictReader(open("analysis/basket_pairs.csv", encoding="utf-8")))
max_lift = max(float(p["lift"]) for p in pairs)
(ok if f"{max_lift:.2f}" == "1.07" else fail)(f"lift tertinggi = {max_lift:.2f}")
must_contain("docs/02_bab1_memo.md", "1,00–1,07", "rentang lift muncul di memo")

# 2d. exposure — eligible vs kontrol
exp = list(csv.DictReader(open("lab/exposure.csv", encoding="utf-8")))
is_el = lambda r: str(r.get("eligible", "0")).strip() in ("1", "True", "true")  # noqa: E731
el = [r for r in exp if is_el(r)]
ko = [r for r in exp if not is_el(r)]
saldo = lambda rows: sum(float(r["saldo_jun_idr"] or 0) for r in rows)  # noqa: E731
(ok if (len(el), len(ko)) == (3032, 20968) else fail)(f"eligible {len(el):,} · kontrol {len(ko):,}")
(ok if f"{saldo(el)/1e9:.3f}" == "13.777" else fail)(f"saldo eligible Rp{saldo(el)/1e9:.3f} M")
(ok if f"{saldo(ko)/1e9:.3f}" == "10.605" else fail)(f"saldo kontrol Rp{saldo(ko)/1e9:.3f} M")

# 2e. Juara + eligible (klaim di memo §13)
by_id_rfm = {r["customer_id"]: r for r in scored}
by_id_exp = {r["customer_id"]: r for r in exp}
juara_el = [c for c in by_id_rfm if by_id_rfm[c]["segment"] == "Juara" and c in by_id_exp and is_el(by_id_exp[c])]
(ok if len(juara_el) == 1579 else fail)(f"Juara + eligible = {len(juara_el):,} (memo menulis 1.579)")
must_contain("docs/02_bab1_memo.md", "1.579", "Juara+eligible muncul di memo")

# 2f. konsentrasi saldo
conc = {r["segmen"]: r for r in csv.DictReader(open("analysis/balance_concentration.csv", encoding="utf-8"))}
(ok if conc["top 5%"]["pct_saldo"] == "32.97" else fail)(f"top 5% saldo = {conc['top 5%']['pct_saldo']}%")
must_contain("README.md", "32,97%", "top 5% saldo muncul di README")
must_contain("README.md", "63,36%", "top 20% saldo muncul di README")

# 2g. laporan kalibrasi §6 harus memakai angka konsentrasi yang sama (bukan angka basi)
for seg_name in ("top 1%", "top 5%", "top 10%", "top 20%"):
    want = f"{float(conc[seg_name]['pct_saldo']):.2f}".replace(".", ",") + "%"
    must_contain("docs/01_calibration_report.md", want, f"laporan kalibrasi: {seg_name} = {want}")
    if seg_name in ("top 5%", "top 20%"):
        must_contain("README.md", want, f"README: {seg_name} = {want}")

# ─────────────────────────── 3. sisa file lama ───────────────────────────
print("\n[3] Rujukan ke file yang sudah dihapus")
for dead in ("rfm_analysis.csv", "market_basket_analysis.csv"):
    hits = [p for p, t in DOCS.items() if dead in t]
    (fail if hits else ok)(f"tidak ada rujukan ke {dead}" + (f" (masih di {hits})" if hits else ""))
    if os.path.exists(f"analysis/{dead}"):
        warn(f"file lama masih ada di disk: analysis/{dead}")

# ─────────────────────────── ringkasan ───────────────────────────
print("\n" + "=" * 60)
print(f"GAGAL: {len(fails)} · PERINGATAN: {len(warns)}")
for f in fails:
    print(f"  - {f}")
print("=" * 60)
sys.exit(1 if fails else 0)
