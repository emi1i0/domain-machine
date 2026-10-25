# Research playbook

Web research is for **conflicts and context**, never for availability (use the scripts for that —
search engines are stale and registrar search pages can leak the query to front-runners).

## Contents
1. What to research, by depth
2. Company / product conflicts
3. Trademarks
4. Taken domains: who holds them, are they for sale
5. Meaning and slang
6. Recording findings

---

## 1. What to research, by depth

| Check | quick | standard | deep |
|---|---|---|---|
| Company/product conflicts (web search) | top 5 | top 10–12 | top 15–20 |
| Trademark search | — (warn instead) | top 5, main market | top 10, every target market |
| Handles (`check_handles.py`) | — | top 10 | whole shortlist |
| Meaning/slang in target languages | own judgement | top 10 + web if unsure | every shortlisted name |
| Taken `.com` analysis (parked? for sale?) | — | top 5 whose `.com` is taken | all outstanding names with taken `.com` |
| Competitor naming landscape | — | brief | yes: how do 10–20 competitors name themselves |
| Porkbun premium/price verification | — | if keys configured | yes (guide setup if missing) |

Run independent searches in parallel. Budget: quick ≈ 5–10 searches, standard ≈ 15–30, deep ≈ 40–80.

## 2. Company / product conflicts

Queries per name (adapt to language/market):
- `"<name>"` + the category (e.g. `"vexo" app`, `"vexo" software`, `"vexo" startup`)
- `"<name>.com"` and `"<name>.io"`
- `<name> crunchbase`, `<name> linkedin company`, `<name> product hunt`
- App stores when relevant: `"<name>" site:apps.apple.com`, `site:play.google.com`
- GitHub for dev tools: `"<name>" site:github.com`

Verdicts: **clear** (nothing relevant), **noise** (unrelated uses in other industries — usually fine),
**adjacent** (similar industry, small) or **conflict** (same space, active). Conflict → penalty, usually drop.

## 3. Trademarks

You can't run an official clearance; do a **knockout search** and say so in the report.
- Global: WIPO Global Brand Database — https://branddb.wipo.int
- US: USPTO trademark search — https://tmsearch.uspto.gov
- EU: EUIPO eSearch / TMview (covers many national offices) — https://www.tmdn.org/tmview
- UK: https://trademarks.ipo.gov.uk
- Latin America: INPI Argentina (https://portaltramites.inpi.gob.ar), IMPI Mexico (MARCia),
  INPI Brazil (busca.inpi.gov.br)
These sites are often JS-heavy; if fetching fails, do a web search like
`"<name>" trademark`, `"<name>" registered trademark <class keyword>`, `"<name>" marca registrada`,
and report the verdict as "preliminary (web)". Verdicts: `clear`, `caution` (similar mark in
related class or unclear), `conflict` (live mark, same/related class), `unchecked`.
Always add: "this is not legal advice; for a flagship brand, get a professional clearance search."

## 4. Taken domains

For great names whose `.com` is taken, fetch `http://<name>.com` (WebFetch) and classify:
- **active business** — note industry; same space = conflict.
- **parked / for sale** — look for "for sale", "make an offer", Afternic/Sedo/Atom/GoDaddy banners.
  Note it under `aftermarket` in the analysis with the marketplace link. Typical aftermarket prices for
  brandable .coms range from ~$1k to $50k+; give the asking price only if the page shows one.
- **dead / no site** — the holder may sell; mention a broker or a direct WHOIS/RDAP-contact approach.

## 5. Meaning and slang

See naming_strategies.md §5. When unsure, search `"<name>" meaning`, `"<name>" significado`,
`"<name>" slang`, `"<name>" <language> word`. Record anything negative in `risks`.

## 6. Recording findings

Every claim in the report that came from the web needs a source URL in `sources`. Keep notes terse:
"Vexo Ltd — UK logistics firm, unrelated (noise)". Never invent a finding; if a check wasn't run,
say "unchecked".
