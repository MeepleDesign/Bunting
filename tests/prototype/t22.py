import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
html='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>'
(D/'test.html').write_text(html)
# tiny png for upload
import base64
(D/'pic.png').write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='))
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':1000}); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){}"); await pg.add_init_script("window.__openAll=1"); pg.set_default_timeout(5000); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str((D/'test.html').resolve())); await pg.wait_for_timeout(300)
      async def st(n,c):
        try: await c; print(W,'ok',n)
        except Exception as e: print(W,'FAIL',n,str(e)[:180])
      sh=lambda n: pg.screenshot(path=str(D/f'{n}-{W}.png'),full_page=False) if True else None
      await st('demo', pg.click('[data-demo="tony"]'))
      await st('bell', pg.click('[data-bell]')); print(W,'notifs',await pg.locator('.nitem').count(), 'unread',await pg.locator('.nitem.unread').count())
      await sh('bell')
      await st('read one', pg.click('.nitem >> nth=1')); print(W,'view after notif', await pg.locator('main h1').first.inner_text())
      await st('ws', pg.click('[data-nav2="workspace"]') if await pg.locator('[data-nav2="workspace"]').count() else pg.click('.nav [data-nav="workspace"]'))
      print(W,'whopays', await pg.locator('h2:has-text("Who\'s paying")').count(), 'pastalb', await pg.locator('[data-pastalbum]').count())
      await st('open catering', pg.click('[data-booking="catering"]'))
      print(W,'split chips', await pg.locator('.modal [data-splitto]').count(), 'receipts', await pg.locator('.modal [data-receipt]').count())
      await st('split', pg.click('.modal [data-splitto] >> nth=1'))
      print(W,'split rows', (await pg.locator('.modal .splitlist').inner_text()).replace('\n',' | ')[:200])
      print(W,'pay btn', await pg.locator('.modal [data-pay]').inner_text() if await pg.locator('.modal [data-pay]').count() else 'none')
      await st('cohost paid', pg.click('.modal [data-splitpaid]'))
      print(W,'after paid', (await pg.locator('.modal .splitlist').inner_text()).replace('\n',' | ')[:200])
      await st('receipt', pg.click('.modal [data-receipt] >> nth=0'))
      print(W,'receipt', (await pg.locator('.modal').inner_text()).replace('\n',' | ')[:400])
      if W==1280: await pg.locator('.modal').screenshot(path=str(D/'receipt.png'))
      await st('back', pg.click('.modal [data-close]')); print(W,'back to booking', await pg.locator('.modal #btitle').count())
      await st('close', pg.click('.modal [data-close]'))
      # cohost add
      await st('add coplanner', pg.click('[data-cohost]')); await pg.fill('#ch-name','Jo Lewis'); await st('submit', pg.click('#cohostform button[type=submit]'))
      print(W,'whopays', (await pg.locator('section:has(h2:has-text("Who\'s paying"))').inner_text()).replace('\n',' | ')[:250])
      await st('past album', pg.click('[data-pastalbum]')); print(W,'past photos', await pg.locator('.modal .aph:not(.add)').count())
      await st('photo', pg.click('.modal .aph >> nth=1')); print(W,'lightbox', await pg.locator('.modal .bigphoto').count())
      await st('next', pg.click('.modal [data-phnav="1"]')); await st('close lb', pg.click('.modal [data-close]')); await st('close alb', pg.click('.modal [data-close]'))
      # guests album
      await st('guests', pg.click('.nav [data-nav="guests"]') if W==1280 else pg.evaluate("__dbg.setView('guests')"))
      await st('album tab', pg.click('[data-gtab="album"]'))
      await pg.set_input_files('#alb-files', [str(D/'pic.png'),str(D/'pic.png')]); await pg.wait_for_timeout(600)
      print(W,'album photos', await pg.locator('.album .aph:not(.add)').count())
      await st('open now', pg.check('#alb-open')); await st('inv tab', pg.click('[data-gtab="invite"]'))
      print(W,'invite album', await pg.locator('.phone :text("party album is open")').count())
      # search map + access
      await pg.evaluate("__dbg.S.search.cat='venue';__dbg.setView('search')")
      print(W,'access filters', await pg.locator('[data-accf]').count(), 'venues', await pg.locator('.results .sup').count())
      await st('stepfree', pg.check('[data-accf="stepfree"]')); print(W,'venues stepfree', await pg.locator('.results .sup').count())
      await st('map', pg.click('[data-smode="map"]')); print(W,'pins', await pg.locator('[data-mpin]').count())
      await st('pin', pg.click('[data-mpin] >> nth=0')); print(W,'sel card', await pg.locator('.mapwrap ~ .results .sup, .results .sup').count())
      await sh('map')
      await st('open from map', pg.click('.sup >> nth=0')); print(W,'access section', await pg.locator('.modal h3:has-text("Accessibility")').count()); await st('close', pg.click('.modal [data-close] >> nth=-1'))
      await st('list', pg.click('[data-smode="list"]'))
      # supplier payments
      await pg.evaluate("__dbg.loadAccount('supplier');__dbg.setView('supplier')")
      await st('pay tab', pg.evaluate("__dbg.S.supTab='money';__dbg.setView('supplier')")); print(W,'pay rows', await pg.locator('main table tbody tr').count(), 'invoices', await pg.locator('[data-invoice]').count())
      await sh('suppay')
      await st('invoice', pg.click('[data-invoice] >> nth=0')); print(W,'invoice', (await pg.locator('.modal').inner_text()).replace('\n',' | ')[:300]); await st('close', pg.click('.modal [data-close] >> nth=-1'))
      await st('csv', pg.click('[data-csv]'))
      await st('settings', pg.evaluate("__dbg.S.supTab='settings';__dbg.setView('supplier')")); await st('vatreg off', pg.uncheck('#lg-vatreg')); print(W,'vat field', await pg.locator('#lg-vat').count())
      # admin
      await pg.evaluate("__dbg.setView('admin')"); print(W,'admin h1', await pg.locator('main h1').first.inner_text())
      await sh('admin')
      await st('sup tab', pg.evaluate("document.querySelector('.ditem[data-atab=suppliers]').click()")); print(W,'checks', await pg.locator('[data-approve]').count())
      if await pg.locator('[data-approve]').count(): await st('approve', pg.click('[data-approve] >> nth=0'))
      await st('open hg', pg.click('tr[data-aopen="hovegraze"]')); await st('pause', pg.click('[data-pause="hovegraze"]'))
      await st('support', pg.evaluate("document.querySelector('.ditem[data-atab=support]').click()"));
      if W<780 and await pg.locator('[data-asup]').count(): await st('open conv', pg.click('[data-asup] >> nth=0'))
      if await pg.locator('#areplyin').count():
        await pg.fill('#areplyin','Hi from Bunting'); await pg.press('#areplyin','Enter'); print(W,'reply', (await pg.locator('#amsgs .msg').last.inner_text())[:40])
      await st('money', pg.evaluate("document.querySelector('.ditem[data-atab=money]').click()")); print(W,'money rows', await pg.locator('main table tbody tr').count())
      await st('settings', pg.evaluate("document.querySelector('.ditem[data-atab=settings]').click()")); await pg.fill('#as-comm','10'); await pg.press('#as-comm','Tab'); await pg.wait_for_timeout(100)
      await st('ov', pg.evaluate("document.querySelector('.ditem[data-atab=overview]').click()")); print(W,'overview', (await pg.locator('.minis').inner_text()).replace('\n',' ')[:250])
      await pg.evaluate("__dbg.S.search.cat='catering';__dbg.setView('search')"); print(W,'hovegraze hidden', await pg.locator('.sup:has-text("Hove Grazing")').count())
      print(W,'errs',errs)
      await pg.close()
    await b.close()
asyncio.run(main())
