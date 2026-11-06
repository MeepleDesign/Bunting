import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':900}); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){}"); await pg.add_init_script("window.__openAll=1"); pg.set_default_timeout(5000); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(D/'test.html')); await pg.wait_for_timeout(300)
      async def st(n,c):
        try: await c; print(W,'ok',n)
        except Exception as e: print(W,'FAIL',n,str(e)[:200])
      txt=lambda sel: pg.locator(sel).first.inner_text()
      await st('demo', pg.click('[data-demo="tony"]'))
      await pg.evaluate("__dbg.setView('workspace')"); await pg.wait_for_timeout(200)
      print(W,'TL offer', await pg.locator('.tlc:has-text("offered a follow-up")').count())
      print(W,'appt card e1:', (await txt('section.card:has(h3:text-is("Viewings, tastings and chats"))')).replace('\n',' | ')[:300])
      await st('choose', pg.click('.tlc [data-vpick] >> nth=0')); await st('opt', pg.click('[data-vpickopt="1"]')); await st('confirm', pg.click('[data-vpickgo]')); await pg.wait_for_timeout(200)
      print(W,'after pick', (await txt('section.card:has(h3:text-is("Viewings, tastings and chats"))')).replace('\n',' | ')[:300])
      # e2 compare
      await pg.select_option('#ev-switch','e2'); await pg.wait_for_timeout(300)
      print(W,'appt card e2:', (await txt('section.card:has(h3:text-is("Viewings, tastings and chats"))')).replace('\n',' | ')[:400])
      print(W,'maybe pressed', await pg.locator('[data-vverdict="vw3|maybe"][aria-pressed="true"]').count())
      await st('top', pg.click('[data-vverdict="vw3|yes"]')); print(W,'yes pressed', await pg.locator('[data-vverdict="vw3|yes"][aria-pressed="true"]').count())
      await pg.fill('[data-vnote="vw3"]','Great garden'); await pg.dispatch_event('[data-vnote="vw3"]','change'); await pg.wait_for_timeout(100)
      print(W,'note', await pg.evaluate("__dbg.ACC.tony.vnotes.vw3.n"))
      # ask a cake maker (not listing times)
      await pg.evaluate("__dbg.S.search.cat='cake';__dbg.setView('search')")
      cake=await pg.evaluate("Object.values(__dbg.SUP).filter(s=>s.cat==='cake')[0].id"); await st('cake', pg.click(f'.results [data-open="{cake}"], .results .sup >> nth=0'))
      print(W,'cake section:', (await txt('.modal h3:has-text("See it first") + *')).replace('\n',' | ')[:200] if await pg.locator('.modal h3:has-text("See it first")').count() else 'none')
      await st('ask', pg.click('.modal [data-vreq]'))
      await pg.fill('#vq-d0', await pg.evaluate("(()=>{const d=new Date();d.setDate(d.getDate()+5);return d.toISOString().slice(0,10)})()")); await pg.fill('#vq-t0','17:30')
      await st('send', pg.click('#vreqform button[type=submit]')); await pg.wait_for_timeout(200)
      print(W,'after ask:', (await txt('.modal .vbox')).replace('\n',' | ')[:200] if await pg.locator('.modal .vbox').count() else 'no vbox')
      await st('close', pg.click('.modal [data-close] >> nth=0'))
      # supplier answers
      await pg.evaluate(f"__dbg.loadAccount('supplier');__dbg.S.supplierAs='{cake}';__dbg.S.supTab='overview';__dbg.setView('supplier')"); await pg.wait_for_timeout(200)
      print(W,'todo request', await pg.locator('.todorow:has-text("request from Tony")').count())
      await st('reply', pg.click('.todorow:has-text("request from Tony") button')); await st('accept', pg.click('.modal [data-vaccept]')); await pg.wait_for_timeout(200)
      st2=await pg.evaluate(f"__dbg.S && JSON.stringify((window.__dbg.SUP['{cake}'],1))")
      # Pier & Plate: Jess request -> offer other times with fee
      await pg.evaluate("__dbg.loadAccount('supplier');__dbg.S.supTab='calendar';__dbg.setView('supplier')"); await pg.wait_for_timeout(200)
      print(W,'req card', await pg.locator('h2:has-text("Tasting requests")').count())
      await st('open jess', pg.click('.vrow:has-text("Jess") >> nth=0')); await st('offer other', pg.click('[data-vofferfor]'))
      d=await pg.evaluate("(()=>{const d=new Date();d.setDate(d.getDate()+8);return d.toISOString().slice(0,10)})()")
      await pg.fill('#vo-d0',d); await pg.fill('#vo-t0','11:00'); await pg.select_option('#vo-charge','1'); await pg.wait_for_timeout(100); await pg.fill('#vo-fee','20')
      await st('send offer', pg.click('#voffform button[type=submit]')); await pg.wait_for_timeout(200)
      print(W,'waiting list', await pg.locator('.vrow:has-text("Jess")').count(), (await txt('section.card:has(h2:has-text("Upcoming tastings"))')).replace('\n',' | ')[-150:])
      # offer follow-up from a booking
      await pg.evaluate("__dbg.S.supTab='bookings';__dbg.setView('supplier')"); await st('open bk', pg.click('tr.click:has-text("Sam") >> nth=0'))
      await st('offer fu', pg.click('.modal [data-voffer]')); print(W,'offer title', await txt('#votitle'), '| free note', await pg.locator('#voffform p:has-text("Free, as they")').count())
      await pg.fill('#vo-d0',d); await pg.fill('#vo-t0','14:00'); await st('send fu', pg.click('#voffform button[type=submit]')); await pg.wait_for_timeout(200)
      # settings fee mode
      await pg.evaluate("__dbg.S.supTab='calendar';__dbg.setView('supplier')")
      await st('free', pg.select_option('[data-vsfeemode]','free')); await pg.wait_for_timeout(100); print(W,'fee field after free', await pg.locator('[data-vsfee]').count())
      await st('charge', pg.select_option('[data-vsfeemode]','charge')); await pg.wait_for_timeout(100); print(W,'fee after charge', await pg.locator('[data-vsfee]').input_value())
      # planner sees offer in booking detail
      await pg.evaluate("__dbg.loadAccount('tony');__dbg.setView('workspace')"); await pg.wait_for_timeout(200)
      await st('booking', pg.click('[data-booking="catering"]')); print(W,'bk followups:', (await txt('.modal h3:has-text("follow-ups")')), '|', (await pg.locator('.modal .vbox:has-text("offered")').count()))
      print(W,'cake confirmed for tony:', await pg.evaluate(f"(__dbg.S.events.find(e=>e.id==='e2')&&1)"))
      print(W,'errs',errs)
    await b.close()
asyncio.run(main())
