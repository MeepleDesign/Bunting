import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':1000}); await pg.add_init_script("window.__openAll=1"); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){}"); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(D/'test.html')); await pg.click('[data-demo="tony"]')
      await pg.click('[data-booking="venue"]'); print(await pg.evaluate("[...document.querySelectorAll('.modal [data-receipt]')].map(b=>{const r=b.getBoundingClientRect();let p=b,c=[];while(p){const cs=getComputedStyle(p);if(cs.display==='none'||cs.visibility==='hidden'||cs.opacity==='0')c.push(p.tagName+'.'+p.className);p=p.parentElement}return [r.width,r.height,c.join('|')]})")); await pg.click('.modal [data-receipt] >> nth=0'); print(W,'venue receipt', (await pg.locator('.modal .refund').inner_text()).replace('\n',' | ')); await pg.click('.modal [data-close]'); await pg.click('.modal [data-close]')
      if await pg.locator('[data-booking="cake"]').count():
        await pg.click('[data-booking="cake"]'); await pg.click('.modal [data-receipt] >> nth=0'); print(W,'cake receipt', (await pg.locator('.modal .refund').inner_text()).replace('\n',' | ')); await pg.click('.modal [data-close]'); await pg.click('.modal [data-close]')
      await pg.evaluate("__dbg.loadAccount('supplier');__dbg.setView('supplier')"); await pg.evaluate("__dbg.S.supTab='pricing';__dbg.setView('supplier')")
      print(W,'vatcard', (await pg.locator('#vatcard').inner_text()).replace('\n',' | ')[:300])
      await pg.select_option('[data-vata] >> nth=0','E'); print(W,'after change', await pg.locator('#vatcard .alert').count(), await pg.locator('#vatcard .pill').inner_text())
      await pg.check('#vat-confirm'); await pg.locator('#vatcard').screenshot(path=str(D/f'vatcard-{W}.png'))
      await pg.evaluate("__dbg.S.supTab='money';__dbg.setView('supplier')"); print(W,'vat helper', (await pg.locator('section:has(h2:has-text("VAT return helper"))').inner_text()).replace('\n',' | ')[:300])
      await pg.click('section:has(h2:has-text("VAT return helper")) summary'); await pg.locator('section:has(h2:has-text("VAT return helper"))').screenshot(path=str(D/f'vath-{W}.png'))
      await pg.select_option('#vatq','1'); await pg.click('[data-vatcsv]')
      await pg.evaluate("__dbg.setView('admin')"); await pg.evaluate("document.querySelector('.ditem[data-atab=settings]').click()"); print(W,'taxcodes rows', await pg.locator('.tctable tbody tr').count())
      await pg.locator('.tctable').screenshot(path=str(D/f'tc-{W}.png'))
      await pg.check('#as-vat'); await pg.evaluate("document.querySelector('.ditem[data-atab=money]').click()"); print(W,'bunting vat', (await pg.locator('section:has(h2:has-text("Bunting\'s VAT return"))').inner_text()).replace('\n',' | ')[:200])
      await pg.evaluate("document.querySelector('.ditem[data-atab=compliance]').click()"); await pg.click('[data-comprun]'); await pg.wait_for_timeout(300); print(W,'toast', await pg.locator('.toast').inner_text(), 'pulse', await pg.locator('.compitem.pulse').count())
      print(W,errs)
    await b.close()
asyncio.run(main())
