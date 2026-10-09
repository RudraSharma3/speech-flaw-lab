import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_DIR = path.resolve(__dirname, '..');
const SCREENSHOTS_DIR = path.join(ROOT_DIR, 'docs', 'screenshots');

if (!fs.existsSync(SCREENSHOTS_DIR)) {
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
}

// Check for system Microsoft Edge or Chrome executable
const edgePaths = [
  'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
];
let browserExecutable = undefined;
for (const p of edgePaths) {
  if (fs.existsSync(p)) {
    browserExecutable = p;
    break;
  }
}

async function capture() {
  console.log('Starting Playwright screenshot capture...');
  console.log('Target directory:', SCREENSHOTS_DIR);
  console.log('Browser executable:', browserExecutable || 'default bundled chromium');

  const launchOptions = {
    headless: true,
  };
  if (browserExecutable) {
    launchOptions.executablePath = browserExecutable;
  }

  const browser = await chromium.launch(launchOptions);
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
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

    // 1. Upload Page (Initial Ready State)
    console.log('1. Capturing upload_page.png...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'upload_page.png'),
      fullPage: false,
    });

    // 2. Sample Loaded
    console.log('2. Loading benchmark sample...');
    // Look for sample buttons or select element
    const sampleSelector = page.locator('button:has-text("JFK Moon Speech — Level 2"), select, button:has-text("Level 2")').first();
    if (await sampleSelector.count() > 0) {
      await sampleSelector.click();
      await page.waitForTimeout(2000);
    } else {
      // Fallback: click any sample chip
      const chip = page.locator('button:has-text("Level")').first();
      if (await chip.count() > 0) {
        await chip.click();
        await page.waitForTimeout(2000);
      }
    }

    console.log('Capturing sample_loaded.png...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'sample_loaded.png'),
      fullPage: false,
    });

    // 3. Flaw Selected with Causal Explanation
    console.log('3. Selecting flaw for explanation...');
    const flawRow = page.locator('tr:has-text("rushed"), tr:has-text("monotone"), button:has-text("rushed"), button:has-text("monotone")').first();
    if (await flawRow.count() > 0) {
      await flawRow.click();
      await page.waitForTimeout(1000);
    }
    // Scroll causal explanation into view
    const causalCard = page.locator('h2:has-text("Causal Acoustic Deviation"), h3:has-text("Causal")').first();
    if (await causalCard.count() > 0) {
      await causalCard.scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
    }

    console.log('Capturing flaw_selected_explanation.png...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'flaw_selected_explanation.png'),
      fullPage: false,
    });

    // 4. Spectrogram View (Mel Spectrogram Heatmap)
    console.log('4. Navigating to Acoustic Plots & Spectrogram view...');
    const acousticTab = page.locator('button:has-text("Acoustic Contours")').first();
    if (await acousticTab.count() > 0) {
      await acousticTab.click();
      await page.waitForTimeout(1000);
    }

    const specToggle = page.locator('#spectrogram-toggle-btn, button:has-text("Mel Spectrogram")').first();
    if (await specToggle.count() > 0) {
      await specToggle.click();
      await page.waitForTimeout(2000);
    }

    console.log('Capturing spectrogram_view.png...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'spectrogram_view.png'),
      fullPage: false,
    });

    // 5. Compare Gradient View (Levels 4 -> 0)
    console.log('5. Navigating to Compare Gradient view...');
    const compareTab = page.locator('button:has-text("Compare Gradient")').first();
    if (await compareTab.count() > 0) {
      await compareTab.click();
      await page.waitForTimeout(2000);
    }

    console.log('Capturing compare_gradient_view.png...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'compare_gradient_view.png'),
      fullPage: false,
    });

    // 6. Limitations Panel
    console.log('6. Navigating to Limitations panel...');
    // Return to overview tab
    const overviewTab = page.locator('button:has-text("Dashboard & Grounding")').first();
    if (await overviewTab.count() > 0) {
      await overviewTab.click();
      await page.waitForTimeout(1000);
    }

    const limitationsHeader = page.locator('h2:has-text("Known Limitations & Failure Modes"), h3:has-text("Limitations")').first();
    if (await limitationsHeader.count() > 0) {
      await limitationsHeader.scrollIntoViewIfNeeded();
      await page.waitForTimeout(1000);
    }

    console.log('Capturing limitations_panel.png...');
    await page.screenshot({
      path: path.join(SCREENSHOTS_DIR, 'limitations_panel.png'),
      fullPage: false,
    });

    console.log('All screenshots captured successfully into docs/screenshots/!');
  } catch (err) {
    console.error('Error during screenshot capture:', err);
  } finally {
    await browser.close();
  }

  console.log('\n================================================================================');
  console.log('CONSOLE ERROR REPORT:');
  if (consoleErrors.length === 0) {
    console.log('Zero console errors detected. Clean execution.');
  } else {
    console.log(`Detected ${consoleErrors.length} console error(s):`);
    consoleErrors.forEach((e, idx) => console.log(`  ${idx + 1}. ${e}`));
  }
  console.log('================================================================================');
}

capture();
