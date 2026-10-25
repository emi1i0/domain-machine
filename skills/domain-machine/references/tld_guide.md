# TLD guide

Prices change; **always fetch live prices** with `check_domains.py --pricing com,io,ai,...`
(Porkbun public price list, cached 24 h). The tiers below are orientation only.
Facts about ccTLD rules change too — when a ccTLD is a serious contender, confirm its current
registration rules with a quick web search of the registry's site before recommending it.

## Contents
1. Choosing the TLD set to check
2. gTLD notes
3. ccTLD notes (startup "hacks" and markets)
4. Traps: renewals, premium, reserved, HSTS
5. Registry RDAP/WHOIS coverage (what the script can verify)

---

## 1. Choosing the TLD set

Build the set from four buckets, then de-duplicate. Typical size: quick 5–7, standard 8–12, deep 12–20.

1. **Universal core** — always: `com`. Add `net`, `org` only if the project is non-profit/community (org)
   or infrastructure (net).
2. **Category set** — pick by project type:
   - Dev tools / SaaS / tech: `io` `dev` `app` `so` `sh` `tech` `cloud` `run` `tools`
   - AI products: `ai` (expensive) plus `io` `app` `dev`
   - Consumer / mobile apps: `app` `co` `me` `fun` `life`
   - Commerce: `shop` `store` `co` `market`
   - Media / creators: `tv` `fm` `studio` `blog` `news` `me`
   - Gaming / communities: `gg` `games` `club` `community`
   - Design / agencies: `design` `studio` `agency` `works`
   - Finance: `finance` `money` `capital` `fund` (check prices; some have high renewals)
   - Health: `health` `care` `clinic` (some restricted / pricey)
   - Personal / portfolio: `me` `dev` `page` `xyz`
3. **Market ccTLDs** — for each target country: its ccTLD and the common second level, e.g.
   Argentina `com.ar` (and `ar`), Mexico `mx` `com.mx`, Brazil `com.br`, Spain `es`, Germany `de`,
   UK `co.uk` `uk`, France `fr`, Chile `cl`, Colombia `co`/`com.co`, India `in`, Canada `ca`, Australia `com.au`.
   For a "global" project with no specific market, skip this bucket unless the user is based somewhere
   and wants a local mirror; ask once.
4. **User wishes** — any TLD the user names.

## 2. gTLD notes

| TLD | Notes |
|---|---|
| `.com` | The default trust signal. Most short real words taken; coined names often free. Moderate, steady price. If the .com is taken by an active business in the same space, treat the name as risky even on other TLDs. |
| `.net` `.org` | Fine secondary; `.org` reads as non-profit/community. |
| `.app` `.dev` `.page` | Google Registry. **HSTS-preloaded**: sites only load over HTTPS (fine with any modern host, but tell the user). Cheap-ish, credible for software. |
| `.ai` | Technically a ccTLD (Anguilla) used as a gTLD. Popular for AI; **expensive** and registrars commonly require a **2-year minimum**. Many short names are premium. |
| `.io` | ccTLD (British Indian Ocean Territory) used by tech. Higher renewal than first year at many registrars. The 2024 UK–Mauritius Chagos agreement raised questions about the TLD's long-term future; ccTLDs can be retired by IANA if the country code disappears, though any change would take years. Mention as a minor long-term risk for a flagship brand. |
| `.co` | Colombia, marketed as "company". Easily confused with .com (mail sent to .com by mistake). |
| `.so` `.sh` | Somalia / Saint Helena; short and used by dev tools (`notion.so` historically). Pricey. |
| `.xyz` | Very cheap first year, **renewal much higher**, and widely abused → spam-filter reputation risk for email. |
| `.tech` `.online` `.site` `.store` `.fun` | Cheap first year, **renewal often 5–10×**. Some have poor email/spam reputation. |
| `.cloud` `.run` `.tools` `.studio` `.design` `.agency` | Descriptive new gTLDs; fine as secondary or for hacks, check renewal. |
| `.me` | Montenegro; personal brands, apps. |
| `.tv` `.fm` `.gg` | Tuvalu / Micronesia / Guernsey; media, audio, gaming. Pricey. |
| `.ly` | Libya. Good hacks (`bit.ly`), but has content rules and political-instability history — flag. |

## 3. ccTLD notes

Residency / local-presence requirements matter: recommend a ccTLD only if the user can register it.

| TLD | Requirement (verify current rules) |
|---|---|
| `.com.ar` / `.ar` | NIC Argentina. Registration through nic.ar with a validated identity (Argentine tax ID — CUIT/CUIL — or foreign-entity procedure). Cheap. Not sold by most international registrars. |
| `.com.br` | Registro.br; requires a Brazilian CPF/CNPJ. |
| `.mx` `.com.mx` | Open to anyone via most registrars. |
| `.es` | Open (EU and non-EU) via registrars. WHOIS is IP-restricted → the script can only give a DNS-based guess. |
| `.de` | Open; non-German registrants need an admin contact/trustee in Germany at some registrars. |
| `.fr` `.eu` `.it` | EU/EEA residence or citizenship. |
| `.uk` `.co.uk` | Open. |
| `.ca` | Canadian Presence Requirements. |
| `.us` | US nexus required. |
| `.com.au` | Australian presence + ABN. |
| `.jp` | Japanese address required. |
| `.in` `.cl` `.co` `.me` `.io` `.ai` | Open. |

## 4. Traps to call out in the report

- **Renewal ≫ first year**: always show both prices; flag when renewal is > 2× registration.
- **Premium names**: registries price some "unregistered" names at hundreds or thousands per year.
  RDAP/WHOIS show them as free. Only the Porkbun check (`--porkbun`) or the registrar checkout reveals
  it. In the report, mark top picks as "premium not verified" when Porkbun was not used.
- **Reserved names**: some registries block names (country names, generic words, 1–2 letters). Same
  detection limits as premium.
- **Recently dropped / pending delete**: rare false "available" during the redemption window —
  another reason the report says "confirm at checkout".
- **HSTS TLDs** (`.app .dev .page` and others from Google Registry): HTTPS only.
- **Email reputation**: cheap abused TLDs land in spam more often; mention if the brand depends on email.

## 5. What the script can verify

- **RDAP (high confidence)**: all gTLDs, plus many ccTLDs (e.g. `ai`, `br`, `uk`, `fr`, `ca`, `in`, `ar`).
  The IANA bootstrap file decides; run `--pricing <tlds>` to see `"rdap": true/false` per TLD.
- **WHOIS fallback (medium confidence)**: TLDs without RDAP (e.g. `io`, `co`, `me`, `de`, `cl`, `us`,
  `jp`, `mx`, `gg`, `com.ar`). Parsed by known "not found" phrases.
- **DNS only (low confidence)**: when the registry can't be queried (e.g. `.es`). NXDOMAIN means
  probably free, but a registered domain without nameservers also returns NXDOMAIN.
- **Porkbun (high confidence + price + premium)**: for TLDs Porkbun sells. Rate limited.
