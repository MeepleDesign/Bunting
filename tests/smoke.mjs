// Smoke test for the hosted demo: builds with the fake Supabase, serves public/, and drives it with Playwright.
// Run: npm test  (needs Playwright; uses BUNTING_FAKE=1)
import { execSync } from 'node:child_process';
import { createServer } from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

execSync('node scripts/build-demo.mjs', { env: { ...process.env, BUNTING_FAKE: '1' }, stdio: 'inherit' });
const types = { html: 'text/html', js: 'text/javascript', svg: 'image/svg+xml' };
const server = createServer((req, res) => {
  let p = new URL(req.url, 'http://x').pathname; if (p === '/') p = '/bunting.html';
  const f = 'public' + p;
  if (!existsSync(f)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'content-type': types[f.split('.').pop()] || 'application/octet-stream' }); res.end(readFileSync(f));
}).listen(0);
const base = 'http://127.0.0.1:' + server.address().port;

const OWNER = { user: { id: '11111111-1111-1111-1111-111111111111', email: 'boardgames@meepledesign.com' } };
const FRIEND = { user: { id: '22222222-2222-2222-2222-222222222222', email: 'friend@example.com' } };
const STRANGER = { user: { id: '33333333-3333-3333-3333-333333333333', email: 'stranger@example.com' } };
let failures = 0;
const check = (ok, what) => { console.log((ok ? '✓ ' : '✗ ') + what); if (!ok) failures++; };

const browser = await chromium.launch();
const ctx = await browser.newContext();
await ctx.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
// Seed members: Tony is owner, friend is a contributor.
await ctx.addInitScript(() => {
  if (!localStorage.getItem('fake.supabase')) localStorage.setItem('fake.supabase', JSON.stringify({
    bunting_docs: [], bunting_profiles: [{ id: '11111111-1111-1111-1111-111111111111', name: 'Tony Webb' }],
    bunting_members: [{ email: 'boardgames@meepledesign.com', role: 'owner' }, { email: 'friend@example.com', role: 'contributor' }] }));
});
async function open(sess) {
  const page = await ctx.newPage();
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  if (sess) await page.addInitScript(s => sessionStorage.setItem('fake.session', s), JSON.stringify(sess));
  await page.goto(base + '/'); await page.waitForTimeout(1200);
  return { page, errs };
}
const docs = page => page.evaluate(() => JSON.parse(localStorage.getItem('fake.supabase')).bunting_docs);

// 1. Owner opens an empty demo and loads the demo data
const A = await open(OWNER);
check(await A.page.locator('#bunting-account').innerText().then(t => t.includes('boardgames@meepledesign.com') && t.includes('Members')), 'owner sees account bar with Members link');
const load = A.page.locator('[data-loaddemo]');
check(await load.count() > 0, 'owner is offered "Load demo data" on an empty database');
await load.first().click(); await A.page.waitForTimeout(2500);
const after = await docs(A.page);
check(after.filter(d => d.coll === 'suppliers').length > 5, 'demo data written to the database (' + after.length + ' docs)');
check(after.some(d => d.path === 'admin/settings'), 'admin settings saved by the owner');

// 2. Contributor sees the shared data and can write
const B = await open(FRIEND);
const names = await A.page.evaluate(() => JSON.parse(localStorage.getItem('fake.supabase')).bunting_docs.filter(d => d.coll === 'suppliers').map(d => d.data.name).filter(Boolean));
const seesSupplier = async page => { const b = page.getByText('Browse without an account'); if (await b.count()) { await b.first().click(); await page.waitForTimeout(500); } const s2 = page.locator('[data-nav="search"],[data-go="search"]'); if (await s2.count()) { await s2.first().click(); await page.waitForTimeout(800); } const t = await page.locator('body').innerText(); return names.some(n => t.includes(n)); };
check(await seesSupplier(B.page), 'contributor sees shared suppliers');
const wrote = await B.page.evaluate(async () => { const db = await window.claude.use('db'); try { await db.doc('notifs/test1').set({ id: 'test1', text: 'hello' }); return 'ok'; } catch (e) { return e.code; } });
check(wrote === 'ok', 'contributor can write shared data');
const denied = await B.page.evaluate(async () => { const db = await window.claude.use('db'); try { await db.doc('admin/settings').set({ commission: 1 }); return 'ok'; } catch (e) { return e.code; } });
check(denied === 'permission_denied', 'contributor cannot change admin settings (' + denied + ')');

// 3. Live updates reach the owner's page
// (write after the listener is attached)
const seen2 = A.page.evaluate(() => new Promise(async res => {
  const db = await window.claude.use('db');
  db.collection('notifs').onSnapshot(qs => { if (qs.docChanges().some(c => c.doc.id === 'live2' && c.type === 'added')) res(true); });
  setTimeout(() => res(false), 5000);
}));
await A.page.waitForTimeout(300);
await B.page.evaluate(async () => { const db = await window.claude.use('db'); await db.doc('notifs/live2').set({ id: 'live2', text: 'from friend' }); });
check(await seen2, 'a change in one tab arrives live in another');

// 4. Feedback is private
await B.page.evaluate(async () => { const db = await window.claude.use('db'); const me = await (await window.claude.use('user')).me(); await db.doc('feedback/' + me.id).set({ uid: me.id, items: [{ text: 'Nice' }] }); });
const C = await open(STRANGER);
const strangerFeedback = await C.page.evaluate(async () => { const db = await window.claude.use('db'); return (await db.collection('feedback').get()).size; });
check(strangerFeedback === 0, 'other people cannot read feedback');
const ownerFeedback = await A.page.evaluate(async () => { const db = await window.claude.use('db'); return (await db.collection('feedback').get()).size; });
check(ownerFeedback >= 1, 'owner can read feedback');
check(await C.page.locator('#bunting-account').innerText().then(t => t.includes('Ask Tony')), 'signed-in non-member is told to ask for access');
const sw = await C.page.evaluate(async () => { const db = await window.claude.use('db'); try { await db.doc('notifs/x').set({ a: 1 }); return 'ok'; } catch (e) { return e.code; } });
check(sw === 'invalid_argument', 'non-member writes are refused, so the demo goes read-only');

// 5. Signed-out visitor
const D = await open(null);
check(await D.page.locator('#bunting-account a[href="/login"]').count() === 1, 'visitor sees Sign in');
check(await seesSupplier(D.page), 'visitor can look around');
check(await D.page.evaluate(async () => (await (await window.claude.use('user')).can('data.write')) === false), 'visitor is read-only');

// 6. Downloads and big documents
const dl = D.page.waitForEvent('download', { timeout: 3000 }).catch(() => null);
await D.page.evaluate(async () => { const d = await window.claude.use('downloads'); await d.save({ filename: 'test.csv', data: 'a,b' }); });
check(!!(await dl), 'downloads save a file');
const big = await B.page.evaluate(async () => { const db = await window.claude.use('db'); try { await db.doc('images/big').set({ src: 'x'.repeat(300000) }); return 'ok'; } catch (e) { return e.code; } });
check(big === 'invalid_argument', 'documents over 256 KB are refused');

for (const [n, x] of Object.entries({ owner: A, contributor: B, stranger: C, visitor: D })) check(!x.errs.length, `no page errors for ${n}${x.errs.length ? ': ' + x.errs.slice(0, 2).join(' | ') : ''}`);
await A.page.screenshot({ path: 'tests/output-owner.png' });
await browser.close(); server.close();
console.log(failures ? `\n${failures} check(s) failed` : '\nAll checks passed');
process.exit(failures ? 1 : 0);
