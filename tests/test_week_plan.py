"""Feature 4: plan a week of posts (content calendar)."""
import csv, io, json, re, zipfile
from conftest import FORMATS

PRODUCTS = """CGP water pump: CGP brand water pump, part no. 1234344, for Greaves CIFA and Conmat transit mixers. Ready stock in Ahmedabad.
Hydraulic pump - Hydraulic pump for Schwing Stetter concrete pumps, supply across India.
Mixer roller: Support roller for transit mixer drums."""

PLAN = {"posts": [
    {"day": 2, "product": "Hydraulic pump", "angle": "dealer enquiry", "template": "ribbon", "eyebrow": "Ready stock", "headline": "Hydraulic Pump",
     "subhead": "For Schwing Stetter pumps", "category": "Concrete pump spares", "compat": "Schwing Stetter", "cta": "Enquire on WhatsApp",
     "bullets": ["Supply across India"], "specs": [{"label": "Application", "value": "Schwing Stetter"}]},
    {"day": 1, "product": "cgp water pump", "angle": "stock", "template": "showcase", "eyebrow": "Ready stock", "headline": "CGP Water Pump",
     "subhead": "Flat 10% off this week", "category": "Transit mixer spares", "compat": "Greaves CIFA | Conmat", "cta": "Enquire now",
     "bullets": ["Part No. 1234344"], "specs": [{"label": "Part No.", "value": "1234344"}]},
    {"day": 3, "product": "Mixer roller", "angle": "viral", "template": "quadGrid", "headline": "Support Roller", "bullets": []},
    {"day": 4, "product": "Unknown thing", "angle": "stock", "template": "showcase", "headline": "Nope"},
]}


def handler(calls):
    def h(prompt):
        if "You plan a week" in prompt:
            return PLAN
        prod = re.search(r"Product name: (.+)", prompt).group(1)
        calls.append(prod)
        if prod == "Mixer roller" and calls.count(prod) == 1:
            return 429
        return {"caption": f"Caption for {prod}, enquire on WhatsApp +91 63527 76505", "hashtags": "#PARCO", "whatsapp": f"{prod} enquiries: +91 63527 76505"}
    return h


def plan(page, ai):
    caps = []
    ai.handler = handler(caps)
    page.evaluate("() => { WEEK_PACE.gap=0; WEEK_PACE.wait=50; }")
    page.click("#weekBtn")
    page.fill("#wkList", PRODUCTS)
    page.select_option("#wkN", "5")
    page.fill("#wkStart", "2026-11-09")
    page.click("#wkPlan")
    page.wait_for_selector("#wkCal .wk-row")
    return caps


def test_plan_is_one_call_and_validated(page, ai):
    caps = plan(page, ai)
    assert len(ai.calls) == 1 and not caps
    p = ai.calls[0]
    assert "1. CGP water pump: CGP brand water pump" in p and "2. Hydraulic pump: Hydraulic pump for Schwing" in p and "Plan 5 posts" in p
    wk = page.evaluate("() => WK.entries.map(e=>({date:e.date,product:e.product,angle:e.angle,template:e.template,sub:e.text.sub,sample:e.sample,hasPhoto:!!e.photo}))")
    assert [e["product"] for e in wk] == ["CGP water pump", "Hydraulic pump", "Mixer roller"]  # sorted by day, unknown product dropped
    assert [e["date"] for e in wk] == ["2026-11-09", "2026-11-10", "2026-11-11"]
    assert wk[0]["sub"] == "" and wk[2]["angle"] == "fitment" and wk[2]["template"] in ("showcase", "specsheet", "ribbon")
    assert all(e["sample"] and e["hasPhoto"] for e in wk)  # no uploaded photos: sample photos, flagged
    assert page.locator(".wk-flag").count() == 3
    keys = page.evaluate("() => WK.entries.map(e=>e.sampleKey)")
    assert keys[0] == "cgp" and keys[1] == "hydpumps"  # closest sample by name; weak matches rotate


