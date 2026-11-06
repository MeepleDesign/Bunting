import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':900}); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){}"); await pg.add_init_script("window.__openAll=1"); pg.set_default_timeout(5000); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(D/'test.html')); await pg.wait_for_timeout(300)
      async def st(n,c):
        try: await c; print(W,'ok',n)
        except Exception as e: print(W,'FAIL',n,str(e)[:200])
      await st('demo', pg.evaluate("__dbg.loadAccount('supplier');__dbg.S.supTab='overview';__dbg.setView('supplier')")); await pg.wait_for_timeout(200)
      print(W,'refcard', (await pg.locator('.refcard').inner_text()).replace('\n',' | ')[:300])
      await pg.locator('.refcard').screenshot(path=str(D/f'ref-{W}.png'))
      await st('invite', pg.click('[data-refinvite]'))
      await pg.fill('#rf-name','Hove Bloom Florals'); await pg.select_option('#rf-cat','flowers'); await pg.fill('#rf-contact','@hovebloom')
      await st('submit', pg.click('#refform button[type=submit]')); await pg.wait_for_timeout(150)
      print(W,'sent', (await pg.locator('.modal .vbox').inner_text()).replace('\n',' | ')[:200])
      await st('done', pg.click('.modal [data-close] >> nth=-1'))
      print(W,'invited count', await pg.locator('.refcard .ministat >> nth=0').inner_text())
      await pg.evaluate("__dbg.S.admTab='areas';__dbg.setView('admin')"); await pg.wait_for_timeout(150)
      print(W,'areas rows', await pg.locator('.areatbl tbody tr').count(), (await pg.locator('.areatbl tbody').inner_text()).replace('\t',' ').replace('\n',' | ')[:400])
      await pg.screenshot(path=str(D/f'areas-{W}.png'),full_page=True)
      await st('sel eastbourne', pg.click('tr[data-areasel="Eastbourne"]')); 
      await st('open', pg.click('[data-areaopen="Eastbourne"]')); print(W,'eb status', await pg.locator('tr[data-areasel="Eastbourne"] .pill').first.inner_text())
      await st('sel horsham', pg.click('tr[data-areasel="Horsham"]')); await st('push', pg.click('[data-areapush="Horsham"]')); print(W,'horsham', (await pg.locator('tr[data-areasel="Horsham"]').inner_text()).replace('\t',' ')[:80])
      await st('min', pg.fill('#ar-min','3')); await pg.dispatch_event('#ar-min','change'); await pg.wait_for_timeout(100)
      print(W,'after min3', (await pg.locator('.areatbl tbody').inner_text()).replace('\t',' ').replace('\n',' | ')[:300], await pg.locator('#ar-min').count())
      print(W,'nav areas', await pg.locator('.ditem[data-atab="areas"]').count())
      print(W,'errs',errs); await pg.close()
    await b.close()
asyncio.run(main())
