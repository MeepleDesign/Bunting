import asyncio, pathlib
from playwright.async_api import async_playwright
D=pathlib.Path.cwd()
(D/'test.html').write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+(D/'fete-prototype.html').read_text()+'</body></html>')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1280,'height':900}); await pg.add_init_script("window.__openAll=1"); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){}"); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    await pg.goto('file://'+str(D/'test.html')); await pg.click('[data-demo="tony"]'); await pg.click('[data-tourdismiss]') if await pg.locator('[data-tourdismiss]').count() else None
    await pg.click('[data-booking="venue"]'); await pg.click('.modal [data-close] >> nth=-1')
    await pg.evaluate("for(let i=0;i<15;i++)__dbg.S.event.guests.push({id:'gx'+i,name:'Extra '+i,status:'yes',diet:'',paid:false})"); await pg.evaluate("__dbg.setView('workspace')")
    await pg.click('[data-booking="catering"]'); print('before', (await pg.locator('.modal .kv').inner_text()).replace('\n',' '))
    await pg.click('.modal [data-pay]'); await pg.wait_for_timeout(200)
    print('after pay', await pg.evaluate("(()=>{const l=__dbg.S.event.lines.find(x=>x.cat==='catering');return JSON.stringify(l.booking.payments.map(p=>[p.kind,p.amount]))})()"))
    await pg.evaluate("__dbg.S.event.guests.filter(g=>g.id.startsWith('gx')).forEach(g=>{g.status='no'})"); await pg.evaluate("__dbg.setView('workspace')"); await pg.wait_for_timeout(200)
    print('toast', await pg.locator('.toast').inner_text())
    print('pays', await pg.evaluate("(()=>{const l=__dbg.S.event.lines.find(x=>x.cat==='catering');return JSON.stringify(l.booking.payments.map(p=>[p.kind,p.amount]))})()"))
    await pg.click('[data-booking="catering"]'); print('kv', (await pg.locator('.modal .kv').inner_text()).replace('\n',' ')); print('receipts', await pg.locator('.modal [data-receipt]').all_inner_texts())
    await pg.click('.modal [data-receipt] >> nth=-1'); print('rc', (await pg.locator('.modal').inner_text())[:200].replace('\n',' | '))
    await pg.evaluate("__dbg.setView('workspace')"); await pg.evaluate("__dbg.setView('guests')"); print('note', await pg.locator('.phone p.sub:has-text("change your reply")').count())
    print(errs); await b.close()
asyncio.run(main())
