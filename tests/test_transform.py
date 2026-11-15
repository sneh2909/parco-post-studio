"""Stretch (side handles), rotation (round handle) and selectable template shapes."""
import math

from conftest import FORMATS, set_format, shot


def pick(page, template, sel):
    page.evaluate("async () => { await document.fonts.ready; await scriptFonts(); }")
    page.evaluate("() => { for(const sp of SAMPLE_PH){ if(state.photos.length>=4) break; if(!state.photos.includes(sp)) state.photos.push(sp); } }")
    page.evaluate(f"() => {{ state.template='{template}'; state.look='auto'; SEL=null; updSel(); render(); }}")
    page.wait_for_timeout(150)
    page.evaluate(f"() => {{ SEL='{sel}'; updSel(); render(); }}")
    page.wait_for_timeout(150)
    page.locator("#cv").scroll_into_view_if_needed()


def client(page, x, y):
    return page.evaluate("([x,y]) => { const r=cv.getBoundingClientRect(); return [r.left+x*r.width/cv.width, r.top+y*r.height/cv.height]; }", [x, y])


def drag(page, a, b, steps=8, shift=False):
    page.mouse.move(*client(page, *a))
    if shift:
        page.keyboard.down("Shift")
    page.mouse.down()
    page.mouse.move(*client(page, *b), steps=steps)
    page.mouse.up()
    if shift:
        page.keyboard.up("Shift")
    page.wait_for_timeout(150)


def handle(page, kind, i=0, j=0):
    return page.evaluate(f"() => {{ const k=selHandles(selRect()).L.find(k=>k.kind==='{kind}'&&k.i==={i}&&k.j==={j}); return [k.x,k.y]; }}")


def quad(page):
    return page.evaluate("() => selRect().q")


def off(page, id_):
    return page.evaluate(f"() => {{ const m=curMap(false); return (m&&m['{id_}'])||{{}}; }}")


def test_side_handle_stretches_one_axis_and_keeps_opposite_edge(page):
    pick(page, "showcase", "photo0")
    q0 = quad(page)
    w0 = math.dist(q0[0], q0[1])
    hx, hy = handle(page, "side", 1, 0)
    drag(page, (hx, hy), (hx + 160, hy + 40))  # vertical wobble must not change the height
    o = off(page, "photo0")
    assert abs(o["sx"] - (w0 + 160) / w0) < 0.02
    assert "sy" not in o
    q1 = quad(page)
    assert abs(q1[0][0] - q0[0][0]) <= 1.5 and abs(q1[3][0] - q0[3][0]) <= 1.5  # left edge stays put
    assert abs(math.dist(q1[0], q1[3]) - math.dist(q0[0], q0[3])) <= 1  # height unchanged
    # bottom handle stretches height only
    hx, hy = handle(page, "side", 0, 1)
    drag(page, (hx, hy), (hx, hy - 80))
    o2 = off(page, "photo0")
    assert o2["sy"] < 1 and abs(o2["sx"] - o["sx"]) < 1e-9
    page.keyboard.press("Control+z")
    page.wait_for_timeout(150)
    assert "sy" not in off(page, "photo0")


def test_rotation_handle_snaps_and_hit_test_follows(page):
    pick(page, "showcase", "photo0")
    f = page.evaluate("() => { const f=selFrame(selRect()); return [f.c.x,f.c.y]; }")
    hx, hy = handle(page, "rot", 0, -1)
    r = math.dist((hx, hy), f)
    drag(page, (hx, hy), (f[0] + r, f[1] + 3))  # quarter turn clockwise, 1-2 degrees off: snaps to 90
    assert off(page, "photo0")["rot"] == 90
    q = quad(page)
    ux = ((q[1][0] - q[0][0]), (q[1][1] - q[0][1]))
    assert abs(ux[0]) < 1 and ux[1] > 0  # top edge now points down the canvas
    # a point just inside the rotated frame hits the photo
    assert page.evaluate("() => { const f=selFrame(selRect()); const p={x:f.c.x+f.ux.x*f.w*0.4,y:f.c.y+f.ux.y*f.w*0.4}; return hitsAt(p).some(h=>h.id==='photo0'); }")
    # shift snaps to 15 degree steps
    hx, hy = handle(page, "rot", 0, -1)
    f = page.evaluate("() => { const f=selFrame(selRect()); return [f.c.x,f.c.y]; }")
    a = math.atan2(hy - f[1], hx - f[0]) + math.radians(37)
    r = math.dist((hx, hy), f)
    drag(page, (hx, hy), (f[0] + r * math.cos(a), f[1] + r * math.sin(a)), shift=True)
    assert off(page, "photo0")["rot"] % 15 == 0 and off(page, "photo0")["rot"] != 90
    page.click("#selReset")
    page.wait_for_timeout(150)
    assert off(page, "photo0") == {}


