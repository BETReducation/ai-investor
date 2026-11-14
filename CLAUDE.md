# Working on this repo

Solo repo (Gary only). Push directly to main.

## New pages

A new `/learn/<level>/<slug>` lesson doesn't need a hand-written route: add one entry
to `LESSON_PAGES` in `app.py` (slug, level, file, title) and create the HTML file — the
route and the site-search entry are both generated from that list.

For any other new page/route, if it needs a nav entry: every page, including the Signals
page (`signal_config.html`), loads the one shared nav from `static/js/nav.js`, so add it
there once. Also add an entry to `SEARCH_PAGE_INDEX` in `app.py` (site search) unless the page
is a lesson (see above, automatic) or an Alpha post (also automatic — search queries live
content, no index entry needed).

## General

- Small, frequent commits with descriptive messages.
