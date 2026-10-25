# Naming strategies

Generate across **many** strategies, not just synonyms. Diversity in the long list is what
finds the gem; the filters later remove the junk. Tag every candidate with its strategy so the
report can show which directions worked and the user can steer ("more like #3").

## Contents
1. Strategy catalogue
2. Domain-specific patterns (modifiers, hacks)
3. Generation procedure
4. Self-screening before checking
5. Multilingual and cultural checks

---

## 1. Strategy catalogue

| Strategy | What it is | Examples | Good when |
|---|---|---|---|
| **descriptive** | Says what it does | `invoicefast`, `petcare` | SEO-heavy, local business, B2B utility |
| **compound** | Two real words fused | `facebook`, `dropbox`, `mailchimp` | Most startups. Concrete noun + action/quality is the classic |
| **portmanteau** | Two words overlapped | `instagram` (instant+telegram), `pinterest`, `groupon` | When two concepts define the product |
| **coined / invented** | New pronounceable word | `kodak`, `xerox`, `vercel`, `zalando` | Want a fully ownable brand; .com more likely free; needs marketing to give meaning |
| **altered spelling** | Real word with vowel drop / swap / suffix | `flickr`, `tumblr`, `lyft`, `fiverr` | Real word is taken. Fails the radio test more often — score accordingly |
| **affix** | Root + brandable suffix/prefix | `spotify`, `shopify`, `optimizely`, `zapier` | Fast way to make a taken word ownable. `-ify -ly -io -ia -ora -era -ex -o -a -iq -hub -kit -base -stack` |
| **metaphor / evocative** | A word that evokes the feeling, not the function | `amazon`, `oracle`, `slack`, `stripe` | Consumer brands, strong identity. Real words → .com almost always taken; pair with modifiers or other TLDs |
| **foreign word** | Meaning in another language | `volvo` (Latin "I roll"), `hulu` (Mandarin), `ikea`… `asana` (Sanskrit) | Global brands; verify meaning & pronunciation with research |
| **classical roots** | Latin/Greek morphemes | `novartis`, `veritas`, `lumen`, `axios`, `kairos` | Serious / enterprise / health / finance |
| **personal / founder** | People or invented personas | `tesla`, `ford`, `wendy's` | Craft, luxury, local, consultancies |
| **acronym / initialism** | Letters | `ibm`, `hbo` | Rarely good for new brands — LLLL.com is all taken; avoid unless user asks |
| **number / symbol** | Numerals in the name | `7eleven`, `1password`, `99designs` | Only when the number is meaningful; hurts the radio test |
| **playful / reduplication** | Rhymes, doubling, sounds | `hubspot`, `tiktok`, `jujutsu`, `bitbit` | Consumer / fun / gaming |
| **local slang** | Market-specific colloquialism | (es-AR) `che`, `posta`; (pt-BR) `bora` | Hyper-local products only, ask before using |

## 2. Domain-specific patterns

These rescue a great name whose bare .com is taken. They are legitimate, widely used, but each
costs a bit of brand strength — the scoring rubric penalises them slightly.

- **Verb prefixes**: `get` `try` `use` `go` `join` `hey` `hello` `meet` `with` `my` `the` → `getvexo.com`, `usevexo.com`
- **Suffix nouns**: `app` `hq` `labs` `studio` `ai` `io` `dev` `team` `cloud` `club` `co` `inc` `works` `kit` `now` `land` → `vexohq.com`
- **Category suffix**: name + what it is → `vexopay.com`, `vexocrm.com` (clear, very common in SaaS)
- **Domain hacks**: the TLD completes the word → `bit.ly`, `del.icio.us`, `instagr.am`, `goo.gl`.
  Only use TLDs that exist and are open to registration (check the TLD guide and `--pricing`).
  Hack finder: for each candidate word, see if its last 2–4 letters form a real TLD
  (`.ly .io .ai .co .me .sh .so .es .is .it .us .in .at .to .am .fm .gg .re .st .ink .app .dev`).
- **Country/market suffix**: `vexo.com.ar`, `vexo.de` for local presence (see TLD guide)

## 3. Generation procedure

1. Extract **seed concepts** from the briefing: what it does (verbs), what it is (nouns), the outcome
   for the user (benefits), the feeling (adjectives), the audience, metaphors (animals, nature,
   mythology, physics, places), and the market language(s). Aim for 25–40 seeds.
2. For each strategy above that fits the project's tone, generate a batch. Rough budget per mode:
   - quick: 40–60 names total, 5–7 strategies
   - standard: 100–150 names, 8–10 strategies
   - deep: 200–350 names over 2–3 rounds, all fitting strategies + modifiers + hacks
3. Keep names **lowercase ASCII `a-z0-9-`** (IDNs only if the user explicitly wants them).
4. Run availability **across the core TLD set first** (see TLD guide), then:
   - Names with nothing free at all → drop unless outstanding.
   - Outstanding names with only the bare .com taken → generate modifier variants
     (`get-`, `-hq`, category suffix) and re-check them (round 2).
   - Look at which strategies produced free + good names and lean into them (round 3, deep mode).

## 4. Self-screening before checking

Drop or flag before spending checks on them:
- Exact or near match of a famous brand (Google, Meta, Notion…) — legal risk and zero chance.
- Hard to spell after hearing it once (ambiguous `c/k/q`, `ph/f`, `i/y`, doubled letters) — keep only if
  otherwise exceptional, and flag it.
- Over 15 characters for the main brand (modifiers can stretch to ~18).
- Hyphens and digits — avoid unless meaningful.
- Accidental words when letters run together (classic failures: `expertsexchange`, `penisland`,
  `therapistfinder`, `whorepresents`). Read every compound **without** word boundaries.
- Letter clusters that look like other letters in lowercase (`rn`→`m`, `cl`→`d`, `vv`→`w`, `l`/`I`).

## 5. Multilingual and cultural checks

Global brands must not mean something bad elsewhere. For every shortlisted name:
- Check meaning in the major languages of the target markets (at least: English, Spanish,
  Portuguese, French, German, Italian, plus the user's language and any market languages).
- Classic failures: Nova ("no va" in Spanish — mostly myth, but the concern is real), Pajero
  (Spanish slang), Fiat "Uno" fine but "Mist" (= manure in German), "Kinder" fine, "Bimbo" (bakery
  in Mexico, insult in English).
- Pronunciation: will English, Spanish and the user's language speakers say it the same way?
  Provide a pronunciation hint (`VEK-so`) in the report for coined names.
- Use web search for "<name> meaning", "<name> slang", "<name> significado", Urban Dictionary,
  Wiktionary when in doubt. In deep mode do this for every shortlisted name.
