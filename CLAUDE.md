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
  - Sign-in: optional; `config.js` has `users:[]` so everyone goes straight in. Saved posts live in one shared `posts` collection (old `posts~<userId>` data is merged in). Back up / Restore exports the library as JSON.
  - AI (bring your own key): `AI` holds provider (Gemini/Claude) and key in `localStorage` only (`parco-ai-v1`). Call it through `const s=await cap.sample; s.json(prompt,{images})`; `null` means no key, so fall back to local logic.
  - Design ideas: `getIdeas()` / `showIdeas()` / `ideaState()`. Ideas can carry `decos:[{type,color,x,y,w,rot,back}]` and `tags:[{text,preset,x,y}]` (0–1 coordinates), checked by `cleanIdeaExtras()`: at most 4 decorations and 2 tags, keys from `DECOS`/`DECO_COLORS`/`TB_PRESETS`, tag words must come from the write-up, `PRICE_RE` drops price/offer words. Applying an idea writes AI items (`ai:true`) into `state.decos[template][every format]` and `state.texts[template]`, replacing earlier AI items and keeping the user's own. `pushUndoAll()` snapshots style + decos + texts.
  - Caption languages (Caption tab): `pickCapLang(lang)` keeps one version per language in `state.captions[lang]` = `{caption,hashtags,whatsapp,src,post?}` (`state.capLang` is the one shown; `src` is product+write-up, so an older write-up asks again). `keepCap()` stores edits before switching and saving. The "translate the text on the post" toggle also stores/applies `post` (eyebrow, headline, sub, category, cta, bullets). Saved posts and backups include `captions`/`capLang`.
  - Indic fonts: canvas text does not trigger webfont loading and Google splits Noto Devanagari/Gujarati by script, so call `scriptFonts()` (loads them with sample text) before rendering Hindi/Gujarati.
  - Background remover: `openCut()`; loads onnxruntime-web 1.20.1 from jsDelivr, model from `models/silueta.*.txt` (gzip+base64 parts), WASM from `ortw/`; falls back to `models/u2netp.txt` with WebGL.
  - Automatic clean-up: `cutoutPhoto(img,onMsg)` runs the AI cut-out headless (dialog defaults: `aiProbability` → `alphaFrom` → `softEdge` → `trimOut`) and returns a PNG blob. `isMessy(img)` samples the border (not transparent, not near-white, not one plain colour). `addFiles` → `checkMessy` shows `#cutHint` ("Clean background", opt-in auto-run in `localStorage` `parco-autocut`); `queueCut`/`runCutQ` process photos one at a time, keep `orig` for the ↺ revert, push `'__photo__'` onto `UNDO` (`PHOTO_UNDO`), and open the manual dialog (`openCut`) when a cut fails. Tests stub `aiProbability`.
  - Week planner (`#weekModal`, "📅 Plan a week"): `weekPrompt` → one AI call → `cleanWeek` (products must match the pasted list, angles from `WEEK_ANGLES`, 1-photo templates, `noPrice` drops price words and stock lines the write-up does not support). `weekState(entry)` builds a full post from the current brand/look/contact settings. `saveWeekDrafts` saves through `saveCurrent({scheduledAt,draft:true})` (the save button's logic); library cards show the date. Captions are written lazily per post (`weekCaptions`, paced by `WEEK_PACE`, one retry after a 429) and copied into saved drafts. `exportWeek` makes one ZIP (`makeZip`, stored) of PNGs in all 3 sizes plus `captions.csv`. Entries without a matching uploaded photo use a sample photo (`weekPhoto`) and are flagged. No auto-posting.
  - `saveCurrent(extra)` serialises the current `state` to the library (used by the Save button and the week planner, which swaps `state`/`S` temporarily).
- `assets.js` — `window.PARCO_ASSETS` (logos, sample photos). Large; avoid reading it whole.
- `config.js` — sign-in accounts. Manage with `node tools/users.mjs add|password|remove|list`.

## Conventions
- Brand palette (PARCO catalog): indigo `#2b3990`, logo blue `#1f74c9`, orange `#f26522`, amber `#fbb412`. Themes in `THEMES`.
- Marketing is enquiry-only: no prices in copy.
- Test changes by serving locally (`python -m http.server 8000`) and checking all three sizes (square, portrait 4:5, story 9:16) and looks.
- Automated tests: `python -m pytest tests -q` (Playwright, Chromium). `tests/conftest.py` serves the repo and mocks the Gemini endpoint (`ai.handler = lambda prompt: {...}`); no real keys. Canvas screenshots of each size go to `tests/out/` (gitignored).
- Never commit `.env` or API keys: the repo and site are public.
