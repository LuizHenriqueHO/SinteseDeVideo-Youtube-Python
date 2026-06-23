import puppeteer from 'puppeteer-core';
import fs from 'fs';

const CHROME = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const BASE = 'http://127.0.0.1:5000';
const OUT = './shots';
fs.mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: 'new',
  args: ['--no-sandbox', '--window-size=1440,900'],
});

const page = await browser.newPage();
await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });

async function shot(name) {
  await new Promise(r => setTimeout(r, 350));
  await page.screenshot({ path: `${OUT}/${name}.png`, fullPage: true });
  console.log('shot', name);
}
async function go(path) {
  await page.goto(BASE + path, { waitUntil: 'networkidle2' });
}

// ---- Autenticar (registra; se já existir, faz login) ----
await go('/cadastro');
await page.type('#name', 'Rafael');
await page.type('#email', 'preview@tubify.dev');
await page.type('#password', 'senha123');
await page.type('#confirm_password', 'senha123');
await Promise.all([
  page.waitForNavigation({ waitUntil: 'networkidle2' }),
  page.click('button[type="submit"]'),
]);
if (!page.url().includes('/dashboard')) {
  await go('/login');
  await page.type('#email', 'preview@tubify.dev');
  await page.type('#password', 'senha123');
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'networkidle2' }),
    page.click('button[type="submit"]'),
  ]);
}
console.log('autenticado, url:', page.url());

// ---- Páginas (claro) ----
const pages = [
  ['/', 'index'],
  ['/login', 'login'],
  ['/cadastro', 'cadastro'],
  ['/recuperar-senha', 'recuperar_senha'],
  ['/plans', 'plans'],
  ['/configuracoes', 'configuracoes'],
  ['/configuracoes?tab=aparencia', 'configuracoes_aparencia'],
  ['/configuracoes?tab=resumo', 'configuracoes_resumo'],
  ['/dashboard', 'dashboard'],
  ['/favoritos', 'favoritos'],
  ['/__preview_summary', 'summary'],
];
for (const [path, name] of pages) {
  await go(path);
  await shot(name);
}

// ---- Dark mode ----
await page.evaluateOnNewDocument(() => { try { localStorage.setItem('tubify_theme', 'escuro'); } catch (e) {} });
const darkPages = [['/', 'index'], ['/plans', 'plans'], ['/dashboard', 'dashboard'], ['/configuracoes', 'configuracoes'], ['/__preview_summary', 'summary'], ['/login', 'login']];
for (const [path, name] of darkPages) {
  await go(path);
  await shot(name + '_dark');
}

// ---- Mobile (navbar + menu) ----
await page.evaluateOnNewDocument(() => { try { localStorage.setItem('tubify_theme', 'claro'); } catch (e) {} });
await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 1 });
await go('/');
await shot('index_mobile');

await browser.close();
console.log('DONE');
