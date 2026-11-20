const puppeteer = require('/tmp/screenshot-tool/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const OUT_DIR = path.resolve(__dirname, '../docs/evidence/day-2');
const BASE_URL = 'http://localhost:5174';

async function capture() {
  if (!fs.existsSync(OUT_DIR)) {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  }

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,960']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 960, deviceScaleFactor: 2 });

  // 1. Dashboard
  console.log('1. Capturing Dashboard...');
  await page.goto(`${BASE_URL}`, { waitUntil: 'networkidle0', timeout: 15000 });
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(OUT_DIR, '01-dashboard.png') });
  console.log('Saved 01-dashboard.png');

  // 2. Inventory Management
  console.log('2. Capturing Inventory view...');
  await page.evaluate(() => {
    const heading = document.querySelector('.section-panel');
    if (heading) heading.scrollIntoView({ behavior: 'instant', block: 'start' });
    else window.scrollTo(0, 180);
  });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(OUT_DIR, '02-inventory.png') });
  console.log('Saved 02-inventory.png');

  // 3. Forecast and Shortage Risk
  console.log('3. Capturing Forecast and Shortage Risk...');
  await page.evaluate(() => {
    window.scrollTo(0, 0);
    const buttons = Array.from(document.querySelectorAll('nav.page-navigation button'));
    const btn = buttons.find(b => b.textContent.includes('Stockout risk'));
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 2000));
  // Click the first enabled risk cell button to open the Trajectory Drawer
  await page.evaluate(() => {
    const cell = document.querySelector('button.risk-cell:not([disabled])');
    if (cell) cell.click();
  });
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(OUT_DIR, '03-forecast-risk.png') });
  console.log('Saved 03-forecast-risk.png');

  // 4. Incidents and Network Routes
  console.log('4. Capturing Incidents and Events...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('nav.page-navigation button'));
    const btn = buttons.find(b => b.textContent.includes('Overview'));
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 1500));
  await page.evaluate(() => {
    const lowerGrid = document.querySelector('.lower-grid');
    if (lowerGrid) {
      lowerGrid.scrollIntoView({ behavior: 'instant', block: 'start' });
    } else {
      window.scrollTo(0, 600);
    }
  });
  await new Promise(r => setTimeout(r, 1000));
  await page.screenshot({ path: path.join(OUT_DIR, '04-incidents.png') });
  console.log('Saved 04-incidents.png');

  // 5. Allocation Recommendations
  console.log('5. Capturing Allocation Recommendations...');
  await page.evaluate(() => {
    window.scrollTo(0, 0);
    const buttons = Array.from(document.querySelectorAll('nav.page-navigation button'));
    const btn = buttons.find(b => b.textContent.includes('Recommendations'));
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(OUT_DIR, '05-allocations.png') });
  console.log('Saved 05-allocations.png');

  // 6. System Health
  console.log('6. Capturing System Health...');
  await page.evaluate(() => {
    window.scrollTo(0, 0);
    const buttons = Array.from(document.querySelectorAll('nav.page-navigation button'));
    const btn = buttons.find(b => b.textContent.includes('System health'));
    if (btn) btn.click();
  });
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(OUT_DIR, '06-system-health.png') });
  console.log('Saved 06-system-health.png');

  // 7. Grafana Monitoring
  console.log('7. Capturing Grafana Monitoring...');
  try {
    const grafanaUrl = 'http://admin:local-demo-only@localhost:3000/d/fuel-supply-platform/fuel-supply-platform?orgId=1&kiosk';
    await page.goto(grafanaUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await new Promise(r => setTimeout(r, 5000));
    await page.screenshot({ path: path.join(OUT_DIR, '07-grafana.png') });
    console.log('Saved 07-grafana.png');
  } catch (err) {
    console.log('Grafana capture error:', err.message);
  }

  await browser.close();
  console.log('All screenshots captured successfully!');
}

capture().catch(err => {
  console.error('Capture failed:', err);
  process.exit(1);
});
