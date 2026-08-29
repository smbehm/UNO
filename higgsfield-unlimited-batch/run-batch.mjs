#!/usr/bin/env node
/**
 * Higgsfield Unlimited Batch Runner
 *
 * Automates prompt submission on higgsfield.ai in a real browser so the
 * Unlimited toggle applies (CLI/MCP always use credits).
 *
 * Usage:
 *   node run-batch.mjs setup    # one-time: log in, pick model, enable Unlimited
 *   node run-batch.mjs batch    # run all prompts in prompts.json
 *   node run-batch.mjs dry-run  # verify page + toggle without generating
 */

import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = __dirname;
const CONFIG_PATH = path.join(ROOT, 'config.json');
const PROMPTS_PATH = path.join(ROOT, 'prompts.json');
const PROFILE_DIR = path.join(ROOT, 'browser-profile');
const MANIFEST_PATH = path.join(ROOT, 'runs', 'manifest.jsonl');
const STATE_PATH = path.join(ROOT, 'state.json');

const DEFAULT_CONFIG = {
  startUrl: 'https://higgsfield.ai/',
  maxWaitMinutes: 45,
  pauseBetweenPromptsSeconds: 8,
  requireUnlimitedToggle: true,
  headless: false,
  slowMoMs: 0,
};

function loadJson(filePath, fallback = null) {
  if (!fs.existsSync(filePath)) return fallback;
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function saveJson(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, 'utf8');
}

function appendManifest(entry) {
  fs.mkdirSync(path.dirname(MANIFEST_PATH), { recursive: true });
  fs.appendFileSync(MANIFEST_PATH, `${JSON.stringify(entry)}\n`, 'utf8');
}

function waitForEnter(message) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(message, () => {
      rl.close();
      resolve();
    });
  });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ensureConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    fs.copyFileSync(path.join(ROOT, 'config.example.json'), CONFIG_PATH);
    console.log('Created config.json from example.');
  }
  return { ...DEFAULT_CONFIG, ...loadJson(CONFIG_PATH, {}) };
}

function ensurePrompts() {
  if (!fs.existsSync(PROMPTS_PATH)) {
    fs.copyFileSync(path.join(ROOT, 'prompts.example.json'), PROMPTS_PATH);
    console.log('Created prompts.json from example — edit it with your 10 scenes.');
  }
  const prompts = loadJson(PROMPTS_PATH, []);
  if (!Array.isArray(prompts) || prompts.length === 0) {
    throw new Error('prompts.json must be a non-empty array of prompt strings.');
  }
  return prompts;
}

async function launchBrowser(config) {
  fs.mkdirSync(PROFILE_DIR, { recursive: true });

  const launchOptions = {
    headless: config.headless,
    slowMo: config.slowMoMs,
    viewport: { width: 1440, height: 900 },
    args: ['--disable-blink-features=AutomationControlled'],
  };

  let browser;
  try {
    browser = await chromium.launch({ ...launchOptions, channel: 'chrome' });
  } catch {
    console.log('Chrome not found — using bundled Chromium.');
    browser = await chromium.launch(launchOptions);
  }

  const context = await browser.newContext({
    storageState: fs.existsSync(STATE_PATH) ? STATE_PATH : undefined,
    userAgent:
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  });

  const page = await context.newPage();
  return { browser, context, page };
}

async function saveSession(context) {
  await context.storageState({ path: STATE_PATH });
}

