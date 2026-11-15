# PARCO Post Studio — to do

## Shared library with real logins (next)
- Backend so the same login shows the same saved posts on every device, including the product photos.
- Proposed: Supabase (free tier, works with the GitHub Pages site): real logins, a shared posts table, photo storage, access rules so only signed-in team members can read or change anything.
- Only the public (anon) key goes in the code; never the service key.
- Move existing local posts up once so nothing is lost.
- Open questions: Supabase or another provider (e.g. Firebase)? One login per team member, or one shared team login?

## Text styling, not built yet
- Line spacing.
- Alignment for the template's own text.
- A bigger font list.
- A free colour picker (today: 13 colours, including the theme colours).

## Brand Posters, left from the plan
- Diagonal Ribbon: features as a tick row (today: icon strip).
- Photo First: a smaller contact strip (today: the shared contact strip).

## Later
- Reels and videos from the same layouts.
- Split `index.html` into a few files before the reels work.
