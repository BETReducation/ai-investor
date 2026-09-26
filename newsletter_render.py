"""Renders the weekly newsletter email (HTML + plain text).

Pure functions only — no Flask or database access — so app.py owns data
loading and this file owns layout. Table-based markup with inline styles
because Outlook/Gmail ignore most modern CSS.
"""
import re
from html import escape

BASE_URL_DEFAULT = "https://growthcapitalgroup.co"

# Arm colours match the site nav (Education blue, Tools purple, Arena gold, GCG green).
GREEN, BLUE, PURPLE, GOLD = "#00b894", "#3b82f6", "#a855f7", "#f59e0b"
INK, MUTED, BORDER, BG, CARD = "#0f172a", "#5b6478", "#e6e9f0", "#f4f6fa", "#ffffff"
NAVY = "#0b1020"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

DISCLAIMER = ("Growth Capital Group content is educational and describes historical market behaviour. "
              "It is not financial advice or a recommendation to buy or sell anything. Past performance "
              "doesn't guarantee future results.")


def _abs(url: str, base: str) -> str:
    url = (url or "").strip()
    if url.startswith(("http://", "https://", "mailto:")):
        return url
    return base.rstrip("/") + "/" + url.lstrip("/")


def _utm(url: str, base: str, section: str) -> str:
    """Own-site links get UTM tags so we can see which sections get clicked without Resend click tracking."""
    url = _abs(url, base)
    if not url.startswith(base):
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source=newsletter&utm_medium=email&utm_campaign=weekly&utm_content={section}"


def _paras(text: str) -> str:
    out = []
    for block in (text or "").strip().split("\n\n"):
        block = block.strip()
        if block:
            out.append(f'<p style="margin:0 0 12px;font-size:15px;line-height:1.65;color:{INK};">'
                       f'{escape(block).replace(chr(10), "<br>")}</p>')
    return "".join(out)


def _bullets(text: str) -> str:
    """One bullet per non-empty line; leading -, * or • markers are stripped."""
    items = [re.sub(r"^\s*[-*•]\s*", "", ln).strip() for ln in (text or "").splitlines()]
    lis = "".join(f'<li style="margin:0 0 8px;">{escape(i)}</li>' for i in items if i)
    return (f'<ul style="margin:0 0 14px;padding-left:20px;font-size:15px;line-height:1.6;color:{INK};">{lis}</ul>')


def _button(label: str, url: str, colour: str, outline: bool = False) -> str:
    bg = "transparent" if outline else colour
    fg = colour if outline else "#ffffff"
    border = f"border:1px solid {colour};" if outline else ""
    return (f'<table role="presentation" cellpadding="0" cellspacing="0" align="left" style="margin:6px 8px 0 0;"><tr>'
            f'<td style="background:{bg};{border}border-radius:8px;">'
            f'<a href="{escape(url, quote=True)}" style="display:inline-block;padding:11px 20px;font-family:{FONT};'
            f'font-size:14px;font-weight:700;color:{fg};text-decoration:none;">{escape(label)}</a>'
            f'</td></tr></table>')


def _section(number: str, eyebrow: str, title: str, colour: str, body: str, cta_html: str = "") -> str:
    return (
        f'<tr><td style="padding:0 16px 16px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:{CARD};border:1px solid {BORDER};border-top:4px solid {colour};border-radius:12px;">'
        f'<tr><td style="padding:22px 22px 18px;font-family:{FONT};">'
        f'<div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;font-weight:700;color:{colour};margin-bottom:6px;">'
        f'{escape(number)} &middot; {escape(eyebrow)}</div>'
        f'<div style="font-size:20px;font-weight:800;color:{INK};margin-bottom:12px;letter-spacing:-.01em;">{escape(title)}</div>'
        f'{body}{cta_html}<div style="clear:both;"></div>'
        f'</td></tr></table></td></tr>'
    )