def test_drafts_lazy_captions_and_export(page, ai, tmp_path):
    caps = plan(page, ai)
    page.click("#wkDrafts")
    page.wait_for_function("() => WK.entries.every(e=>e.libId) && !wkBusy")
    docs = page.evaluate("async () => (await LOCAL.db.collection('posts').get()).docs.map(d=>d.data())")
    assert len(docs) == 3 and all(d["draft"] and d["scheduledAt"] for d in docs) and not any(d["caption"] for d in docs)
    hyd = next(d for d in docs if d["product"] == "Hydraulic pump")
    assert not any("stock" in b["label"].lower() for b in hyd["badges"])  # no stock claim when the write-up has none
    assert hyd["text"]["compat"] == "Schwing Stetter" and hyd["text"]["eyebrow"] == ""  # stock line not in its write-up
    page.wait_for_selector("#lib .card")
    assert "Draft" in page.inner_text("#lib") and "📅" in page.inner_text("#lib")
    # one caption on its own, then the rest lazily on export (with one 429 retried)
    page.click("[data-wkcap='1']")
    page.wait_for_function("() => !!WK.entries[1].caption && !wkBusy")
    assert caps == ["Hydraulic pump"]
    with page.expect_download(timeout=60000) as dl:
        page.click("#wkExport")
    assert caps == ["Hydraulic pump", "CGP water pump", "Mixer roller", "Mixer roller"]
    z = zipfile.ZipFile(dl.value.path())
    names = z.namelist()
    assert len([n for n in names if n.endswith(".png")]) == 9 and "captions.csv" in names
    assert z.testzip() is None
    for n in names:
        if n.endswith(".png"):
            data = z.read(n)
            w, h = int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
            fmt = n.rsplit("-", 1)[1][:-4]
            assert data[:8] == b"\x89PNG\r\n\x1a\n" and (w, h) == {"square": (1080, 1080), "portrait": (1080, 1350), "story": (1080, 1920)}[fmt]
            (tmp_path / n).write_bytes(data)
    rows = list(csv.DictReader(io.StringIO(z.read("captions.csv").decode("utf-8-sig"))))
    assert [r["date"] for r in rows] == ["2026-11-09", "2026-11-10", "2026-11-11"]
    assert rows[1]["caption"].startswith("Caption for Hydraulic pump") and rows[0]["sample_photo"] == "yes"
    docs = page.evaluate("async () => (await LOCAL.db.collection('posts').get()).docs.map(d=>d.data())")
    assert all(d["caption"] for d in docs)  # captions written into the drafts too
    import shutil, pathlib
    out = pathlib.Path(__file__).parent / "out"; out.mkdir(exist_ok=True)
    for n in names:
        if n.startswith("2026-11-09") or n.startswith("2026-11-10"):
            shutil.copy(tmp_path / n, out / ("f4-" + n))


def test_photo_upload_clears_flag(page, ai):
    plan(page, ai)
    page.evaluate("""async () => { const c=document.createElement('canvas'); c.width=200; c.height=200; const x=c.getContext('2d'); x.fillStyle='#fff'; x.fillRect(0,0,200,200); x.fillStyle='#333'; x.fillRect(50,50,100,100);
        const b=await new Promise(r=>c.toBlob(r,'image/png')); const dt=new DataTransfer(); dt.items.add(new File([b],'p.png',{type:'image/png'}));
        const inp=document.getElementById('wkPh0'); inp.files=dt.files; inp.dispatchEvent(new Event('change',{bubbles:true})); }""")
    page.wait_for_function("() => !WK.entries[0].sample")
    assert page.locator(".wk-flag").count() == 2


def test_no_key(page, ai):
    page.evaluate("() => AI.set(null)")
    page.click("#weekBtn"); page.fill("#wkList", PRODUCTS); page.click("#wkPlan")
    page.wait_for_function("() => document.getElementById('wkMsg').textContent.includes('AI is off')")
    assert not ai.calls
