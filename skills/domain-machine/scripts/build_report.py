#!/usr/bin/env python3
"""
domain-machine: render the final report (HTML + Markdown) from an analysis file.

The analysis file is JSON written by the agent (schema: references/report_schema.md).
It points at one or more availability result files produced by check_domains.py
and optionally a handles file produced by check_handles.py.

Usage:
  build_report.py --analysis domain-research/acme/analysis.json
  build_report.py --analysis analysis.json --html report.html --md report.md
"""

import argparse
import html
import json
import sys
import time
from pathlib import Path

LABELS = {
    "en": {
        "title": "Domain report", "generated": "Generated", "mode": "Depth", "candidates": "Names explored",
        "checked": "Domains checked", "available": "Available", "top": "Top picks",
        "recommendation": "Recommendation", "matrix": "Full availability matrix", "filter": "Filter names...",
        "only_com": "Only names with .com available", "only_any": "Only names with something available",
        "name": "Name", "score": "Score", "strategy": "Strategy", "why": "Why", "risks": "Risks",
        "register": "Register", "price": "1st year / renewal", "premium": "PREMIUM", "aftermarket": "Taken, but maybe buyable",
        "next": "Next steps", "method": "Method & caveats", "sources": "Sources", "handles": "Handles",
        "trademark": "Trademark", "legend": "OK = available · – = taken · ~ = low confidence · ? = unknown",
        "caveat": ("Availability was checked against registry RDAP/WHOIS and public DNS at the time shown. "
                   "Nothing is guaranteed until checkout: names can be registered at any moment, and registries "
                   "may hold reserved or premium-priced names that look free. Trademark notes are preliminary "
                   "research, not legal advice."),
        "best": "Best domain", "alt": "Also free", "pron": "Say it", "domain": "Domain",
        "st_available": "available", "st_likely_available": "likely available", "st_taken": "taken",
        "st_likely_taken": "likely taken", "st_unknown": "unknown",
        "tm_clear": "clear", "tm_caution": "caution", "tm_conflict": "conflict", "tm_unchecked": "not checked",
    },
    "es": {
        "title": "Informe de dominios", "generated": "Generado", "mode": "Profundidad", "candidates": "Nombres explorados",
        "checked": "Dominios chequeados", "available": "Disponibles", "top": "Mejores opciones",
        "recommendation": "Recomendación", "matrix": "Matriz completa de disponibilidad", "filter": "Filtrar nombres...",
        "only_com": "Solo nombres con .com libre", "only_any": "Solo nombres con algo libre",
        "name": "Nombre", "score": "Puntaje", "strategy": "Estrategia", "why": "Por qué", "risks": "Riesgos",
        "register": "Registrar", "price": "1er año / renovación", "premium": "PREMIUM", "aftermarket": "Tomados, pero quizás comprables",
        "next": "Próximos pasos", "method": "Método y advertencias", "sources": "Fuentes", "handles": "Usuarios",
        "trademark": "Marca", "legend": "OK = libre · – = tomado · ~ = baja confianza · ? = desconocido",
        "caveat": ("La disponibilidad se verificó contra RDAP/WHOIS de cada registry y DNS público en el momento indicado. "
                   "Nada está garantizado hasta el checkout: cualquiera puede registrarlo en cualquier momento, y los registries "
                   "pueden tener nombres reservados o con precio premium que parecen libres. Las notas de marca son "
                   "investigación preliminar, no asesoramiento legal."),
        "best": "Mejor dominio", "alt": "También libres", "pron": "Se dice", "domain": "Dominio",
        "st_available": "libre", "st_likely_available": "probablemente libre", "st_taken": "tomado",
        "st_likely_taken": "probablemente tomado", "st_unknown": "desconocido",
        "tm_clear": "sin conflictos", "tm_caution": "precaución", "tm_conflict": "conflicto", "tm_unchecked": "sin verificar",
    },
    "pt": {
        "title": "Relatório de domínios", "generated": "Gerado", "mode": "Profundidade", "candidates": "Nomes explorados",
        "checked": "Domínios verificados", "available": "Disponíveis", "top": "Melhores opções",
        "recommendation": "Recomendação", "matrix": "Matriz completa de disponibilidade", "filter": "Filtrar nomes...",
        "only_com": "Só nomes com .com livre", "only_any": "Só nomes com algo livre",
        "name": "Nome", "score": "Nota", "strategy": "Estratégia", "why": "Por quê", "risks": "Riscos",
        "register": "Registrar", "price": "1º ano / renovação", "premium": "PREMIUM", "aftermarket": "Ocupados, mas talvez compráveis",
        "next": "Próximos passos", "method": "Método e ressalvas", "sources": "Fontes", "handles": "Usuários",
        "trademark": "Marca", "legend": "OK = livre · – = ocupado · ~ = baixa confiança · ? = desconhecido",
        "caveat": ("A disponibilidade foi verificada via RDAP/WHOIS dos registries e DNS público no momento indicado. "
                   "Nada é garantido até o checkout, e registries podem ter nomes reservados ou premium que parecem livres. "
                   "Notas de marca são pesquisa preliminar, não aconselhamento jurídico."),
        "best": "Melhor domínio", "alt": "Também livres", "pron": "Pronúncia", "domain": "Domínio",
        "st_available": "livre", "st_likely_available": "provavelmente livre", "st_taken": "ocupado",
        "st_likely_taken": "provavelmente ocupado", "st_unknown": "desconhecido",
        "tm_clear": "sem conflitos", "tm_caution": "cautela", "tm_conflict": "conflito", "tm_unchecked": "não verificado",
    },
}

