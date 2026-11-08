"""Stretch (side handles), rotation (round handle) and selectable template shapes."""
import math

from conftest import FORMATS, set_format, shot


def pick(page, template, sel):
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
