#!/usr/bin/env python3
"""Regenerate GUIDE.md and site/index.html from README.md + tutorials/*/README.md.

    pip install markdown
    python3 tools/build.py

Optionally set REPO_URL to turn script references into links, e.g.
    REPO_URL=https://github.com/you/cloudways-cookbook python3 tools/build.py
"""
import html
import os
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
REPO_URL = os.environ.get("REPO_URL", "").rstrip("/")
UPDATED = "October 30, 2026"

# (dir, title, description, minutes, short nav label)
TUTORIALS = [
    ("01-first-server", "First server and app", "Start the free trial, launch a server, connect over SSH and SFTP.", 10, "Start"),
    ("02-deploy-apps", "Deploy apps", "WordPress, Git deployments, Laravel and PHP, and Node.js on Velocity.", 20, "Deploy"),
    ("03-api-and-automation", "API and automation", "Access Tokens, the v2 API, and scripts that run your fleet.", 20, "API"),
    ("04-mcp-ai-agents", "MCP and AI agents", "Drive Cloudways from Claude, Cursor, VS Code and friends.", 15, "MCP"),
    ("05-ops-basics", "Ops basics", "Domains, SSL, backups, staging, monitoring and scaling.", 15, "Ops"),
]

ARROW = '<svg class="ar" viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h10M9 4l4 4-4 4"/></svg>'
ARROW_L = '<svg class="ar" viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M13 8H3M7 4L3 8l4 4"/></svg>'
EXT = '<svg viewBox="0 0 16 16" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M5 11l6-6M6 5h5v5"/></svg>'


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


# ---------------------------------------------------------------- GUIDE.md
def build_guide():
    parts = [read("README.md")] + [read(f"tutorials/{t[0]}/README.md") for t in TUTORIALS]
    guide = "\n\n---\n\n".join(parts)

    def fix(m):
        text, target = m.group(1), m.group(2)
        if target.startswith(("http://", "https://", "#")):
            return m.group(0)
        if REPO_URL:
            clean = re.sub(r"^(\.\./)+|^\./", "", target)
            return f"[{text}]({REPO_URL}/blob/main/{clean})"
        return text if text.startswith("`") else f"`{text}`"

    guide = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", fix, guide)
    (ROOT / "GUIDE.md").write_text(guide, encoding="utf-8")


# ---------------------------------------------------------------- helpers
def md_to_html(text):
    return markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])


def strip_md_links(md_text):
    """Relative links -> section anchors or plain code; external links kept."""
    def fix(m):
        label, target = m.group(1), m.group(2)
        if target.startswith(("http://", "https://", "#")):
            return m.group(0)
        mt = re.search(r"(\d\d)-[a-z-]+/README\.md", target)
        if mt and int(mt.group(1)) <= len(TUTORIALS):
            return f"[{label}](#t{int(mt.group(1))})"
        clean = re.sub(r"^(\.\./)+|^\./", "", target)
        if REPO_URL:
            return f"[{label}]({REPO_URL}/blob/main/{clean})"
        return label if label.startswith("`") else f"`{label}`"
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", fix, md_text)


def decorate(body):
    def callout(m):
        inner = m.group(1)
        low = re.sub(r"<[^>]+>", "", inner).lower()[:70]
        kind, label = "note", "Note"
        if "tip" in low:
            kind, label = "tip", "Tip"
        elif "disclaimer" in low or "warning" in low or "never" in low:
            kind, label = "warn", "Heads up"
        return f'<aside class="callout {kind}"><span class="cl">{label}</span><div>{inner}</div></aside>'
    body = re.sub(r"<blockquote>\s*(.*?)\s*</blockquote>", callout, body, flags=re.S)

    def code(m):
        cls = m.group(1) or ""
        ml = re.search(r"language-(\w+)", cls)
        lang = ml.group(1) if ml else "text"
        return (f'<figure class="code"><figcaption><span>{lang}</span>'
                f'<button class="copy" type="button" aria-label="Copy code">Copy</button></figcaption>'
                f'<pre><code>{m.group(2)}</code></pre></figure>')
    body = re.sub(r'<pre><code(?: class="([^"]*)")?>(.*?)</code></pre>', code, body, flags=re.S)

    body = body.replace("<li>[ ] ", '<li class="todo"><input type="checkbox"> ')
    body = body.replace("<li>[x] ", '<li class="todo"><input type="checkbox" checked> ')
    body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    body = re.sub(r'<a href="(https?://[^"]+)"([^>]*)>(.*?)</a>',
                  lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener"{m.group(2)}>{m.group(3)}</a>',
                  body, flags=re.S)
    return body


