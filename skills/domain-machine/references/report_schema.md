# analysis.json schema

`build_report.py --analysis analysis.json` renders `report.html` and `report.md` next to it.
Paths inside are relative to the analysis file. Every field except `project`, `candidates`,
`availability_files` and `shortlist` is optional.

```json
{
  "project": {
    "name": "Acme",
    "summary": "One-sentence description of the project and what the name must convey."
  },
  "language": "es",
  "labels": {},
  "mode": "deep",
  "generated_at": "2026-10-25 14:00 UTC",
  "tlds": ["com", "io", "ai", "dev", "app", "co", "com.ar"],
  "availability_files": ["availability.json", "round2.json", "shortlist_porkbun.json"],
  "handles_file": "handles.json",

  "candidates": [
    {
      "name": "vexo",
      "strategy": "coined",
      "rationale": "Short, sharp, evokes 'vector' + 'exo'; fits a dev-tool tone.",
      "pronunciation": "VEK-so",
      "scores": {"memorability": 8, "radio": 9, "pronounce": 9, "fit": 7, "distinct": 8, "brevity": 10, "domain": 8},
      "score": 8.3,
      "risks": [".com held by a parked page", "renewal on .io is 1.8x"],
      "trademark": "clear",
      "handles": {"github": "taken", "npm": "free"}
    }
  ],

  "shortlist": ["vexo.io", "getvexo.com", "lumora.com"],

  "recommendation": "Paragraphs separated by blank lines. '- ' lines become bullets. **bold** works.",
  "aftermarket": [
    {"domain": "vexo.com", "note": "Parked at Afternic, make-offer", "url": "https://..."}
  ],
  "next_steps": ["Register vexo.io today (2-year)", "Grab @vexo on X manually"],
  "methodology": "Optional extra notes on what was and wasn't checked.",
  "sources": [{"title": "Vexo Ltd – Companies House", "url": "https://..."}]
}
```

Notes
- `language`: built-in labels for `en`, `es`, `pt`. For any other language pass translated
  strings in `labels` (same keys as `LABELS["en"]` in build_report.py) so the whole report matches
  the user's language.
- `candidates`: include **all** scored names (shortlist and runners-up). Names that were only
  checked, never scored, still appear in the matrix with no score.
- `shortlist`: full domains, ordered best first; these become the "Top picks" cards. 5 (quick),
  8–10 (standard), 12–15 (deep).
- `handles` inside a candidate is used only if `handles_file` doesn't cover that name.
- `trademark`: `clear | caution | conflict | unchecked`.
- When several availability files mention the same domain, a high-confidence result wins.
