#!/usr/bin/env python3
"""
domain-machine: bulk domain availability checker (stdlib only).

Pipeline per domain:
  1. DNS-over-HTTPS NS lookup  -> delegated NS records mean "taken" (high confidence).
  2. RDAP (IANA bootstrap)     -> 404 = available, 200 = taken.
  3. WHOIS port 43 fallback    -> for TLDs without (working) RDAP.
  4. DNS-only verdict          -> NXDOMAIN with no registry answer = "likely_available" (low confidence).
  5. Optional Porkbun API      -> real price + premium flag (needs API keys, rate limited).

Queries go to registries / public resolvers, never to registrar search boxes,
so the names being considered are not leaked to anyone who could front-run them.

Usage:
  check_domains.py --names vexo,lumora --tlds com,io,ai,dev
  check_domains.py --names-file names.txt --tlds com,io --out results.json
  check_domains.py --domains vexo.com,lumora.io
  check_domains.py --domains-file shortlist.txt --porkbun --out shortlist.json
  check_domains.py --pricing com,io,ai          # just print registration/renewal prices
"""

import argparse
import concurrent.futures as cf
import json
import os
import random
import re
import socket
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

VERSION = "0.1.1"
UA = f"domain-machine/{VERSION} (domain availability research tool)"
CACHE_DIR = Path(os.environ.get("DOMAIN_MACHINE_CACHE", Path.home() / ".cache" / "domain-machine"))
CONFIG_FILE = Path(os.environ.get("DOMAIN_MACHINE_CONFIG", Path.home() / ".config" / "domain-machine" / "config.json"))
CACHE_TTL = 24 * 3600

RDAP_BOOTSTRAP_URL = "https://data.iana.org/rdap/dns.json"
PORKBUN_PRICING_URL = "https://api.porkbun.com/api/json/v3/pricing/get"
PORKBUN_CHECK_URL = "https://api.porkbun.com/api/json/v3/domain/checkDomain/{domain}"
PORKBUN_PING_URL = "https://api.porkbun.com/api/json/v3/ping"
DOH_ENDPOINTS = [
    ("https://cloudflare-dns.com/dns-query", {"accept": "application/dns-json"}),
    ("https://dns.google/resolve", {}),
]

# WHOIS phrases meaning "this domain is not registered". Lowercased substring match.
WHOIS_FREE_PATTERNS = [
    "no match for", "no match!!", "not found", "no data found", "no entries found",
    "status: free", "status: available", "object_not_found", "does not exist",
    "no matching record", "is available for registration", "no object found",
    "domain not registered", "nothing found", "no information available",
    "no se encuentra registrado", "no existe", "not registered",
]
# Phrases meaning the server refused / limited us; result must be "unknown".
WHOIS_BLOCKED_PATTERNS = [
    "rate limit", "limit exceeded", "too many", "access denied", "not authorised",
    "not authorized", "quota", "try again later", "blacklisted", "temporarily",
]
# Per-server query templates (default is "{domain}\r\n").
WHOIS_QUERY_OVERRIDES = {
    "whois.denic.de": "-T dn {domain}\r\n",
    "whois.jprs.jp": "{domain}/e\r\n",
}
# Known-broken or restricted endpoints: skip straight to the next method.
RDAP_SKIP = set()
WHOIS_SKIP = {"whois.nic.es"}  # .es WHOIS requires IP pre-authorisation

LABEL_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")

_print_lock = threading.Lock()
_host_sems = {}
_host_sems_lock = threading.Lock()
_rdap_failures = {}


def log(msg, quiet=False):
    if not quiet:
        with _print_lock:
            print(msg, file=sys.stderr, flush=True)


def host_sem(host, limit):
    with _host_sems_lock:
        if host not in _host_sems:
            _host_sems[host] = threading.BoundedSemaphore(limit)
        return _host_sems[host]


def http(url, method="GET", headers=None, data=None, timeout=15):
    """Returns (status, body_text, headers). status 0 means network failure."""
    h = {"User-Agent": UA}
    h.update(headers or {})
    body = json.dumps(data).encode() if data is not None else None
    if body is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace"), dict(r.headers)
    except urllib.error.HTTPError as e:
        try:
            txt = e.read().decode("utf-8", "replace")
        except Exception:
            txt = ""
        return e.code, txt, dict(e.headers or {})
    except Exception as e:  # timeouts, DNS errors, TLS errors
        return 0, str(e), {}