def make_tabs(body, idx):
    m = re.search(rf'(<h2 id="t{idx}-client-configs">.*?</h2>)(.*?)(?=<h2 |\Z)', body, re.S)
    if not m:
        return body
    head, rest = m.group(1), m.group(2)
    parts = re.split(r"(?=<h3>)", rest)
    intro, panels = parts[0], [p for p in parts[1:] if p.strip()]
    if len(panels) < 2:
        return body
    tabs, bodies = [], []
    for k, p in enumerate(panels):
        title = re.match(r"<h3>(.*?)</h3>", p, re.S).group(1)
        content = re.sub(r"^<h3>.*?</h3>", "", p, count=1, flags=re.S)
        sel = "true" if k == 0 else "false"
        tabs.append(f'<button role="tab" id="tab-{idx}-{k}" aria-controls="panel-{idx}-{k}" aria-selected="{sel}" tabindex="{0 if k == 0 else -1}">{title}</button>')
        hid = "" if k == 0 else " hidden"
        bodies.append(f'<div role="tabpanel" id="panel-{idx}-{k}" aria-labelledby="tab-{idx}-{k}"{hid}>{content}</div>')
    tabs_html = f'<div class="tabs">{intro}<div role="tablist" aria-label="Client">{"".join(tabs)}</div>{"".join(bodies)}</div>'
    return body.replace(m.group(0), head + tabs_html)


def section_html(i, t):
    tid, title, blurb, mins, _ = t
    idx = i + 1
    md_text = read(f"tutorials/{tid}/README.md")
    md_text = re.sub(r"^# .*\n", "", md_text, count=1)
    md_text = strip_md_links(md_text)
    body = decorate(md_to_html(md_text))
    body = re.sub(r"<p><strong>Next:</strong>.*?</p>", "", body, flags=re.S)

    def h2(m):
        slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", m.group(1)).lower()).strip("-")
        return f'<h2 id="t{idx}-{slug}">{m.group(1)}</h2>'
    body = re.sub(r"<h2>(.*?)</h2>", h2, body)
    body = make_tabs(body, idx)

    prev_ = TUTORIALS[i - 1] if i > 0 else None
    next_ = TUTORIALS[i + 1] if i < len(TUTORIALS) - 1 else None
    pager = '<nav class="pager" aria-label="Pagination">'
    pager += (f'<a href="#t{idx-1}" class="pg prev"><span>Previous</span><b>{ARROW_L}{html.escape(prev_[1])}</b></a>' if prev_ else "<span></span>")
    pager += (f'<a href="#t{idx+1}" class="pg next"><span>Next</span><b>{html.escape(next_[1])}{ARROW}</b></a>' if next_
              else '<a href="#resources" class="pg next"><span>Finally</span><b>Resources and safety' + ARROW + '</b></a>')
    pager += "</nav>"

    return f'''<section class="tut" id="t{idx}">
  <div class="c-wide"><header class="th reveal"><span class="bn" aria-hidden="true">{idx:02d}</span>
    <div><p class="eyebrow">Tutorial {idx:02d} &middot; about {mins} min</p><h1>{html.escape(title)}</h1><p class="sub">{html.escape(blurb)}</p></div></header></div>
  <div class="c-read body reveal">{body}{pager}</div>
</section>'''


