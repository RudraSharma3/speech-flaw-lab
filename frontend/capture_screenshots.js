import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import crypto from 'crypto';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');
const SCREENSHOTS_DIR = path.join(ROOT_DIR, 'docs', 'screenshots');

if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

function getFileSha256(filePath) {
  const data = fs.readFileSync(filePath);
  return crypto.createHash('sha256').update(data).digest('hex');
}

async function capture() {
  console.log('Starting Playwright screenshot capture...');
  console.log('Target directory:', SCREENSHOTS_DIR);

  const browser = await chromium.launch({
    channel: 'msedge',
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  const consoleLogs = [];
  const consoleErrors = [];

  page.on('console', (msg) => {
    const text = msg.text();
    consoleLogs.push(`[${msg.type()}] ${text}`);
    if (msg.type() === 'error') {
      consoleErrors.push(text);
    }
  });

  page.on('pageerror', (err) => {
    consoleErrors.push(`[PAGE ERROR] ${err.message}`);
  });

  const BASE_URL = 'http://localhost:8000';

  try {
    console.log(`Navigating to ${BASE_URL}...`);
    await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // 1. Upload Page (Focused on top upload panel, dropzone & transcript inputs)
    console.log('1. Capturing upload_page.png...');
    // Scroll strictly to top to show upload zone and header
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(500);
    const uploadDropzone = page.locator('text=Drag & drop audio file here, or click to browse');
    if (await uploadDropzone.count() > 0) {
      await uploadDropzone.scrollIntoViewIfNeeded();
    }
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'upload_page.png'),
      fullPage: false,
    });

    // 2. Sample Loaded (Scroll to show ScoreCard & Waveform clearly)
    console.log('2. Loading benchmark sample & capturing sample_loaded.png...');
    // Select Level 1 flawed take
    const sampleBtn = page.locator('button:has-text("JFK Moon Speech — Level 1")').first();
    if (await sampleBtn.count() > 0) {
      await sampleBtn.click();
      await page.waitForTimeout(2500);
    }
    // Wait for ScoreCard overall score to appear
    await page.waitForSelector('text=Score', { state: 'visible', timeout: 10000 });
    // Scroll so the waveform viewer and scorecard are top of viewport
    const scoreCard = page.locator('text=Deterministic Score Breakdown').first();
    if (await scoreCard.count() > 0) {
      await scoreCard.scrollIntoViewIfNeeded();
      await page.waitForTimeout(800);
    }
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'sample_loaded.png'),
      fullPage: false,
    });

    // 3. Flaw Selected with Causal Explanation
    console.log('3. Selecting flaw & asserting explanation card is visible...');
    // Click Next Flaw button or flaw badge to activate causal explanation card
    const nextFlawBtn = page.locator('button[title="Next Flaw"]').first();
    if (await nextFlawBtn.count() > 0) {
      await nextFlawBtn.click();
      await page.waitForTimeout(1000);
    }
    // Assert Causal Explanation Card text is visible
    const explanationHeading = page.locator('text=Why It Hurts').first();
    await explanationHeading.waitFor({ state: 'visible', timeout: 10000 });
    const isVisible = await explanationHeading.isVisible();
    if (!isVisible) {
      throw new Error('ASSERTION FAILED: Causal Explanation Card "Why It Hurts" is not visible!');
    }
    console.log('   [ASSERTION PASSED]: "Why It Hurts" causal explanation card verified visible.');

    // Scroll Causal Explanation Card to center
    await explanationHeading.scrollIntoViewIfNeeded();
    await page.waitForTimeout(800);
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'flaw_selected_explanation.png'),
      fullPage: false,
    });

    // 4. Spectrogram View (Mel Spectrogram Heatmap)
    console.log('4. Navigating to Acoustic Plots & Mel Spectrogram...');
    const acousticTab = page.locator('button:has-text("Acoustic Contours")').first();
    await acousticTab.waitFor({ state: 'visible', timeout: 10000 });
    await acousticTab.click();
    await page.waitForTimeout(1000);

    const specToggle = page.locator('#spectrogram-toggle-btn, button:has-text("Mel Spectrogram")').first();
    if (await specToggle.count() > 0) {
      await specToggle.click();
      await page.waitForTimeout(2500);
    }

    // Scroll to the Plotly chart
    const plotCanvas = page.locator('.plotly, #spectrogram-plot-container').first();
    if (await plotCanvas.count() > 0) {
      await plotCanvas.scrollIntoViewIfNeeded();
      await page.waitForTimeout(800);
    }

    console.log('Capturing spectrogram_view.png...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'spectrogram_view.png'),
      fullPage: false,
    });

    // 5. Compare Gradient View (Levels 4 -> 0)
    console.log('5. Navigating to Compare Gradient view...');
    const compareTab = page.locator('button:has-text("Compare Gradient")').first();
    await compareTab.waitFor({ state: 'visible', timeout: 10000 });
    await compareTab.click();
    await page.waitForTimeout(2000);

    const gradientHeader = page.locator('text=Monotonic Prosodic Quality Gradient').first();
    if (await gradientHeader.count() > 0) {
      await gradientHeader.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
    }

    console.log('Capturing compare_gradient_view.png...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'compare_gradient_view.png'),
      fullPage: false,
    });

    // 6. Limitations Panel
    console.log('6. Navigating to Limitations panel...');
    const overviewTab = page.locator('button:has-text("Dashboard & Grounding")').first();
    await overviewTab.waitFor({ state: 'visible', timeout: 10000 });
    await overviewTab.click();
    await page.waitForTimeout(1000);

    const limitationsHeader = page.locator('text=Known Limitations & Empirical Boundaries, text=Known Limitations, text=Limitations').first();
    if (await limitationsHeader.count() > 0) {
      await limitationsHeader.scrollIntoViewIfNeeded();
      await page.waitForTimeout(1000);
    }

    console.log('Capturing limitations_panel.png...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'limitations_panel.png'),
      fullPage: false,
    });

    console.log('\nAll 6 screenshots successfully captured into docs/screenshots/!');

    // Verify SHA-256 of all six
    const files = [
      'upload_page.png',
      'sample_loaded.png',
      'flaw_selected_explanation.png',
      'spectrogram_view.png',
      'compare_gradient_view.png',
      'limitations_panel.png',
    ];

    console.log('\n================================================================================');
    console.log('SCREENSHOT SHA-256 INTEGRITY REPORT:');
    const hashes = new Map();
    for (const f of files) {
      const fullP = path.join(SCREENSHOTS_DIR, f);
      const stat = fs.statSync(fullP);
      const hash = getFileSha256(fullP);
      console.log(`- ${f.padEnd(30)} Size: ${stat.size.toString().padStart(7)} bytes | SHA-256: ${hash}`);
      if (hashes.has(hash)) {
        throw new Error(`CRITICAL DUPLICATE ERROR: ${f} has identical SHA-256 to ${hashes.get(hash)}!`);
      }
      hashes.set(hash, f);
    }
    console.log('ALL SIX SCREENSHOTS ARE DISTINCT AND VALIDATED.');
    console.log('================================================================================');

  } catch (err) {
    console.error('Error during screenshot capture:', err);
    process.exit(1);
  } finally {
    await browser.close();
  }

  console.log('\n================================================================================');
  console.log('CONSOLE ERROR REPORT:');
  const realErrors = consoleErrors.filter((e) => !e.includes('vite.svg'));
  if (realErrors.length === 0) {
    console.log('Zero runtime JavaScript console errors detected.');
  } else {
    console.log(`Detected ${realErrors.length} console error(s):`);
    realErrors.forEach((e, idx) => console.log(`  ${idx + 1}. ${e}`));
  }
  console.log('================================================================================');
}

capture();
