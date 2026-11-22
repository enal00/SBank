"""
Bangun `analysis/rfm_viewer.html` — satu file HTML mandiri (tanpa server,
tanpa Python, tanpa internet) yang bisa dibuka dengan klik dua kali.

Kenapa ada:
  Tabel RFM punya 24.000 baris. CSV sebesar itu bisa dibuka di Excel, tapi
  tidak bisa dibaca. File ini menaruh seluruh data di dalam HTML-nya sendiri
  (bukan fetch, jadi tetap jalan saat dibuka dari file://), lalu menambahkan
  pencarian, filter segmen, pengurutan, dan pembagian halaman.

Jalankan setelah gen/bab2_rfm.py:
    uv run python gen/build_rfm_viewer.py
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "analysis")


def load_rows() -> list[dict]:
    path = os.path.join(OUT, "rfm_scored.csv")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_segments() -> list[dict]:
    path = os.path.join(OUT, "rfm_segments.csv")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build() -> None:
    rows = load_rows()
    segments = load_segments()

    cities = sorted({r["city"] for r in rows})
    channels = sorted({r["channel"] for r in rows})
    seg_names = [s["segment"] for s in segments]

    # data ringkas: [id, kota_idx, kanal_idx, R, F, M, kode, segmen_idx]
    data = [
        [
            r["customer_id"],
            cities.index(r["city"]),
            channels.index(r["channel"]),
            int(r["recency_days"]),
            int(r["freq"]),
            round(float(r["monetary"])),
            r["rfm_code"],
            seg_names.index(r["segment"]),
        ]
        for r in rows
    ]

    total_m = sum(r[5] for r in data)
    top10 = sorted((r[5] for r in data), reverse=True)[: max(1, len(data) // 10)]
    cards = {
        "nasabah": len(data),
        "uang_miliar": round(total_m / 1e9, 2),
        "top10": round(100 * sum(top10) / total_m, 1) if total_m else 0,
        "segmen": len(segments),
        "tanpa_txn": sum(1 for r in data if r[4] == 0),
    }
    seg_payload = [
        {
            "name": s["segment"],
            "n": int(s["customers"]),
            "pct_n": float(s["pct_customers"]),
            "pct_m": float(s["pct_monetary"]),
            "median": int(float(s["median_monetary"])),
            "avg_freq": float(s["avg_freq"]),
            "saldo": float(s["saldo_jun_idr"]),
            "pct_saldo": float(s["pct_saldo"]),
        }
        for s in segments
    ]

    payload = {
        "cities": cities,
        "channels": channels,
        "segments": seg_names,
        "rows": data,
        "cards": cards,
        "seg": seg_payload,
    }

    html = TEMPLATE.replace("__PAYLOAD__", json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    path = os.path.join(OUT, "rfm_viewer.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"ditulis: {path}  ({len(html) / 1024:.0f} KB, {len(data):,} baris)")
    print("segmen:", Counter(r[7] for r in data).most_common())


TEMPLATE = r"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RFM 24.000 nasabah — SeaBank (data sintetis)</title>
<style>
  :root{
    --bg:#fbfbfa; --card:#fff; --ink:#191919; --muted:#6b6b6b; --line:#e6e4e0;
    --accent:#0b5fff; --accent-soft:#eaf1ff; --good:#0a7f4f; --warn:#b4530a; --bad:#b3261e;
  }
  @media (prefers-color-scheme: dark){
    :root{ --bg:#16161a; --card:#1e1e24; --ink:#ececf0; --muted:#a0a0aa; --line:#2e2e38;
           --accent:#6ea8ff; --accent-soft:#22304a; }
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
       font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
  .wrap{max-width:1180px;margin:0 auto;padding:28px 20px 60px}
  h1{font-size:22px;margin:0 0 4px;letter-spacing:-.01em}
  .sub{color:var(--muted);font-size:13px;margin:0 0 22px}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:22px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
  .card .k{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
  .card .v{font-size:20px;font-weight:650;margin-top:3px;font-variant-numeric:tabular-nums}
  .card .u{font-size:11px;color:var(--muted)}
  h2{font-size:14px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);
     margin:26px 0 10px;font-weight:600}
  table{border-collapse:collapse;width:100%;background:var(--card);
        border:1px solid var(--line);border-radius:10px;overflow:hidden}
  th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
  th{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);
     background:var(--card);position:sticky;top:0;z-index:2;cursor:pointer;user-select:none}
  th:hover{color:var(--accent)}
  td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
  tbody tr:hover{background:var(--accent-soft)}
  .segsummary td:first-child{font-weight:600}
  .bar{height:5px;border-radius:3px;background:var(--line);position:relative;min-width:60px}
  .bar i{position:absolute;inset:0 auto 0 0;border-radius:3px;background:var(--accent)}
  .controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:14px 0}
  input[type=search],select{background:var(--card);color:var(--ink);border:1px solid var(--line);
      border-radius:8px;padding:8px 10px;font:inherit;min-width:150px}
  input[type=search]{min-width:240px}
  input[type=search]:focus,select:focus{outline:2px solid var(--accent);outline-offset:1px}
  .chips{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 6px}
  .chip{border:1px solid var(--line);background:var(--card);color:var(--muted);
        border-radius:999px;padding:5px 11px;font-size:12px;cursor:pointer}
  .chip[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#fff}
  .pager{display:flex;gap:8px;align-items:center;justify-content:flex-end;margin-top:12px;color:var(--muted);font-size:13px}
  button.pg{background:var(--card);border:1px solid var(--line);color:var(--ink);border-radius:8px;
            padding:6px 12px;cursor:pointer;font:inherit}
  button.pg:disabled{opacity:.4;cursor:default}
  .pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;
        background:var(--accent-soft);color:var(--accent)}
  .s-Juara{background:#e7f6ee;color:#0a7f4f}
  .s-Tidak{background:#fdecea;color:#b3261e}
  .s-Berisiko{background:#fff2e0;color:#b4530a}
  .s-Loyal{background:#e8f0ff;color:#0b5fff}
  .s-Tidur,.s-Tanpa{background:#f0f0f2;color:#6b6b6b}
  @media (prefers-color-scheme: dark){
    .s-Juara{background:#123524;color:#5fd39b}
    .s-Tidak{background:#3a1a17;color:#ff8a80}
    .s-Berisiko{background:#3a2a12;color:#ffb86b}
    .s-Loyal{background:#152540;color:#8ab4ff}
    .s-Tidur,.s-Tanpa{background:#26262e;color:#9a9aa4}
  }
  .note{color:var(--muted);font-size:12px;margin-top:18px;border-top:1px solid var(--line);padding-top:12px}
  @media print{ .controls,.pager,.chips{display:none} th{position:static} }
</style>
</head>
<body>
<div class="wrap">
  <h1>RFM — 24.000 nasabah SeaBank</h1>
  <p class="sub">Data <strong>sintetis</strong> skala 1:1.000 · periode 2025 · tanggal acuan 31 Des 2025 ·
     R = hari sejak transaksi terakhir, F = jumlah transaksi, M = total transaksi masuk.
     Skor 1–5 berbasis kuintil (5 = terbaik).</p>

  <div class="cards" id="cards"></div>

  <h2>Ringkasan per segmen</h2>
  <table class="segsummary"><thead><tr>
    <th>Segmen</th><th class="num">Nasabah</th><th class="num">% nasabah</th>
    <th class="num">% uang masuk</th><th class="num">Median uang masuk</th>
    <th class="num">Transaksi/bln</th><th class="num">Saldo Juni</th><th>Porsi saldo</th>
  </tr></thead><tbody id="segbody"></tbody></table>

  <h2>Semua nasabah</h2>
  <div class="chips" id="chips"></div>
  <div class="controls">
    <input type="search" id="q" placeholder="Cari ID nasabah, kota, atau kanal…" autocomplete="off">
    <select id="chan"><option value="">Semua kanal</option></select>
    <select id="per"><option value="50">50 baris</option><option value="100" selected>100 baris</option>
      <option value="250">250 baris</option><option value="1000">1.000 baris</option></select>
  </div>
  <table id="tbl"><thead><tr>
    <th data-k="0">ID</th><th data-k="1">Kota</th><th data-k="2">Kanal</th>
    <th class="num" data-k="3">R (hari)</th><th class="num" data-k="4">F</th>
    <th class="num" data-k="5">M (Rp)</th><th data-k="6">Kode</th><th data-k="7">Segmen</th>
  </tr></thead><tbody id="body"></tbody></table>
  <div class="pager">
    <span id="info"></span>
    <button class="pg" id="prev">← Sebelumnya</button>
    <button class="pg" id="next">Berikutnya →</button>
  </div>

  <p class="note">Dibuat oleh <code>gen/build_rfm_viewer.py</code> dari <code>analysis/rfm_scored.csv</code>.
     Seluruh data tertanam di dalam file ini — tidak butuh internet maupun server.
     Klik judul kolom untuk mengurutkan.</p>
</div>

<script>
const D = __PAYLOAD__;
const R = D.rows, C = D.cities, CH = D.channels, S = D.segments;

const fmtRp = n => "Rp" + n.toLocaleString("id-ID");
const fmtNum = n => n.toLocaleString("id-ID");

// kartu ringkasan
const cards = [
  ["Nasabah", fmtNum(D.cards.nasabah), "di master"],
  ["Uang masuk 2025", "Rp" + D.cards.uang_miliar.toLocaleString("id-ID", {maximumFractionDigits:1}) + " miliar", "total transaksi CR"],
  ["Top 10% kuasai", D.cards.top10 + "%", "dari total uang masuk"],
  ["Tanpa transaksi", fmtNum(D.cards.tanpa_txn), "nasabah pasif 2025"],
  ["Segmen", D.cards.segmen, "aturan RFM"],
];
document.getElementById("cards").innerHTML = cards.map(([k,v,u]) =>
  `<div class="card"><div class="k">${k}</div><div class="v">${v}</div><div class="u">${u}</div></div>`).join("");

// ringkasan segmen
const segBody = document.getElementById("segbody");
segBody.innerHTML = D.seg.map(s => {
  const cls = "s-" + s.name.split(" ")[0];
  const w = Math.min(100, s.pct_saldo);
  return `<tr>
    <td><span class="pill ${cls}">${s.name}</span></td>
    <td class="num">${fmtNum(s.n)}</td>
    <td class="num">${s.pct_n.toFixed(1)}%</td>
    <td class="num">${s.pct_m.toFixed(1)}%</td>
    <td class="num">${fmtRp(s.median)}</td>
    <td class="num">${s.avg_freq.toFixed(1)}</td>
    <td class="num">${fmtRp(Math.round(s.saldo))}</td>
    <td><div style="display:flex;align-items:center;gap:8px">
      <div class="bar"><i style="width:${w}%"></i></div><span class="num">${s.pct_saldo.toFixed(1)}%</span>
    </div></td></tr>`;
}).join("");

// chip filter segmen
const chips = document.getElementById("chips");
let activeSeg = new Set();
chips.innerHTML = S.map((name, i) =>
  `<button class="chip" data-i="${i}" aria-pressed="false">${name}</button>`).join("");
chips.addEventListener("click", e => {
  const b = e.target.closest(".chip"); if (!b) return;
  const i = +b.dataset.i;
  if (activeSeg.has(i)) { activeSeg.delete(i); b.setAttribute("aria-pressed","false"); }
  else { activeSeg.add(i); b.setAttribute("aria-pressed","true"); }
  page = 0; render();
});

// dropdown kanal
const chan = document.getElementById("chan");
CH.forEach((c, i) => chan.add(new Option(c.replace(/_/g," "), i)));

// state
let sortKey = 5, sortDir = -1, page = 0, per = 100, q = "", chanSel = "";
const qEl = document.getElementById("q"), perEl = document.getElementById("per");

qEl.addEventListener("input", () => { q = qEl.value.trim().toLowerCase(); page = 0; render(); });
perEl.addEventListener("change", () => { per = +perEl.value; page = 0; render(); });
chan.addEventListener("change", () => { chanSel = chan.value === "" ? "" : +chan.value; page = 0; render(); });

document.querySelectorAll("#tbl thead th").forEach(th => th.addEventListener("click", () => {
  const k = +th.dataset.k;
  if (sortKey === k) sortDir = -sortDir; else { sortKey = k; sortDir = (k === 0 || k === 1 || k === 2 || k === 6 || k === 7) ? 1 : -1; }
  page = 0; render();
}));

function filtered(){
  return R.filter(r => {
    if (activeSeg.size && !activeSeg.has(r[7])) return false;
    if (chanSel !== "" && r[2] !== chanSel) return false;
    if (q) {
      const hay = r[0].toLowerCase() + " " + C[r[1]].toLowerCase() + " " + CH[r[2]].toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

function render(){
  const rows = filtered();
  rows.sort((a,b) => {
    const x = a[sortKey], y = b[sortKey];
    if (typeof x === "string") return sortDir * x.localeCompare(y);
    return sortDir * (x - y);
  });
  const pages = Math.max(1, Math.ceil(rows.length / per));
  if (page >= pages) page = pages - 1;
  const slice = rows.slice(page*per, page*per + per);
  document.getElementById("body").innerHTML = slice.map(r => {
    const cls = "s-" + S[r[7]].split(" ")[0];
    return `<tr><td>${r[0]}</td><td>${C[r[1]]}</td><td>${CH[r[2]].replace(/_/g," ")}</td>
      <td class="num">${fmtNum(r[3])}</td><td class="num">${fmtNum(r[4])}</td>
      <td class="num">${fmtRp(r[5])}</td><td>${r[6]}</td>
      <td><span class="pill ${cls}">${S[r[7]]}</span></td></tr>`;
  }).join("");
  document.getElementById("info").textContent =
    `${fmtNum(rows.length)} nasabah · halaman ${page+1} dari ${pages}`;
  document.getElementById("prev").disabled = page === 0;
  document.getElementById("next").disabled = page >= pages - 1;
}
document.getElementById("prev").onclick = () => { page--; render(); window.scrollTo({top:400,behavior:"smooth"}); };
document.getElementById("next").onclick = () => { page++; render(); window.scrollTo({top:400,behavior:"smooth"}); };
render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build()