def _stat_tile(value, label: str) -> str:
    return (f'<td width="33%" style="padding:4px;" valign="top"><div style="background:{BG};border-radius:10px;'
            f'padding:12px 6px;text-align:center;font-family:{FONT};">'
            f'<div style="font-size:24px;font-weight:800;color:{INK};line-height:1.1;">{value}</div>'
            f'<div style="font-size:11px;color:{MUTED};margin-top:4px;">{escape(label)}</div></div></td>')


def _stats_block(activity: dict, progress: dict) -> tuple[str, str]:
    tiles = [
        (activity.get("login", 0), "Logins"),
        (activity.get("signal", 0), "Signals checked"),
        (activity.get("backtest", 0), "Backtests run"),
        (activity.get("ai_request", 0), "AI questions"),
        (activity.get("lessons_distinct", 0), "Lessons opened"),
        (activity.get("video_play", 0), "Videos watched"),
    ]
    completed = activity.get("lesson_complete", 0)
    total = sum(v for v, _ in tiles) + completed
    rows = "".join(
        f'<tr>{_stat_tile(*tiles[i])}{_stat_tile(*tiles[i + 1])}{_stat_tile(*tiles[i + 2])}</tr>'
        for i in (0, 3)
    )
    done, all_lessons = progress.get("done", 0), progress.get("total", 0)
    if total == 0:
        note = "A quiet week on the platform. A ten-minute lesson or one backtest is a gentle way back in."
    else:
        note = f"You've completed {done} of {all_lessons} lessons"
        note += f", {completed} of them this week." if completed else "."
    body = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table>'
            f'<p style="margin:12px 0 14px;font-size:13px;color:{MUTED};line-height:1.6;">{escape(note)}</p>')
    text = "\n".join(f"  {v} {l}" for v, l in tiles) + f"\n  {note}"
    return body, text