def test_template_shapes_are_selectable(page):
    want = {"ribbon": ["deco_circle", "deco_blockA", "deco_dots", "photo0"],
            "trioRow": ["deco_slab", "photo0", "photo1", "photo2"],
            "trioCircles": ["deco_arc", "photo0"],
            "quadGrid": ["photo0", "photo3"]}
    for fmt in FORMATS:
        set_format(page, fmt)
        for tpl, ids in want.items():
            page.evaluate(f"() => {{ state.template='{tpl}'; render(); }}")
            page.wait_for_timeout(150)
            have = page.evaluate("() => hitRects.map(h=>h.id)")
            for i in ids:
                assert i in have, (fmt, tpl, i)
    # spec sheet: stage rings on a cut-out photo (classic), white circle frame travels with the photo otherwise
    page.evaluate("() => { state.template='specsheet'; state.look='classic'; render(); }")
    page.wait_for_timeout(150)
    assert "deco_stage" in page.evaluate("() => hitRects.map(h=>h.id)")


def test_shape_stretch_and_alt_click_picks_underneath(page):
    pick(page, "ribbon", "deco_circle")
    q0 = quad(page)
    hx, hy = handle(page, "side", 0, 1)
    drag(page, (hx, hy), (hx, hy + 120))
    q1 = quad(page)
    assert math.dist(q1[0], q1[3]) > math.dist(q0[0], q0[3]) + 100
    assert abs(math.dist(q1[0], q1[1]) - math.dist(q0[0], q0[1])) <= 1
    # Alt+click on a spot covered by the photo and the dark block selects the next item down
    pt = page.evaluate("""() => { const P=hitRects.find(h=>h.id==='photo0').r, B=hitRects.find(h=>h.id==='deco_blockA').r;
        const x0=Math.max(P.x,B.x), x1=Math.min(P.x+P.w,B.x+B.w), y0=Math.max(P.y,B.y), y1=Math.min(P.y+P.h,B.y+B.h); return [(x0+x1)/2,(y0+y1)/2]; }""")
    page.evaluate("() => { SEL='photo0'; updSel(); render(); }")
    page.wait_for_timeout(150)
    stack = page.evaluate("([x,y]) => hitsAt({x,y}).map(h=>h.id)", pt)
    assert stack[0] == "photo0" and "deco_blockA" in stack
    page.keyboard.down("Alt")
    page.mouse.click(*client(page, *pt))
    page.keyboard.up("Alt")
    page.wait_for_timeout(150)
    assert page.evaluate("() => SEL") == stack[1]


def test_added_decoration_rotation_uses_its_own_angle(page):
    page.evaluate("() => { state.template='showcase'; render(); }")
    page.wait_for_timeout(150)
    page.evaluate("() => addDeco('ring')")
    page.wait_for_timeout(150)
    page.locator("#cv").scroll_into_view_if_needed()
    sel = page.evaluate("() => SEL")
    f = page.evaluate("() => { const f=selFrame(selRect()); return [f.c.x,f.c.y]; }")
    hx, hy = handle(page, "rot", 0, -1)
    r = math.dist((hx, hy), f)
    drag(page, (hx, hy), (f[0] - r, f[1]))  # quarter turn anticlockwise
    d = page.evaluate("() => selDeco()")
    assert d["rot"] == -90
    assert page.evaluate("() => document.getElementById('dcRot').value") == "-90"
    assert "rot" not in off(page, sel)  # not doubled up in offsets
    hx, hy = handle(page, "side", 1, 0)
    drag(page, (hx, hy), (hx, hy - 90))  # after a -90 turn the right handle sits on top
    assert off(page, sel)["sx"] > 1.3
    page.click("#dcDup")
    page.wait_for_timeout(150)
    assert off(page, page.evaluate("() => SEL"))["sx"] == off(page, sel)["sx"]


