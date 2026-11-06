import asyncio, pathlib
from playwright.async_api import async_playwright
html='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'+pathlib.Path('fete-prototype.html').read_text()+'</body></html>'
pathlib.Path('test.html').write_text(html)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for W in (1280,390):
      pg=await b.new_page(viewport={'width':W,'height':1000}); await pg.add_init_script("try{localStorage.setItem('bunting.tour','{\"seen\":true}')}catch(e){}"); await pg.add_init_script("window.__openAll=1"); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
      await pg.goto('file://'+str(pathlib.Path('test.html').resolve()))
      async def st(n,c):
        try: await c; print(W,'ok',n)
        except Exception as e: print(W,'FAIL',n,str(e)[:160])
      await st('demo', pg.click('[data-demo="tony"]'))
      await st('guests', pg.click('.nav [data-nav="guests"]'))
      await st('invite tab', pg.click('[data-gtab="invite"]'))
      await st('title', pg.fill('#inv-title','Sam is 40!'))
      print(W,'live title', await pg.locator('#invprev h2').inner_text())
      await st('dress', pg.fill('#inv-dress','90s fancy dress'))
      await st('font', pg.click('[data-invfont="script"]'))
      await st('colour', pg.click('[data-invcol="4"]'))
      await st('plus', pg.check('[data-invflag="plusOnes"]'))
      await st('question', pg.fill('#inv-question','What song gets you dancing?')); await pg.locator('#inv-question').dispatch_event('change')
      await st('invite image', pg.click('[data-cover-invite]')); await st('preset', pg.click('[data-cpreset="dj|3"]')); await st('save', pg.click('[data-csave]'))
      if W==1280: await pg.screenshot(path='inv.png',full_page=True)
      await st('plus-one', pg.check('#guest-plus'))
      await st('answer', pg.fill('#guest-ans','Mr Brightside')); await pg.locator('#guest-ans').dispatch_event('change')
      await st('list tab', pg.click('[data-gtab="list"]'))
      print(W,'coming', await pg.locator('.stat .v').first.inner_text(), 'plus pill', await pg.locator('.gr .pill:has-text("+1")').count())
      await st('invite tab', pg.click('[data-gtab="invite"]')); print(W,'send card', (await pg.locator('.sendcard').inner_text())[:60].replace('\n',' '))
      sw=await pg.evaluate('document.documentElement.scrollWidth'); print(W,'sw',sw,'errs',errs); await pg.close()
    await b.close()
asyncio.run(main())
