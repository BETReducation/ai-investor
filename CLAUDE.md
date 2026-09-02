# Working on this repo

Solo repo (Gary only). Push directly to main.

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

- Small, frequent commits with descriptive messages.