def test_screens_all_sizes(page):
    for fmt in FORMATS:
        set_format(page, fmt)
        for tpl in ["showcase", "specsheet", "trioCircles", "quadGrid", "trioList"]:
            page.evaluate(f"""() => {{ state.template='{tpl}'; const m=curMap(true);
                m.photo0={{sx:1.3,sy:0.8,rot:12}}; m.photo1={{rot:-20,sy:1.2}}; SEL='photo0'; updSel(); render(); }}""")
            shot(page, f"transform_{tpl}_{fmt}")


# ---------- gap fixes: buried items, nested tags, crop, text width, cards, old saves ----------

def frame_center(page):
    return page.evaluate("() => { const f=selFrame(selRect()); return [f.c.x,f.c.y]; }")


def test_tap_again_picks_underneath_then_drag_moves_it(page):
    pick(page, "trioList", "photo1")
    # a point on photo1 that also covers a buried shape
    pt = page.evaluate("""() => { const P=hitRects.find(h=>h.id==='photo1').r; for(let fy=0.5;fy<0.9;fy+=0.04) for(const fx of [0.5,0.35,0.65]){ const q={x:P.x+P.w*fx,y:P.y+P.h*fy}, s=hitsAt(q), same=[-4,4].every(e=>[{x:q.x+e,y:q.y},{x:q.x,y:q.y+e}].every(z=>hitsAt(z).map(h=>h.id).join()===s.map(h=>h.id).join())); if(s.length>1&&s[0].id==='photo1'&&same&&!handleAt(q)) return [q.x,q.y]; } return null; }""")
    assert pt
    stack = page.evaluate("([x,y]) => hitsAt({x,y}).map(h=>h.id)", pt)
    page.mouse.click(*client(page, *pt))  # tap the selected photo without moving
    page.wait_for_timeout(150)
    under = page.evaluate("() => SEL")
    assert under == stack[1]
    before = off(page, under).get("dx", 0)
    pt = page.evaluate("""() => { const P=hitRects.find(h=>h.id==='photo1').r; for(let fy=0.1;fy<0.95;fy+=0.03) for(const fx of [0.5,0.3,0.7]){ const q={x:P.x+P.w*fx,y:P.y+P.h*fy}, s=hitsAt(q).map(h=>h.id); if(s[0]==='photo1'&&s.includes(SEL)&&!handleAt(q)) return [q.x,q.y]; } return null; }""")
    assert pt
    drag(page, pt, (pt[0] + 60, pt[1]))  # dragging now moves the buried item, not the photo on top
    assert page.evaluate("() => SEL") == under
    assert off(page, under)["dx"] - before == 60
    assert "dx" not in off(page, "photo1")


def test_tag_follows_rotated_photo_and_moves_in_its_own_space(page):
    pick(page, "trioFeature", "photo1")
    page.evaluate("() => { state.photos.forEach(p=>p.label='Pump'); render(); }")
    page.wait_for_timeout(150)
    t0 = page.evaluate("() => hitRects.find(h=>h.id==='label_1').r")
    page.evaluate("() => { setRot('photo1',90); render(); }")
    page.wait_for_timeout(150)
    t1 = page.evaluate("() => hitRects.find(h=>h.id==='label_1').r")
    assert abs(t1["x"] - t0["x"]) > 5 or abs(t1["y"] - t0["y"]) > 5  # the tag turned with its photo
    page.evaluate("() => { SEL='label_1'; updSel(); render(); }")
    page.wait_for_timeout(150)
    c0 = frame_center(page)
    drag(page, c0, (c0[0] + 80, c0[1]))  # drag right on screen
    c1 = frame_center(page)
    assert abs(c1[0] - c0[0] - 80) <= 2 and abs(c1[1] - c0[1]) <= 2