def cached_json(name, url, method="GET"):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / name
    if path.exists() and time.time() - path.stat().st_mtime < CACHE_TTL:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    status, body, _ = http(url, method=method, timeout=30)
    if status == 200:
        try:
            data = json.loads(body)
            path.write_text(body, encoding="utf-8")
            return data
        except Exception:
            pass
    if path.exists():  # stale cache beats nothing
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


# ---------------------------------------------------------------- registries

class Registry:
    def __init__(self, offline_pricing=False):
        self.rdap = {}
        boot = cached_json("rdap_dns.json", RDAP_BOOTSTRAP_URL)
        if boot:
            for tlds, urls in boot.get("services", []):
                url = next((u for u in urls if u.startswith("https")), urls[0] if urls else None)
                for t in tlds:
                    self.rdap[t.lower()] = url
        self.pricing = {}
        if not offline_pricing:
            p = cached_json("porkbun_pricing.json", PORKBUN_PRICING_URL, method="POST")
            if p and p.get("status") == "SUCCESS":
                self.pricing = p.get("pricing", {})
        self.whois_path = CACHE_DIR / "whois_servers.json"
        try:
            self.whois = json.loads(self.whois_path.read_text(encoding="utf-8"))
        except Exception:
            self.whois = {}
        self.whois_lock = threading.Lock()

    def rdap_base(self, tld):
        # longest matching suffix: "com.ar" -> "com.ar" or "ar"
        parts = tld.split(".")
        for i in range(len(parts)):
            base = self.rdap.get(".".join(parts[i:]))
            if base:
                return base
        return None

    def whois_server(self, tld):
        top = tld.split(".")[-1]
        with self.whois_lock:
            if top in self.whois:
                return self.whois[top]
        server = None
        try:
            resp = whois_raw("whois.iana.org", top + "\r\n", timeout=10)
            for line in resp.splitlines():
                if line.lower().startswith("whois:"):
                    server = line.split(":", 1)[1].strip() or None
                    break
        except Exception:
            return None  # don't cache failures
        with self.whois_lock:
            self.whois[top] = server
            try:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                self.whois_path.write_text(json.dumps(self.whois, indent=1), encoding="utf-8")
            except Exception:
                pass
        return server

    def price(self, tld):
        p = self.pricing.get(tld)
        if not p:
            return None, None
        try:
            return float(p.get("registration")), float(p.get("renewal"))
        except Exception:
            return None, None


# ---------------------------------------------------------------- lookups

def doh_ns(domain):
    """Returns 'delegated', 'nxdomain', 'nodata' or 'error'."""
    for url, headers in DOH_ENDPOINTS:
        q = f"{url}?name={urllib.parse.quote(domain)}&type=NS"
        with host_sem(urllib.parse.urlparse(url).netloc, 16):
            status, body, _ = http(q, headers=headers, timeout=10)
        if status != 200:
            continue
        try:
            d = json.loads(body)
        except Exception:
            continue
        rc = d.get("Status")
        if rc == 3:
            return "nxdomain"
        if rc == 0:
            if any(a.get("type") == 2 for a in d.get("Answer", []) or []):
                return "delegated"
            return "nodata"
        # SERVFAIL etc: often a registered domain with broken DNS
        if rc == 2:
            return "servfail"
    return "error"


def rdap_lookup(base, domain, retries=3):
    """Returns ('available'|'taken'|'unknown', detail)."""
    url = base.rstrip("/") + "/domain/" + domain
    host = urllib.parse.urlparse(url).netloc
    if host in RDAP_SKIP or _rdap_failures.get(host, 0) >= 3:
        return "unknown", "rdap skipped (server unreliable this run)"
    for attempt in range(retries):
        with host_sem(host, 3):
            status, body, headers = http(url, headers={"Accept": "application/rdap+json"}, timeout=12)
        if status == 0:
            # network failure: count it so a dead server stops costing time for every domain
            _rdap_failures[host] = _rdap_failures.get(host, 0) + 1
            if attempt >= 1 or _rdap_failures[host] >= 3:
                return "unknown", "rdap unreachable"
        if status == 404:
            return "available", "rdap 404"
        if status == 200:
            try:
                d = json.loads(body)
                if d.get("objectClassName") == "domain" or d.get("ldhName"):
                    return "taken", "rdap 200"
            except Exception:
                pass
            return "unknown", "rdap 200 without a domain object"
        if status in (429, 503) or status == 0:
            wait = headers.get("Retry-After") if headers else None
            try:
                wait = float(wait)
            except Exception:
                wait = 2 ** attempt + random.random()
            time.sleep(min(wait, 20))
            continue
        if status == 400:
            return "unknown", "rdap 400 (registry rejected the query)"
        return "unknown", f"rdap http {status}"
    return "unknown", "rdap rate limited / unreachable"


