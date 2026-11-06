import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':900}); await pg.add_init_script("window.__openAll=1"); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(D/'test.html')); await pg.wait_for_timeout(300)
      print(W,'offer', await pg.locator('.tourcard').count()); await pg.screenshot(path=str(D/f'tour0-{W}.png'))
      for role,n in (('planner',7),('supplier',7),('guest',4)):
        await pg.click(f'[data-tourstart="{role}"]'); await pg.wait_for_timeout(200)
        for i in range(n):
          v=await pg.evaluate("__dbg.S.view"); print(W,role,i,v, await pg.locator('.tourcard b').first.inner_text())
          if role=='guest' and i==1: await pg.screenshot(path=str(D/f'inv-{W}.png'),full_page=True)
          await pg.click('[data-tournext]'); await pg.wait_for_timeout(250)
          if await pg.locator('.modal [data-close]').count(): await pg.click('.modal [data-close] >> nth=-1')
        print(W,'end', (await pg.locator('.tourcard').inner_text())[:40].replace('\n',' '))
      await pg.click('[data-tourend]')
      print(W,'tour btn', await pg.locator('[data-tourreopen]').count()); await pg.click('.fabs [data-tourreopen]'); print(W,'reoffer', await pg.locator('.tourcard [data-tourstart]').count(), (await pg.locator('.tourcard b').first.inner_text())); await pg.click('[data-tourdismiss]')
      # guest actions on invite page
      await pg.evaluate("__dbg.loadAccount('tony');__dbg.setView('guests')"); await pg.click('[data-openinvite]')
      await pg.click('[data-rsvp="yes"]'); print(W,'rsvp ok', await pg.locator('main h1, main .invpage').count())
      if await pg.locator('[data-guestpay]').count(): await pg.click('[data-guestpay]'); print(W,'paid', await pg.locator('[data-greceipt]').count())
      await pg.click('[data-invback]'); print(W,'back', await pg.evaluate("__dbg.S.view"))
      # feedback
      await pg.click('.fbbtn[data-feedback]'); await pg.click('[data-fbmood="confused"]'); await pg.fill('#fb-text','Could not find album'); await pg.click('#fbform button[type=submit]')
      await pg.evaluate("__dbg.setView('admin')"); await pg.click('.ditem[data-atab="feedback"]') if W>900 else await pg.evaluate("document.querySelector('.ditem[data-atab=\"feedback\"]').click()")
      print(W,'fb', await pg.locator('.fbitem').count())
      # requests
      await pg.evaluate("__dbg.loadAccount('supplier');__dbg.setView('supplier')")
      print(W,'todo rows', await pg.locator('.todorow').count()); await pg.click('[data-reqgo] >> nth=0'); print(W,'opened', await pg.locator('.reqitem.open').count()); await pg.screenshot(path=str(D/f'req-{W}.png'))
      await pg.evaluate("document.querySelector('.ditem[data-stab=\"requests\"]').click()"); print(W,'req page rows', await pg.locator('.reqrow').count())
      await pg.click('[data-reqf="done"]'); print(W,'done', await pg.locator('.reqrow').count())
      print(W,errs)
    await b.close()
asyncio.run(main())