def test_hidden_photo_leaves_no_clickable_tag(page):
    page.evaluate("() => { for(const sp of SAMPLE_PH){ if(state.photos.length>=4) break; if(!state.photos.includes(sp)) state.photos.push(sp); } state.photos.forEach(p=>p.label='Pump'); state.template='quadTags'; const m=curMap(true); m.photo0={hide:true}; render(); }")
    page.wait_for_timeout(150)
    ids = page.evaluate("() => hitRects.map(h=>h.id)")
    assert "photo0" not in ids and "label" not in ids and "label_1" in ids


def test_crop_cuts_the_photo_without_moving_it(page):
    pick(page, "showcase", "photo0")
    q0 = quad(page)
    # a strip on the left of the photo that the crop will not touch
    strip = page.evaluate("""() => { const f=selFrame(selRect()); return [Math.round(f.c.x-f.w*0.45),Math.round(f.c.y-f.h*0.3),Math.round(f.w*0.2),Math.round(f.h*0.6)]; }""")
    page.evaluate("() => { SEL=null; render(); }")
    page.wait_for_timeout(150)
    before = page.evaluate("(r) => Array.from(cx.getImageData(...r).data).join(',')", strip)
    page.evaluate("() => { SEL='photo0'; updSel(); render(); }")
    page.wait_for_timeout(150)
    page.click("#selCrop")
    page.wait_for_timeout(150)
    hx, hy = handle(page, "side", 1, 0)
    drag(page, (hx, hy), (hx - 200, hy))
    o = off(page, "photo0")
    assert o["crop"]["r"] > 0.1 and "dx" not in o and "sx" not in o  # only the edge moved
    q1 = quad(page)
    assert abs(q1[0][0] - q0[0][0]) <= 1 and q1[1][0] < q0[1][0] - 150
    assert page.is_visible("#selUncrop")
    page.evaluate("() => { SEL=null; render(); }")
    page.wait_for_timeout(150)
    after = page.evaluate("(r) => Array.from(cx.getImageData(...r).data).join(',')", strip)
    assert after == before  # the uncropped part of the photo did not move or rescale
    page.evaluate("() => { SEL='photo0'; updSel(); render(); }")
    page.wait_for_timeout(150)
    page.click("#selUncrop")
    assert "crop" not in off(page, "photo0")


def test_touch_tap_cycles(browser, base_url):
    ctx = browser.new_context(viewport={"width": 420, "height": 900}, has_touch=True, is_mobile=True)
    ctx.route("**/config.js", lambda r: r.fulfill(status=200, content_type="application/javascript", body="window.PARCO_CONFIG={users:[]};"))
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(base_url)
    pg.wait_for_function("() => typeof state==='object' && state.photos.length>0 && !document.getElementById('app').hidden")
    pick(pg, "trioList", "photo1")
    pg.locator("#cv").scroll_into_view_if_needed()
    pg.wait_for_timeout(300)
    pt = pg.evaluate("""() => { const P=hitRects.find(h=>h.id==='photo1').r; for(let fy=0.5;fy<0.9;fy+=0.04) for(const fx of [0.5,0.35,0.65]){ const q={x:P.x+P.w*fx,y:P.y+P.h*fy}, s=hitsAt(q), same=[-4,4].every(e=>[{x:q.x+e,y:q.y},{x:q.x,y:q.y+e}].every(z=>hitsAt(z).map(h=>h.id).join()===s.map(h=>h.id).join())); if(s.length>1&&s[0].id==='photo1'&&same&&!handleAt(q)) return [q.x,q.y]; } return null; }""")
    stack = pg.evaluate("([x,y]) => hitsAt({x,y}).map(h=>h.id)", pt)
    pg.locator("#cv").scroll_into_view_if_needed()
    pg.touchscreen.tap(*client(pg, *pt))
    pg.wait_for_timeout(200)
    assert pg.evaluate("() => SEL") == stack[1]
    ctx.close()
    assert not errors, errors


