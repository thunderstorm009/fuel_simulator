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

  // 1. Dashboard / Overview
  console.log('1. Capturing Dashboard Overview...');
  await page.screenshot({ path: path.join(OUT_DIR, '01-dashboard.png'), fullPage: false });

  // 2. Guided Tour
  console.log('2. Capturing Guided Tour...');
  const tourBtn = page.getByRole('button', { name: /Interactive Judging Tour/i });
  if (await tourBtn.isVisible()) {
    await tourBtn.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: path.join(OUT_DIR, '02-guided-tour.png') });
    // Dismiss tour
    const dismissBtn = page.getByRole('button', { name: /✕|Dismiss/i });
    if (await dismissBtn.isVisible()) await dismissBtn.click();
    await page.waitForTimeout(500);
  }

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
  // Open trajectory drawer if risk cell available
  const riskCell = page.locator('button.risk-cell').first();
  if (await riskCell.isVisible()) {
    await riskCell.click();
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: path.join(OUT_DIR, '03-forecast-risk.png') });

  // Close drawer if open (escape or close button)
  const closeBtn = page.getByRole('button', { name: /Close|✕/i }).first();
  if (await closeBtn.isVisible()) await closeBtn.click().catch(() => {});
  await page.waitForTimeout(500);

  // 4. Recommendations
  console.log('4. Capturing Recommendations...');
  await navTo('Recommendations');
  await page.screenshot({ path: path.join(OUT_DIR, '04-recommendations.png') });

  // 5. What-If Simulator
  console.log('5. Capturing What-If Simulator...');
  const whatIfBtn = page.getByRole('button', { name: /What-If|Simulate/i }).first();
  if (await whatIfBtn.isVisible()) {
    await whatIfBtn.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(OUT_DIR, '05-what-if.png') });
    const closeDrawer = page.getByRole('button', { name: /Close|✕/i }).first();
    if (await closeDrawer.isVisible()) await closeDrawer.click().catch(() => {});
  }

  // 6. Decision History
  console.log('6. Capturing Decision History...');
  await navTo('Decisions');
  await page.screenshot({ path: path.join(OUT_DIR, '06-decision-history.png') });

  // 7. Alert Center
  console.log('7. Capturing Alert Center...');
  await navTo('Alerts');
  await page.screenshot({ path: path.join(OUT_DIR, '07-alerts.png') });

  // 8. Network View
  console.log('8. Capturing Network View...');
  await navTo('Network');
  await page.screenshot({ path: path.join(OUT_DIR, '08-network.png') });

  // 9. Model Evaluation
  console.log('9. Capturing Evaluation...');
  await navTo('Evaluation');
  await page.screenshot({ path: path.join(OUT_DIR, '09-evaluation.png') });

  // 10. System Health
  console.log('10. Capturing System Health...');
  await navTo('System health');
  await page.screenshot({ path: path.join(OUT_DIR, '10-system-health.png') });

  await browser.close();
  console.log('All screenshots captured successfully in', OUT_DIR);
}

main().catch(err => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
