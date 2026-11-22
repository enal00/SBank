"""
RFM, market basket, dan agregat dana per segmen — semuanya dari data mentah.

Kenapa skrip ini ada:
  `analysis/rfm_analysis.csv` versi lama hanya berisi freq + monetary, tanpa
  skor R/F/M dan tanpa segmen, sehingga angka "sebaran Recency" di memo tidak
  bisa dilacak ke file mana pun. Skrip ini menghitung ulang dari
  `data/transactions.csv` (1.075.753 baris) dan menulis artefak yang bisa
  dibuka manusia maupun mesin:

    analysis/rfm_scored.csv    satu baris per nasabah + skor + segmen
    analysis/rfm_segments.csv  ringkasan per segmen (kecil, bisa dibaca)
    analysis/basket_categories.csv  volume per kategori merchant
    analysis/basket_pairs.csv       pasangan kategori yang muncul bersamaan

Aturan yang dipakai (ditulis eksplisit supaya bisa dibantah):
  Tanggal acuan   : 2025-12-31 (akhir data)
  R (recency)     : hari sejak transaksi terakhir ke tanggal acuan. Kecil = baru.
  F (frequency)   : jumlah transaksi pada 2025.
  M (monetary)    : total nominal transaksi masuk (direction == CR), rupiah.
  Skor 1-5        : kuintil berbasis peringkat (bukan batas nominal tetap),
                    supaya sebaran tetap 20/20/20/20/20 meski data miring.
  Nasabah tanpa transaksi 2025: R = hari sejak join_date, F = 0, M = 0.

Jalankan:  uv run python gen/bab2_rfm.py
"""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "analysis")
LAB = os.path.join(BASE, "lab")

REF_DATE = date(2025, 12, 31)


