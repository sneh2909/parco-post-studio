"""Extra design looks: each paints its own background and reuses a base look's layout colours."""
from conftest import FORMATS, set_format, shot

NEW = ["blueprint", "graphite", "carbon", "vivid", "steel"]
COLOUR = {"green": "forest", "greenNight": "forest", "navyLight": "navy", "tealLight": "teal", "maroonLight": "maroon"}


def canvas_hash(page):
    return page.evaluate("() => { const d=cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data; let h=0; for(let i=0;i<d.length;i+=97) h=(h*31+d[i])|0; return h; }")


def test_looks_buttons_and_every_template(page):
    keys = page.evaluate("() => [...document.querySelectorAll('#looks [data-look]')].map(b=>b.dataset.look)")
    assert keys[0] == "auto" and set(NEW) <= set(keys) and set(COLOUR) <= set(keys) and len(keys) == 14
    assert "studio" not in keys and "catalogue" not in keys
    tpls = page.evaluate("() => Object.keys(TEMPLATES)")
    for look in NEW + list(COLOUR):
        page.evaluate(f"() => document.querySelector('[data-look={look}]').click()")
        assert page.evaluate("() => state.look") == look
        if look in COLOUR:  # colour looks also pick their colours
            assert page.evaluate("() => state.theme") == COLOUR[look]
            assert page.evaluate("() => state.colors.ink") == page.evaluate(f"() => THEMES['{COLOUR[look]}'].ink")
        for t in tpls:
            page.evaluate(f"() => {{ state.template='{t}'; render(); }}")
        assert page.evaluate("() => LOOK") == "classic"  # restored after rendering


def test_new_looks_differ_from_their_base(page):
    page.evaluate("() => { state.template='brandHero'; render(); }")
    for fmt in FORMATS:
        set_format(page, fmt)
        seen = {}
        for look in ["classic", "night", "site"] + NEW + list(COLOUR):
            page.evaluate("() => document.querySelector('[data-th=parco]').click()")
            page.evaluate(f"() => {{ document.querySelector('[data-look={look}]').click(); render(); }}")
            page.wait_for_timeout(60)
            seen[look] = canvas_hash(page)
            shot(page, f"look-{look}-{fmt}")
        assert len(set(seen.values())) == len(seen)
        for look in NEW + list(COLOUR):
            base = page.evaluate(f"() => LOOKS['{look}'].base")
            assert base in ("classic", "night", "site")


def test_ideas_offer_new_looks(page):
    page.evaluate("() => AI.set(null)")
    looks = page.evaluate("async () => { const out=[]; for(let i=0;i<4;i++){ const r=await getIdeas(); r.list.forEach(d=>{ out.push(d.look); ideaSeen.push(d); }); } return out; }")
    assert any(l not in ("classic", "night", "site") for l in looks)
