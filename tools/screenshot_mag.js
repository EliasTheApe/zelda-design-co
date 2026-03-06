const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  // Set viewport wider than the magazine
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 2 });
  
  const projectRoot = path.resolve(__dirname, '..');
  const filePath = 'file://' + path.resolve(projectRoot, 'prototypes/about_magazine.html');
  await page.goto(filePath, { waitUntil: 'networkidle0' });
  
  // Wait for fonts
  await page.waitForTimeout(2000);
  
  // Find the magazine scene element and screenshot just that
  const el = await page.$('.magazine-scene');
  await el.screenshot({
    path: path.resolve(projectRoot, 'assets/renders/magazine_render.png'),
    omitBackground: false
  });
  
  await browser.close();
  console.log('Done: assets/renders/magazine_render.png');
})();
