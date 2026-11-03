# PARCO Post Studio

Make branded social media posts for **PARCO Engineering Corporation**, Ahmedabad (since 1971): add product photos and a short write-up, pick a template, adjust anything, and download PNGs for Instagram/Facebook feed (1:1, 4:5) and WhatsApp Status (9:16).

**Live site:** https://sneh2909.github.io/parco-post-studio/

## Features
- 13 templates for 1–4 photos, in three looks (Classic, Night, Site) and five PARCO catalog colour themes
- Every item can be moved, resized, restyled (20 fonts) or hidden; Undo/Redo; changes stay with that post
- Add text boxes, 44 decorations (with strength / amount / fade / rotate), and a WhatsApp enquiry button
- Background remover that runs in the browser (AI cut-out model, plus a plain-colour mode)
- PARCO logo watermark, brand logo box, product details, highlights
- Saved posts library (stored in the browser on each device)
- Shared team password screen

## Run it locally
It is a static site, so any local web server works:

```bash
python -m http.server 8000
# then open http://localhost:8000
```
(Opening `index.html` directly from disk will not load the background-remover model; use a server.)

## Change the team password
```bash
node tools/set-password.mjs "your new password"
git commit -am "Change password" && git push
```
The password screen only keeps casual visitors out: the site and its code are public.

## Project layout
| Path | What it is |
|---|---|
| `index.html` | The whole app: HTML, CSS and JavaScript (canvas rendering, templates, editor) |
| `assets.js` | Built-in images as data URLs: PARCO and NASCO logos, sample product photos |
| `config.js` | Team password hash |
| `models/` | Background-remover models (silueta, u2netp), base64 text so GitHub Pages serves them |
| `ortw/` | ONNX Runtime WebAssembly binary used by the background remover |
| `tools/set-password.mjs` | Changes the password in `config.js` |

## Deploy
GitHub Pages serves the `main` branch from the repository root. Every push to `main` updates the site in a minute or two.
