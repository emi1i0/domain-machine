---
name: domain-machine
description: Finds, checks and ranks domain names for a project. It brainstorms brandable names from the project's context (repo files or a short briefing), checks real availability in bulk across relevant TLDs through registry RDAP/WHOIS (not Google), researches conflicts (companies, trademarks, social handles, meanings in other languages, aftermarket), scores candidates and delivers an HTML and Markdown report with a ranked shortlist. Use whenever the user wants a domain or a name for a project, startup, product, app, brand or website, asks whether domains are available, wants name ideas with free .com/.io/.ai/etc, or says things like "find me a domain", "what should I call this", "busca dominios", "necesito un nombre para mi proyecto".
---

# Domain Machine

Turn "I need a name and a domain" into a researched, ranked, **verified** shortlist.

Pipeline: **Brief → Generate → Check → Iterate → Research → Score → Report → Refine**

## Ground rules

- **Talk in the user's language** throughout, and write the report in it (`language` in the analysis).
- **Availability comes only from `scripts/check_domains.py`.** Never claim a domain is free because a
  search result, your memory or a registrar page suggests so. Report the script's confidence level.
- **Never type candidate domains into registrar search pages** or ask the user to do so before they
  decide: some of those searches leak to front-runners. The script queries registries directly.
- Be honest about limits: "available" means not registered at check time. Premium, reserved and
  last-minute registrations are possible until checkout. Trademark notes are preliminary, not legal advice.
- Keep the user in the loop at the two decision points (brief confirmation, shortlist feedback);
  otherwise just work.

## Setup (once per session)

Find a Python 3 interpreter: try `python3 --version`, then `python --version`, then `py -3 --version`
(Windows). Use the first that works as `PY` below. The scripts use only the standard library.
`SKILL_DIR` is the directory of this file. If no Python is available, tell the user and stop:
web search alone can't verify availability.

Work folder: `./domain-research/<project-slug>/` in the current directory, unless the user picks
another place. Put every intermediate file there (names lists, JSON results, analysis, report).

## 1. Brief

Gather context **before** asking anything:
- In a repo, read what describes the project: README, package.json / pyproject / Cargo.toml descriptions,
  docs/, landing page copy, app store text. Skim, don't audit.
- From the conversation: anything the user already said about the product, audience, tone, markets.

Then send **one** compact message confirming your understanding and asking only what is missing.
If the AskUserQuestion tool is available, use it for the multiple-choice parts. Cover:
1. **What it is & who it's for** (confirm your summary in 1–2 lines).
2. **Depth** — always ask unless the user already said it; never assume:
   - *quick*: ~50 names, core TLDs, top 5. A few minutes.
   - *standard*: ~120 names, 8–12 TLDs, conflicts + light trademark, top 8–10.
   - *deep*: 200–350 names in several rounds, 12–20 TLDs, full conflict/trademark/handle/meaning
     research, premium check, top 12–15. Takes a while; best result.
3. **Markets & languages** — global, or specific countries (decides ccTLDs, trademark offices, language checks).
4. **Tone** — e.g. serious/technical, friendly, playful, premium, local.
5. **Budget** — standard registration only, or open to premium / aftermarket (up to roughly how much)?
6. **Constraints** — must-include words, words to avoid, max length, TLDs they insist on, names they already like.
7. **Premium detection (Porkbun)** — first run `$PY "$SKILL_DIR/scripts/check_domains.py" --porkbun-status`.
   - `working: true` → don't ask; say in one line that premium detection is on.
   - Otherwise ask once, in plain words. For example: *"Optional: some 'free' domains are actually
     premium (the registry charges $100s–$1000s). With a free Porkbun API key (2-minute setup)
     I can detect that and confirm real prices. Want me to walk you through it? (yes / not now)"*
     Recommend it for deep mode or when they're about to buy.
   - **yes** → follow the guided setup in `references/porkbun_setup.md` right away, before generating
     names. You can generate while they're on the Porkbun site if they prefer.
   - **no / not now** → continue without it, mark premium as "not verified" in the report, and don't
     ask again in this session.
   - If the status shows `source: template` or `working: false` with an error, they started the setup
     earlier: offer to finish or fix it instead of starting over.

