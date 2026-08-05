# Working on this repo

This site is edited by more than one person (Gary and Connor), sometimes at the same
time, sometimes not — often on different parts of the site. Git already tracks who
changed what and when, so there's no separate changelog to maintain. The habits below
are just about making concurrent edits go smoothly.

## Before starting work

Run `git fetch && git log --oneline HEAD..origin/main` to see if anything's landed on
the remote that isn't local yet. If there's new work, skim the commit messages so you
know roughly what changed before editing nearby files.

## Before pushing

Push normally. If it's rejected because the remote has moved on:

1. `git fetch origin`, then look at what's new (`git log --oneline HEAD..origin/main`
   and `git diff --stat HEAD..origin/main`) — get a sense of which files overlap with
   what you just changed.
2. `git merge origin/main` (don't force-push, don't discard the other person's work).
3. If it merges cleanly, don't just trust that — re-check the specific area you were
   both touching: read the merged code, confirm both sets of changes still make sense
   together, and re-run whatever verification applies (page loads, JS syntax, a live
   request against the affected endpoint, etc.) before pushing the merge commit.
4. If there are real conflict markers, resolve them by understanding both sides' intent
   — don't blindly pick one side.

## New pages

A new `/learn/<level>/<slug>` lesson doesn't need a hand-written route: add one entry
to `LESSON_PAGES` in `app.py` (slug, level, file, title) and create the HTML file — the
route and the site-search entry are both generated from that list.

For any other new page/route, if it needs a nav entry: most pages share one nav via
`static/js/nav.js` (a single `document.write()`d block), so add it there once. A few
older standalone pages (currently `strategy-lab.html`, `strategy-lab-forex.html`,
`signal_config.html`, `portfolio-balancer.html`) still carry their own inline `<nav>`
instead of loading `nav.js` — add it to those too if the change should reach them.
Also add an entry to `SEARCH_PAGE_INDEX` in `app.py` (site search) unless the page is a
lesson (see above, automatic) or an Alpha post (also automatic — search queries live
content, no index entry needed).

## General

- Don't assume an unfamiliar change in the working tree or git history is a mistake —
  check `git log`/`git blame` for authorship before "cleaning it up" or reverting it.
- Small, frequent commits with descriptive messages make all of the above much easier,
  for both people's sake.
