import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':1000}); await pg.add_init_script("window.__openAll=1"); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){}"); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(D/'test.html')); await pg.evaluate("__dbg.loadAccount('supplier');__dbg.setView('supplier')")
      await pg.evaluate("__dbg.S.supTab='profile';__dbg.setView('supplier')"); await pg.set_input_files('#prof-files',[str(D/'pic.png')]*3); await pg.wait_for_timeout(700)
      print(W,'photos', await pg.locator('.pph:not(.add)').count()); await pg.click('[data-phcover="2"]'); await pg.click('[data-proftag] >> nth=2'); await pg.fill('#pf-blurb','New description'); await pg.locator('#pf-blurb').dispatch_event('change')
      await pg.screenshot(path=str(D/f'sp-prof-{W}.png'),full_page=True)
      await pg.evaluate("__dbg.S.supTab='docs';__dbg.setView('supplier')"); print(W,'docs', [x.split('\n')[0] for x in await pg.locator('.docitem').all_inner_texts()])
      await pg.click('[data-docedit="ins"]'); await pg.select_option('#df-ins-cover','£5m'); await pg.fill('#df-ins-exp','2027-11-30'); await pg.locator('#df-ins-exp').dispatch_event('change')
      await pg.click('[data-docsubmit="ins"]'); print(W,'toast', await pg.locator('.toast').inner_text())
      await pg.set_input_files('#df-ins-file',[str(D/'pic.png')]) if await pg.locator('#df-ins-file').count() else None
      await pg.click('[data-docsubmit="ins"]'); print(W,'after', await pg.locator('.docitem').first.inner_text())
      await pg.click('[data-docedit="reg"]'); await pg.fill('#df-reg-council','Brighton & Hove City Council'); await pg.locator('#df-reg-council').dispatch_event('change'); await pg.fill('#df-reg-date','2024-03-01'); await pg.locator('#df-reg-date').dispatch_event('change'); await pg.click('[data-docsubmit="reg"]')
      await pg.screenshot(path=str(D/f'sp-docs-{W}.png'),full_page=True)
      await pg.evaluate("__dbg.S.supTab='settings';__dbg.setView('supplier')"); await pg.select_option('#bz-type','Limited company'); print(W,'tax label', await pg.locator('label[for="bz-tax"]').inner_text())
      await pg.check('#set-away'); await pg.screenshot(path=str(D/f'sp-set-{W}.png'),full_page=True)
      await pg.evaluate("__dbg.S.search.cat='catering';__dbg.setView('search')"); print(W,'pp in search', await pg.locator('.sup:has-text("Pier & Plate")').count())
      await pg.evaluate("__dbg.setView('admin')"); print(W,'admin checks', await pg.locator('.ditem[data-atab="suppliers"]').inner_text())
      print(W,errs)
    await b.close()
asyncio.run(main())
