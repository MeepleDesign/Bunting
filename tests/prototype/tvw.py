import asyncio, pathlib, json
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
      await st('demo', pg.click('[data-demo="tony"]'))
      evs=await pg.evaluate("__dbg.S.events.map(e=>[e.id,e.name,(e.lines.find(l=>l.cat==='catering')||{}).booking?.sup||null])"); print(W,'events',evs)
      # switch to an event without Pier & Plate
      target=[e for e in evs if e[2]!='pierplate'][0][0]
      await pg.evaluate(f"__dbg.S.event=__dbg.S.events.find(e=>e.id==='{target}');__dbg.S.lines=__dbg.S.event.lines;__dbg.S.search.cat='catering';__dbg.setView('search')")
      await st('open pp', pg.click('.sup:has-text("Pier & Plate")'))
      print(W,'see first:', (await pg.locator('.modal h3:has-text("See it first") ~ p').inner_text())[:200])
      await st('vbook', pg.click('.modal [data-vbook]'))
      print(W,'modal intro:', (await pg.locator('#vwform p.muted').inner_text())[:200])
      await st('slot', pg.click('.modal [data-vslot]:not([disabled]) >> nth=0'))
      await pg.select_option('#vw-ev', target)
      print(W,'fee calc:', (await pg.locator('#vwform .calc').inner_text()).replace('\n',' | '))
      print(W,'submit label:', await pg.locator('#vwform button[type=submit]').inner_text())
      await st('submit', pg.click('#vwform button[type=submit]')); await pg.wait_for_timeout(200)
      print(W,'vbox:', (await pg.locator('.modal .vbox').last.inner_text()).replace('\n',' | ')[:250])
      await st('receipt', pg.click('.modal [data-vreceipt]')); print(W,'receipt:', (await pg.locator('.modal .refund').inner_text()).replace('\n',' | ')[:250])
      await st('close r', pg.click('.modal [data-close] >> nth=0'))
      # now book Pier & Plate for the same event
      print(W,'after receipt close, supplier modal?', await pg.locator('.modal [data-vbook], .modal .vbox').count())
      if not await pg.locator('.modal [data-confirm]').count():
        await pg.evaluate("__dbg.S.search.cat='catering';__dbg.setView('search')"); await st('reopen', pg.click('.sup:has-text("Pier & Plate")'))
      await st('confirm', pg.click('.modal [data-confirm]')); await st('book', pg.click('.modal [data-book]')); await pg.wait_for_timeout(300)
      # confirm if needed
      for sel in ['.modal [data-confirmbook]','.modal button:has-text("Confirm")','.modal button:has-text("Pay")']:
        if await pg.locator(sel).count():
          await st('confirm '+sel, pg.click(sel+' >> nth=0')); await pg.wait_for_timeout(300); break
      pays=await pg.evaluate(f"(()=>{{const e=__dbg.S.events.find(e=>e.id==='{target}');const l=e.lines.find(l=>l.booking&&l.booking.sup==='pierplate');return l?l.booking.payments.map(p=>[p.kind,p.amount]):null}})()")
      print(W,'booking payments', pays)
      vw=await pg.evaluate("__dbg.ACC.pierplate?null:null")
      # supplier side
      await pg.evaluate("__dbg.loadAccount('supplier');__dbg.S.supTab='calendar';__dbg.setView('supplier')")
      print(W,'settings how:', await pg.locator('[data-vswhere]').count(), 'fee', await pg.locator('[data-vsfee]').input_value(), 'credit', await pg.locator('[data-vscredit]').is_checked())
      print(W,'upcoming:', (await pg.locator('.vrow').first.inner_text()).replace('\n',' | ') if await pg.locator('.vrow').count() else None)
      await st('tick video', pg.check('[data-vswhere="video"]')); await pg.wait_for_timeout(100); print(W,'link field', await pg.locator('[data-vslink]').count())
      await st('per person', pg.select_option('[data-vsfeeper]','person'))
      await pg.evaluate("__dbg.S.supTab='money';__dbg.setView('supplier')")
      print(W,'tasting rows in payments', await pg.locator('main table tbody tr:has-text("Tasting")').count())
      # DJ chat: video/phone, phone required
      await pg.evaluate("__dbg.loadAccount('tony');__dbg.S.event=__dbg.S.events.find(e=>e.id==='e2');__dbg.S.lines=__dbg.S.event.lines;__dbg.S.search.cat='dj';__dbg.setView('search')")
      await st('dj', pg.click('.sup:has-text("Shoreline")'))
      print(W,'dj see first:', (await pg.locator('.modal h3:has-text("See it first") ~ p').inner_text())[:200] if await pg.locator('.modal h3:has-text("See it first")').count() else 'none')
      if await pg.locator('.modal [data-vbook]').count():
        await st('dj vbook', pg.click('.modal [data-vbook]')); print(W,'how chips', await pg.locator('[data-vhow]').count())
        await st('phone', pg.click('[data-vhow="phone"]')); await st('slot', pg.click('.modal [data-vslot]:not([disabled]) >> nth=0'))
        await st('submit no phone', pg.click('#vwform button[type=submit]')); await pg.wait_for_timeout(100); print(W,'still open', await pg.locator('#vwform').count())
        await pg.fill('#vw-phone','07700 900123'); await st('submit', pg.click('#vwform button[type=submit]')); await pg.wait_for_timeout(200)
        print(W,'dj vbox', (await pg.locator('.modal .vbox').last.inner_text()).replace('\n',' | ')[:200] if await pg.locator('.modal .vbox').count() else 'none')
      # cancel tasting: late keeps fee, early refunds
      # cancel: the DJ chat is free; cancel the Pier & Plate tasting late (kept, but it was credited) -> test early cancel on a new paid one via supplier
      await st('close', pg.click('.modal [data-close] >> nth=0'))
      await pg.evaluate("__dbg.loadAccount('supplier');__dbg.S.supTab='calendar';__dbg.setView('supplier')")
      n=await pg.locator('.vrow').count(); print(W,'supplier vrows',n)
      await st('open sview', pg.click('.vrow:has-text("Mum") >> nth=0')); print(W,'sview:', (await pg.locator('.modal .calc').inner_text()).replace('\n',' | ')[:300])
      await st('sup cancel', pg.click('.modal [data-vcancel]')); await pg.wait_for_timeout(200); print(W,'toast', await pg.locator('.toast').inner_text())
      print(W,'errs',errs)
    await b.close()
asyncio.run(main())
