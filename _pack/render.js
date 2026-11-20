// Renders _pack/brief.html (2 A4 pages) to _pack/out/brief.pdf
const path = require('path');
const fs = require('fs');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
  const opts = process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {};
  const browser = await chromium.launch(opts);
  const page = await browser.newPage();
  await page.goto('file://' + path.join(__dirname, 'brief.html'));
  await page.evaluate(() => document.fonts.ready);
  const fit = await page.evaluate(() => [...document.querySelectorAll('.page')].map(p => p.scrollHeight <= p.clientHeight + 1));
  if (fit.includes(false)) { const h = await page.evaluate(() => [...document.querySelectorAll('.page')].map(p => p.scrollHeight)); console.error('Content overflows an A4 page (heights, limit 1123):', h); process.exit(1); }
  fs.mkdirSync(path.join(__dirname, 'out'), { recursive: true });
  await page.pdf({ path: path.join(__dirname, 'out', 'brief.pdf'), format: 'A4', printBackground: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });
  // Page-1 band of the schedule (intro + two session cards), used while the source still shows Little Heroes.
  if (fs.existsSync(path.join(__dirname, 'page1-band.html'))) {
    const band = await browser.newPage();
    await band.goto('file://' + path.join(__dirname, 'page1-band.html'));
    await band.evaluate(() => document.fonts.ready);
    await band.pdf({ path: path.join(__dirname, 'out', 'page1-band.pdf'), preferCSSPageSize: true, printBackground: true, margin: { top: 0, bottom: 0, left: 0, right: 0 } });
  }
  await browser.close();
})();