def render_newsletter(content: dict, *, name: str, activity: dict, progress: dict,
                      unsubscribe_url: str, base_url: str = BASE_URL_DEFAULT,
                      profile_url: str = "") -> tuple[str, str]:
    """Returns (html, plain_text). `content` is the admin-edited issue."""
    base = base_url.rstrip("/")
    profile_url = profile_url or f"{base}/profile"

    def u(path, sec):
        return _utm(path, base, sec)

    subject = content.get("subject") or "Your weekly Growth Capital Group briefing"
    preheader = content.get("preheader") or ""
    intro = content.get("intro") or ""
    first = (name or "there").split()[0]

    parts = []
    text = [f"GROWTH CAPITAL GROUP: {subject}", "", f"Hi {first},", "", intro, ""]

    # 1. Personal stats
    stats_html, stats_text = _stats_block(activity, progress)
    parts.append(_section("01", "Your week", "Your week in numbers", GREEN, stats_html,
                          _button("Open your profile", u("/profile", "stats"), GREEN)))
    text += ["1. YOUR WEEK IN NUMBERS", stats_text, f"   {base}/profile", ""]

    # 2. Alpha roundup
    alpha = [a for a in content.get("alpha", []) if a.get("include", True)]
    if alpha:
        rows = ""
        for a in alpha:
            rows += (f'<div style="padding:10px 0;border-top:1px solid {BORDER};">'
                     f'<div style="font-size:12px;color:{MUTED};margin-bottom:2px;">{escape(a.get("author_name", ""))}</div>'
                     f'<a href="{escape(u(a.get("url") or "/alpha", "alpha"), quote=True)}" '
                     f'style="font-size:15px;font-weight:700;color:{INK};text-decoration:none;">{escape(a.get("title", ""))}</a>'
                     f'<div style="font-size:14px;color:{MUTED};line-height:1.55;margin-top:3px;">{escape(a.get("snippet", ""))}</div></div>')
        parts.append(_section("02", "Alpha", "This week from our partners", GREEN, rows + '<div style="height:8px;"></div>',
                              _button("Read on Alpha", u("/alpha", "alpha"), GREEN)))
        text += ["2. THIS WEEK FROM OUR PARTNERS"]
        text += [f"  - {a.get('author_name', '')}: {a.get('title', '')} ({_abs(a.get('url') or '/alpha', base)})" for a in alpha]
        text += [f"  {base}/alpha", ""]

    # 3. Assets in focus
    assets = [a for a in content.get("assets", []) if a.get("include", True)]
    if assets:
        by_author = {}
        for a in assets:
            by_author.setdefault(a.get("author_name", ""), {"label": a.get("label", ""), "items": []})["items"].append(a)
        rows = (f'<p style="margin:0 0 6px;font-size:14px;color:{MUTED};line-height:1.6;">'
                f'What our partners are following at the moment. See how each has behaved historically with the tools below.</p>')
        for author, grp in by_author.items():
            rows += (f'<div style="font-size:13px;color:{INK};font-weight:700;padding:12px 0 4px;">{escape(author)} '
                     f'<span style="font-weight:400;color:{MUTED};">&middot; {escape(grp["label"])}</span></div>'
                     f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">')
            for i in grp["items"]:
                rows += (f'<tr><td style="padding:8px 12px 8px 0;border-top:1px solid {BORDER};width:38%;font-size:14px;font-weight:700;color:{INK};" valign="top">'
                         f'{escape(i.get("asset", ""))}</td>'
                         f'<td style="padding:8px 0;border-top:1px solid {BORDER};font-size:13px;line-height:1.5;color:{MUTED};" valign="top">'
                         f'{escape(i.get("note", ""))}</td></tr>')
            rows += '</table>'
        cta = (_button("Backtest an asset", u("/backtester", "assets"), PURPLE) +
               _button("Check signals", u("/tools/signals", "assets"), PURPLE, outline=True))
        parts.append(_section("03", "Tools", "Assets in focus", PURPLE, rows, cta))
        text += ["3. ASSETS IN FOCUS"]
        for author, grp in by_author.items():
            text.append(f"  {author} ({grp['label']})")
            text += [f"    - {i.get('asset', '')}" + (f": {i['note']}" if i.get("note") else "") for i in grp["items"]]
        text += [f"  Backtester: {base}/backtester", f"  Signals: {base}/tools/signals", ""]

    # 4. Events
    events = [e for e in content.get("events", []) if e.get("include", True)]
    if events:
        rows = ""
        for e in events:
            dot = {"high": "#ef4444", "medium": GOLD}.get((e.get("impact") or "").lower(), "#94a3b8")
            rows += (f'<tr><td style="padding:8px 0;border-top:1px solid {BORDER};font-size:13px;color:{MUTED};width:110px;" valign="top">'
                     f'{escape(e.get("when", ""))}</td>'
                     f'<td style="padding:8px 0;border-top:1px solid {BORDER};font-size:14px;color:{INK};" valign="top">'
                     f'<span style="color:{dot};">&#9679;</span> <b>{escape(e.get("country", ""))}</b> {escape(e.get("title", ""))}</td></tr>')
        body = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rows}</table>'
                f'<p style="margin:10px 0 12px;font-size:12px;color:{MUTED};">Red = high impact, amber = medium. Times are UK time.</p>')
        parts.append(_section("04", "Education", "On the calendar this week", BLUE, body,
                              _button("Learn how markets react", u("/learn/intermediate/central-bank-policy", "events"), BLUE)))
        text += ["4. ON THE CALENDAR THIS WEEK"]
        text += [f"  {e.get('when', '')}  {e.get('country', '')} {e.get('title', '')}" for e in events]
        text += [f"  {base}/learn/intermediate/central-bank-policy", ""]

    # 5. Business update
    if (content.get("business") or "").strip():
        link = content.get("business_link") or "/roadmap"
        parts.append(_section("05", "Growth Capital Group", "What we've been building", GREEN, _bullets(content["business"]),
                              _button("See the roadmap", u(link, "business"), GREEN)))
        bullet_lines = [re.sub(r"^\s*[-*•]\s*", "", ln).strip() for ln in content["business"].splitlines()]
        text += ["5. WHAT WE'VE BEEN BUILDING"] + [f"  - {b}" for b in bullet_lines if b] + [f"  {_abs(link, base)}", ""]

    # 6. Arena
    if (content.get("arena") or "").strip():
        link = content.get("arena_link") or "/arena"
        cta = _button("Enter the Arena", u(link, "arena"), GOLD)
        artifact = (content.get("artifact_url") or "").strip()
        if artifact:
            cta += _button("This week's explainer", artifact, "#b45309", outline=True)
        parts.append(_section("06", "Arena", "Market XI, data and more", GOLD, _paras(content["arena"]), cta))
        text += ["6. ARENA", content["arena"].strip(), f"  {_abs(link, base)}"]
        if artifact:
            text.append(f"  This week's explainer: {artifact}")
        text.append("")

    # 7. Thought of the week
    if (content.get("thought") or "").strip():
        link = content.get("thought_link") or "/learn"
        summary = (content.get("thought_summary") or "").strip()
        body = f'<div style="border-left:3px solid {BLUE};padding:2px 0 2px 14px;margin-bottom:14px;">{_paras(content["thought"])}</div>'
        if summary:
            body += (f'<p style="margin:0 0 14px;font-size:14px;line-height:1.6;color:{MUTED};">'
                     f'<b style="color:{INK};">In the lesson:</b> {escape(summary)}</p>')
        parts.append(_section("07", "Education", "Thought of the week", BLUE, body,
                              _button(content.get("thought_cta") or "Take the lesson", u(link, "thought"), BLUE)))
        text += ["7. THOUGHT OF THE WEEK", content["thought"].strip()]
        if (content.get("thought_summary") or "").strip():
            text.append(f"  In the lesson: {content['thought_summary'].strip()}")
        text += [f"  {_abs(link, base)}", ""]

    text += ["--", DISCLAIMER, "", f"Manage your preferences: {profile_url}", f"Unsubscribe: {unsubscribe_url}"]

    header_img = f"{base}/static/newsletter/header.png"
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><title>{escape(subject)}</title></head>
<body style="margin:0;padding:0;background:{BG};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{escape(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};"><tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="width:100%;max-width:600px;">
<tr><td style="background:{NAVY};border-radius:0 0 16px 16px;overflow:hidden;" align="center">
  <a href="{escape(u("/", "header"), quote=True)}"><img src="{header_img}" alt="Growth Capital Group - The Sunday briefing" width="600" style="display:block;width:100%;max-width:600px;height:auto;border:0;border-radius:0 0 16px 16px;"></a>
</td></tr>
<tr><td style="padding:26px 24px 18px;font-family:{FONT};">
  <div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;font-weight:700;color:{GREEN};">The Sunday briefing</div>
  <div style="font-size:26px;font-weight:800;color:{INK};letter-spacing:-.02em;margin:6px 0 10px;">Hi {escape(first)},</div>
  {_paras(intro)}
</td></tr>
{"".join(parts)}
<tr><td style="padding:12px 24px 34px;font-family:{FONT};font-size:12px;line-height:1.7;color:{MUTED};" align="center">
  <p style="margin:0 0 10px;">{escape(DISCLAIMER)}</p>
  <p style="margin:0;"><a href="{escape(profile_url, quote=True)}" style="color:{MUTED};">Manage preferences</a> &middot;
  <a href="{escape(unsubscribe_url, quote=True)}" style="color:{MUTED};">Unsubscribe</a></p>
  <p style="margin:10px 0 0;">Growth Capital Group &middot; We measure opens to improve the newsletter.</p>
</td></tr>
</table></td></tr></table></body></html>'''
    return html, "\n".join(text)
