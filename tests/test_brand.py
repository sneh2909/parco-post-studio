"""Brand Poster family: every piece is its own item, layouts fit all sizes, watermark stays off logo and contact strip."""
from conftest import FORMATS, set_format, shot

SETUP = """async () => { await document.fonts.ready; await scriptFonts();
  Object.assign(state,{theme:'forest',colors:{...THEMES.forest},look:'classic'});
  state.text.headline='Oil Cooler Assembly Hino J05E'; state.text.compat='KOBELCO 220';
  state.specs=[{k:'Make',v:'CVPK'},{k:'Engine',v:'HINO J05E'}];
  state.badges=[{icon:'box',label:'Ready Stock'},{icon:'truck',label:'Pan-India'},{icon:'shield',label:'Superior Quality'}];
  for(const sp of SAMPLE_PH){ if(state.photos.length>=3) break; if(!state.photos.includes(sp)) state.photos.push(sp); }
  state.photos[1].label='Oil Cooler'; state.photos[2].label='Oil Cooler Cover'; }"""
BRAND = ["brandHero", "brandSplit", "brandBand", "brandWall"]


def test_every_piece_is_an_item(page):
    page.evaluate(SETUP)
    for tpl in BRAND:
        for fmt in FORMATS:
            set_format(page, fmt)
            page.evaluate(f"() => {{ state.template='{tpl}'; render(); }}")
            page.wait_for_timeout(150)
            ids = set(i.split("_")[0] if not i.startswith("deco_") else i for i in page.evaluate("() => hitRects.map(h=>h.id)"))
            want = {"deco_band", "deco_stripe", "since", "sincelab", "year", "logo", "headline", "fitment", "pill", "pk", "pv",
                    "photo0", "photo1", "photo2", "label", "feat", "ficon", "fline", "ftext", "contact", "phoneicon", "phones",
                    "divider", "email", "web", "icon", "address", "rule", "edge", "tagline", "tagtext", "tagrule"}
            assert want <= ids, (tpl, fmt, want - ids)
            # the engine model is already in the headline, so it gets no pill
            assert page.evaluate("() => hitRects.filter(h=>/^pill/.test(h.id)).length") == 1
            shot(page, f"brand_{tpl}_{fmt}")


def test_small_piece_moves_rotates_resizes(page):
    page.evaluate(SETUP)
    page.evaluate("() => { state.template='brandHero'; render(); }")
    page.wait_for_timeout(150)
    page.evaluate("() => { SEL='ficon_1'; updSel(); render(); }")
    page.wait_for_timeout(150)
    hs = page.evaluate("() => selHandles(selRect()).L.map(k=>k.kind)")
    assert "rot" in hs and "corner" in hs
    r0 = page.evaluate("() => selRect().r")
    page.evaluate("() => { setRot('ficon_1',30); setScale('ficon_1',1.5); const o=getOff('ficon_1'); setOff('ficon_1',o.dx+20,o.dy); render(); }")
    page.wait_for_timeout(150)
    r1 = page.evaluate("() => selRect().r")
    assert r1["w"] > r0["w"] * 1.4 and abs((r1["x"] + r1["w"] / 2) - (r0["x"] + r0["w"] / 2) - 20) < 2


def test_layouts_fit_with_1_2_3_photos(page):
    page.evaluate(SETUP)
    bad = page.evaluate("""() => { const out=[], all=state.photos.slice(); for(const t of %s) for(const f of Object.keys(FORMATS)) for(const k of [1,2,3]) for(const lk of ['classic','night','site']){
        state.photos=all.slice(0,k); const F=FORMATS[f], c=document.createElement('canvas'), x=c.getContext('2d'); c.width=F.w; c.height=F.h;
        const sv=S, sl=LOOK, ss=SZ; S={...state,template:t,format:f,look:lk}; LOOK=lk; SZ={head:1,text:1,foot:1,logo:1,brand:1,photo:1};
        let ok=false; for(const sc of [1,.93,.86,.79,.72,.65,.58,.52]){ if(TPL[t](x,F.w,F.h,sc).ok){ ok=true; break; } } S=sv; LOOK=sl; SZ=ss; if(!ok) out.push([t,f,k,lk]); }
      state.photos=all; return out; }""" % BRAND)
    assert bad == []


def test_photo_cards_never_overlap(page):
    page.evaluate(SETUP)
    for tpl in BRAND:
        for fmt in FORMATS:
            set_format(page, fmt)
            for k in [2, 3]:
                page.evaluate(f"() => {{ window._all=window._all||state.photos.slice(); state.photos=_all.slice(0,{k}); state.template='{tpl}'; render(); }}")
                page.wait_for_timeout(120)
                rs = page.evaluate("() => hitRects.filter(h=>/^photo\\d$/.test(h.id)).map(h=>h.r)")
                assert len(rs) == k
                for i in range(k):
                    for j in range(i + 1, k):
                        a, b = rs[i], rs[j]
                        ov = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]) > 1 and min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]) > 1
                        assert not ov, (tpl, fmt, k, a, b)
    page.evaluate("() => { state.photos=_all; }")