/** Track job IDs and completion via Higgsfield API responses in the browser. */
function attachJobTracker(page) {
  const tracker = {
    activeJobs: new Set(),
    completedJobs: new Set(),
    failedJobs: new Set(),
    lastJobId: null,
  };

  page.on('response', async (response) => {
    const url = response.url();
    if (!url.includes('higgsfield')) return;

    try {
      if (response.request().method() === 'POST' && /\/jobs(\/v2)?\//.test(url)) {
        if (response.status() >= 200 && response.status() < 300) {
          const body = await response.json().catch(() => null);
          const jobId =
            body?.id ??
            body?.job_set_id ??
            body?.jobSetId ??
            body?.data?.id ??
            body?.data?.job_set_id;
          if (jobId) {
            tracker.activeJobs.add(String(jobId));
            tracker.lastJobId = String(jobId);
          }
        }
      }

      if (/\/jobs(\/v2)?\/.+\/(status)?/.test(url) || /\/job-sets\//.test(url)) {
        const body = await response.json().catch(() => null);
        const status = (
          body?.status ??
          body?.data?.status ??
          body?.jobs?.[0]?.status ??
          ''
        ).toLowerCase();

        const idMatch = url.match(/\/(?:jobs(?:\/v2)?|job-sets)\/([^/?]+)/);
        const jobId = idMatch?.[1] ?? tracker.lastJobId;
        if (!jobId) return;

        if (['completed', 'complete', 'succeeded', 'success', 'done'].includes(status)) {
          tracker.activeJobs.delete(String(jobId));
          tracker.completedJobs.add(String(jobId));
        }
        if (['failed', 'error', 'cancelled', 'canceled'].includes(status)) {
          tracker.activeJobs.delete(String(jobId));
          tracker.failedJobs.add(String(jobId));
        }
        if (['in_progress', 'processing', 'queued', 'pending', 'running'].includes(status)) {
          tracker.activeJobs.add(String(jobId));
        }
      }
    } catch {
      // Ignore parse errors on non-JSON responses.
    }
  });

  return tracker;
}

async function waitForLoginIfNeeded(page) {
  const url = page.url();
  if (/sign-in|login|clerk|accounts\./i.test(url)) {
    console.log('\n>>> Please sign in to Higgsfield in the browser window.');
    console.log('>>> When you see the app (not the login page), press Enter here.\n');
    await waitForEnter('');
    await saveSession(page.context());
  }
}

async function findPromptInput(page) {
  const selectors = [
    'textarea[placeholder*="prompt" i]',
    'textarea[placeholder*="describe" i]',
    'textarea',
    '[contenteditable="true"]',
    '[role="textbox"]',
  ];

  for (const selector of selectors) {
    const el = page.locator(selector).first();
    if (await el.isVisible({ timeout: 1500 }).catch(() => false)) {
      return el;
    }
  }

  throw new Error('Could not find a prompt input (textarea). Scroll to the generator panel.');
}

async function findGenerateButton(page) {
  const candidates = [
    page.getByRole('button', { name: /^generate$/i }),
    page.getByRole('button', { name: /generate/i }),
    page.locator('button:has-text("Generate")'),
  ];

  for (const btn of candidates) {
    if (await btn.first().isVisible({ timeout: 1500 }).catch(() => false)) {
      return btn.first();
    }
  }

  throw new Error('Could not find the Generate button.');
}

async function ensureUnlimitedOn(page) {
  // Look for Unlimited toggle — Higgsfield shows it near the generate panel.
  const unlimitedLabel = page.getByText(/^unlimited$/i).first();
  const hasLabel = await unlimitedLabel.isVisible({ timeout: 3000 }).catch(() => false);

  if (!hasLabel) {
    console.warn('WARNING: Unlimited toggle not visible. This model may not support Unlimited,');
    console.warn('         or you may need to scroll to the generate panel.');
    return false;
  }

  // Walk up to a switch/checkbox/button sibling.
  const container = unlimitedLabel.locator('xpath=ancestor::*[self::label or self::div][1]');
  const toggle = container.locator('button[role="switch"], input[type="checkbox"], button').first();

  if (await toggle.isVisible({ timeout: 2000 }).catch(() => false)) {
    const ariaChecked = await toggle.getAttribute('aria-checked');
    const checked = await toggle.isChecked().catch(() => null);

    const isOn = ariaChecked === 'true' || checked === true;
    if (!isOn) {
      console.log('Turning Unlimited toggle ON...');
      await toggle.click();
      await sleep(500);
    } else {
      console.log('Unlimited toggle is already ON.');
    }
    return true;
  }

  // Fallback: click the label area if it's a custom toggle.
  console.log('Could not detect toggle state — clicking Unlimited label area.');
  await unlimitedLabel.click({ force: true }).catch(() => {});
  return true;
}