def build_html():
    sections = "\n".join(section_html(i, t) for i, t in enumerate(TUTORIALS))

    readme = read("README.md")
    extra_md = ""
    for h in ("Additional resources", "Safety notes for hackers"):
        m = re.search(rf"^## {h}\n(.*?)(?=^## |\Z)", readme, flags=re.S | re.M)
        if m:
            extra_md += f"## {h}\n{m.group(1)}\n"
    extra = decorate(md_to_html(strip_md_links(extra_md)))
    extra = re.sub(r"<h2>(.*?)</h2>", lambda m: f'<h2 id="r-{re.sub(r"[^a-z0-9]+", "-", m.group(1).lower()).strip("-")}">{m.group(1)}</h2>', extra)

    index_rows = "".join(
        f'<a class="irow" href="#t{i+1}"><span class="inum">{i+1:02d}</span><span class="it">{html.escape(t[1])}</span>'
        f'<span class="id">{html.escape(t[2])}</span><span class="im">{t[3]} min</span><span class="ia">{ARROW}</span></a>'
        for i, t in enumerate(TUTORIALS))

    menu = "".join(f'<a href="#t{i+1}" data-spy="t{i+1}"><i>{i+1:02d}</i>{html.escape(t[4])}</a>' for i, t in enumerate(TUTORIALS))
    menu += '<a href="#resources" data-spy="resources"><i>+</i>More</a>'

    out = (TEMPLATE
           .replace("@@UPDATED@@", UPDATED)
           .replace("@@MENU@@", menu)
           .replace("@@INDEX@@", index_rows)
           .replace("@@SECTIONS@@", sections)
           .replace("@@EXTRA@@", extra)
           .replace("@@EXT@@", EXT)
           .replace("@@ARROW@@", ARROW))
    (ROOT / "site").mkdir(exist_ok=True)
    (ROOT / "site" / "index.html").write_text(out, encoding="utf-8")


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Cloudways Cookbook</title>
<meta name="description" content="A field guide to launching, deploying and automating on Cloudways: Git, API v2, MCP and ops basics.">
<script>(function(){var t=null;try{t=localStorage.getItem('theme')}catch(e){}var d=t==='dark'||(t!=='light'&&matchMedia('(prefers-color-scheme: dark)').matches);if(d)document.documentElement.classList.add('dark')})()</script>
<style>
:root{--bg:#f6f4ee;--bg2:#efece3;--ink:#16150f;--mut:#6b685d;--line:#dcd8cb;--acc:#e0431b;--accsoft:rgba(224,67,27,.09);--code:#15140f;--codeink:#ece8dc;--codeline:#2a281f;--serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;--sans:ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color-scheme:light}
.dark{--bg:#0f0f0c;--bg2:#171611;--ink:#efece3;--mut:#9a968a;--line:#2b2a22;--acc:#ff6a3d;--accsoft:rgba(255,106,61,.12);--code:#0a0a08;--codeline:#26241c;color-scheme:dark}
*{box-sizing:border-box}html{scroll-padding-top:84px}
body{margin:0;background:var(--bg);color:var(--ink);font:16.5px/1.75 var(--sans);-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:inherit;text-decoration-color:var(--line);text-underline-offset:3px;text-decoration-thickness:1px;transition:text-decoration-color .2s,color .2s}
a:hover{color:var(--acc);text-decoration-color:var(--acc)}
::selection{background:var(--acc);color:#fff}
.c-wide{max-width:1040px;margin:0 auto;padding:0 32px}.c-read{max-width:740px;margin:0 auto;padding:0 24px}
/* header */
header.top{position:sticky;top:0;z-index:50;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:saturate(1.4) blur(14px);-webkit-backdrop-filter:saturate(1.4) blur(14px);border-bottom:1px solid var(--line)}
.bar{display:flex;align-items:center;gap:28px;height:58px;max-width:1180px;margin:0 auto;padding:0 32px}
.mark{display:flex;align-items:center;gap:9px;font-weight:650;font-size:15px;letter-spacing:-.01em;text-decoration:none;white-space:nowrap}
.mark i{width:10px;height:10px;border-radius:50%;background:var(--acc);display:block}
nav.menu{display:flex;gap:2px;overflow-x:auto;scrollbar-width:none;flex:1}nav.menu::-webkit-scrollbar{display:none}
nav.menu a{display:flex;align-items:baseline;gap:7px;padding:8px 12px;font-size:14px;color:var(--mut);text-decoration:none;border-radius:8px;white-space:nowrap;position:relative}
nav.menu a i{font:500 10.5px var(--mono);font-style:normal;opacity:.7}
nav.menu a::after{content:"";position:absolute;left:12px;right:12px;bottom:3px;height:1px;background:var(--ink);transform:scaleX(0);transform-origin:left;transition:transform .3s cubic-bezier(.2,.7,.2,1)}
nav.menu a:hover{color:var(--ink)}nav.menu a:hover::after,nav.menu a.on::after{transform:scaleX(1)}nav.menu a.on{color:var(--ink)}nav.menu a.on i{color:var(--acc);opacity:1}
.tools{display:flex;align-items:center;gap:6px}
.iconbtn{width:34px;height:34px;display:grid;place-items:center;border:1px solid var(--line);border-radius:9px;background:transparent;color:var(--ink);cursor:pointer;transition:background .2s,border-color .2s}
.iconbtn:hover{background:var(--bg2);border-color:var(--mut)}
.ext{display:flex;align-items:center;gap:5px;font-size:13.5px;color:var(--mut);text-decoration:none;padding:0 8px}.ext:hover{color:var(--ink)}
.progress{height:2px}.progress i{display:block;height:100%;width:0;background:var(--acc)}
/* hero */
.hero{padding:96px 0 40px}
.kicker{font:500 12px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin:0 0 28px;display:flex;align-items:center;gap:12px}
.kicker::before{content:"";width:28px;height:1px;background:var(--mut)}
.hero h1{font:400 clamp(44px,8.2vw,104px)/.98 var(--serif);letter-spacing:-.035em;margin:0 0 30px;max-width:11.5em}
.hero h1 em{font-style:italic;color:var(--acc);letter-spacing:-.02em}
.lede{font-size:clamp(18px,2vw,21px);line-height:1.6;color:var(--mut);max-width:34em;margin:0 0 34px}
.cta{display:flex;gap:26px;flex-wrap:wrap;align-items:center}
.btn{display:inline-flex;align-items:center;gap:10px;background:var(--ink);color:var(--bg);padding:13px 22px;border-radius:999px;font-weight:600;font-size:15px;text-decoration:none;transition:transform .25s,background .25s}
.btn:hover{background:var(--acc);color:#fff;transform:translateY(-1px)}.btn .ar{transition:transform .25s}.btn:hover .ar{transform:translateX(4px)}
.link{display:inline-flex;align-items:center;gap:8px;font-weight:600;font-size:15px;text-decoration:none;border-bottom:1px solid var(--ink);padding-bottom:2px}.link:hover{border-color:var(--acc)}
.meta{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin-top:72px}
.meta div{padding:18px 20px 18px 0}.meta div+div{padding-left:20px;border-left:1px solid var(--line)}
.meta dt{font:500 11px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--mut);margin:0 0 4px}.meta dd{margin:0;font-weight:600;font-size:15px}
/* offer + changed */
.sec-label{font:500 12px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin:0 0 22px}
.offer{padding:56px 0 12px}
.offer-lede{margin:0 0 28px;max-width:40em;color:var(--mut);font-size:17px;line-height:1.65}
.two{display:grid;grid-template-columns:1fr 1fr;gap:0;border-top:1px solid var(--ink)}
.two article{padding:22px 28px 8px 0}.two article+article{padding-left:28px;border-left:1px solid var(--line)}
.two small,.three small{font:500 11px var(--mono);color:var(--acc);letter-spacing:.1em}
.two h3,.three h3{font:400 24px/1.2 var(--serif);letter-spacing:-.015em;margin:8px 0 10px}
.two p,.three p{margin:0;color:var(--mut);font-size:15px;line-height:1.65}
.two ul{margin:12px 0 0;padding-left:18px;color:var(--mut);font-size:15px;line-height:1.65}
.two li{margin:6px 0}.two li::marker{color:var(--acc)}
.changed{padding:88px 0 12px}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:0;border-top:1px solid var(--ink)}
.three article{padding:22px 28px 8px 0}.three article+article{padding-left:28px;border-left:1px solid var(--line)}
/* index */
.index{padding:88px 0 40px}
.irow{display:grid;grid-template-columns:56px minmax(180px,1.1fr) 2fr 70px 24px;gap:20px;align-items:baseline;padding:26px 0;border-top:1px solid var(--line);text-decoration:none;position:relative;transition:padding .35s cubic-bezier(.2,.7,.2,1)}
.irow:last-child{border-bottom:1px solid var(--line)}
.irow::before{content:"";position:absolute;inset:0 -16px;background:var(--bg2);opacity:0;transition:opacity .3s;z-index:-1;border-radius:6px}
.irow:hover{padding-left:14px;color:var(--ink)}.irow:hover::before{opacity:1}
.inum{font:500 12.5px var(--mono);color:var(--mut)}.it{font:400 clamp(24px,3.2vw,34px)/1.1 var(--serif);letter-spacing:-.02em}
.id{color:var(--mut);font-size:15px;line-height:1.55}.im{font:500 12px var(--mono);color:var(--mut);text-align:right}.ia{color:var(--mut);transition:transform .3s,color .3s;align-self:center}
.irow:hover .ia{transform:translateX(6px);color:var(--acc)}.irow:hover .it{color:var(--acc)}
/* tutorials */
.tut{padding:110px 0 30px;border-top:1px solid var(--line);margin-top:70px}
.th{display:flex;gap:40px;align-items:flex-end;padding-bottom:42px}
.bn{font:400 clamp(96px,16vw,190px)/.8 var(--serif);letter-spacing:-.06em;color:transparent;-webkit-text-stroke:1.2px var(--acc);flex:none;user-select:none}
.eyebrow{font:500 12px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin:0 0 12px}
.th h1{font:400 clamp(34px,5vw,56px)/1.05 var(--serif);letter-spacing:-.03em;margin:0 0 14px}.sub{margin:0;color:var(--mut);font-size:18px;max-width:30em}
.body h2{font:400 31px/1.15 var(--serif);letter-spacing:-.02em;margin:64px 0 16px;padding-top:26px;border-top:1px solid var(--line)}
.body h2:first-child{margin-top:8px;border-top:0;padding-top:0}
.body h3{font:650 17px/1.3 var(--sans);margin:34px 0 8px;letter-spacing:-.005em}
.body p{margin:0 0 16px}.body ul,.body ol{padding-left:22px;margin:0 0 18px}.body li{margin:6px 0}.body li::marker{color:var(--acc)}
.body strong{font-weight:650}
.body p a,.body li a,.body td a{text-decoration-color:var(--acc);font-weight:500}
code{font:.86em var(--mono);background:var(--bg2);border:1px solid var(--line);padding:1px 6px;border-radius:5px;word-break:break-word}
.code{margin:22px 0;border-radius:12px;overflow:hidden;background:var(--code);border:1px solid var(--codeline)}
.code figcaption{display:flex;justify-content:space-between;align-items:center;padding:8px 8px 8px 16px;border-bottom:1px solid var(--codeline);font:500 11px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:#8d897c}
.copy{font:500 11px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:#bdb8a8;background:transparent;border:1px solid #38352b;border-radius:7px;padding:5px 10px;cursor:pointer;transition:.2s}
.copy:hover{background:var(--acc);border-color:var(--acc);color:#fff}.copy.done{color:#8fe3a7;border-color:#2f5b3d}
.code pre{margin:0;padding:16px 18px;overflow:auto}.code code{background:none;border:0;padding:0;color:var(--codeink);font-size:13.5px;line-height:1.7;word-break:normal}
.tablewrap{overflow:auto;margin:22px 0}
table{border-collapse:collapse;width:100%;font-size:14.5px;line-height:1.55}
th{font:500 11px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--mut);text-align:left;padding:0 16px 10px 0;border-bottom:1px solid var(--ink)}
td{padding:13px 16px 13px 0;border-bottom:1px solid var(--line);vertical-align:top}tr:last-child td{border-bottom:0}
.callout{display:grid;grid-template-columns:auto 1fr;gap:16px;margin:26px 0;padding:18px 22px;border-left:2px solid var(--ink);background:var(--bg2);border-radius:0 10px 10px 0}
.callout .cl{font:600 11px var(--mono);letter-spacing:.12em;text-transform:uppercase;padding-top:5px}.callout p:last-child{margin:0}.callout p{font-size:15.5px}
.callout.tip{border-color:#2f8f5b}.callout.tip .cl{color:#2f8f5b}.callout.warn{border-color:var(--acc);background:var(--accsoft)}.callout.warn .cl{color:var(--acc)}
li.todo{list-style:none;margin-left:-22px}li.todo input{margin-right:10px;accent-color:var(--acc);transform:scale(1.1)}
/* tabs */
.tabs [role=tablist]{display:flex;gap:4px;border-bottom:1px solid var(--line);margin:22px 0 4px;overflow-x:auto;scrollbar-width:none}
.tabs [role=tab]{font:600 14px var(--sans);color:var(--mut);background:none;border:0;padding:11px 14px;cursor:pointer;position:relative;white-space:nowrap}
.tabs [role=tab]::after{content:"";position:absolute;left:10px;right:10px;bottom:-1px;height:2px;background:var(--acc);transform:scaleX(0);transition:transform .25s}
.tabs [role=tab]:hover{color:var(--ink)}.tabs [role=tab][aria-selected=true]{color:var(--ink)}.tabs [role=tab][aria-selected=true]::after{transform:scaleX(1)}
.tabs [role=tabpanel]{animation:fade .35s ease}.tabs [role=tab]:focus-visible{outline:2px solid var(--acc);outline-offset:-2px;border-radius:6px}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
/* pager */
.pager{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:72px 0 0}
.pg{display:flex;flex-direction:column;gap:6px;padding:20px 22px;border:1px solid var(--line);border-radius:12px;text-decoration:none;transition:border-color .25s,background .25s,transform .25s}
.pg span{font:500 11px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--mut)}.pg b{display:flex;align-items:center;gap:9px;font:400 21px/1.2 var(--serif);letter-spacing:-.01em}
.pg.next{text-align:right}.pg.next b{justify-content:flex-end}
.pg:hover{border-color:var(--ink);background:var(--bg2);transform:translateY(-2px)}.pg.next:hover .ar{transform:translateX(4px)}.pg.prev:hover .ar{transform:translateX(-4px)}.pg .ar{transition:transform .25s}
/* toc */
#toc{position:fixed;top:120px;left:calc(50% + 410px);width:190px;display:none}
#toc h5{font:500 11px var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--mut);margin:0 0 12px}
#toc ul{list-style:none;margin:0;padding:0;border-left:1px solid var(--line)}#toc li a{display:block;padding:5px 0 5px 14px;margin-left:-1px;border-left:1px solid transparent;font-size:13px;line-height:1.4;color:var(--mut);text-decoration:none}
#toc li a:hover{color:var(--ink)}#toc li a.on{color:var(--ink);border-left-color:var(--acc)}
@media(min-width:1320px){#toc.show{display:block}}
/* footer */
footer.end{margin-top:140px;border-top:1px solid var(--ink);padding:80px 0 56px}
footer h2{font:400 clamp(44px,9vw,120px)/.95 var(--serif);letter-spacing:-.04em;margin:0 0 40px}footer h2 em{color:var(--acc)}
.fgrid{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:32px;font-size:14.5px;color:var(--mut)}.fgrid a{color:var(--ink)}.fgrid h6{font:500 11px var(--mono);letter-spacing:.12em;text-transform:uppercase;margin:0 0 10px;color:var(--mut)}
.fgrid p{margin:0 0 6px;line-height:1.6}
/* reveal */
.reveal{opacity:0;transform:translateY(18px);transition:opacity .8s cubic-bezier(.2,.7,.2,1),transform .8s cubic-bezier(.2,.7,.2,1)}.reveal.in{opacity:1;transform:none}
@media(prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none}*{animation:none!important}}
@media(max-width:860px){.bar{padding:0 16px;gap:10px}.ext{display:none}.mark span{display:none}.c-wide{padding:0 20px}.hero{padding:56px 0 20px}.meta{grid-template-columns:1fr 1fr}.meta div:nth-child(3){border-left:0;padding-left:0}.meta div:nth-child(n+3){border-top:1px solid var(--line)}
.two,.three{grid-template-columns:1fr}.two article+article,.three article+article{border-left:0;padding-left:0;border-top:1px solid var(--line);margin-top:16px;padding-top:22px}
.irow{grid-template-columns:36px 1fr 20px;row-gap:6px}.id{grid-column:2/3;grid-row:2}.im{display:none}.ia{grid-row:1;grid-column:3}
.th{flex-direction:column;align-items:flex-start;gap:14px}.pager{grid-template-columns:1fr}.fgrid{grid-template-columns:1fr}}
</style></head><body id="top">
<header class="top"><div class="bar"><a class="mark" href="#top"><i></i><span>Cloudways Cookbook</span></a>
<nav class="menu" aria-label="Sections">@@MENU@@</nav>
<div class="tools"><a class="ext" href="https://support.cloudways.com" target="_blank" rel="noopener">Official docs @@EXT@@</a>
<button class="iconbtn" id="theme" type="button" aria-label="Toggle theme"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button></div></div>
<div class="progress"><i id="prog"></i></div></header>

<main>
<div class="c-wide hero"><p class="kicker">A field guide, updated @@UPDATED@@</p>
<h1>Shipping on <em>Cloudways</em>.</h1>
<p class="lede">Launch a server, deploy with Git, automate with the v2 API, and hand the boring parts to an AI agent. Written for developers who learn by doing.</p>
<div class="cta"><a class="btn" href="#t1">Start the walkthrough @@ARROW@@</a><a class="link" href="#t3">Skip to the API</a></div>
<dl class="meta"><div><dt>Level</dt><dd>Comfortable with a CLI</dd></div><div><dt>API</dt><dd>v2, Bearer tokens</dd></div><div><dt>Agents</dt><dd>MCP server</dd></div><div><dt>Time</dt><dd>About 80 minutes</dd></div></dl></div>

<div class="c-wide offer reveal"><p class="sec-label">Hackathon signup</p>
<p class="offer-lede">Sign up only through this link so the promo applies: <a href="https://unified.cloudways.com/signup?coupon=CWFEST20" target="_blank" rel="noopener"><strong>unified.cloudways.com/signup?coupon=CWFEST20</strong></a> (code <code>CWFEST20</code>). From there you have two paths:</p>
<div class="two">
<article><small>NO CARD</small><h3>Trial only</h3>
<p>Skip the credit card and use the platform on trial:</p>
<ul>
<li><strong>Flexible</strong> or <strong>Autonomous</strong>: 2&nbsp;GB or 4&nbsp;GB server</li>
<li><strong>Velocity</strong>: Starter pack (2&nbsp;GB server)</li>
</ul></article>
<article><small>$20 CREDITS</small><h3>Add a card</h3>
<p>To unlock the <strong>$20 worth of credits</strong>, add your credit card details after signup with that link, then use the platform as usual.</p></article>
</div>
<p class="offer-lede" style="margin:28px 0 0"><strong>Winners:</strong> every winner gets a Cloudways Velocity <strong>Starter pack for 3 months</strong>.</p></div>

<div class="c-wide changed"><p class="sec-label">What changed in 2026</p><div class="three">
<article><small>AUTH</small><h3>Tokens replace API keys</h3><p>The email and API key flow ended on Oct 15, 2026. Send an Access Token as a Bearer header instead.</p></article>
<article><small>VERSION</small><h3>v2 is the current API</h3><p>The base URL is <code>api.cloudways.com/api/v2</code>. v1 is sunset, though some help articles still show it.</p></article>
<article><small>ACCESS</small><h3>Owners only</h3><p>Only the primary account owner can create tokens. Team members can't, so plan who holds the keys.</p></article></div></div>

<div class="c-wide index"><p class="sec-label">The path</p>@@INDEX@@</div>

@@SECTIONS@@

<section class="tut" id="resources"><div class="c-wide"><header class="th reveal"><span class="bn" aria-hidden="true">+</span><div><p class="eyebrow">Appendix</p><h1>Resources and safety</h1><p class="sub">Where to go next, and how not to get burned.</p></div></header></div>
<div class="c-read body reveal">@@EXTRA@@</div></section>
</main>

<nav id="toc" aria-label="On this page"><h5>On this page</h5><ul></ul></nav>

<footer class="end"><div class="c-wide"><h2>Now go <em>ship</em> something.</h2>
<div class="fgrid"><div><h6>About</h6><p>An unofficial community guide, checked against Cloudways documentation on @@UPDATED@@. Items marked <em>(verify)</em> were read from docs but not tested on a live account.</p></div>
<div><h6>Official</h6><p><a href="https://support.cloudways.com" target="_blank" rel="noopener">Help Center</a></p><p><a href="https://developers.cloudways.com/docs" target="_blank" rel="noopener">API reference</a></p><p><a href="https://developers.cloudways.com/play" target="_blank" rel="noopener">API Playground</a></p></div>
<div><h6>Build</h6><p>Regenerate this page with <code>python3 tools/build.py</code>.</p></div></div></div></footer>

<script>
(function(){
var root=document.documentElement,$=function(s,c){return (c||document).querySelector(s)},$$=function(s,c){return [].slice.call((c||document).querySelectorAll(s))};
$('#theme').addEventListener('click',function(){var d=root.classList.toggle('dark');try{localStorage.setItem('theme',d?'dark':'light')}catch(e){}});
var reduceMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href^="#"]');if(!a)return;var id=a.getAttribute('href').slice(1);if(!id)return;var el=document.getElementById(id);if(!el)return;e.preventDefault();el.scrollIntoView({behavior:reduceMotion?'auto':'smooth',block:'start'});try{history.pushState(null,'','#'+id)}catch(err){}});
$$('.copy').forEach(function(b){b.addEventListener('click',function(){var t=$('code',b.closest('.code')).innerText;
 function ok(){b.textContent='Copied';b.classList.add('done');setTimeout(function(){b.textContent='Copy';b.classList.remove('done')},1500)}
 function fb(){var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{document.execCommand('copy');ok()}catch(e){}a.remove()}
 if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(ok,fb)}else fb()})});
$$('.tabs').forEach(function(box){var tabs=$$('[role=tab]',box),panels=$$('[role=tabpanel]',box);
 function pick(i,focus){tabs.forEach(function(t,k){var s=k===i;t.setAttribute('aria-selected',s);t.tabIndex=s?0:-1;panels[k].hidden=!s});if(focus)tabs[i].focus()}
 tabs.forEach(function(t,i){t.addEventListener('click',function(){pick(i)});t.addEventListener('keydown',function(e){
  var n=tabs.length;if(e.key==='ArrowRight'){e.preventDefault();pick((i+1)%n,1)}else if(e.key==='ArrowLeft'){e.preventDefault();pick((i-1+n)%n,1)}else if(e.key==='Home'){e.preventDefault();pick(0,1)}else if(e.key==='End'){e.preventDefault();pick(n-1,1)}})})});
if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -8% 0px',threshold:.04});$$('.reveal').forEach(function(el){io.observe(el)})}else{$$('.reveal').forEach(function(el){el.classList.add('in')})}
var links=$$('[data-spy]'),secs=links.map(function(l){return document.getElementById(l.dataset.spy)}),toc=$('#toc'),tocUl=$('ul',toc),curSec=null,tocLinks=[];
function buildToc(sec){tocUl.innerHTML='';tocLinks=[];if(!sec){toc.classList.remove('show');return}
 var hs=$$('h2',sec);if(!hs.length){toc.classList.remove('show');return}
 hs.forEach(function(h){if(!h.id)return;var li=document.createElement('li'),a=document.createElement('a');a.href='#'+h.id;a.textContent=h.textContent;li.appendChild(a);tocUl.appendChild(li);tocLinks.push([a,h])});toc.classList.add('show')}
function onScroll(){var y=window.scrollY,h=document.documentElement.scrollHeight-innerHeight;$('#prog').style.width=(h>0?y/h*100:0)+'%';
 var ref=y+innerHeight*.3,cur=-1;secs.forEach(function(s,i){if(s&&s.offsetTop<=ref)cur=i});
 links.forEach(function(l,i){l.classList.toggle('on',i===cur)});
 var sec=cur>=0?secs[cur]:null;if(sec!==curSec){curSec=sec;buildToc(sec);var menu=$('nav.menu'),on=$('a.on',menu);if(menu&&on){var left=on.offsetLeft-menu.clientWidth/2+on.clientWidth/2;menu.scrollTo({left:Math.max(0,left),behavior:'auto'})}}
 var act=null;tocLinks.forEach(function(p){if(p[1].getBoundingClientRect().top<innerHeight*.35)act=p[0]});tocLinks.forEach(function(p){p[0].classList.toggle('on',p[0]===act)})}
addEventListener('scroll',onScroll,{passive:true});addEventListener('resize',onScroll);onScroll();
})();
</script></body></html>'''

if __name__ == "__main__":
    build_guide()
    build_html()
    print("built GUIDE.md and site/index.html")
