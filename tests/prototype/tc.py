import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':1000}); await pg.add_init_script("window.__openAll=1"); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){}"); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(D/'test.html')); await pg.wait_for_timeout(200); await pg.evaluate("__dbg.setView('admin')")
      print(W,'attn',(await pg.locator('section:has(h2:has-text("Needs attention"))').inner_text()).replace('\n',' | '))
      await pg.click('button.attn:has-text("compliance")'); await pg.screenshot(path=str(D/f'comp-{W}.png'),full_page=True)
      print(W,'items',(await pg.locator('.compitem').all_inner_texts())[:6])
      await pg.click('[data-compremind] >> nth=0'); await pg.click('[data-comprenew] >> nth=0'); await pg.click('[data-compkeep]'); await pg.click('[data-comprun]')
      print(W,'after', await pg.locator('.compitem').count())
      await pg.evaluate("__dbg.loadAccount('supplier');__dbg.setView('supplier')"); await pg.evaluate("__dbg.S.supTab='money';__dbg.setView('supplier')"); print(W,'tax', (await pg.locator('section:has(h2:has-text("Tax year"))').inner_text()).replace('\n',' | ')[:200])
      await pg.click('[data-taxcsv]')
      await pg.evaluate("__dbg.S.search.cat='all';__dbg.setView('search')"); print(W,'disco card', (await pg.locator('.sup:has-text("Disco Bay")').inner_text()).replace('\n',' ')[:150] if await pg.locator('.sup:has-text("Disco Bay")').count() else 'none')
      print(W,errs)
    await b.close()
asyncio.run(main())
