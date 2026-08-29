# Higgsfield Unlimited Overnight Batch

Run a queue of prompts on **[higgsfield.ai](https://higgsfield.ai)** in a real browser with **Unlimited mode ON** — so generations do not deduct credits (unlike the official CLI).

## Important

- **Unlimited only works on the website**, not through the official Higgsfield CLI.
- Higgsfield's terms note that Unlimited is intended for normal personal use; heavy automation may be slowed or reviewed. Use reasonable pauses between prompts.
- **Unlimited allows only 1 concurrent generation** — this script runs prompts **one at a time** on purpose.
- Keep your PC awake overnight (disable sleep in Windows Power settings).

## What you need

- Windows 10/11
- [Node.js 18+](https://nodejs.org/)
- Google Chrome installed (recommended)
- Higgsfield account with Unlimited active on your chosen model

## Quick start (Windows)

### 1. One-time setup

Double-click **`setup.bat`**, or in PowerShell:

```powershell
cd path\to\higgsfield-unlimited-batch
npm.cmd install
npx.cmd playwright install chrome
npm.cmd run setup
```

In the browser that opens:

1. Sign in to Higgsfield
2. Open the **exact model/page** you use for scenes (e.g. Seedance, Kling, Cinema Studio)
3. Set duration, aspect ratio, references, etc.
4. Turn **Unlimited ON** (not Credit Mode)
5. Return to the terminal and press **Enter**

### 2. Add your prompts

Copy and edit `prompts.json`:

```powershell
copy prompts.example.json prompts.json
notepad prompts.json
```

Use a JSON array of strings — one prompt per scene:

```json
[
  "Scene 1: wide underwater reef at dawn, cinematic 16:9",
  "Scene 2: sea turtle glides past ancient ruins"
]
```

### 3. Test (optional)

```powershell
npm.cmd run dry-run
```

Confirms the prompt box, Generate button, and Unlimited toggle are detected.

### 4. Run overnight

Double-click **`run-overnight.bat`**, or:

```powershell
npm.cmd run batch
```

Leave **both** the terminal and Chrome window open. Progress is logged to `runs/manifest.jsonl`.

## Files

| File | Purpose |
|------|---------|
| `setup.bat` | First-time install + setup |
| `run-overnight.bat` | Start the batch queue |
| `prompts.json` | Your scene prompts (you create this) |
| `config.json` | Saved start URL and timing (auto-created) |
| `state.json` | Saved login session |
| `runs/manifest.jsonl` | Log of each prompt (success/fail) |

## Config options (`config.json`)

| Key | Default | Description |
|-----|---------|-------------|
| `startUrl` | set during setup | Page URL with your model + settings |
| `maxWaitMinutes` | 45 | Max wait per prompt (Unlimited queue can be slow) |
| `pauseBetweenPromptsSeconds` | 8 | Pause between scenes |
| `requireUnlimitedToggle` | true | Verify Unlimited is ON before each prompt |
| `headless` | false | Must stay `false` for login + Unlimited |

## Troubleshooting

**PowerShell blocks npm** — use `npm.cmd` instead of `npm`, or run the `.bat` files.

**"Could not find prompt input"** — during setup, scroll until the generator panel is visible, then press Enter.

**Unlimited toggle not found** — your model may not be on Unlimited. Check **Manage Account → Subscription → Active unlimited models**.

**Generation times out** — increase `maxWaitMinutes` in `config.json`. Unlimited uses the standard (slower) queue.

**Session expired** — run `npm.cmd run setup` again and sign in.

**Prompt failed mid-batch** — the script retries once, logs the error, and continues. Check `runs/manifest.jsonl`.

## Re-run setup

If you change models or settings:

```powershell
npm.cmd run setup
```

Navigate to the new page, enable Unlimited, press Enter.
