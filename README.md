# domain-machine

**A Claude Code skill that finds a name and a domain for your project, and checks that the domain is really free.**

Normally you think of a name, find it taken, try another, and end up with 40 browser tabs. Domain Machine
does that loop for you:

1. **Brief.** It reads your repo (README, package.json, docs) or asks a few short questions: what the project is, who it's for, tone, markets, budget, and how deep to go.
2. **Generate.** It brainstorms 50–350 names using more than 12 naming strategies: compounds, portmanteaus, coined words, metaphors, classical roots, foreign words, `get-`/`-hq` modifiers, domain hacks and more.
3. **Check.** It bulk-checks real availability straight from the registries: DNS-over-HTTPS prefilter, then **RDAP**, then a **WHOIS** fallback. No Googling, and no registrar search boxes that could leak your idea to front-runners.
4. **Iterate.** Good names whose `.com` is taken get modifier variants, and strategies that work get more rounds.
5. **Research.** It looks for companies with the same name, does a trademark knockout search (WIPO, USPTO, EUIPO, national offices), checks handles (GitHub, npm, PyPI, crates.io), looks for bad meanings in other languages, and checks whether a taken `.com` is parked or for sale.
6. **Score.** A weighted rubric covers memorability, the radio test, pronunciation, fit, distinctiveness, brevity and domain quality, with penalties for conflicts.
7. **Report.** You get a polished **HTML report** (top-pick cards plus a sortable, filterable availability matrix, in light and dark themes) and a **Markdown** version, with live first-year and renewal prices and direct register links.

The agent talks to you in your language, and the report is written in it too. It works for any market: global, or specific countries with their ccTLDs.

## Install

At the prompt of a Claude Code session:

```
/plugin install domain-machine --marketplace emi1i0/domain-machine
```

Answer `y` to add the marketplace, then pick a scope. From a shell:

```
claude plugin install domain-machine --marketplace emi1i0/domain-machine
```

**Requirements:** Python 3.8 or newer on your PATH (`python3`, `python` or `py`). Standard library only, nothing to `pip install`.

## Use

Just ask, in any language:

> find me a domain for this project
>
> necesito un nombre y dominio para una app de recetas para estudiantes, modo profundo
>
> are there good .ai domains for an AI tutoring startup?

Or invoke it directly with `/domain-machine:domain-machine`.

You choose the depth each time:

| Depth | Names | TLDs | Research | Shortlist |
|---|---|---|---|---|
| quick | ~50 | 5–7 | quick conflict check | 5 |
| standard | ~120 | 8–12 | conflicts, light trademark, handles | 8–10 |
| deep | 200–350, several rounds | 12–20 | full conflicts, trademarks per market, handles, meanings, aftermarket, premium check | 12–15 |

When it finishes, the **HTML report opens in your browser** automatically. Everything lives in
`./domain-research/<project>/`, and the skill adds a `.gitignore` inside `domain-research/` so that
**only `report.md` gets versioned**. The working files (name lists, JSON results, the HTML) stay local,
and your project's own `.gitignore` is never touched.

## Optional: Porkbun API keys

Without keys, everything works: availability comes from the registries, and list prices come from Porkbun's
public price list. With free [Porkbun API keys](https://porkbun.com/account/api), the skill also detects
**premium-priced** names (these look free in RDAP/WHOIS) and confirms the real price before you buy.
You don't need to set it up in advance: at the start of each run the skill checks for keys and, if
there are none, asks whether you want them. If you say yes, it walks you through the 2-minute setup
step by step and verifies the keys at the end. The keys never pass through the chat. The steps are
in [`skills/domain-machine/references/porkbun_setup.md`](skills/domain-machine/references/porkbun_setup.md).
To do it by hand, save the keys to `~/.config/domain-machine/config.json`:

```json
{"porkbun_api_key": "pk1_...", "porkbun_secret_api_key": "sk1_..."}
```

## Using the scripts on their own

```bash
# availability matrix: names x TLDs
python3 skills/domain-machine/scripts/check_domains.py --names vexo,lumora --tlds com,io,ai,dev --matrix

# live prices + whether each TLD has RDAP
python3 skills/domain-machine/scripts/check_domains.py --pricing com,io,ai,co,com.ar

# handles on GitHub / npm / PyPI / crates.io
python3 skills/domain-machine/scripts/check_handles.py --names vexo,lumora
```

## How reliable is "available"?

| Method | Used for | Confidence |
|---|---|---|
| DNS NS records present | any TLD | taken: high |
| RDAP 404 / 200 | all gTLDs + many ccTLDs (`.ai`, `.uk`, `.fr`, `.br`, `.ca`…) | high |
| WHOIS "not found" phrases | ccTLDs without RDAP (`.io`, `.co`, `.me`, `.de`, `.com.ar`, `.jp`…) | medium |
| DNS NXDOMAIN only | registries that can't be queried (e.g. `.es`) | low (`likely_available`) |
| Porkbun checkDomain | TLDs Porkbun sells | high, plus price and premium flag |

Nothing is guaranteed until checkout. Someone can register a name between the check and your purchase,
and some registries hold reserved or premium names. Trademark findings are a preliminary knockout search,
not legal advice.

## Layout

```
.claude-plugin/        plugin.json + marketplace.json
skills/domain-machine/
  SKILL.md             the workflow the agent follows
  scripts/             init_workspace.py · check_domains.py · check_handles.py · build_report.py
  references/          naming strategies · TLD guide · scoring rubric · research playbook · report schema · Porkbun setup
```

## License

MIT