def test_text_box_width_handle(page):
    page.evaluate("() => { state.template='showcase'; render(); }")
    page.wait_for_timeout(150)
    page.evaluate("() => addTB('body')")
    page.wait_for_timeout(150)
    page.locator("#cv").scroll_into_view_if_needed()
    page.evaluate("() => { const b=selTB(); b.text='Write your message here and it wraps across a few lines'; render(); }")
    page.wait_for_timeout(150)
    assert page.evaluate("() => selHandles(selRect()).L.filter(k=>k.kind==='side').length") == 2
    q0 = quad(page)
    w0 = page.evaluate("() => selTB().w")
    hx, hy = handle(page, "side", 1, 0)
    drag(page, (hx, hy), (hx - 150, hy))
    assert page.evaluate("() => selTB().w") < w0 - 0.1
    assert page.evaluate("() => document.getElementById('tbW').value") == str(page.evaluate("() => selTB().w"))
    q1 = quad(page)
    assert abs(q1[0][0] - q0[0][0]) <= 2 and abs(q1[0][1] - q0[0][1]) <= 2  # top-left corner pinned


def test_everything_rotates_and_cards_only_grow(page):
    pick(page, "duoCards", "headline")
    assert page.evaluate("() => selHandles(selRect()).L.some(k=>k.kind==='rot')")
    # every part now has side handles: the headline stretches wider without moving its left edge
    q0 = quad(page)
    hx, hy = handle(page, "side", 1, 0)
    drag(page, (hx, hy), (hx + 80, hy))
    assert off(page, "headline")["sx"] > 1.05
    q1 = quad(page)
    assert abs(q1[0][0] - q0[0][0]) <= 2
    pick(page, "duoCards", "card")
    hx, hy = handle(page, "side", 1, 0)
    drag(page, (hx, hy), (hx - 120, hy))
    assert off(page, "card").get("sx", 1) == 1
    drag(page, (hx, hy), (hx + 60, hy))
    assert off(page, "card")["sx"] > 1


def test_old_saved_offsets_still_load(page):
    page.evaluate("""() => { state.photos.forEach(p=>p.label='Pump'); state.template='duoSplit'; state.format='square';
        state.offsets={duoSplit:{square:{photo0:{dx:40,s:1.1},label:{dx:10},deco_panelA:{dx:5,hide:true},headline:{font:'Oswald'}}}}; render(); }""")
    page.wait_for_timeout(200)
    ids = page.evaluate("() => hitRects.map(h=>h.id)")
    assert "photo0" in ids and "photo1" in ids and "label" in ids and "deco_panelA" not in ids


def test_tap_on_tag_of_selected_photo_selects_the_tag(page):
    pick(page, "trioFeature", "photo1")
    page.evaluate("() => { state.photos.forEach(p=>p.label='Pump'); render(); }")
    page.wait_for_timeout(150)
    pt = page.evaluate("""() => { const r=hitRects.find(h=>h.id==='label_1').r; return [r.x+r.w/2,r.y+r.h/2]; }""")
    stack = page.evaluate("([x,y]) => hitsAt({x,y}).map(h=>h.id)", pt)
    assert stack[:2] == ["label_1", "photo1"]
    assert not page.evaluate("([x,y]) => !!handleAt({x,y})", pt)
    page.mouse.click(*client(page, *pt))
    page.wait_for_timeout(150)
    assert page.evaluate("() => SEL") == "label_1"  # the top item, as before
    page.mouse.click(*client(page, *pt))
    page.wait_for_timeout(150)
    assert page.evaluate("() => SEL") == "photo1"
    page.mouse.click(*client(page, *pt))  # repeated taps keep walking down
    page.wait_for_timeout(150)
    assert page.evaluate("() => SEL") == stack[2] if len(stack) > 2 else "label_1"