def whois_raw(server, query, timeout=12):
    with socket.create_connection((server, 43), timeout=timeout) as s:
        s.settimeout(timeout)
        s.sendall(query.encode("utf-8"))
        chunks = []
        while True:
            c = s.recv(4096)
            if not c:
                break
            chunks.append(c)
    return b"".join(chunks).decode("utf-8", "replace")


def whois_lookup(server, domain):
    if server in WHOIS_SKIP:
        return "unknown", f"whois {server} restricted"
    tmpl = WHOIS_QUERY_OVERRIDES.get(server, "{domain}\r\n")
    try:
        with host_sem(server, 2):
            resp = whois_raw(server, tmpl.format(domain=domain))
            time.sleep(0.3)
    except Exception as e:
        return "unknown", f"whois error: {e.__class__.__name__}"
    low = resp.lower()
    if not low.strip():
        return "unknown", "whois empty response"
    if any(p in low for p in WHOIS_BLOCKED_PATTERNS) and len(low) < 600:
        return "unknown", "whois rate limited"
    if any(p in low for p in WHOIS_FREE_PATTERNS):
        # guard: a record that clearly has a registrar/creation date is taken
        if re.search(r"(creation date|created|registered|registrar:|nserver|name server)\s*:", low) and \
                "not found" not in low[:200]:
            return "taken", "whois record"
        return "available", "whois not-found"
    if domain.split(".")[0] in low or "domain" in low:
        return "taken", "whois record"
    return "unknown", "whois unparsed"


PLACEHOLDER_KEY = "PASTE_YOUR_API_KEY_HERE"
PLACEHOLDER_SECRET = "PASTE_YOUR_SECRET_KEY_HERE"


def porkbun_keys():
    k, s, _ = porkbun_keys_source()
    return k, s


def porkbun_keys_source():
    """Returns (key, secret, source) with source in env|config|template|none."""
    k = os.environ.get("PORKBUN_API_KEY")
    s = os.environ.get("PORKBUN_SECRET_API_KEY") or os.environ.get("PORKBUN_SECRET_KEY")
    if k and s:
        return k.strip(), s.strip(), "env"
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        k, s = cfg.get("porkbun_api_key"), cfg.get("porkbun_secret_api_key")
        if k in (None, "", PLACEHOLDER_KEY) or s in (None, "", PLACEHOLDER_SECRET):
            return None, None, "template"
        return k.strip(), s.strip(), "config"
    except FileNotFoundError:
        pass
    except Exception:
        return None, None, "template"  # file exists but isn't valid JSON yet
    return None, None, "none"


def porkbun_status():
    """Never prints the keys themselves."""
    k, s, source = porkbun_keys_source()
    out = {"configured": bool(k), "source": source, "config_file": str(CONFIG_FILE), "working": False}
    if not k:
        out["message"] = ("config file exists but still has placeholders or invalid JSON"
                          if source == "template" else "no keys found")
        return out
    if not (k.startswith("pk1_") and s.startswith("sk1_")):
        out["message"] = "keys don't look like Porkbun keys (expected pk1_... and sk1_...); check they aren't swapped"
    status, body, _ = http(PORKBUN_PING_URL, method="POST", data={"apikey": k, "secretapikey": s}, timeout=20)
    try:
        d = json.loads(body)
    except Exception:
        d = {}
    if d.get("status") == "SUCCESS":
        out["working"] = True
        out["message"] = "keys valid"
    else:
        out["message"] = d.get("message") or f"http {status}"
        hint = (d.get("next_action") or {}).get("hint")
        if hint:
            out["hint"] = hint
    return out


def porkbun_init():
    """Create the config file with placeholders (never overwrites real keys)."""
    if CONFIG_FILE.exists():
        return {"created": False, "config_file": str(CONFIG_FILE), "message": "already exists, left untouched"}
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"porkbun_api_key": PLACEHOLDER_KEY,
                                       "porkbun_secret_api_key": PLACEHOLDER_SECRET}, indent=2) + "\n",
                           encoding="utf-8")
    return {"created": True, "config_file": str(CONFIG_FILE)}


