# PARCO Post Studio — notes for Claude Code

Static single-page app (no build step) hosted on GitHub Pages from `main` / root.
Users: the PARCO Engineering Corporation team (Ahmedabad), posting product promos for NASCO and other spare-part brands.

## Structure
- `index.html` — everything: UI markup, CSS (theme tokens at the top), and one big `<script>`.
  - Rendering is all Canvas 2D. `renderPost(ctx,W,H,state)` draws a post; templates live in `TPL`, `REF` (Feature Pro, Duo Launch, Trio Pedestal) and `ART` (Duo Spotlight, Duo Panels, Trio Hero/Medallions/Slant, Quad Polaroid/Mosaic). `TEMPLATES` holds names, photo count `n`, and default `look`.
  - `el(id, box, fn)` wraps every drawable item so it can be selected, moved, resized, re-fonted or hidden. Per-post overrides live in `state.offsets[template][format][id]`.
  - Shared contact footer: `stdFooter()` / `contactFooter()` / `barFooter()` — same position on every template (heights `CB1`, `CB2`, `CTAG`).
  - Add-ons: decorations (`DECOS`, `drawDeco`, `state.decos`), text boxes (`drawTextBoxes`, `state.texts`), optional extras (`drawExtras`, `state.extra`), WhatsApp button (`waButton`).
  - Storage: `LOCAL` (IndexedDB) provides `db` (posts), `assets` (uploaded photo blobs) and `downloads`. Library code calls it through `cap.*`.
  - Sign-in: user IDs in `config.js` (`PARCO_CONFIG.users`, PBKDF2-SHA256, 150k iterations). Saved posts are namespaced per user (`posts~<userId>` in IndexedDB).
  - Background remover: `openCut()`; loads onnxruntime-web 1.20.1 from jsDelivr, model from `models/silueta.*.txt` (gzip+base64 parts), WASM from `ortw/`; falls back to `models/u2netp.txt` with WebGL.
- `assets.js` — `window.PARCO_ASSETS` (logos, sample photos). Large; avoid reading it whole.
- `config.js` — sign-in accounts. Manage with `node tools/users.mjs add|password|remove|list`.

## Conventions
- Brand palette (PARCO catalog): indigo `#2b3990`, logo blue `#1f74c9`, orange `#f26522`, amber `#fbb412`. Themes in `THEMES`.
- Marketing is enquiry-only: no prices in copy.
- Test changes by serving locally (`python -m http.server 8000`) and checking all three sizes (square, portrait 4:5, story 9:16) and looks.
- Never commit `.env` or API keys: the repo and site are public.
