// node render.js <outdir> [scale 1|2] [onlyTimes comma list]
const p = require('puppeteer-core'), path = require('path'), fs = require('fs');
const out = process.argv[2], S = +(process.argv[3] || 1), only = process.argv[4];
const FPS = 30, N = 10 * FPS;
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const b = await p.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: 'new', args: ['--allow-file-access-from-files'] });
  const pg = await b.newPage(); await pg.setViewport({ width: 1920, height: 1080 });
  await pg.goto('file://' + path.join(__dirname, 'intro.html') + '?s=' + S, { waitUntil: 'networkidle0' });
  await pg.evaluate(() => window.ready);
  const times = only ? only.split(',').map(Number) : Array.from({ length: N }, (_, i) => i / FPS);
  for (const [i, t] of times.entries()) {
    await pg.evaluate(t => window.draw(t), t);
    const el = await pg.$('canvas');
    await el.screenshot({ path: path.join(out, only ? `t${t}.png` : String(i).padStart(4, '0') + '.png'), type: 'png' });
  }
  await b.close();
})();