def porkbun_check(domain, keys, quiet=False):
    """Porkbun checkDomain. Rate limited (typically 1 check / 10 s). Returns dict or None."""
    for _ in range(4):
        status, body, _ = http(PORKBUN_CHECK_URL.format(domain=domain), method="POST",
                               data={"apikey": keys[0], "secretapikey": keys[1]}, timeout=20)
        try:
            d = json.loads(body)
        except Exception:
            d = {}
        if d.get("status") == "SUCCESS":
            r = d.get("response", {})
            lim = d.get("limits", {})
            try:
                if int(lim.get("used", 0)) >= int(lim.get("limit", 1)):
                    time.sleep(float(lim.get("TTL", 10)) + 0.5)
            except Exception:
                pass
            return r
        msg = (d.get("message") or body or "").lower()
        if "limit" in msg or status == 429:
            log(f"  porkbun rate limit, waiting... ({domain})", quiet)
            time.sleep(11)
            continue
        log(f"  porkbun error for {domain}: {d.get('message') or status}", quiet)
        return None
    return None


# ---------------------------------------------------------------- orchestration

def check_one(domain, reg, use_dns=True):
    sld, _, tld = domain.partition(".")
    res = {"domain": domain, "name": sld, "tld": tld, "status": "unknown",
           "confidence": "low", "method": None, "detail": ""}
    reg_price, renew_price = reg.price(tld)
    res["price_registration"] = reg_price
    res["price_renewal"] = renew_price
    res["premium"] = None

    dns = doh_ns(domain) if use_dns else "skipped"
    res["dns"] = dns
    if dns == "delegated":
        res.update(status="taken", confidence="high", method="dns", detail="has NS records")
        return res

    base = reg.rdap_base(tld)
    if base:
        st, detail = rdap_lookup(base, domain)
        if st != "unknown":
            res.update(status=st, confidence="high", method="rdap", detail=detail)
            return res
        res["detail"] = detail

    server = reg.whois_server(tld)
    if server:
        st, detail = whois_lookup(server, domain)
        if st != "unknown":
            res.update(status=st, confidence="medium", method="whois", detail=detail)
            return res
        res["detail"] = (res["detail"] + "; " if res["detail"] else "") + detail

    if dns == "nxdomain":
        res.update(status="likely_available", confidence="low", method="dns",
                   detail=(res["detail"] + "; " if res["detail"] else "") + "NXDOMAIN, registry not queryable")
    elif dns in ("nodata", "servfail"):
        res.update(status="likely_taken", confidence="low", method="dns",
                   detail=(res["detail"] + "; " if res["detail"] else "") + f"DNS {dns}")
    return res


def normalize(domain):
    d = domain.strip().lower().rstrip(".")
    d = re.sub(r"^https?://", "", d).split("/")[0]
    if d.startswith("www."):
        d = d[4:]
    try:
        d = d.encode("idna").decode("ascii")
    except Exception:
        return None
    if "." not in d:
        return None
    sld = d.split(".")[0]
    if not LABEL_RE.match(sld):
        return None
    return d


def read_list(path):
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            items.extend(x.strip() for x in line.split(",") if x.strip())
    return items


def split_csv(s):
    return [x.strip().lstrip(".") for x in (s or "").split(",") if x.strip()]


SYMBOL = {"available": "OK", "taken": "--", "likely_available": "ok?",
          "likely_taken": "-?", "unknown": "??", "invalid": "xx"}


