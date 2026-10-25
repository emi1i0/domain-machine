# Guided setup: Porkbun API keys (premium detection)

Without keys the skill already works: availability comes from the registries, and **list prices**
come from Porkbun's public price endpoint. Keys add a per-domain registrar check that reveals
**premium pricing** (names that look free in RDAP/WHOIS but cost hundreds or thousands) and confirms
the real price.

## How to guide the user

Speak in the user's language. Go **one step at a time**: send a step, wait for "done" (or a
question), then send the next. Keep each message short. Use the user's OS for paths and commands.
The keys should never pass through the chat: the user pastes them into a file on their own machine.

### Step 1: account
> Create a free account at https://porkbun.com (Sign Up, top right). You don't need to buy anything
> or add a card. Tell me when you're logged in. If you already have an account, just log in.

### Step 2: create the key
> Go to https://porkbun.com/account/api → in "Create API Key" type any title (e.g. `domain-machine`)
> → **Create**. Porkbun shows two values: an **API Key** (`pk1_...`) and a **Secret Key** (`sk1_...`).
> The secret is shown **only once**, so leave that window open. Don't paste them here.

### Step 3: the config file (you create it, they fill it)
Run:
```bash
$PY "$SKILL_DIR/scripts/check_domains.py" --porkbun-init
```
It creates the config file (default `~/.config/domain-machine/config.json`; on Windows that's
`C:\Users\<user>\.config\domain-machine\config.json`) with two placeholders. It never overwrites an
existing file. Then tell the user the **full absolute path** from the output and how to open it:
- Windows: `notepad "<path>"`
- macOS: `open -e "<path>"`
- Linux: `nano "<path>"` (or their editor)

> Open that file, replace `PASTE_YOUR_API_KEY_HERE` with the API Key (pk1_...) and
> `PASTE_YOUR_SECRET_KEY_HERE` with the Secret Key (sk1_...). Keep the quotes, save, and tell me.

(Alternative for users who prefer it: environment variables `PORKBUN_API_KEY` and
`PORKBUN_SECRET_API_KEY`. Windows: `setx PORKBUN_API_KEY "pk1_..."` then restart the terminal and
Claude Code. macOS/Linux: `export ...` lines in `~/.zshrc` or `~/.bashrc`.)

### Step 4: verify
```bash
$PY "$SKILL_DIR/scripts/check_domains.py" --porkbun-status
```
- `working: true` → confirm it's on. One line: "Premium detection is on. I'll use it on the shortlist."
- `source: template` → the placeholders are still there, or the file isn't valid JSON (a missing quote or
  comma). Ask them to check and save again.
- `message: Invalid API key` → a key was copied incompletely or the two keys are swapped. If the secret
  window is closed, they can delete that key on the same page and create a new one.
- Other errors → show the `message` and `hint` fields, and suggest checking the API section of the
  Porkbun account page.

## Rules

- Never print, log or repeat the keys, and never put them in reports or analysis files.
- If the user pastes keys into the chat anyway, write them into the config file for them, don't echo
  them back, and suggest regenerating the key later since it passed through the chat.
- If the user gets stuck or loses interest, drop it: the skill works without keys.
- The checkDomain endpoint is rate limited (about one check every ~10 s), so use `--porkbun` only on the
  shortlist (`--porkbun-max`, default 40).
