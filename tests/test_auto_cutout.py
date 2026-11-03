"""Feature 3: automatic background removal for messy photos.

The ONNX model is replaced by a stub (aiProbability) so tests are fast and offline;
test_real_model runs the bundled model once (needs the jsDelivr CDN).
"""
import os
import pytest
from conftest import FORMATS, set_format, shot

# makes test images in the page: 'messy' = random noisy background, 'white', 'plain' (one colour), 'png' (transparent)
MAKE = """async (kind) => { const c=document.createElement('canvas'); c.width=400; c.height=300; const x=c.getContext('2d');
  if(kind==='messy'){ for(let i=0;i<400;i+=20) for(let j=0;j<300;j+=20){ x.fillStyle=`hsl(${(i*7+j*13)%360},60%,${30+(i+j)%50}%)`; x.fillRect(i,j,20,20); } }
  else if(kind==='white'){ x.fillStyle='#fbfbfb'; x.fillRect(0,0,400,300); }
  else if(kind==='plain'){ x.fillStyle='#3b6ea8'; x.fillRect(0,0,400,300); }
  x.fillStyle='#222'; x.beginPath(); x.arc(200,150,90,0,7); x.fill();
  const b=await new Promise(r=>c.toBlob(r,'image/png')); return new File([b],kind+'.png',{type:'image/png'}); }"""

STUB = """() => { window.__cutCalls=0; window.aiProbability = async (src,cv,msg) => { window.__cutCalls++; msg('Downloading the AI model (part 1 of 3, first time only)…');
  await new Promise(r=>setTimeout(r,150)); if(window.__cutFail) throw new Error('model failed');
  const {w,h}=src, p=new Float32Array(w*h); for(let y=0;y<h;y++) for(let x=0;x<w;x++){ const dx=x-w/2, dy=y-h/2; p[y*w+x]=dx*dx+dy*dy<(h*0.3)**2?1:0; } return p; }; }"""


def add(page, *kinds):
    page.evaluate(f"""async () => {{ const mk={MAKE}; const fs=[]; for(const k of {list(kinds)!r}) fs.push(await mk(k)); await addFiles(fs); }}""")


def test_detects_messy_photos(page):
    r = page.evaluate(f"""async () => {{ const mk={MAKE}; const out={{}};
        for(const k of ['messy','white','plain']){{ const f=await mk(k); const img=await loadImg(URL.createObjectURL(f)); out[k]=isMessy(img); }}
        for(const k of Object.keys(ASSETS.photos)) out['sample_'+k]=isMessy(await loadImg(ASSETS.photos[k].src)); return out; }}""")
    assert r["messy"] and not r["white"] and not r["plain"], r
    print({k: v for k, v in r.items() if k.startswith("sample_")})


def test_hint_clean_revert_and_undo(page):
    page.evaluate(STUB)
    add(page, "white", "messy")
    page.wait_for_selector("#cutHint:not([hidden])")
    assert "Photo 3 has a busy background" in page.inner_text("#cutHint")  # sample photo is 1, white is 2
    assert page.evaluate("() => window.__cutCalls") == 0  # no auto-run unless asked
    page.click("#cutAuto")
    page.wait_for_function("() => state.photos[2].orig && state.photos[2].png")
    ph = page.evaluate("() => ({png: state.photos[2].png, w: state.photos[2].img.width, h: state.photos[2].img.height})")
    assert ph["png"] and ph["w"] < 400 and ph["h"] < 300  # trimmed to the product
    assert page.is_hidden("#cutHint")
    for fmt in FORMATS:
        set_format(page, fmt); shot(page, f"f3-clean-{fmt}")
    page.click("#undoBtn")
    page.wait_for_function("() => !state.photos[2].orig")
    assert page.is_hidden("#cutHint")  # undone photo is not offered again
    page.evaluate("() => { state.photos[2].cutDismissed=false; queueCut([state.photos[2].uid]); }")
    page.wait_for_function("() => !!state.photos[2].orig")
    page.click("[data-uncut='2']")  # one-click revert
    page.wait_for_function("() => !state.photos[2].orig")


def test_auto_setting_runs_a_queue(page):
    page.evaluate(STUB)
    page.evaluate("() => localStorage.setItem('parco-autocut','1')")
    add(page, "messy", "messy", "plain")
    page.wait_for_function("() => document.getElementById('cutHint').textContent.includes('of 2')")
    assert "Downloading the AI model" in page.inner_text("#cutHint")
    page.wait_for_function("() => state.photos.filter(p=>p.orig).length===2 && !cutQBusy")
    assert page.evaluate("() => window.__cutCalls") == 2 and page.evaluate("() => !state.photos[3].orig")


def test_failure_opens_manual_dialog(page):
    page.evaluate(STUB)
    page.evaluate("() => { window.__cutFail=true; }")
    add(page, "messy")
    page.click("#cutAuto")
    page.wait_for_selector("#cutModal:not([hidden])")
    assert page.evaluate("() => cutIdx") == 1 and page.is_hidden("#cutHint")


@pytest.mark.skipif(os.environ.get("SKIP_MODEL") == "1", reason="model test disabled")
def test_real_model(page):
    page.set_default_timeout(180_000)
    add(page, "messy")
    r = page.evaluate("""async () => { const msgs=[]; const b=await cutoutPhoto(state.photos[1].img, m=>msgs.push(m)); const img=await loadImg(URL.createObjectURL(b));
        return {type:b.type, alpha:hasAlpha(img), w:img.width, msgs}; }""")
    assert r["type"] == "image/png" and r["alpha"] and r["msgs"], r
