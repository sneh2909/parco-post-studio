"""Feature 1: AI-placed decorations and tags on design ideas."""
from conftest import FORMATS, set_format, shot

WRITEUP = "CGP brand water pump, part no. 1234344, for Greaves CIFA and Conmat transit mixers. Supply across India."


def idea(template, look, decos, tags):
    return {"name": f"{template} {look}", "template": template, "look": look, "theme": "parco", "head": "Oswald",
            "body": "Barlow", "foot": "band", "why": "test", "decos": decos, "tags": tags}


MESSY = idea("showcase", "classic",
             decos=[{"type": "gear", "color": "pop", "x": 0.9, "y": 0.12, "w": 0.15, "rot": 20, "back": False},
                    {"type": "dots", "color": "purple", "x": 2, "y": -1, "w": 3, "rot": 400, "back": True},  # bad colour, out of range
                    {"type": "unicorn", "color": "pop", "x": 0.5, "y": 0.5, "w": 0.2},                      # unknown type: dropped
                    {"type": "ring", "color": "ink", "x": 0.1, "y": 0.9, "w": 0.1},
                    {"type": "sparkle", "color": "accent", "x": 0.2, "y": 0.2, "w": 0.1},
                    {"type": "line", "color": "blue", "x": 0.5, "y": 0.6, "w": 0.3}],                       # 5th valid: over the cap
             tags=[{"text": "Flat 20% off", "preset": "pill", "x": 0.5, "y": 0.1},
                   {"text": "Ready stock", "preset": "slant", "x": 0.5, "y": 0.1},                         # not in write-up
                   {"text": "Rs 500 only", "preset": "pill", "x": 0.5, "y": 0.1},
                   {"text": "Part No. 1234344", "preset": "neon", "x": -3, "y": 0.99},                     # bad preset, clamped
                   {"text": "Greaves CIFA", "preset": "pill", "x": 0.7, "y": 0.2},
                   {"text": "Conmat", "preset": "pill", "x": 0.3, "y": 0.2}])                              # over the cap

IDEAS = {"ideas": [MESSY, idea("specsheet", "night", [{"type": "orb", "color": "blue", "x": 0.8, "y": 0.3, "w": 0.4, "back": True}], []),
                   idea("ribbon", "site", [], [{"text": "Transit mixers", "preset": "head", "x": 0.5, "y": 0.05}])]}


def setup(page, ai):
    ai.handler = lambda p: IDEAS
    page.evaluate(f"() => {{ state.writeup={WRITEUP!r}; state.product='CGP water pump'; }}")


def test_validation_rules(page, ai):
    setup(page, ai)
    r = page.evaluate("async () => (await getIdeas()).list")
    d = r[0]
    assert len(d["decos"]) == 4
    assert [x["type"] for x in d["decos"]] == ["gear", "dots", "ring", "sparkle"]
    dots = d["decos"][1]
    assert dots["color"] == "pop" and dots["x"] == 1 and dots["y"] == 0 and dots["w"] == 0.6 and dots["rot"] == 45 and dots["back"] is True
    assert [t["text"] for t in d["tags"]] == ["Part No. 1234344", "Greaves CIFA"]
    assert d["tags"][0]["preset"] == "pill" and d["tags"][0]["x"] == 0.3 and d["tags"][0]["y"] == 0.82
    assert "Decorations" in ai.calls[-1] and "Ready stock" in ai.calls[-1]


def test_price_filter_and_ready_stock(page):
    ok = page.evaluate("""() => ['₹999','Rs. 450','Rs500','10% OFF','Big sale','Best price','Special offer','Discounted','Buy now','Great deals']
        .map(t=>tagAllowed(t,'₹999 Rs. 450 Rs500 10% off big sale best price special offer discounted buy now great deals'))""")
    assert not any(ok)
    assert page.evaluate("() => tagAllowed('Ready stock','Ready stock in Ahmedabad')")
    assert not page.evaluate("() => tagAllowed('Ready stock','Stock in Ahmedabad')")
    assert page.evaluate("() => tagAllowed('Dealer enquiries','Dealer enquiry welcome')") is False  # word not in write-up
    assert page.evaluate("() => tagAllowed('Dealers welcome','Dealer enquiries welcome')")
    assert page.evaluate("() => tagAllowed('पानी पंप','पानी पंप स्टॉक में')")


def test_preview_apply_undo_all_sizes(page, ai):
    setup(page, ai)
    # a user-added text box must survive applying an idea
    page.evaluate("() => { state.template='showcase'; addTB('body'); }")
    before = page.evaluate("() => JSON.stringify({d:state.decos,t:state.texts,tpl:state.template,th:state.theme})")
    page.click("#ideasBtn")
    page.wait_for_selector("#ideasGrid .idea canvas")
    assert "2 tags" in page.inner_text("#ideasGrid .idea:first-child small")
    # preview canvases differ between idea 1 (with decos) and the same idea without
    page.click("#ideasGrid .idea:first-child .btn")
    st = page.evaluate("() => ({decos:state.decos.showcase, texts:state.texts.showcase})")
    for fmt in FORMATS:
        lst = st["decos"][fmt]
        assert len(lst) == 4 and all(x["ai"] for x in lst)
        W, H = page.evaluate(f"() => [FORMATS['{fmt}'].w, FORMATS['{fmt}'].h]")
        for x in lst:  # same shape as addDeco, and fully on the post
            assert set(["id", "type", "x", "y", "w", "h", "color", "op", "rot", "k", "n", "back"]) <= set(x)
            assert 0 <= x["x"] and x["x"] + x["w"] <= W and 0 <= x["y"] and x["y"] + x["h"] <= H
    texts = st["texts"]
    assert len(texts) == 3 and not texts[0].get("ai") and [t["text"] for t in texts[1:]] == ["Part No. 1234344", "Greaves CIFA"]
    assert set(["id", "text", "size", "font", "bold", "bg", "color", "w", "align", "x", "y", "op"]) <= set(texts[1])
    for fmt in FORMATS:
        set_format(page, fmt)
        shot(page, f"f1-idea-{fmt}")
        hits = page.evaluate("() => hitRects.filter(h=>h.kind==='el').map(h=>h.id)")
        assert sum(h.startswith("add_ai") for h in hits) == 4 and sum(h.startswith("tb_ai") for h in hits) == 2
    # applying another idea replaces the AI items, keeps the user's
    page.click("#ideasBtn"); page.wait_for_selector("#ideasGrid .idea canvas")
    page.click("#ideasGrid .idea:first-child .btn")
    assert page.evaluate("() => state.texts.showcase.length") == 3
    page.click("#undoBtn")
    page.click("#undoBtn")
    after = page.evaluate("() => JSON.stringify({d:state.decos,t:state.texts,tpl:state.template,th:state.theme})")
    assert after == before


def test_no_key_falls_back(page, ai):
    page.evaluate("() => AI.set(null)")
    r = page.evaluate("async () => await getIdeas()")
    assert r["ai"] is False and len(r["list"]) == 3 and not ai.calls
