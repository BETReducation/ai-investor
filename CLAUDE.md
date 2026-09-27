# Working on this repo

Solo repo (Gary only). Push directly to main.

## New pages

A new `/learn/<level>/<slug>` lesson doesn't need a hand-written route: add one entry
to `LESSON_PAGES` in `app.py` (slug, level, file, title) and create the HTML file — the
route and the site-search entry are both generated from that list.

For any other new page/route, if it needs a nav entry: most pages share one nav via
`static/js/nav.js` (a single `document.write()`d block), so add it there once.
`signal_config.html` still carries its own inline `<nav>` instead of loading `nav.js` —
it gates its dashboard behind an in-page login overlay (`signInBtn`/`logoutBtn`/
`usernameDisplay`/`loginOverlay`) wired into its own auth flow, so it wasn't safe to
swap over wholesale; add nav changes there by hand too, and add an entry to
`SEARCH_PAGE_INDEX` in `app.py` (site search) unless the page is a
lesson (see above, automatic) or an Alpha post (also automatic — search queries live
content, no index entry needed).

## General

- Small, frequent commits with descriptive messages.
