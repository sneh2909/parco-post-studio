"""Feature 2: one-click captions in English, Hinglish, Hindi, Gujarati."""
import json, re
from conftest import FORMATS, set_format, shot

REPLIES = {
    "Hindi": {"caption": "CGP water pump अब Ahmedabad में उपलब्ध है। WhatsApp पर पूछें: +91 63527 76505", "hashtags": "#PARCO #WaterPump",
              "whatsapp": "CGP water pump — पूछताछ: +91 63527 76505",
              "post": {"eyebrow": "स्टॉक में", "headline": "CGP वॉटर पंप", "subhead": "ट्रांजिट मिक्सर के लिए मज़बूत", "category": "ट्रांजिट मिक्सर पार्ट्स",
                       "cta": "WhatsApp पर पूछें", "bullets": ["Ahmedabad में स्टॉक", "पूरे भारत में सप्लाई", "डीलर पूछताछ का स्वागत"]}},
    "Gujarati": {"caption": "CGP water pump હવે Ahmedabad માં ઉપલબ્ધ છે. WhatsApp: +91 63527 76505", "hashtags": "#PARCO #WaterPump",
                 "whatsapp": "CGP water pump — પૂછપરછ: +91 63527 76505",
                 "post": {"eyebrow": "સ્ટોકમાં", "headline": "CGP વોટર પંપ", "subhead": "ટ્રાન્ઝિટ મિક્સર માટે મજબૂત", "category": "ટ્રાન્ઝિટ મિક્સર સ્પેર્સ",
                          "cta": "WhatsApp પર પૂછો", "bullets": ["Ahmedabad માં સ્ટોક", "આખા ભારતમાં સપ્લાય", "ડીલર પૂછપરછ આવકાર્ય"]}},
    "Hinglish": {"caption": "CGP water pump ab Ahmedabad mein ready. WhatsApp karein: +91 63527 76505", "hashtags": "#PARCO", "whatsapp": "Enquire: +91 63527 76505"},
}


def handler(prompt):
    lang = re.search(r"- Language: (\w+)\.", prompt).group(1)
    r = dict(REPLIES[lang])
    if '"post"' not in prompt:
        r.pop("post", None)
    return r


def open_caption(page, ai):
    ai.handler = handler
    page.click("[data-tab=caption]")


def test_switching_keeps_edits_and_only_asks_once(page, ai):
    open_caption(page, ai)
    english = page.input_value("#caption")
    page.fill("#caption", english + " EDITED")
    page.click("[data-cl=Hindi]")
    page.wait_for_function("() => state.capLang==='Hindi'")
    assert "उपलब्ध" in page.input_value("#caption")
    p = ai.calls[-1]
    assert "Hindi in Devanagari script" in p and "keep part names, brand names, machine names and part numbers in English" in p
    assert '"caption"' in p and '"post"' not in p
    page.fill("#caption", "हिंदी EDITED")
    page.click("[data-cl=English]")
    page.wait_for_function("() => state.capLang==='English'")
    assert page.input_value("#caption").endswith(" EDITED")
    page.click("[data-cl=Hindi]")
    page.wait_for_function("() => state.capLang==='Hindi'")
    assert page.input_value("#caption") == "हिंदी EDITED" and len(ai.calls) == 1
    assert page.inner_text("#capLangs").count("Ready") == 2
    page.click("#capRegen")
    page.wait_for_function("() => document.getElementById('caption').value.includes('उपलब्ध')")
    assert len(ai.calls) == 2


def test_saved_posts_and_backup_keep_versions(page, ai):
    open_caption(page, ai)
    page.click("[data-cl=Gujarati]"); page.wait_for_function("() => state.capLang==='Gujarati'")
    page.click("#save"); page.wait_for_function("() => !!state.libId && !document.getElementById('save').disabled")
    saved = page.evaluate("async () => (await LOCAL.db.collection('posts').doc(state.libId).get()).data()")
    assert set(saved["captions"]) == {"English", "Gujarati"} and saved["capLang"] == "Gujarati"
    with page.expect_download() as dl:
        page.click("#libExport")
    data = json.loads(open(dl.value.path(), encoding="utf-8").read())
    assert data["posts"][0]["data"]["captions"]["Gujarati"]["caption"].startswith("CGP water pump હવે")
    page.click("#newPost")
    assert page.evaluate("() => Object.keys(state.captions).length") == 0
    page.click("[data-open]"); page.wait_for_function("() => !!state.libId")
    page.click("[data-tab=caption]")
    assert page.evaluate("() => Object.keys(state.captions).sort()") == ["English", "Gujarati"]


def test_no_key(page, ai):
    page.evaluate("() => AI.set(null)")
    open_caption(page, ai)
    page.click("[data-cl=Hindi]")
    page.wait_for_function("() => document.getElementById('capStatus').textContent.includes('AI is off')")
    assert page.evaluate("() => state.capLang") == "English" and not ai.calls


def test_translate_post_text_renders_and_fits(page, ai):
    open_caption(page, ai)
    page.check("#capPost")
    for lang, word, font in [("Hindi", "वॉटर", "Noto Sans Devanagari"), ("Gujarati", "વોટર", "Noto Sans Gujarati")]:
        page.click(f"[data-cl={lang}]")
        page.wait_for_function(f"() => state.capLang==='{lang}' && state.text.headline.includes('{word}')")
        assert page.evaluate(f"() => document.fonts.check('800 40px \"{font}\"', '{word}')")
        for tpl in ["showcase", "ribbon"]:
            page.evaluate(f"() => {{ state.template='{tpl}'; syncUI(); render(); }}")
            for fmt in FORMATS:
                set_format(page, fmt)
                W, H = page.evaluate(f"() => [FORMATS['{fmt}'].w, FORMATS['{fmt}'].h]")
                rects = page.evaluate("() => hitRects.filter(h=>h.kind==='el').map(h=>({id:h.id,...h.r}))")
                assert rects
                for r in rects:  # every text item stays on the post
                    assert r["x"] >= -4 and r["x"] + r["w"] <= W + 4 and r["y"] >= -4 and r["y"] + r["h"] <= H + 4, (lang, tpl, fmt, r)
                shot(page, f"f2-{lang}-{tpl}-{fmt}")
    # going back to English restores the original post text
    page.click("[data-cl=English]")
    page.wait_for_function("() => state.text.headline==='Water Pump'")