STATUS_ORDER = {"available": 0, "likely_available": 1, "unknown": 2, "likely_taken": 3, "taken": 4, "invalid": 5}


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def money(v):
    return f"${v:,.2f}" if isinstance(v, (int, float)) else "—"


def register_links(domain):
    return [
        ("Porkbun", f"https://porkbun.com/checkout/search?q={domain}"),
        ("Namecheap", f"https://www.namecheap.com/domains/registration/results/?domain={domain}"),
        ("Cloudflare", "https://domains.cloudflare.com/"),
    ]


def paragraphs(text):
    """Very small markdown-lite: blank-line paragraphs, '- ' bullets, **bold**."""
    import re
    out, bullets = [], []
    def inline(t):
        t = esc(t)
        return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    for block in str(text or "").split("\n\n"):
        lines = [l for l in block.splitlines() if l.strip()]
        if lines and all(l.lstrip().startswith(("- ", "* ")) for l in lines):
            out.append("<ul>" + "".join(f"<li>{inline(l.lstrip()[2:])}</li>" for l in lines) + "</ul>")
        elif lines:
            out.append("<p>" + inline(" ".join(lines)) + "</p>")
    return "\n".join(out)


def load(analysis_path):
    a = json.loads(Path(analysis_path).read_text(encoding="utf-8"))
    base = Path(analysis_path).parent
    results = {}
    checked_at = None
    files = a.get("availability_files") or []
    if isinstance(files, str):
        files = [files]
    for f in files:
        p = (base / f) if not Path(f).is_absolute() else Path(f)
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("checked_at"):
            checked_at = d["checked_at"].replace("T", " ").replace("Z", " UTC")
        for r in d.get("results", []):
            prev = results.get(r["domain"])
            # later / higher-confidence results win (e.g. a porkbun-verified shortlist run)
            if not prev or r.get("confidence") == "high" or prev.get("confidence") != "high":
                results[r["domain"]] = r
    handles = {}
    hf = a.get("handles_file")
    if hf:
        p = (base / hf) if not Path(hf).is_absolute() else Path(hf)
        for h in json.loads(p.read_text(encoding="utf-8")):
            handles[h["name"]] = h
    return a, results, handles, checked_at


