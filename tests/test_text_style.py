"""Word-like text styles: whole text or picked words, in every size, undoable, and stale styles drop when the text changes."""
from conftest import FORMATS, set_format, shot

SETUP = """async () => { await document.fonts.ready; state.template='brandHero'; Object.assign(state,{theme:'forest',colors:{...THEMES.forest},look:'classic'});
  state.text.headline='Oil Cooler Assembly Hino J05E'; SEL=null; updSel(); render(); }"""


def pick(page, sel):
    page.evaluate(f"() => {{ SEL='{sel}'; updSel(); render(); }}")
    page.wait_for_timeout(250)


def pixels(page, rect):
    return page.evaluate("(r) => Array.from(cx.getImageData(Math.round(r.x),Math.round(r.y),Math.max(1,Math.round(r.w)),Math.max(1,Math.round(r.h))).data).join(',')", rect)


def rect(page, id_):
    return page.evaluate(f"() => hitRects.find(h=>h.id==='{id_}').r")


def test_toolbar_shows_words_for_text_only(page):
    page.evaluate(SETUP); page.wait_for_timeout(200)
    pick(page, "headline")
    assert page.is_visible("#tsCtl")
    words = page.evaluate("() => [...document.querySelectorAll('#tsWords button')].map(b=>b.textContent)")
    assert words == ["Whole text", "OIL", "COOLER", "ASSEMBLY", "HINO", "J05E"]
    pick(page, "photo0")
    assert not page.is_visible("#tsCtl")
    pick(page, "phones")  # contact numbers are text too
    assert page.is_visible("#tsCtl") and "+91" in page.inner_text("#tsWords")


def test_one_word_bold_colour_in_every_size_and_undo(page):
    page.evaluate(SETUP); page.wait_for_timeout(200)
    pick(page, "headline")
    page.evaluate("() => { SEL=null; render(); }"); page.wait_for_timeout(200)
    r = rect(page, "headline"); before = pixels(page, r)
    pick(page, "headline")
    page.click("#tsWords [data-tsw='4']")
    page.click("#tsB")
    page.select_option("#tsColor", "pop")
    ts = page.evaluate("() => curMap(false).headline.ts")
    assert ts["w"]["4"]["t"] == "J05E" and ts["w"]["4"]["b"] is True and ts["w"]["4"]["color"] == "pop" and not ts.get("all")
    for f in FORMATS:
        assert page.evaluate(f"() => state.offsets.brandHero['{f}'].headline.ts.w['4'].color") == "pop"
    page.evaluate("() => { SEL=null; render(); }"); page.wait_for_timeout(250)
    after = pixels(page, r)
    assert after != before
    # only the last word changed: the left half of the headline is identical
    left = {**r, "w": r["w"] * 0.45}
    page.evaluate("() => { const m=curMap(false); m._ts=m.headline.ts; delete m.headline.ts; render(); }"); page.wait_for_timeout(250)
    plain_left = pixels(page, left)
    page.evaluate("() => { const m=curMap(false); m.headline.ts=m._ts; delete m._ts; render(); }"); page.wait_for_timeout(250)
    assert pixels(page, left) == plain_left
    set_format(page, "story"); page.wait_for_timeout(200)
    shot(page, "textstyle-story")
    page.click("#undoBtn"); page.click("#undoBtn")
    assert not page.evaluate("() => ((curMap(false)||{}).headline||{}).ts")


def test_whole_text_preset_copy_paste_and_clear(page):
    page.evaluate(SETUP); page.wait_for_timeout(200)
    pick(page, "fitment")
    page.select_option("#tsPreset", "hlpop")
    assert page.evaluate("() => curMap(false).fitment.ts.all") == {"hl": "pop", "color": "white"}
    page.click("#tsCopy")
    pick(page, "ftext")
    page.click("#tsPaste")
    assert page.evaluate("() => curMap(false).ftext.ts.all") == {"hl": "pop", "color": "white"}
    page.click("#tsClear")
    assert not page.evaluate("() => (curMap(false).ftext||{}).ts")


def test_changed_text_drops_stale_word_style(page):
    page.evaluate(SETUP); page.wait_for_timeout(200)
    pick(page, "headline")
    page.click("#tsWords [data-tsw='4']"); page.click("#tsU")
    page.evaluate("() => { SEL=null; state.text.headline='Oil Cooler Assembly Hino Long'; render(); }"); page.wait_for_timeout(250)
    r = rect(page, "headline"); styled = pixels(page, r)
    page.evaluate("() => { delete curMap(false).headline.ts; render(); }"); page.wait_for_timeout(250)
    assert pixels(page, r) == styled  # J05E's underline does not jump onto the new word


def test_text_box_words(page):
    page.evaluate(SETUP); page.wait_for_timeout(200)
    page.evaluate("() => { addTB('body'); }"); page.wait_for_timeout(250)
    sel = page.evaluate("() => SEL")
    assert sel.startswith("tb_") and page.is_visible("#tsCtl")
    page.click("#tsWords button:nth-child(2)"); page.click("#tsI")
    assert any(v.get("i") for v in page.evaluate(f"() => Object.values(curMap(false)['{sel}'].ts.w)"))
