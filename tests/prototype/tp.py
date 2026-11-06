import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':900}); await pg.add_init_script("window.__openAll=1"); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){}"); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(D/'test.html')); await pg.evaluate("__dbg.loadAccount('supplier');__dbg.setView('supplier')")
      await pg.click('[data-preview-search]'); await pg.wait_for_timeout(500)
      print(W,'banner', (await pg.locator('.pvbanner').inner_text()).replace('\n',' | '))
      await pg.screenshot(path=str(D/f'pv-{W}.png'))
      await pg.select_option('#sort','low'); print(W,'after sort', (await pg.locator('.pvbanner .small').inner_text())[:60])
      await pg.click('[data-preview-profile-of]'); print(W,'modal', await pg.locator('.modal h1').count()); await pg.click('.modal [data-close] >> nth=-1')
      await pg.click('[data-preview-exit]'); print(W,'back', await pg.locator('main h1').first.inner_text())
      # hidden case
      await pg.evaluate("__dbg.SUP.pierplate.away=true"); await pg.click('[data-preview-search]'); print(W,'hidden', (await pg.locator('.pvbanner .small').inner_text())[:90], await pg.locator('.hiddenme').count())
      print(W,errs)
    await b.close()
asyncio.run(main())