If the user says "just go" or answers partially, choose sensible defaults (standard depth, global,
tone inferred from the project), state them in one line and continue.

## 2. Generate

Read `references/naming_strategies.md`. Extract 25–40 seed concepts, then generate candidates
across many strategies (count per depth is in that file). Self-screen (famous brands, accidental words,
spelling traps). Save one name per line, with the strategy as a trailing comment, to
`names_r1.txt`:

```
vexo        # coined
getvexo     # modifier
lumora      # portmanteau
```

Keep the strategy map in your notes. You'll need it for the analysis.

## 3. Check availability

Read `references/tld_guide.md` and build the TLD set (core + category + markets + user wishes).
Run the check:

```bash
$PY "$SKILL_DIR/scripts/check_domains.py" --names-file names_r1.txt --tlds com,io,ai,dev,app,co \
    --out availability_r1.json --matrix
```

- About 1–3 s per domain with 12 parallel workers. For more than about 1,500 domains, split the run or
  check the bare names on `com` plus 3–4 key TLDs first.
- `--pricing com,io,ai` prints live first-year and renewal prices and shows whether each TLD has RDAP.
- Status values: `available` / `taken` (high or medium confidence), `likely_available` / `likely_taken`
  (DNS-only guess), `unknown`. Treat `likely_*` and `unknown` as unverified in the report.

## 4. Iterate

Look at the matrix:
- Strong names whose bare `.com` is taken → make modifier variants (`get-`, `use-`, `-hq`, `-app`,
  category suffix) and check them in `names_r2.txt` → `availability_r2.json`.
- See which strategies produce good free names and generate more in that direction.
- quick: at most 1 extra round · standard: 1–2 · deep: 2–3, until there are at least 3× as many
  good free candidates as shortlist slots.

## 5. Research

Read `references/research_playbook.md` and run the checks for the chosen depth on the
pre-shortlist (the ~2× shortlist-size best names). Run web searches in parallel. Check handles:

```bash
$PY "$SKILL_DIR/scripts/check_handles.py" --names-file preshortlist.txt --out handles.json
```

If Porkbun keys are working (from the brief), verify the shortlist for real price and premium status
(`--porkbun`, about 10 s per domain, so tell the user the expected wait). Drop or flag premium names
that are over budget. If the keys aren't set up, don't ask again here; the report marks premium as
unverified.

```bash
$PY "$SKILL_DIR/scripts/check_domains.py" --domains-file shortlist.txt --porkbun --out shortlist_porkbun.json
```

## 6. Score

Score with `references/scoring_rubric.md`: seven weighted criteria plus hard penalties. Pick a
**diverse** shortlist (at most 2 per root, several strategies). For each pick, choose the single
best domain, and list the other free TLDs as alternatives.

## 7. Report

Write `analysis.json` following `references/report_schema.md` (project, language, mode, tlds,
availability files, handles file, all scored candidates, ordered shortlist, recommendation, aftermarket,
next steps, sources). Then render it:

```bash
$PY "$SKILL_DIR/scripts/build_report.py" --analysis domain-research/<slug>/analysis.json
```

This writes `report.html` (cards, a sortable and filterable matrix, light/dark themes) and
`report.md`. If the host can preview or publish HTML (for example an Artifact tool), offer it.

In chat, give a tight summary instead of the full report:
- the top 3–5 domains, each with a one-line reason and price;
- the recommendation in 2–3 sentences;
- the full paths to both report files;
- a reminder that availability changes, so they should register the winner soon (multi-year if
  the renewal price is stable).

## 8. Refine

Ask what they liked and disliked: names, strategies, length, TLDs. Each refinement round reuses the
work folder (`names_r3.txt`, ...), runs only the new checks, and regenerates the same report with
the merged results. Note the round in `methodology`.
