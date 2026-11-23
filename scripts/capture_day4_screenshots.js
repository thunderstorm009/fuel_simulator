import { chromium } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const OUT_DIR = path.resolve(__dirname, '../docs/evidence/day-4/screens');
const BASE_URL = process.env.WEB_BASE_URL || 'http://localhost:5173';

async function main() {
  if (!fs.existsSync(OUT_DIR)) {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 2
  });
  const page = await context.newPage();

  console.log('Navigating to', BASE_URL);
  await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);

  // 1. Guided Tour (Open by default on fresh visit)
  console.log('1. Capturing Guided Tour...');
  const tourModal = page.locator('.guided-tour, [role="dialog"]').first();
  if (await tourModal.isVisible()) {
    await page.screenshot({ path: path.join(OUT_DIR, '02-guided-tour.png') });
    console.log('Saved 02-guided-tour.png');
    // Dismiss tour
    const dismissBtn = page.getByRole('button', { name: /✕|Dismiss|Skip/i }).first();
    if (await dismissBtn.isVisible()) {
      await dismissBtn.click();
      await page.waitForTimeout(500);
    }
  } else {
    // Try opening via toggle button
    const tourToggle = page.getByRole('button', { name: /Interactive Judging Tour/i });
    if (await tourToggle.isVisible()) {
      await tourToggle.click();
      await page.waitForTimeout(500);
      await page.screenshot({ path: path.join(OUT_DIR, '02-guided-tour.png') });
      console.log('Saved 02-guided-tour.png');
      const dismissBtn = page.getByRole('button', { name: /✕|Dismiss|Skip/i }).first();
      if (await dismissBtn.isVisible()) await dismissBtn.click();
    }
  }

  // 2. Dashboard / Overview
  console.log('2. Capturing Dashboard Overview...');
  await page.screenshot({ path: path.join(OUT_DIR, '01-dashboard.png') });
  console.log('Saved 01-dashboard.png');

  // Helper to click nav
  async function navTo(text) {
    const navBtn = page.locator('nav.page-navigation button').filter({ hasText: new RegExp(text, 'i') });
    if (await navBtn.isVisible()) {
      await navBtn.click();
      await page.waitForTimeout(1500);
    }
  }

  // 3. Stockout Risk
  console.log('3. Capturing Stockout Risk & Trajectory...');
  await navTo('Stockout risk');
  const riskCell = page.locator('button.risk-cell').first();
  if (await riskCell.isVisible()) {
    await riskCell.click();
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: path.join(OUT_DIR, '03-forecast-risk.png') });
  console.log('Saved 03-forecast-risk.png');

  const closeBtn = page.getByRole('button', { name: /Close|✕/i }).first();
  if (await closeBtn.isVisible()) await closeBtn.click().catch(() => {});
  await page.waitForTimeout(500);

  // 4. Recommendations
  console.log('4. Capturing Recommendations...');
  await navTo('Recommendations');
  await page.screenshot({ path: path.join(OUT_DIR, '04-recommendations.png') });
  console.log('Saved 04-recommendations.png');

  // 5. What-If Simulator (Click Details on recommendation card)
  console.log('5. Capturing What-If Simulator...');
  const detailsBtn = page.getByRole('button', { name: /Details|Hide details/i }).first();
  if (await detailsBtn.isVisible()) {
    const text = await detailsBtn.textContent();
    if (text && text.includes('Details') && !text.includes('Hide')) {
      await detailsBtn.click();
      await page.waitForTimeout(1000);
    }
  }
  // Scroll down to What-If simulator in card
  const whatIfBox = page.locator('.whatif-simulator, .candidate-simulator, .whatif-panel').first();
  if (await whatIfBox.isVisible()) {
    await whatIfBox.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
  }
  await page.screenshot({ path: path.join(OUT_DIR, '05-what-if.png') });
  console.log('Saved 05-what-if.png');

  // 6. Decision History
  console.log('6. Capturing Decision History...');
  await navTo('Decisions');
  await page.screenshot({ path: path.join(OUT_DIR, '06-decision-history.png') });
  console.log('Saved 06-decision-history.png');

  // 7. Alert Center
  console.log('7. Capturing Alert Center...');
  await navTo('Alerts');
  await page.screenshot({ path: path.join(OUT_DIR, '07-alerts.png') });
  console.log('Saved 07-alerts.png');

  // 8. Network View
  console.log('8. Capturing Network View...');
  await navTo('Network');
  await page.screenshot({ path: path.join(OUT_DIR, '08-network.png') });
  console.log('Saved 08-network.png');

  // 9. Model Evaluation
  console.log('9. Capturing Evaluation...');
  await navTo('Evaluation');
  await page.screenshot({ path: path.join(OUT_DIR, '09-evaluation.png') });
  console.log('Saved 09-evaluation.png');

  // 10. System Health
  console.log('10. Capturing System Health...');
  await navTo('System health');
  await page.screenshot({ path: path.join(OUT_DIR, '10-system-health.png') });
  console.log('Saved 10-system-health.png');

  await browser.close();
  console.log('All screenshots captured successfully in', OUT_DIR);
}

main().catch(err => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