def build(a, results, handles, checked_at):
    lang = (a.get("language") or "en").split("-")[0].lower()
    L = dict(LABELS.get(lang, LABELS["en"]))
    L.update(a.get("labels") or {})
    proj = a.get("project", {})
    cands = a.get("candidates", [])
    cand_by_name = {c["name"].lower(): c for c in cands}

    tlds = a.get("tlds") or sorted({r["tld"] for r in results.values()})
    names = sorted({r["name"] for r in results.values() if r.get("status") != "invalid"})
    rows = []
    for n in names:
        c = cand_by_name.get(n, {})
        cells = {}
        for t in tlds:
            r = results.get(f"{n}.{t}")
            if r:
                cells[t] = {"s": r["status"], "p": r.get("price_registration"), "r": r.get("price_renewal"),
                            "pm": r.get("premium"), "m": r.get("method"), "d": r.get("detail")}
        rows.append({"name": n, "score": c.get("score"), "strategy": c.get("strategy", ""),
                     "cells": cells})

    n_checked = len(results)
    n_avail = sum(1 for r in results.values() if r["status"] == "available")
    generated = a.get("generated_at") or time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    # ---- top picks
    shortlist = a.get("shortlist") or []
    picks = []
    for d in shortlist:
        d = d.lower()
        name = d.split(".")[0]
        c = cand_by_name.get(name, {"name": name})
        r = results.get(d, {})
        alts = [f"{name}.{t}" for t in tlds if f"{name}.{t}" != d and
                results.get(f"{name}.{t}", {}).get("status") == "available"]
        picks.append((d, c, r, alts))

    def status_badge(r):
        s = r.get("status", "unknown")
        txt = L.get("st_" + s, L["st_unknown"])
        return f'<span class="badge b-{esc(s)}">{esc(txt)}</span>'

    cards = []
    for i, (d, c, r, alts) in enumerate(picks, 1):
        flags = c.get("risks") or c.get("flags") or []
        prem = f' <span class="badge b-premium">{L["premium"]}</span>' if r.get("premium") else ""
        h = handles.get(c.get("name", ""), {}).get("platforms", {})
        hs = " ".join(f'<span class="h h-{esc(v["status"])}">{esc(k)}</span>' for k, v in h.items()) if h else \
            " ".join(f'<span class="h h-{esc(v)}">{esc(k)}</span>' for k, v in (c.get("handles") or {}).items())
        tm = c.get("trademark")
        cards.append(f"""
<article class="card">
  <div class="card-head">
    <span class="rank">{i}</span>
    <h3 class="dom">{esc(d)}</h3>
    {status_badge(r)}{prem}
    <span class="score">{esc(c.get("score", ""))}</span>
  </div>
  <div class="meta">
    <span>{esc(c.get("strategy", ""))}</span>
    {f'<span>{L["pron"]}: <em>{esc(c["pronunciation"])}</em></span>' if c.get("pronunciation") else ""}
    <span>{L["price"]}: {money(r.get("price_registration"))} / {money(r.get("price_renewal"))}</span>
  </div>
  {f'<p class="why">{esc(c.get("rationale"))}</p>' if c.get("rationale") else ""}
  {('<ul class="risks">' + "".join(f"<li>{esc(x)}</li>" for x in flags) + "</ul>") if flags else ""}
  <div class="foot">
    {f'<div><span class="k">{L["trademark"]}</span> <span class="tm tm-{esc(tm)}">{esc(L.get("tm_" + str(tm), tm))}</span></div>' if tm else ""}
    {f'<div><span class="k">{L["handles"]}</span> {hs}</div>' if hs else ""}
    {f'<div><span class="k">{L["alt"]}</span> {esc(", ".join(alts[:6]))}</div>' if alts else ""}
    <div class="links">{" ".join(f'<a href="{esc(u)}" target="_blank" rel="noopener">{esc(n)}</a>' for n, u in register_links(d))}</div>
  </div>
</article>""")

    after = a.get("aftermarket") or []
    after_html = ""
    if after:
        after_html = f"<section><h2>{L['aftermarket']}</h2><ul class='plain'>" + "".join(
            f"<li><strong>{esc(x.get('domain'))}</strong> — {esc(x.get('note', ''))}"
            + (f" <a href='{esc(x['url'])}' target='_blank' rel='noopener'>↗</a>" if x.get("url") else "")
            + "</li>" for x in after) + "</ul></section>"
    nxt = a.get("next_steps") or []
    next_html = (f"<section><h2>{L['next']}</h2><ol>" + "".join(f"<li>{esc(x)}</li>" for x in nxt)
                 + "</ol></section>") if nxt else ""
    srcs = a.get("sources") or []
    src_html = (f"<section><h2>{L['sources']}</h2><ul class='plain small'>" + "".join(
        f"<li><a href='{esc(s.get('url'))}' target='_blank' rel='noopener'>{esc(s.get('title') or s.get('url'))}</a></li>"
        for s in srcs) + "</ul></section>") if srcs else ""

    data = json.dumps({"tlds": tlds, "rows": rows}, ensure_ascii=False).replace("</", "<\\/")
    title = f"{proj.get('name') or 'Project'} · {L['title']}"

    page = f"""<!doctype html>
<html lang="{esc(lang)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>
:root {{
  --bg:#f7f7f5; --panel:#ffffff; --ink:#1b1b1a; --muted:#6b6b66; --line:#e4e3de; --accent:#2f5bea;
  --ok:#1f8a4c; --ok-bg:#e3f4ea; --no:#9a9a94; --no-bg:#efefec; --warn:#a86a00; --warn-bg:#fbf0d9;
  --bad:#b4232a; --bad-bg:#fbe4e4;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#121211; --panel:#1b1b1a; --ink:#ecebe6; --muted:#9d9c96; --line:#2c2c2a; --accent:#7d9bff;
    --ok:#5fd394; --ok-bg:#16301f; --no:#6f6f6a; --no-bg:#222220; --warn:#f0b54a; --warn-bg:#33270f;
    --bad:#ff7b7b; --bad-bg:#3a1a1a;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#121211; --panel:#1b1b1a; --ink:#ecebe6; --muted:#9d9c96; --line:#2c2c2a; --accent:#7d9bff;
  --ok:#5fd394; --ok-bg:#16301f; --no:#6f6f6a; --no-bg:#222220; --warn:#f0b54a; --warn-bg:#33270f;
  --bad:#ff7b7b; --bad-bg:#3a1a1a;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:15px/1.55 ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
main {{ max-width:1080px; margin:0 auto; padding:40px 16px 80px; }}
h1 {{ font-size:28px; letter-spacing:-.02em; margin:0 0 4px; }}
h2 {{ font-size:19px; margin:44px 0 14px; letter-spacing:-.01em; }}
.sub {{ color:var(--muted); margin:0 0 20px; max-width:70ch; }}
.stats {{ display:flex; flex-wrap:wrap; gap:10px; margin:18px 0 0; }}
.stat {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:10px 14px; min-width:120px; }}
.stat b {{ display:block; font-size:22px; font-variant-numeric:tabular-nums; }}
.stat span {{ color:var(--muted); font-size:12.5px; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:14px; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 16px 14px; }}
.card-head {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; }}
.rank {{ width:24px; height:24px; border-radius:50%; background:var(--ink); color:var(--bg); font-size:12px;
  display:inline-flex; align-items:center; justify-content:center; font-weight:600; }}
.dom {{ font:600 18px/1.2 ui-monospace, "SF Mono", Menlo, Consolas, monospace; margin:0; word-break:break-all; }}
.score {{ margin-left:auto; font-weight:700; font-variant-numeric:tabular-nums; }}
.meta {{ display:flex; flex-wrap:wrap; gap:4px 14px; color:var(--muted); font-size:13px; margin:8px 0 6px; }}
.why {{ margin:6px 0; }}
.risks {{ margin:6px 0; padding-left:18px; color:var(--warn); font-size:13.5px; }}
.foot {{ border-top:1px solid var(--line); margin-top:10px; padding-top:10px; display:grid; gap:6px; font-size:13px; }}
.k {{ color:var(--muted); margin-right:4px; }}
.links a {{ color:var(--accent); margin-right:12px; text-decoration:none; font-weight:500; }}
.links a:hover {{ text-decoration:underline; }}
.badge {{ font-size:11.5px; padding:2px 8px; border-radius:99px; font-weight:600; }}
.b-available {{ background:var(--ok-bg); color:var(--ok); }}
.b-likely_available, .b-unknown {{ background:var(--warn-bg); color:var(--warn); }}
.b-taken, .b-likely_taken {{ background:var(--no-bg); color:var(--no); }}
.b-premium {{ background:var(--bad-bg); color:var(--bad); }}
.h {{ display:inline-block; font-size:12px; padding:0 6px; border-radius:4px; margin-right:3px; }}
.h-free {{ background:var(--ok-bg); color:var(--ok); }}
.h-taken {{ background:var(--no-bg); color:var(--no); text-decoration:line-through; }}
.h-unknown {{ background:var(--warn-bg); color:var(--warn); }}
.tm {{ font-weight:600; }} .tm-clear {{ color:var(--ok); }} .tm-caution {{ color:var(--warn); }} .tm-conflict {{ color:var(--bad); }}
.reco {{ background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--accent);
  border-radius:10px; padding:4px 18px; }}
.controls {{ display:flex; flex-wrap:wrap; gap:10px 18px; align-items:center; margin-bottom:10px; font-size:13.5px; }}
.controls input[type=search] {{ padding:7px 10px; border:1px solid var(--line); border-radius:8px; background:var(--panel);
  color:var(--ink); font:inherit; min-width:200px; }}
.legend {{ color:var(--muted); font-size:12.5px; }}
.tablewrap {{ overflow-x:auto; background:var(--panel); border:1px solid var(--line); border-radius:12px; }}
table {{ border-collapse:collapse; width:100%; font-size:13px; }}
th, td {{ padding:6px 8px; border-bottom:1px solid var(--line); text-align:center; white-space:nowrap; }}
th {{ position:sticky; top:0; background:var(--panel); cursor:pointer; user-select:none; font-weight:600; color:var(--muted); }}
th:hover {{ color:var(--ink); }}
td.n, th.n {{ text-align:left; font-family:ui-monospace, Menlo, Consolas, monospace; color:var(--ink); }}
td.c {{ font-weight:600; font-size:12px; }}
td.c-available {{ background:var(--ok-bg); color:var(--ok); }}
td.c-likely_available, td.c-unknown {{ background:var(--warn-bg); color:var(--warn); }}
td.c-taken, td.c-likely_taken {{ color:var(--no); }}
td.c-prem {{ background:var(--bad-bg); color:var(--bad); }}
ol, ul.plain {{ padding-left:20px; }} .small {{ font-size:13px; }}
.caveat {{ color:var(--muted); font-size:13px; max-width:80ch; }}
a {{ color:var(--accent); }}
.theme {{ float:right; background:none; border:1px solid var(--line); color:var(--muted); border-radius:8px;
  padding:4px 10px; cursor:pointer; font:inherit; font-size:12.5px; }}
@media (max-width:520px) {{ .cards {{ grid-template-columns:1fr; }} h1 {{ font-size:23px; }} }}
</style>
</head>
<body>
<main>
<button class="theme" onclick="toggleTheme()" aria-label="toggle theme">◐</button>
<h1>{esc(proj.get("name") or "Project")} — {esc(L["title"])}</h1>
<p class="sub">{esc(proj.get("summary", ""))}</p>
<div class="stats">
  <div class="stat"><b>{max(len(cands), len(names))}</b><span>{L["candidates"]}</span></div>
  <div class="stat"><b>{n_checked}</b><span>{L["checked"]}</span></div>
  <div class="stat"><b>{n_avail}</b><span>{L["available"]}</span></div>
  <div class="stat"><b>{esc(a.get("mode", "—"))}</b><span>{L["mode"]}</span></div>
  <div class="stat"><b style="font-size:14px;padding-top:6px">{esc(checked_at or generated)}</b><span>{L["generated"]}</span></div>
</div>

{f'<h2>{L["recommendation"]}</h2><div class="reco">{paragraphs(a.get("recommendation"))}</div>' if a.get("recommendation") else ""}

<h2>{L["top"]}</h2>
<div class="cards">{"".join(cards)}</div>

{after_html}

<h2>{L["matrix"]}</h2>
<div class="controls">
  <input type="search" id="q" placeholder="{esc(L["filter"])}">
  <label><input type="checkbox" id="onlyAny"> {esc(L["only_any"])}</label>
  <label><input type="checkbox" id="onlyCom"> {esc(L["only_com"])}</label>
  <span class="legend">{esc(L["legend"])}</span>
</div>
<div class="tablewrap"><table id="m"><thead></thead><tbody></tbody></table></div>

{next_html}

<section><h2>{L["method"]}</h2><p class="caveat">{esc(L["caveat"])}</p>
{paragraphs(a.get("methodology")) if a.get("methodology") else ""}</section>
{src_html}
</main>
<script id="data" type="application/json">{data}</script>
<script>
(function() {{
  var D = JSON.parse(document.getElementById('data').textContent);
  var sym = {{available:'OK', likely_available:'~ok', taken:'–', likely_taken:'~–', unknown:'?', invalid:'x'}};
  var sortKey = 'score', sortDir = -1;
  function avail(r) {{ var n=0; for (var t in r.cells) if (r.cells[t].s==='available') n++; return n; }}
  function head() {{
    var h = '<tr><th class="n" data-k="name">{esc(L["name"])}</th><th data-k="score">{esc(L["score"])}</th><th data-k="avail">#</th>';
    D.tlds.forEach(function(t) {{ h += '<th data-k="t:'+t+'">.'+t+'</th>'; }});
    document.querySelector('#m thead').innerHTML = h + '</tr>';
    document.querySelectorAll('#m th').forEach(function(th) {{
      th.onclick = function() {{ var k = th.dataset.k; sortDir = (sortKey===k) ? -sortDir : (k==='name'?1:-1); sortKey = k; body(); }};
    }});
  }}
  function val(r, k) {{
    if (k==='name') return r.name; if (k==='score') return r.score==null?-1:+r.score; if (k==='avail') return avail(r);
    var c = r.cells[k.slice(2)]; return c ? -({{available:0,likely_available:1,unknown:2,likely_taken:3,taken:4}}[c.s]||5) : -9;
  }}
  function body() {{
    var q = document.getElementById('q').value.toLowerCase(), oa = document.getElementById('onlyAny').checked,
        oc = document.getElementById('onlyCom').checked;
    var rows = D.rows.filter(function(r) {{
      if (q && r.name.indexOf(q) < 0) return false;
      if (oa && !avail(r)) return false;
      if (oc && !(r.cells.com && r.cells.com.s==='available')) return false;
      return true;
    }});
    rows.sort(function(a,b) {{ var x=val(a,sortKey), y=val(b,sortKey); return (x>y?1:x<y?-1:0)*sortDir || (avail(b)-avail(a)); }});
    var out = rows.map(function(r) {{
      var s = '<tr><td class="n">'+r.name+'</td><td>'+(r.score==null?'':r.score)+'</td><td>'+avail(r)+'</td>';
      D.tlds.forEach(function(t) {{
        var c = r.cells[t];
        if (!c) {{ s += '<td></td>'; return; }}
        var cls = c.pm ? 'c c-prem' : 'c c-'+c.s;
        var tip = r.name+'.'+t+' — '+c.s+(c.p!=null?' · $'+c.p:'')+(c.r!=null?' / $'+c.r:'')+(c.pm?' · PREMIUM':'')+(c.m?' · '+c.m:'');
        s += '<td class="'+cls+'" title="'+tip.replace(/"/g,'&quot;')+'">'+(c.pm?'$$$':sym[c.s]||'?')+'</td>';
      }});
      return s + '</tr>';
    }});
    document.querySelector('#m tbody').innerHTML = out.join('');
  }}
  ['q','onlyAny','onlyCom'].forEach(function(id) {{ document.getElementById(id).addEventListener('input', body); }});
  head(); body();
}})();
function toggleTheme() {{
  var r = document.documentElement, cur = r.getAttribute('data-theme') ||
    (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  r.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
}}
</script>
</body>
</html>
"""

    # ---- markdown
    md = [f"# {proj.get('name') or 'Project'} — {L['title']}", ""]
    if proj.get("summary"):
        md += [f"> {proj['summary']}", ""]
    md += [f"- {L['generated']}: {checked_at or generated}", f"- {L['mode']}: {a.get('mode', '—')}",
           f"- {L['candidates']}: {max(len(cands), len(names))} · {L['checked']}: {n_checked} · {L['available']}: {n_avail}", ""]
    if a.get("recommendation"):
        md += [f"## {L['recommendation']}", "", str(a["recommendation"]).strip(), ""]
    md += [f"## {L['top']}", "", f"| # | {L['domain']} | {L['score']} | {L['strategy']} | {L['price']} | {L['why']} |",
           "|---|---|---|---|---|---|"]
    for i, (d, c, r, alts) in enumerate(picks, 1):
        prem = f" **{L['premium']}**" if r.get("premium") else ""
        st = "" if r.get("status") == "available" else f" ({L.get('st_' + r.get('status', 'unknown'), L['st_unknown'])})"
        why = str(c.get("rationale", "")).replace("|", "/").replace("\n", " ")
        md.append(f"| {i} | **{d}**{st}{prem} | {c.get('score', '')} | {c.get('strategy', '')} | "
                  f"{money(r.get('price_registration'))} / {money(r.get('price_renewal'))} | {why} |")
    md.append("")
    for i, (d, c, r, alts) in enumerate(picks, 1):
        flags = c.get("risks") or c.get("flags") or []
        extra = []
        if flags:
            extra.append(f"{L['risks']}: " + "; ".join(flags))
        if c.get("trademark"):
            extra.append(f"{L['trademark']}: {L.get('tm_' + str(c['trademark']), c['trademark'])}")
        if alts:
            extra.append(f"{L['alt']}: " + ", ".join(alts[:6]))
        if extra:
            md.append(f"- **{d}** — " + " · ".join(extra))
    md.append("")
    if after:
        md += [f"## {L['aftermarket']}", ""] + [f"- **{x.get('domain')}** — {x.get('note', '')}" for x in after] + [""]
    md += [f"## {L['matrix']}", "", L["legend"], ""]
    ranked = sorted(rows, key=lambda r: (-(r["score"] or 0), -sum(1 for c in r["cells"].values() if c["s"] == "available")))
    md.append(f"| {L['name']} | " + " | ".join("." + t for t in tlds) + " |")
    md.append("|---|" + "---|" * len(tlds))
    msym = {"available": "OK", "likely_available": "~ok", "taken": "–", "likely_taken": "~–", "unknown": "?"}
    for r in ranked[:60]:
        md.append(f"| {r['name']} | " + " | ".join(
            ("$$$" if r["cells"][t].get("pm") else msym.get(r["cells"][t]["s"], "?")) if t in r["cells"] else ""
            for t in tlds) + " |")
    if len(ranked) > 60:
        md.append(f"\n_+{len(ranked) - 60} more in the HTML report._")
    md.append("")
    if nxt:
        md += [f"## {L['next']}", ""] + [f"{i}. {x}" for i, x in enumerate(nxt, 1)] + [""]
    md += [f"## {L['method']}", "", L["caveat"], ""]
    if a.get("methodology"):
        md += [str(a["methodology"]).strip(), ""]
    if srcs:
        md += [f"## {L['sources']}", ""] + [f"- [{s.get('title') or s.get('url')}]({s.get('url')})" for s in srcs] + [""]
    return page, "\n".join(md)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Render domain-machine report (HTML + Markdown).")
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--html", help="output HTML path (default: report.html next to analysis)")
    ap.add_argument("--md", help="output Markdown path (default: report.md next to analysis)")
    args = ap.parse_args()
    a, results, handles, checked_at = load(args.analysis)
    page, md = build(a, results, handles, checked_at)
    base = Path(args.analysis).parent
    hp = Path(args.html) if args.html else base / "report.html"
    mp = Path(args.md) if args.md else base / "report.md"
    hp.write_text(page, encoding="utf-8")
    mp.write_text(md, encoding="utf-8")
    print(f"html: {hp.resolve()}\nmd:   {mp.resolve()}")


if __name__ == "__main__":
    main()
