import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (390,1280):
      pg=await b.new_page(viewport={'width':W,'height':844}); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){}"); pg.set_default_timeout(5000); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(D/'test.html')); await pg.wait_for_timeout(300)
      state=lambda: pg.evaluate("[__dbg.S.view, __dbg.S.supTab||'', __dbg.S.modal?__dbg.S.modal.type:'', !!__dbg.S.chatOpen]")
      back=lambda: pg.go_back(wait_until='commit')
      await pg.click('[data-demo="tony"]'); await pg.wait_for_timeout(200); print(W,'start',await state())
      await pg.evaluate("document.querySelector('[data-nav=\"search\"]')?document.querySelector('[data-nav=\"search\"]').click():__dbg.setView('search')"); await pg.wait_for_timeout(200); print(W,'search',await state())
      await pg.click('.results .sup >> nth=0'); await pg.wait_for_timeout(200); print(W,'opened supplier',await state())
      await back(); await pg.wait_for_timeout(300); print(W,'back ->',await state())
      await back(); await pg.wait_for_timeout(300); print(W,'back ->',await state())
      # close a modal with the button should not leave an extra entry
      await pg.evaluate("__dbg.setView('search')"); await pg.wait_for_timeout(200); await pg.click('.results .sup >> nth=0'); await pg.click('.modal [data-close] >> nth=0'); await pg.wait_for_timeout(300); print(W,'closed modal',await state(), 'len',await pg.evaluate("[__dbg.NAV.i,__dbg.NAV.list.length]"))
      await back(); await pg.wait_for_timeout(300); print(W,'back after close ->',await state())
      # messages list -> thread -> back to list
      await pg.evaluate("__dbg.setView('messages')"); await pg.wait_for_timeout(200)
      await pg.locator('.convs .conv').nth(1).click(); await pg.wait_for_timeout(200); print(W,'thread',await state())
      await back(); await pg.wait_for_timeout(300); print(W,'back ->',await state(), 'list visible', await pg.evaluate("!!document.querySelector('.convs')&&document.querySelector('.convs').offsetParent!==null"))
      # supplier tabs
      await pg.evaluate("__dbg.loadAccount('supplier');__dbg.setView('supplier')"); await pg.wait_for_timeout(200)
      await pg.evaluate("[...document.querySelectorAll('[data-stab]')].find(b=>b.dataset.stab==='bookings').click()"); await pg.wait_for_timeout(200); print(W,'cal',await state())
      await pg.evaluate("[...document.querySelectorAll('[data-stab]')].find(b=>b.dataset.stab==='pricing').click()"); await pg.wait_for_timeout(200); print(W,'pricing',await state())
      await back(); await pg.wait_for_timeout(300); print(W,'back ->',await state())
      await pg.go_forward(wait_until='commit'); await pg.wait_for_timeout(300); print(W,'forward ->',await state())
      print(W,'errs',errs)
    await b.close()
asyncio.run(main())
