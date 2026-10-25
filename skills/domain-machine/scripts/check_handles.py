#!/usr/bin/env python3
"""
domain-machine: check whether a brand name is free on developer/package platforms (stdlib only).

Checked automatically (reliable public endpoints):
  github (user/org)  npm  pypi  crates
Listed for manual check (these sites block or mislead automated lookups):
  x, instagram, tiktok, youtube, linkedin, producthunt

Usage:
  check_handles.py --names vexo,lumora
  check_handles.py --names-file shortlist.txt --out handles.json
"""

import argparse
import concurrent.futures as cf
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "domain-machine/0.1.0 (brand name availability research tool)"

AUTO = {
    "github": "https://api.github.com/users/{name}",
    "npm": "https://registry.npmjs.org/{name}",
    "pypi": "https://pypi.org/pypi/{name}/json",
    "crates": "https://crates.io/api/v1/crates/{name}",
}
MANUAL = {
    "x": "https://x.com/{name}",
    "instagram": "https://www.instagram.com/{name}/",
    "tiktok": "https://www.tiktok.com/@{name}",
    "youtube": "https://www.youtube.com/@{name}",
    "linkedin": "https://www.linkedin.com/company/{name}",
    "producthunt": "https://www.producthunt.com/search?q={name}",
}


def probe(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/html"},
                                 method="GET")
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def check(name):
    q = urllib.parse.quote(name)
    out = {"name": name, "platforms": {}, "manual": {k: v.format(name=q) for k, v in MANUAL.items()}}
    for plat, tmpl in AUTO.items():
        status = probe(tmpl.format(name=q))
        if status == 404:
            verdict = "free"
        elif status == 200:
            verdict = "taken"
        else:
            verdict = "unknown"
        out["platforms"][plat] = {"status": verdict, "http": status, "url": tmpl.format(name=q)}
    return out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Check brand handles on dev/package platforms.")
    ap.add_argument("--names", help="comma-separated names")
    ap.add_argument("--names-file", help="file with one name per line")
    ap.add_argument("--out", help="write JSON results here")
    args = ap.parse_args()

    names = [n.strip().lower() for n in (args.names or "").split(",") if n.strip()]
    if args.names_file:
        names += [l.split("#")[0].strip().lower() for l in
                  Path(args.names_file).read_text(encoding="utf-8").splitlines() if l.split("#")[0].strip()]
    names = list(dict.fromkeys(n.split(".")[0] for n in names))
    if not names:
        ap.error("no names given")

    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(check, names))

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(results, indent=1), encoding="utf-8")
    plats = list(AUTO)
    w = max(len(n) for n in names + ["name"])
    print("name".ljust(w) + " | " + " | ".join(p.center(9) for p in plats))
    for r in results:
        print(r["name"].ljust(w) + " | " + " | ".join(r["platforms"][p]["status"].center(9) for p in plats))
    print("\nManual checks (social sites block bots): x, instagram, tiktok, youtube, linkedin, producthunt"
          + (f" - URLs in {args.out}" if args.out else ""))


if __name__ == "__main__":
    main()