def print_matrix(results, tlds):
    by_name = {}
    for r in results:
        by_name.setdefault(r["name"], {})[r["tld"]] = r
    tlds = tlds or sorted({r["tld"] for r in results})
    w = max([len(n) for n in by_name] + [4])
    header = "name".ljust(w) + " | " + " | ".join(t.center(max(len(t), 4)) for t in tlds)
    print(header)
    print("-" * len(header))
    def score(item):
        return -sum(1 for r in item[1].values() if r["status"] == "available")
    for name, row in sorted(by_name.items(), key=score):
        cells = []
        for t in tlds:
            r = row.get(t)
            cells.append((SYMBOL.get(r["status"], "??") if r else "").center(max(len(t), 4)))
        print(name.ljust(w) + " | " + " | ".join(cells))
    print("\nOK=available  --=taken  ok?/-?=low-confidence guess  ??=unknown")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Bulk domain availability checker (RDAP/WHOIS/DNS).")
    ap.add_argument("--names", help="comma-separated base names (combined with --tlds)")
    ap.add_argument("--names-file", help="file with one base name per line")
    ap.add_argument("--tlds", help="comma-separated TLDs, e.g. com,io,ai,com.ar")
    ap.add_argument("--domains", help="comma-separated full domains")
    ap.add_argument("--domains-file", help="file with one full domain per line")
    ap.add_argument("--out", help="write JSON results here")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--no-dns", action="store_true", help="skip DNS prefilter (always ask the registry)")
    ap.add_argument("--porkbun", action="store_true",
                    help="verify available domains with Porkbun API (real price + premium flag; slow)")
    ap.add_argument("--porkbun-max", type=int, default=40, help="cap on Porkbun checks per run")
    ap.add_argument("--pricing", help="print Porkbun prices for these TLDs and exit")
    ap.add_argument("--porkbun-status", action="store_true",
                    help="report whether Porkbun keys are configured and valid (never prints them) and exit")
    ap.add_argument("--porkbun-init", action="store_true",
                    help="create the config file with placeholders for the user to fill in, and exit")
    ap.add_argument("--matrix", action="store_true", help="print a name x TLD matrix to stdout")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if args.porkbun_status:
        print(json.dumps(porkbun_status(), indent=2))
        return
    if args.porkbun_init:
        print(json.dumps(porkbun_init(), indent=2))
        return

    reg = Registry()

    if args.pricing:
        out = {}
        for t in split_csv(args.pricing):
            r, n = reg.price(t)
            out[t] = {"registration": r, "renewal": n, "rdap": bool(reg.rdap_base(t))}
        print(json.dumps(out, indent=2))
        return

    names = split_csv(args.names)
    if args.names_file:
        names += read_list(args.names_file)
    tlds = split_csv(args.tlds)
    domains = split_csv(args.domains)
    if args.domains_file:
        domains += read_list(args.domains_file)
    if names and not tlds:
        ap.error("--names requires --tlds")
    for n in names:
        n = re.sub(r"[^a-z0-9-]", "", n.lower())
        for t in tlds:
            domains.append(f"{n}.{t}")

    seen, valid, invalid = set(), [], []
    for d in domains:
        nd = normalize(d)
        if not nd:
            invalid.append(d)
        elif nd not in seen:
            seen.add(nd)
            valid.append(nd)
    if not valid:
        ap.error("no valid domains to check")

    log(f"checking {len(valid)} domains ({len(invalid)} invalid skipped)...", args.quiet)
    results = []
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(check_one, d, reg, not args.no_dns): d for d in valid}
        for i, f in enumerate(cf.as_completed(futs), 1):
            try:
                results.append(f.result())
            except Exception as e:
                d = futs[f]
                results.append({"domain": d, "name": d.split(".")[0], "tld": d.partition(".")[2],
                                "status": "unknown", "confidence": "low", "method": None,
                                "detail": f"error: {e}"})
            if i % 25 == 0:
                log(f"  {i}/{len(valid)}", args.quiet)
    for d in invalid:
        results.append({"domain": d, "name": d, "tld": "", "status": "invalid",
                        "confidence": "high", "method": None, "detail": "not a valid domain label"})

    porkbun_used = False
    if args.porkbun:
        keys = porkbun_keys()
        if not keys[0]:
            log("porkbun: no API keys found (PORKBUN_API_KEY / PORKBUN_SECRET_API_KEY or "
                f"{CONFIG_FILE}); skipping premium check", args.quiet)
        else:
            todo = [r for r in results if r["status"] in ("available", "likely_available")][: args.porkbun_max]
            log(f"porkbun: verifying {len(todo)} domains (rate limited, ~10 s each)...", args.quiet)
            porkbun_used = True
            for r in todo:
                pb = porkbun_check(r["domain"], keys, args.quiet)
                if not pb:
                    continue
                r["porkbun"] = pb
                avail = str(pb.get("avail", "")).lower() == "yes"
                r["premium"] = str(pb.get("premium", "")).lower() == "yes"
                try:
                    r["price_registration"] = float(pb.get("price"))
                except Exception:
                    pass
                try:
                    r["price_renewal"] = float(pb.get("additional", {}).get("renewal", {}).get("price"))
                except Exception:
                    pass
                if avail:
                    r.update(status="available", confidence="high",
                             method=(r["method"] or "") + "+porkbun")
                else:
                    r.update(status="taken", confidence="high", method="porkbun",
                             detail="registrar reports unavailable (reserved or registered)")

    results.sort(key=lambda r: (r["name"], r["tld"]))
    summary = {}
    for r in results:
        summary[r["status"]] = summary.get(r["status"], 0) + 1
    payload = {
        "tool": "domain-machine/check_domains", "version": VERSION,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_s": round(time.time() - t0, 1),
        "porkbun_verified": porkbun_used,
        "summary": summary, "results": results,
    }
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
        log(f"wrote {args.out}", args.quiet)

    if args.matrix or not args.out:
        print_matrix(results, tlds if names else None)
    print(json.dumps({"summary": summary, "elapsed_s": payload["elapsed_s"]}))
    avail = [r["domain"] for r in results if r["status"] == "available"]
    print("available:", ", ".join(avail[:200]) if avail else "(none)")


if __name__ == "__main__":
    main()