async function isGenerating(page) {
  const generatingTexts = [/generating/i, /in queue/i, /processing/i, /please wait/i];
  for (const pattern of generatingTexts) {
    if (await page.getByText(pattern).first().isVisible({ timeout: 500 }).catch(() => false)) {
      return true;
    }
  }

  const btn = await findGenerateButton(page).catch(() => null);
  if (!btn) return false;
  const disabled = await btn.isDisabled().catch(() => false);
  const text = (await btn.textContent().catch(() => '')) ?? '';
  return disabled || /generating/i.test(text);
}

async function waitForGenerationComplete(page, tracker, config, promptIndex) {
  const deadline = Date.now() + config.maxWaitMinutes * 60 * 1000;
  const startJobCount = tracker.completedJobs.size;
  let sawActivity = false;

  // Give the UI a moment to register the click.
  await sleep(2000);

  while (Date.now() < deadline) {
    if (tracker.failedJobs.size > 0) {
      throw new Error(`Generation failed (job tracking). Check the browser.`);
    }

    if (tracker.completedJobs.size > startJobCount) {
      console.log(`  Job completed (API).`);
      return;
    }

    if (tracker.activeJobs.size > 0) {
      sawActivity = true;
    }

    const generating = await isGenerating(page);
    if (generating) {
      sawActivity = true;
      process.stdout.write('.');
    } else if (sawActivity) {
      console.log('\n  UI shows idle after activity — treating as complete.');
      return;
    }

    await sleep(3000);
  }

  throw new Error(`Timed out after ${config.maxWaitMinutes} minutes on prompt ${promptIndex + 1}.`);
}

async function submitPrompt(page, prompt, tracker, config, index, total) {
  console.log(`\n[${index + 1}/${total}] ${prompt.slice(0, 80)}${prompt.length > 80 ? '…' : ''}`);

  if (config.requireUnlimitedToggle) {
    await ensureUnlimitedOn(page);
  }

  const input = await findPromptInput(page);
  await input.click();
  await input.fill('');
  await input.fill(prompt);

  const beforeCompleted = tracker.completedJobs.size;
  const generateBtn = await findGenerateButton(page);

  if (await generateBtn.isDisabled().catch(() => false)) {
    throw new Error('Generate button is disabled. Check prompt, model settings, or queue.');
  }

  await generateBtn.click();
  console.log('  Submitted — waiting for completion (Unlimited queue may be slower)...');

  await waitForGenerationComplete(page, tracker, config, index);

  appendManifest({
    ts: new Date().toISOString(),
    index: index + 1,
    prompt,
    status: 'completed',
    completedJobs: tracker.completedJobs.size - beforeCompleted,
  });

  if (config.pauseBetweenPromptsSeconds > 0) {
    console.log(`  Pausing ${config.pauseBetweenPromptsSeconds}s before next prompt...`);
    await sleep(config.pauseBetweenPromptsSeconds * 1000);
  }
}

async function runSetup(config) {
  const { browser, context, page } = await launchBrowser(config);

  console.log('\n=== SETUP MODE ===\n');
  console.log('1. A browser window will open.');
  console.log('2. Sign in to Higgsfield if needed.');
  console.log('3. Navigate to YOUR model/workflow page (Seedance, Kling, Cinema Studio, etc.).');
  console.log('4. Set aspect ratio, duration, and any reference images.');
  console.log('5. Turn the UNLIMITED toggle ON (not Credit Mode).');
  console.log('6. Come back here and press Enter to save this page as your batch start URL.\n');

  await page.goto(config.startUrl, { waitUntil: 'domcontentloaded', timeout: 120000 });
  await waitForLoginIfNeeded(page);

  await waitForEnter('Press Enter when the page is ready (model chosen, Unlimited ON)... ');

  const currentUrl = page.url();
  config.startUrl = currentUrl;
  saveJson(CONFIG_PATH, config);

  await ensureUnlimitedOn(page);
  await saveSession(context);

  console.log(`\nSaved start URL: ${currentUrl}`);
  console.log('Saved login session to state.json');
  console.log('\nNext: edit prompts.json with your scenes, then run:  npm run batch\n');

  await browser.close();
}