def read_customers() -> dict[str, dict]:
    out = {}
    with open(os.path.join(DATA, "customers.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out[r["customer_id"]] = r
    return out


def scan_transactions() -> tuple[dict, dict, dict, dict]:
    """Satu kali baca 129 MB: kumpulkan RFM + keranjang kategori per nasabah-bulan."""
    agg: dict[str, dict] = defaultdict(lambda: {"freq": 0, "monetary": 0.0, "last": None})
    basket: dict[tuple[str, str], set[str]] = defaultdict(set)
    cat_amount: dict[str, float] = defaultdict(float)
    cat_count: dict[str, int] = defaultdict(int)

    path = os.path.join(DATA, "transactions.csv")
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cid = r["customer_id"]
            d = date.fromisoformat(r["txn_date"])
            cat = r["merchant_category"] or "TIDAK_DIKETAHUI"

            a = agg[cid]
            a["freq"] += 1
            if a["last"] is None or d > a["last"]:
                a["last"] = d
            if r["direction"] == "CR":
                amt = float(r["amount"])
                a["monetary"] += amt

            basket[(cid, r["txn_date"][:7])].add(cat)
            cat_count[cat] += 1
            cat_amount[cat] += float(r["amount"])

    return agg, basket, cat_amount, cat_count


def quantile_scores(values: list[float], higher_is_better: bool = True) -> list[int]:
    """Skor 1-5 berbasis peringkat: 5 = paling baik (20% teratas), 1 = paling buruk.

    Nilai kembar mendapat skor sama. Peringkat dihitung dari ujung "terbaik",
    bukan dari ujung daftar, supaya arah skor tidak pernah terbalik.
    """
    n = len(values)
    key = (lambda i: values[i]) if higher_is_better else (lambda i: -values[i])
    order = sorted(range(n), key=key, reverse=True)  # index 0 = paling baik
    scores = [0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        mid = (i + j) / 2 / n  # 0.0 = terbaik, 1.0 = terburuk
        s = min(5, max(1, 5 - int(mid * 5)))
        for k in range(i, j + 1):
            scores[order[k]] = s
        i = j + 1
    return scores


def segment_of(r: int, f: int, m: int) -> str:
    """Aturan segmen eksplisit; urutan penting (yang paling spesifik lebih dulu)."""
    if f == 0:
        return "Tanpa transaksi 2025"
    if r <= 2 and f >= 4 and m >= 4:
        return "Tidak boleh hilang"
    if r >= 4 and f >= 4 and m >= 4:
        return "Juara"
    if r >= 3 and f >= 4:
        return "Loyal"
    if r <= 2 and f >= 3:
        return "Berisiko pergi"
    if r >= 4 and f <= 2:
        return "Baru / potensial"
    if r <= 2 and f <= 2 and m <= 2:
        return "Tidur"
    if r == 1 and f <= 2:
        return "Hilang"
    return "Perlu perhatian"


def pct(x: float, total: float) -> float:
    return 100.0 * x / total if total else 0.0


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    customers = read_customers()
    print(f"nasabah di master : {len(customers):,}")

    agg, basket, cat_amount, cat_count = scan_transactions()
    print(f"nasabah bertransaksi 2025: {len(agg):,}")
    print(f"nasabah-bulan di keranjang: {len(basket):,}")

    # ---- RFM mentah -------------------------------------------------------
    rows = []
    for cid, meta in customers.items():
        a = agg.get(cid)
        join = date.fromisoformat(meta["join_date"])
        if a and a["last"]:
            recency = (REF_DATE - a["last"]).days
        else:
            recency = (REF_DATE - join).days
        rows.append(
            {
                "customer_id": cid,
                "join_date": meta["join_date"],
                "channel": meta["acquisition_channel"],
                "city": meta["city"],
                "recency_days": recency,
                "freq": a["freq"] if a else 0,
                "monetary": round(a["monetary"], 2) if a else 0.0,
            }
        )

    r_scores = quantile_scores([float(x["recency_days"]) for x in rows], higher_is_better=False)
    f_scores = quantile_scores([float(x["freq"]) for x in rows], higher_is_better=True)
    m_scores = quantile_scores([float(x["monetary"]) for x in rows], higher_is_better=True)
    for i, x in enumerate(rows):
        x["r_score"], x["f_score"], x["m_score"] = r_scores[i], f_scores[i], m_scores[i]
        x["rfm_code"] = f"{r_scores[i]}{f_scores[i]}{m_scores[i]}"
        # nasabah tanpa transaksi 2025 dipisah lebih dulu: skor mereka 1/1/1
        # dan kalau dibiarkan akan menyamar sebagai segmen "Tidur"
        x["segment"] = (
            "Tanpa transaksi 2025" if x["freq"] == 0 else segment_of(r_scores[i], f_scores[i], m_scores[i])
        )

    # ---- saldo Juni per nasabah (kalau ada) ------------------------------
    saldo: dict[str, float] = {}
    eligible: dict[str, int] = {}
    exp_path = os.path.join(LAB, "exposure.csv")
    if os.path.exists(exp_path):
        with open(exp_path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                try:
                    saldo[r["customer_id"]] = float(r["saldo_jun_idr"])
                except (KeyError, ValueError):
                    pass
                try:
                    eligible[r["customer_id"]] = int(float(r.get("eligible", 0) or 0))
                except ValueError:
                    eligible[r["customer_id"]] = 0

    # ---- agregat per segmen ----------------------------------------------
    groups: dict[str, list[dict]] = defaultdict(list)
    for x in rows:
        groups[x["segment"]].append(x)

    total_m = sum(x["monetary"] for x in rows)
    total_saldo = sum(saldo.get(x["customer_id"], 0.0) for x in rows)

    seg_rows = []
    for seg, items in groups.items():
        monies = sorted(x["monetary"] for x in items)
        n = len(items)
        median = monies[n // 2] if n % 2 else (monies[n // 2 - 1] + monies[n // 2]) / 2
        seg_total_m = sum(monies)
        seg_saldo = sum(saldo.get(x["customer_id"], 0.0) for x in items)
        seg_rows.append(
            {
                "segment": seg,
                "customers": n,
                "pct_customers": round(pct(n, len(rows)), 2),
                "total_monetary": round(seg_total_m),
                "pct_monetary": round(pct(seg_total_m, total_m), 2),
                "avg_monetary": round(seg_total_m / n),
                "median_monetary": round(median),
                "avg_freq": round(sum(x["freq"] for x in items) / n, 1),
                "avg_recency_days": round(sum(x["recency_days"] for x in items) / n),
                "saldo_jun_idr": round(seg_saldo),
                "pct_saldo": round(pct(seg_saldo, total_saldo), 2),
                "eligible_promo_pct": round(pct(sum(eligible.get(x["customer_id"], 0) for x in items), n), 1),
            }
        )
    seg_rows.sort(key=lambda r: -r["pct_monetary"])

    with open(os.path.join(OUT, "rfm_segments.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(seg_rows[0].keys()))
        w.writeheader()
        w.writerows(seg_rows)

    rows.sort(key=lambda x: -x["monetary"])
    with open(os.path.join(OUT, "rfm_scored.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "customer_id", "join_date", "channel", "city",
                "recency_days", "freq", "monetary",
                "r_score", "f_score", "m_score", "rfm_code", "segment",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    # ---- market basket ---------------------------------------------------
    cat_rows = []
    total_cm = len(basket)
    for cat in sorted(cat_count, key=lambda c: -cat_count[c]):
        cm = sum(1 for s in basket.values() if cat in s)
        cat_rows.append(
            {
                "merchant_category": cat,
                "transactions": cat_count[cat],
                "customer_months": cm,
                "pct_customer_months": round(pct(cm, total_cm), 2),
                "total_amount_idr": round(cat_amount[cat]),
                "avg_amount_idr": round(cat_amount[cat] / cat_count[cat]),
            }
        )
    with open(os.path.join(OUT, "basket_categories.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cat_rows[0].keys()))
        w.writeheader()
        w.writerows(cat_rows)

    pair_count: dict[tuple[str, str], int] = defaultdict(int)
    for cats in basket.values():
        if len(cats) < 2:
            continue
        ordered = sorted(cats)
        for i in range(len(ordered)):
            for j in range(i + 1, len(ordered)):
                pair_count[(ordered[i], ordered[j])] += 1
    single = {r["merchant_category"]: r["customer_months"] for r in cat_rows}
    pair_rows = []
    for (a, b), c in sorted(pair_count.items(), key=lambda kv: -kv[1]):
        exp = single[a] * single[b] / total_cm if total_cm else 0
        pair_rows.append(
            {
                "category_a": a,
                "category_b": b,
                "customer_months_both": c,
                "lift": round(c / exp, 2) if exp else 0,
            }
        )
    with open(os.path.join(OUT, "basket_pairs.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pair_rows[0].keys()))
        w.writeheader()
        w.writerows(pair_rows)

    # ---- cetak ringkasan ke layar ---------------------------------------
    print(f"\n=== segmen (urut % monetary) ===")
    print(f"{'segmen':<22}{'nasabah':>8}{'%n':>7}{'%uang':>8}{'median Rp':>13}{'saldo Juni (miliar)':>22}")
    for r in seg_rows:
        print(
            f"{r['segment']:<22}{r['customers']:>8,}{r['pct_customers']:>7.1f}"
            f"{r['pct_monetary']:>8.1f}{r['median_monetary']:>13,}"
            f"{r['saldo_jun_idr'] / 1e9:>22.3f}"
        )
    top10 = rows[: max(1, len(rows) // 10)]
    print(
        f"\ntop 10% monetary = {pct(sum(x['monetary'] for x in top10), total_m):.1f}% total uang masuk"
    )
    print(f"total monetary semua nasabah = Rp{total_m / 1e9:.2f} miliar")
    print(f"total saldo Juni (exposure)  = Rp{total_saldo / 1e9:.3f} miliar")
    print(f"\n=== kategori merchant ===")
    for r in cat_rows:
        print(
            f"{r['merchant_category']:<14}{r['transactions']:>10,} txn"
            f"{r['customer_months']:>9,} nasabah-bulan ({r['pct_customer_months']:>5.1f}%)"
        )
    print(f"\npasangan kategori: {len(pair_rows)} · lift tertinggi:")
    for r in pair_rows[:5]:
        print(
            f"  {r['category_a']} + {r['category_b']}: {r['customer_months_both']:,} nasabah-bulan, lift {r['lift']}"
        )


if __name__ == "__main__":
    main()
