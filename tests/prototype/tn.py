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
      await pg.screenshot(path=str(D/f'dn-ov-{W}.png'))
      if W<900: await pg.click('[data-dnavtoggle]'); await pg.screenshot(path=str(D/f'dn-open-{W}.png'))
      await pg.click('.ditem[data-stab="bookings"]'); await pg.click('.viewseg [data-stab="calendar"]'); print(W,'cal', await pg.locator('.ditem[aria-current="true"]').first.get_attribute('data-stab'))
      await pg.screenshot(path=str(D/f'dn-cal-{W}.png'))
      if W<900: await pg.click('[data-dnavtoggle]')
      await pg.click('.ditem[data-stab="docs"]'); print(W,'docs', await pg.locator('main h2').first.inner_text())
      await pg.evaluate("__dbg.setView('admin')"); 
      if W<900: await pg.click('[data-dnavtoggle]')
      await pg.click('.ditem[data-atab="compliance"]'); await pg.screenshot(path=str(D/f'dn-adm-{W}.png'))
      sw=await pg.evaluate('document.documentElement.scrollWidth'); print(W,'sw',sw,errs)
    await b.close()
asyncio.run(main())