def test_watermark_only_on_photos_and_background(page):
    page.evaluate(SETUP)
    page.evaluate("() => { state.template='brandHero'; render(); }")
    page.wait_for_timeout(150)
    boxes = page.evaluate("() => ['logo','contact','headline','feat','pill'].map(id=>{ const r=hitRects.find(h=>h.id===id).r; const ix=id==='contact'?2:r.w*0.15, iy=id==='contact'?2:r.h*0.2; return [Math.round(r.x+ix),Math.round(r.y+iy),Math.round(r.w-2*ix),Math.round(r.h-2*iy)]; })  // inside rounded corners")
    def grab(mode):
        page.evaluate(f"() => {{ state.wm.mode='{mode}'; state.wm.opacity=0.4; SEL=null; render(); }}")
        page.wait_for_timeout(150)
        return page.evaluate("(bs) => bs.map(b=>Array.from(cx.getImageData(...b).data).join(','))", boxes), \
            page.evaluate("() => { const r=hitRects.find(h=>h.id==='photo0').r; return Array.from(cx.getImageData(Math.round(r.x),Math.round(r.y),Math.round(r.w),Math.round(r.h)).data).join(','); }")
    off_items, off_photo = grab("off")
    on_items, on_photo = grab("post")
    # logo card, contact strip, feature card and pill interiors are untouched; the photo is watermarked
    for name, a, b in zip(["logo", "contact", "headline", "feat", "pill"], off_items, on_items):
        if name != "headline":  # the headline sits on the background, so the watermark shows between its letters
            assert a == b, name
    assert off_photo != on_photo


WANT = ["deco_band", "deco_stripe", "since", "sincelab", "year", "logo", "headline", "fitment", "pill", "pk", "pv",
        "photo0", "photo1", "photo2", "label", "feat", "ficon", "fline", "ftext", "contact", "phoneicon", "phones",
        "divider", "email", "web", "icon", "address", "rule", "edge", "tagline", "tagtext", "tagrule"]


def test_phone_tap_selects_and_drag_moves_every_piece(browser, base_url):
    ctx = browser.new_context(viewport={"width": 430, "height": 932}, has_touch=True, is_mobile=True, device_scale_factor=2)
    ctx.route("**/config.js", lambda r: r.fulfill(status=200, content_type="application/javascript", body="window.PARCO_CONFIG={users:[]};"))
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(base_url)
    pg.wait_for_function("() => typeof state==='object' && state.photos.length>0 && !document.getElementById('app').hidden")
    pg.evaluate(SETUP)
    pg.evaluate("() => { state.template='brandHero'; state.format='portrait'; render(); }")
    pg.wait_for_timeout(300)
    pg.locator("#cv").scroll_into_view_if_needed()
    pg.wait_for_timeout(300)
    def client(x, y):
        return pg.evaluate("([x,y]) => { const r=cv.getBoundingClientRect(); return [r.left+x*r.width/cv.width, r.top+y*r.height/cv.height]; }", [x, y])
    failed = []
    cdp = ctx.new_cdp_session(pg)
    for want in WANT:
        pg.evaluate("() => { SEL=null; TAPC=null; state.offsets={}; render(); }")
        pg.wait_for_timeout(120)
        c = pg.evaluate("(id) => { const h=hitRects.find(h=>h.id===id); const f=selFrame(h); return [f.c.x,f.c.y]; }", want)
        ok = False
        for _ in range(8):  # tap until the piece is selected (buried pieces need a few taps)
            pg.touchscreen.tap(*client(*c))
            pg.wait_for_timeout(120)
            if pg.evaluate("() => SEL") == want:
                ok = True
                break
        if not ok:
            failed.append((want, "not selectable")); continue
        a, b = client(*c), client(c[0] + 60, c[1])
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": a[0], "y": a[1]}]})
        for i in range(1, 7):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": a[0] + (b[0] - a[0]) * i / 6, "y": a[1]}]})
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(150)
        c2 = pg.evaluate("(id) => { const h=hitRects.find(h=>h.id===id); const f=selFrame(h); return [f.c.x,f.c.y]; }", want)
        if abs(c2[0] - c[0] - 60) > 2 or abs(c2[1] - c[1]) > 2:
            failed.append((want, "moved", round(c2[0] - c[0], 1), round(c2[1] - c[1], 1)))
    ctx.close()
    assert not errors, errors
    assert not failed, failed


def test_address_is_readable(page):
    page.evaluate(SETUP)
    for fmt in FORMATS:
        set_format(page, fmt)
        page.evaluate("() => { state.template='brandHero'; render(); }")
        page.wait_for_timeout(150)
        h = page.evaluate("() => { const r=hitRects.find(h=>h.id==='address'); return r.r.h; }")
        size = page.evaluate("() => { const c=document.createElement('canvas').getContext('2d'); return fitLine(c,state.text.address,600,BODY,26,11,1080-80-28-14,0); }")
        assert size >= 20, size


def test_ideas_lead_with_brand_and_use_the_brief(page, ai):
    seen = []
    ai.handler = lambda p: (seen.append(p), {"ideas": [{"name": "x", "template": "showcase", "look": "classic", "theme": "parco"}]})[1]
    page.click("#ideasBtn")
    page.wait_for_function("() => !document.getElementById('ideasGo').disabled")
    page.fill("#ideasBrief", "green theme, premium look for Hino parts")
    page.click("#ideasGo")
    page.wait_for_function("() => !document.getElementById('ideasGo').disabled")
    assert any("green theme, premium look for Hino parts" in p for p in seen)
    first = page.evaluate("() => ideaSeen[ideaSeen.length-3]")
    assert first["template"].startswith("brand") and first["theme"] in ("forest", "navy")
