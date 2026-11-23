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
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();

  console.log('Navigating to', BASE_URL);
  await page.goto(BASE_URL, { waitUntil: 'networkidle', timeout: 30000 });
  await page.waitForTimeout(2000);

  // Helper to click nav buttons
  async function navTo(text) {
    const navBtn = page.locator('nav.page-navigation button').filter({ hasText: new RegExp(text, 'i') });
    if (await navBtn.isVisible()) {
      await navBtn.click();
      await page.waitForTimeout(1200);
    }
  }

  // 1. Dashboard / Overview with HUD (SIMULATED badge, tick, speed, unread count)
  console.log('1. Capturing Dashboard Overview...');
  // Ensure guided tour is closed if open
  const dismissBtn = page.getByRole('button', { name: /✕|Dismiss|Skip/i }).first();
  if (await dismissBtn.isVisible()) {
    await dismissBtn.click();
    await page.waitForTimeout(500);
  }
  await navTo('Overview');
  await page.screenshot({ path: path.join(OUT_DIR, '01-dashboard.png') });
  console.log('Saved 01-dashboard.png');

  // 2. Shortage Risk with confidence intervals
  console.log('2. Capturing Shortage Risk Matrix...');
  await navTo('Stockout risk');
  await page.screenshot({ path: path.join(OUT_DIR, '02-shortage-risk.png') });
  fs.copyFileSync(path.join(OUT_DIR, '02-shortage-risk.png'), path.join(OUT_DIR, '03-forecast-risk.png'));
  console.log('Saved 02-shortage-risk.png (and alias 03-forecast-risk.png)');

  // 3. Trajectory Drawer with p10/p50/p90 bands and drivers
  console.log('3. Capturing Trajectory Drawer...');
  const riskCell = page.locator('button.risk-cell').first();
  if (await riskCell.isVisible()) {
    await riskCell.click();
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: path.join(OUT_DIR, '03-trajectory-drawer.png') });
  console.log('Saved 03-trajectory-drawer.png');
  const closeBtn = page.getByRole('button', { name: /Close|✕/i }).first();
  if (await closeBtn.isVisible()) await closeBtn.click().catch(() => {});
  await page.waitForTimeout(500);

  // 4. Recommendations with human decision workflow (token + operator name inputs)
  console.log('4. Capturing Recommendations...');
  await navTo('Recommendations');
  await page.screenshot({ path: path.join(OUT_DIR, '04-recommendations.png') });
  console.log('Saved 04-recommendations.png');

  // 5. What-If Simulator with candidate builder and counterfactual outcome
  console.log('5. Capturing What-If Simulator...');
  const detailsBtn = page.getByRole('button', { name: /Details|Hide details/i }).first();
  if (await detailsBtn.isVisible()) {
    const text = await detailsBtn.textContent();
    if (text && text.includes('Details') && !text.includes('Hide')) {
      await detailsBtn.click();
      await page.waitForTimeout(1000);
    }
  }
  const whatIfBox = page.locator('.whatif-simulator, .candidate-simulator, .whatif-panel').first();
  if (await whatIfBox.isVisible()) {
    await whatIfBox.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
  }
  await page.screenshot({ path: path.join(OUT_DIR, '05-what-if.png') });
  console.log('Saved 05-what-if.png');

  // 6. Network View with 4 routes, status, transit ticks and disruptions
  console.log('6. Capturing Network View...');
  await navTo('Network');
  await page.screenshot({ path: path.join(OUT_DIR, '06-network.png') });
  fs.copyFileSync(path.join(OUT_DIR, '06-network.png'), path.join(OUT_DIR, '08-network.png'));
  console.log('Saved 06-network.png (and alias 08-network.png)');

  // 7. Incoming Supply View with depot supply arrivals schedule
  console.log('7. Capturing Incoming Supply View...');
  await navTo('Incoming supply');
  await page.screenshot({ path: path.join(OUT_DIR, '07-incoming-supply.png') });
  console.log('Saved 07-incoming-supply.png');

  // 8. Alert Center with incidents, filter, CSV/JSON export buttons
  console.log('8. Capturing Alert Center...');
  await navTo('Alert');
  await page.screenshot({ path: path.join(OUT_DIR, '08-alerts.png') });
  fs.copyFileSync(path.join(OUT_DIR, '08-alerts.png'), path.join(OUT_DIR, '07-alerts.png'));
  console.log('Saved 08-alerts.png (and alias 07-alerts.png)');

  // 9. System Health with data age, component grid, degrade banner
  console.log('9. Capturing System Health...');
  await navTo('System health');
  await page.screenshot({ path: path.join(OUT_DIR, '09-system-health.png') });
  fs.copyFileSync(path.join(OUT_DIR, '09-system-health.png'), path.join(OUT_DIR, '10-system-health.png'));
  console.log('Saved 09-system-health.png (and alias 10-system-health.png)');

  // 10. Guided Tour modal showing judging walkthrough
  console.log('10. Capturing Guided Tour...');
  const tourToggle = page.locator('button[aria-label="Interactive Judging Tour"]');
  if (await tourToggle.isVisible()) {
    await tourToggle.click();
    await page.waitForTimeout(600);
  }
  await page.screenshot({ path: path.join(OUT_DIR, '10-guided-tour.png') });
  fs.copyFileSync(path.join(OUT_DIR, '10-guided-tour.png'), path.join(OUT_DIR, '02-guided-tour.png'));
  console.log('Saved 10-guided-tour.png (and alias 02-guided-tour.png)');

  // Additional views for completeness
  console.log('Capturing Evaluation...');
  await navTo('Evaluation');
  await page.screenshot({ path: path.join(OUT_DIR, '09-evaluation.png') });

  console.log('Capturing Decision History...');
  await navTo('Recommendations');
  const historySec = page.locator('.decision-history, section:has-text("Decision History")').first();
  if (await historySec.isVisible()) {
    await historySec.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
  }
  await page.screenshot({ path: path.join(OUT_DIR, '06-decision-history.png') });

  await browser.close();
  console.log('All screenshots captured successfully in', OUT_DIR);
}

main().catch((err) => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
