import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':1000}); await pg.add_init_script("window.__openAll=1"); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(D/'test.html')); await pg.evaluate("localStorage.setItem('bunting.tour',JSON.stringify({seen:true}))"); await pg.reload()
      await pg.evaluate("__dbg.loadAccount('supplier');__dbg.setView('supplier')"); await pg.screenshot(path=str(D/f'sov-{W}.png'),full_page=True)
      print(W,'todo', await pg.locator('.todorow').count())
      await pg.click('[data-reqgo] >> nth=0'); print(W,'reqgo', await pg.evaluate("__dbg.S.supTab"), await pg.locator('.reqitem.open').count())
      await pg.evaluate("__dbg.S.supTab='pricing';__dbg.setView('supplier')"); print(W,'pricing closed', await pg.locator('.ccard.closed').count()); await pg.screenshot(path=str(D/f'spr-{W}.png'),full_page=True)
      if await pg.locator('.ccard.closed').count(): await pg.click('.ccard.closed .cch >> nth=0'); print(W,'after toggle closed', await pg.locator('.ccard.closed').count())
      await pg.evaluate("__dbg.setView('admin')"); await pg.screenshot(path=str(D/f'aov-{W}.png'),full_page=True)
      await pg.evaluate("__dbg.loadAccount('tony');__dbg.setView('workspace')"); await pg.click('[data-booking="catering"]'); await pg.wait_for_timeout(100); await pg.locator('.modal').screenshot(path=str(D/f'bkm-{W}.png'))
      print(W,'modal closed', await pg.locator('.modal .ccard.closed').count())
      # guest refund
      await pg.click('.modal [data-close] >> nth=-1'); await pg.evaluate("__dbg.setView('guests')"); await pg.click('[data-openinvite]')
      paid=await pg.evaluate("(()=>{const g=__dbg.S.event.guests.find(x=>x.paid&&x.status==='yes');__dbg.S.myGuest=g.id;__dbg.setView('invite');return g.name})()")
      await pg.click('[data-rsvp="no"]'); print(W,'refund toast', await pg.locator('.toast').inner_text(), await pg.locator('[data-grefund]').count())
      await pg.click('[data-grefund]'); print(W,'rc', (await pg.locator('.modal').inner_text())[:120].replace('\n',' | ')); await pg.click('.modal [data-close] >> nth=-1')
      await pg.click('[data-invback]'); await pg.evaluate("__dbg.loadAccount('supplier');__dbg.S.supTab='money';__dbg.setView('supplier')"); print(W,'ledger refund rows', await pg.locator('main tbody tr:has-text("Refund")').count())
      print(W,errs)
    await b.close()
asyncio.run(main())
