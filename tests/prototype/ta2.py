import asyncio, pathlib, json
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
html='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>'
(D/'live.html').write_text(html); FAKE=(D/'fake.js').read_text(); URL='file://'+str(D/'live.html')
async def mk(ctx,uid,owner):
  pg=await ctx.new_page(); await pg.set_viewport_size({'width':1280,'height':900}); pg.set_default_timeout(5000)
  await pg.add_init_script(f"window.__uid={json.dumps(uid)};window.__owner={'true' if owner else 'false'};"+FAKE); pg.errs=[]; pg.on('pageerror',lambda e:pg.errs.append(str(e))); return pg
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(); ctx=await b.new_context()
    A=await mk(ctx,'u_owner',True); await A.goto(URL); await A.evaluate("localStorage.clear()"); await A.reload(); await A.wait_for_timeout(600)
    await A.click('[data-loaddemo]'); await A.wait_for_timeout(900)
    B=await mk(ctx,'u_sophie',False); await B.goto(URL); await B.wait_for_timeout(900)
    print('B admin btn', await B.locator('[data-nav2="admin"]').count())
    await B.evaluate("__dbg.setView('admin')"); print('B admin page', (await B.locator('main').inner_text())[:60].replace('\n',' '))
    await B.evaluate("__dbg.setView('home')"); await B.click('.fbbtn')
    if await B.locator('#fb-text').count(): await B.fill('#fb-text','B feedback'); await B.click('#fbform button[type=submit]'); await B.wait_for_timeout(600)
    # owner enables demo
    await A.evaluate("__dbg.setView('admin')"); await A.click('.ditem[data-atab="settings"]'); await A.check('#as-demo'); await A.wait_for_timeout(900)
    await A.click('.ditem[data-atab="feedback"]'); print('A fb', await A.locator('.fbitem').count())
    await B.wait_for_timeout(500); await B.evaluate("__dbg.setView('admin')"); print('B ro banner', await B.locator('.admro').count(), 'fb item', await B.locator('.ditem[data-atab="feedback"]').count(), 'settings', await B.locator('.ditem[data-atab="settings"]').count())
    await B.click('.ditem[data-atab="suppliers"]'); await B.click('[data-afilter="review"]')
    if await B.locator('[data-approve]').count(): await B.click('[data-approve] >> nth=0'); print('B toast', await B.locator('.toast').inner_text())
    await B.screenshot(path=str(D/'ro.png'))
    print('errs',A.errs,B.errs)
    await b.close()
asyncio.run(main())
