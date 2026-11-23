// Print the single-page edition to PDF with headless Chromium.
// Usage: node make_pdf.cjs <book.html> <book.pdf>
const path = require("node:path");
const { chromium } = require("playwright");

(async () => {
  const [src, dst] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto("file://" + path.resolve(src), { waitUntil: "networkidle" });
  await page.emulateMedia({ media: "print" });
  await page.evaluate(async () => {
    await Promise.all([...document.fonts].map((f) => f.load().catch(() => null)));
    await document.fonts.ready;
  });
  await page.waitForTimeout(500);
  await page.pdf({
    path: dst,
    preferCSSPageSize: true,
    printBackground: false,
    displayHeaderFooter: true,
    headerTemplate: "<span></span>",
    footerTemplate:
      '<div style="width:100%;font-size:8pt;font-family:sans-serif;color:#666;text-align:center">' +
      '<span class="pageNumber"></span></div>',
  });
  await browser.close();
})().catch((err) => { console.error(err.message); process.exit(1); });