def test_old_post_upgrade_keeps_tags_in_place(page):
    page.evaluate("() => { for(const sp of SAMPLE_PH){ if(state.photos.length>=4) break; if(!state.photos.includes(sp)) state.photos.push(sp); } state.photos.forEach(p=>p.label='Pump'); }")
    page.evaluate("async () => { await document.fonts.ready; await scriptFonts(); }")
    old = {"trioFeature": {"square": {"photo1": {"dx": 60, "dy": -20, "s": 1.2}, "label_1": {"dx": 15}, "photo2": {"dx": -30}}},
           "trioCircles": {"portrait": {"photo1": {"dx": 40, "s": 0.9}}}}
    for tpl, fmt in [("trioFeature", "square"), ("trioCircles", "portrait")]:
        set_format(page, fmt)
        # where the live version (tags drawn on their own) puts every tag: photo offsets do not apply to tags
        page.evaluate(f"() => {{ state.template='{tpl}'; state.offsets={{}}; render(); }}")
        page.wait_for_timeout(150)
        lab = {k: v for k, v in old[tpl][fmt].items() if k.startswith("label")}
        page.evaluate(f"() => {{ state.offsets={{'{tpl}':{{'{fmt}':{lab!r}}}}}; render(); }}".replace("True", "true"))
        page.wait_for_timeout(150)
        want = page.evaluate("() => Object.fromEntries(hitRects.filter(h=>h.id.startsWith('label')).map(h=>[h.id,h.r]))")
        page.evaluate(f"() => {{ state.layoutV=1; state.offsets={old!r}; migrateTags(); render(); }}")
        page.wait_for_timeout(150)
        assert page.evaluate("() => state.layoutV") == 2
        got = page.evaluate("() => Object.fromEntries(hitRects.filter(h=>h.id.startsWith('label')).map(h=>[h.id,h.r]))")
        assert set(got) == set(want)
        for k in want:
            for a in "xywh":
                assert abs(got[k][a] - want[k][a]) <= 1.5, (tpl, k, a, got[k], want[k])


def test_small_parts_get_side_handles_outside_and_still_move(page):
    pick(page, "brandHero", "phoneicon")
    f = page.evaluate("() => { const F=selFrame(selRect()); return [F.w,F.h]; }")
    sides = page.evaluate("() => selHandles(selRect()).L.filter(k=>k.kind==='side').length")
    assert sides == 4
    # pressing in the middle of the small icon moves it rather than grabbing a handle
    c = page.evaluate("() => { const F=selFrame(selRect()); return [F.c.x,F.c.y]; }")
    assert not page.evaluate("([x,y]) => !!handleAt({x,y})", c)
    hx, hy = handle(page, "side", 1, 0)
    drag(page, (hx, hy), (hx + 40, hy))
    assert off(page, "phoneicon")["sx"] > 1.2


def test_photo_stretch_or_crop(page):
    pick(page, "showcase", "photo0")
    assert page.is_visible("#selStretch") and page.is_visible("#selCrop")
    assert page.get_attribute("#selStretch", "aria-pressed") == "true"
    q0 = quad(page)
    hx, hy = handle(page, "side", 1, 0)
    drag(page, (hx, hy), (hx + 100, hy))
    o = off(page, "photo0")
    assert o.get("warp") is True and o["sx"] > 1.1 and not o.get("crop")
    q1 = quad(page)
    assert (q1[1][0] - q1[0][0]) > (q0[1][0] - q0[0][0]) + 70   # the photo itself got wider
    page.click("#selCrop")
    assert page.get_attribute("#selCrop", "aria-pressed") == "true" and page.get_attribute("#selStretch", "aria-pressed") == "false"
    hx, hy = handle(page, "side", -1, 0)
    sx = off(page, "photo0")["sx"]
    drag(page, (hx, hy), (hx + 60, hy))
    o = off(page, "photo0")
    assert o["crop"]["l"] > 0.02 and o["sx"] == sx
    page.click("#selStretch")
    assert page.get_attribute("#selStretch", "aria-pressed") == "true"
