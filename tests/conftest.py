"""Playwright harness: serves the repo over HTTP and mocks the AI provider (no real keys, no network AI calls).

Run:  pip install pytest playwright && python -m playwright install chromium
      python -m pytest tests -q
Screenshots of every size go to tests/out/ (gitignored) for a visual check.
"""
import functools, http.server, json, socketserver, threading
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "out"
FORMATS = ["square", "portrait", "story"]


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@pytest.fixture(scope="session")
def base_url():
    handler = functools.partial(_Quiet, directory=str(ROOT))
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/"
    srv.shutdown()


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


class FakeAI:
    """Answers Gemini generateContent calls. `handler(prompt) -> dict` builds the JSON reply."""

    def __init__(self):
        self.calls = []
        self.handler = lambda prompt: {}

    def route(self, route):
        body = json.loads(route.request.post_data or "{}")
        prompt = "".join(p.get("text", "") for c in body.get("contents", []) for p in c.get("parts", []))
        self.calls.append(prompt)
        reply = self.handler(prompt)
        if isinstance(reply, int):
            return route.fulfill(status=reply, content_type="application/json", body=json.dumps({"error": {"message": "mock error"}}))
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(reply)}]}}]}))


@pytest.fixture
def ai():
    return FakeAI()


@pytest.fixture
def page(browser, base_url, ai):
    ctx = browser.new_context(viewport={"width": 1400, "height": 1000}, accept_downloads=True)
    ctx.add_init_script("localStorage.setItem('parco-ai-v1', JSON.stringify({provider:'gemini', key:'test-key', model:''}))")
    ctx.route("https://generativelanguage.googleapis.com/**", ai.route)
    ctx.route("https://api.anthropic.com/**", lambda r: r.abort())
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(base_url)
    pg.wait_for_function("() => typeof state==='object' && state.photos.length>0 && !document.getElementById('app').hidden")
    yield pg
    ctx.close()
    assert not errors, f"page errors: {errors}"


def shot(page, name):
    """Save the main canvas as a PNG for a visual check."""
    OUT.mkdir(exist_ok=True)
    page.wait_for_timeout(120)
    data = page.evaluate("() => document.getElementById('cv').toDataURL('image/png')")
    import base64
    (OUT / f"{name}.png").write_bytes(base64.b64decode(data.split(",", 1)[1]))


def set_format(page, fmt):
    page.click(f"[data-f={fmt}]")
    page.wait_for_function(f"() => state.format==='{fmt}' && document.getElementById('cv').height===FORMATS['{fmt}'].h")