async function runDryRun(config) {
  const { browser, context, page } = await launchBrowser(config);

  console.log('\n=== DRY RUN ===\n');
  await page.goto(config.startUrl, { waitUntil: 'domcontentloaded', timeout: 120000 });
  await waitForLoginIfNeeded(page);

  await findPromptInput(page);
  console.log('OK: Prompt input found.');

  await findGenerateButton(page);
  console.log('OK: Generate button found.');

  if (config.requireUnlimitedToggle) {
    const ok = await ensureUnlimitedOn(page);
    console.log(ok ? 'OK: Unlimited toggle handled.' : 'WARN: Unlimited toggle not confirmed.');
  }

  await saveSession(context);
  console.log('\nDry run passed. Ready for: npm run batch\n');
  await browser.close();
}

async function runBatch(config) {
  const prompts = ensurePrompts();
  const { browser, context, page } = await launchBrowser(config);
  const tracker = attachJobTracker(page);

  console.log('\n=== BATCH RUN ===');
  console.log(`Prompts: ${prompts.length}`);
  console.log(`Start URL: ${config.startUrl}`);
  console.log(`Max wait per prompt: ${config.maxWaitMinutes} min`);
  console.log('Keep this window open overnight. Do not close the browser.\n');

  await page.goto(config.startUrl, { waitUntil: 'domcontentloaded', timeout: 120000 });
  await waitForLoginIfNeeded(page);

  const runStarted = new Date().toISOString();
  let failed = 0;

  for (let i = 0; i < prompts.length; i++) {
    try {
      await submitPrompt(page, prompts[i], tracker, config, i, prompts.length);
    } catch (err) {
      failed++;
      const message = err instanceof Error ? err.message : String(err);
      console.error(`\n  ERROR: ${message}`);
      appendManifest({
        ts: new Date().toISOString(),
        index: i + 1,
        prompt: prompts[i],
        status: 'failed',
        error: message,
      });

      console.log('  Waiting 30s before retrying same prompt once...');
      await sleep(30000);
      try {
        await page.goto(config.startUrl, { waitUntil: 'domcontentloaded', timeout: 120000 });
        await submitPrompt(page, prompts[i], tracker, config, i, prompts.length);
        failed--;
      } catch (retryErr) {
        const retryMsg = retryErr instanceof Error ? retryErr.message : String(retryErr);
        console.error(`  Retry failed: ${retryMsg}`);
        appendManifest({
          ts: new Date().toISOString(),
          index: i + 1,
          prompt: prompts[i],
          status: 'failed_retry',
          error: retryMsg,
        });
      }
    }
  }

  await saveSession(context);
  await browser.close();

  console.log('\n=== DONE ===');
  console.log(`Started: ${runStarted}`);
  console.log(`Finished: ${new Date().toISOString()}`);
  console.log(`Failed: ${failed}/${prompts.length}`);
  console.log(`Log: ${MANIFEST_PATH}`);
}

async function main() {
  const mode = process.argv[2] ?? 'batch';
  const config = ensureConfig();

  switch (mode) {
    case 'setup':
      await runSetup(config);
      break;
    case 'dry-run':
      await runDryRun(config);
      break;
    case 'batch':
      await runBatch(config);
      break;
    default:
      console.error(`Unknown mode: ${mode}. Use setup | batch | dry-run`);
      process.exit(1);
  }
}

main().catch((err) => {
  console.error('\nFatal error:', err.message ?? err);
  process.exit(1);
});
