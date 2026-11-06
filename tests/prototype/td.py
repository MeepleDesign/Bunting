import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':1000}); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){};window.__openAll=1"); pg.set_default_timeout(6000); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(D/'test.html')); await pg.click('[data-demo="tony"]')
      # report
      print(W,'report btns', await pg.locator('[data-report]').count())
      await pg.click('[data-report] >> nth=1'); await pg.click('[data-rptype="noshow"]'); await pg.fill('#rp-text','They never arrived'); await pg.click('[data-rpwant="full"]'); await pg.click('#reportform button[type=submit]')
      print(W,'reported', await pg.locator('.pill:has-text("Reported")').count())
      # perms
      await pg.click('[data-perms]'); print(W,'perm rows', await pg.locator('.permtable tbody tr').count())
      await pg.uncheck('[data-perm="c2.pay"]'); await pg.select_option('#actas','c2'); print(W,'actas banner', await pg.locator('.pvbanner').inner_text())
      await pg.click('[data-booking="catering"]'); await pg.click('.modal [data-pay]'); print(W,'blocked', await pg.locator('.toast').inner_text()); await pg.click('.modal [data-close] >> nth=-1')
      await pg.click('[data-actasexit]')
      # admin disputes
      await pg.evaluate("__dbg.setView('admin')"); await pg.evaluate("document.querySelector('.ditem[data-atab=disputes]').click()")
      print(W,'disputes', await pg.locator('[data-adisp]').count()); await pg.screenshot(path=str(D/f'disp-{W}.png'),full_page=True)
      await pg.click('[data-adisp] >> nth=0'); await pg.click('[data-dout="partial"]'); await pg.click('[data-dresolve]'); print(W,'resolved', await pg.locator('.allclear').count())
      # view as supplier
      await pg.evaluate("document.querySelector('.ditem[data-atab=suppliers]').click()"); await pg.click('tr[data-aopen="bubbles"]'); await pg.click('[data-viewas="bubbles"]')
      print(W,'viewas', (await pg.locator('.pvbanner').inner_text())[:50], 'setup', await pg.locator('.setupcard').count())
      await pg.screenshot(path=str(D/f'viewas-{W}.png'),full_page=True)
      await pg.click('.setupcard button.primary >> nth=0'); print(W,'blocked2', await pg.locator('.toast').inner_text())
      await pg.click('[data-viewasexit]'); print(W,'back', await pg.evaluate("__dbg.S.view"), await pg.evaluate("__dbg.S.viewAs"))
      # auto pause: supplier cancels within 30 days? make booking soon
      await pg.evaluate("__dbg.loadAccount('supplier');__dbg.S.others[0].date=new Date(Date.now()+10*864e5).toISOString().slice(0,10);__dbg.S.supTab='bookings';__dbg.setView('supplier')")
      await pg.click('tr.click:has-text("Priya")'); await pg.click('.modal [data-scancel]'); await pg.click('[data-scxreason="Double booked"]'); await pg.click('[data-scxconfirm]')
      print(W,'paused', await pg.evaluate("__dbg.SUP.pierplate.paused"), await pg.locator('.toast').inner_text())
      await pg.evaluate("__dbg.S.supTab='overview';__dbg.setView('supplier')"); print(W,'pause banner', await pg.locator('.alert:has-text("paused for review")').count())
      print(W,errs)
    await b.close()
asyncio.run(main())
