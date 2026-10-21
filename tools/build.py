#!/usr/bin/env python3
"""Regenerate GUIDE.md and index.html from README.md + tutorials/*/README.md.

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
UPDATED = "October 21, 2026"

TUTORIALS = [
    ("01-first-server", "First server and app", "Start the free trial, launch a server, connect over SSH/SFTP.", "10 min", "🚀"),
    ("02-deploy-apps", "Deploy apps", "WordPress, Git deployments, Laravel/PHP, and Node.js on Velocity.", "20 min", "📦"),
    ("03-api-and-automation", "API and automation", "Access Tokens, the v2 API, and scripts to run your fleet.", "20 min", "⚙️"),
    ("04-mcp-ai-agents", "MCP and AI agents", "Drive Cloudways from Claude, Cursor, VS Code and more.", "15 min", "🤖"),
    ("05-ops-basics", "Ops basics", "Domains, SSL, backups, staging, monitoring, scaling.", "15 min", "🛠️"),
]


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
        return f"`{text}`" if text.startswith("`") is False else text

    guide = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", fix, guide)
    (ROOT / "GUIDE.md").write_text(guide, encoding="utf-8")
    return guide


# ---------------------------------------------------------------- index.html
def md_to_html(text):
    return markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])


def strip_md_links(md_text, tutorial_ids):
    """Relative links -> section anchors or plain code; external links kept."""
    def fix(m):
        label, target = m.group(1), m.group(2)
        if target.startswith(("http://", "https://", "#")):
            return m.group(0)
        mt = re.search(r"(\d\d)-[a-z-]+/README\.md", target)
        if mt and int(mt.group(1)) <= len(tutorial_ids):
            return f"[{label}](#t{int(mt.group(1))})"
        clean = re.sub(r"^(\.\./)+|^\./", "", target)
        if REPO_URL:
            return f"[{label}]({REPO_URL}/blob/main/{clean})"
        return label if label.startswith("`") else f"`{label}`"
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", fix, md_text)


def decorate(body):
    # blockquotes -> callouts
    def callout(m):
        inner = m.group(1)
        kind, icon = "note", "ℹ️"
        low = inner.lower()
        if "tip" in low[:60]:
            kind, icon = "tip", "💡"
        elif "disclaimer" in low[:60] or "warning" in low[:60]:
            kind, icon = "warn", "⚠️"
        return f'<div class="callout {kind}"><span class="ci">{icon}</span><div>{inner}</div></div>'
    body = re.sub(r"<blockquote>\s*(.*?)\s*</blockquote>", callout, body, flags=re.S)

    # code blocks -> framed with copy button
    def code(m):
        cls = m.group(1) or ""
        lang = ""
        ml = re.search(r"language-(\w+)", cls)
        if ml:
            lang = ml.group(1)
        return (f'<div class="code"><div class="codebar"><span>{lang or "text"}</span>'
                f'<button class="copy" type="button">Copy</button></div>'
                f'<pre><code{(" class=" + chr(34) + cls + chr(34)) if cls else ""}>{m.group(2)}</code></pre></div>')
    body = re.sub(r'<pre><code(?: class="([^"]*)")?>(.*?)</code></pre>', code, body, flags=re.S)

    # checkbox lists
    body = body.replace("<li>[ ] ", '<li class="todo"><input type="checkbox"> ')
    body = body.replace("<li>[x] ", '<li class="todo"><input type="checkbox" checked> ')
    # tables: wrap for horizontal scroll
    body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
    # external links open in new tab
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener"', body)
    return body


def section_html(idx, tid, title, blurb, mins, icon):
    md_text = read(f"tutorials/{tid}/README.md")
    md_text = re.sub(r"^# .*\n", "", md_text, count=1)  # drop h1; we render our own header
    md_text = strip_md_links(md_text, TUTORIALS)
    body = decorate(md_to_html(md_text))
    # give h2s ids for nav
    def h2(m):
        slug = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", m.group(1)).lower()).strip("-")
        return f'<h2 id="t{idx}-{slug}">{m.group(1)}</h2>'
    body = re.sub(r"<h2>(.*?)</h2>", h2, body)
    return f'''<section class="tut" id="t{idx}">
  <header class="tuthead"><div class="num">{icon}<b>{idx}</b></div>
    <div><h1>{html.escape(title)}</h1><p>{html.escape(blurb)} <span class="mins">~{mins}</span></p></div></header>
  {body}
</section>'''


def build_html():
    sections = "\n".join(section_html(i + 1, *t[:2], t[2], t[3], t[4]) if False else
                         section_html(i + 1, t[0], t[1], t[2], t[3], t[4]) for i, t in enumerate(TUTORIALS))

    readme = read("README.md")
    extra_md = ""
    for h in ("Additional resources", "Safety notes for hackers"):
        m = re.search(rf"^## {h}\n(.*?)(?=^## |\Z)", readme, flags=re.S | re.M)
        if m:
            extra_md += f"## {h}\n{m.group(1)}\n"
    extra = decorate(md_to_html(strip_md_links(extra_md, TUTORIALS)))

    cards = "".join(
        f'<a class="card" href="#t{i+1}"><div class="cicon">{t[4]}</div><div><h3>{i+1}. {html.escape(t[1])}</h3>'
        f'<p>{html.escape(t[2])}</p><span class="mins">~{t[3]}</span></div></a>'
        for i, t in enumerate(TUTORIALS))

    nav = ""
    for i, t in enumerate(TUTORIALS):
        nav += f'<a class="navt" href="#t{i+1}" data-spy="t{i+1}"><span>{i+1}</span>{html.escape(t[1])}</a>'
    nav += '<a class="navt" href="#resources" data-spy="resources"><span>★</span>Resources & safety</a>'

    page = TEMPLATE.format(updated=UPDATED, cards=cards, nav=nav, sections=sections, extra=extra)
    (ROOT / "index.html").write_text(page, encoding="utf-8")


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cloudways Cookbook: a hacker's guide to getting started</title>
<meta name="description" content="Hands-on guides for launching, deploying, and automating on Cloudways: API v2, MCP, Git, ops basics.">
<style>
:root{{--bg:#fbfbfd;--panel:#fff;--ink:#16202e;--mut:#5d6b7e;--line:#e4e9f1;--acc:#2f6bff;--acc2:#7c4dff;--accbg:#eef3ff;--code:#0f1724;--codeink:#e6edf7;--shadow:0 1px 2px rgba(16,24,40,.05),0 8px 24px rgba(16,24,40,.06)}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0c111b;--panel:#121927;--ink:#e8edf6;--mut:#93a0b5;--line:#243047;--acc:#6b95ff;--acc2:#a58bff;--accbg:#16213a;--code:#080c14;--codeink:#e6edf7;--shadow:0 1px 2px rgba(0,0,0,.4),0 8px 24px rgba(0,0,0,.3)}}}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth;scroll-padding-top:20px}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 Inter,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;display:flex;-webkit-font-smoothing:antialiased}}
a{{color:var(--acc);text-decoration:none}}a:hover{{text-decoration:underline}}
/* sidebar */
aside{{position:sticky;top:0;align-self:flex-start;height:100vh;width:280px;flex:none;padding:26px 18px;border-right:1px solid var(--line);background:var(--panel);overflow:auto}}
.brand{{display:flex;align-items:center;gap:10px;font-weight:700;font-size:16px;margin-bottom:22px;color:var(--ink)}}
.logo{{width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,var(--acc),var(--acc2));display:grid;place-items:center;color:#fff;font-size:17px}}
.navt{{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:9px;color:var(--mut);font-size:14.5px;font-weight:500}}
.navt span{{width:22px;height:22px;border-radius:7px;background:var(--accbg);color:var(--acc);display:grid;place-items:center;font-size:12px;font-weight:700;flex:none}}
.navt:hover{{background:var(--accbg);text-decoration:none;color:var(--ink)}}
.navt.on{{background:var(--accbg);color:var(--ink)}}.navt.on span{{background:var(--acc);color:#fff}}
.side-foot{{margin-top:22px;padding-top:16px;border-top:1px solid var(--line);font-size:12.5px;color:var(--mut)}}
/* main */
main{{flex:1;min-width:0}}.wrap{{max-width:900px;margin:0 auto;padding:0 40px 120px}}
.hero{{margin:0 -40px;padding:72px 40px 56px;background:radial-gradient(1200px 400px at 10% -10%,rgba(47,107,255,.16),transparent 60%),radial-gradient(900px 400px at 100% 0,rgba(124,77,255,.14),transparent 55%)}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px}}
.chip{{font-size:12.5px;font-weight:600;padding:5px 11px;border-radius:999px;background:var(--panel);border:1px solid var(--line);color:var(--mut)}}
.hero h1{{font-size:clamp(34px,5vw,52px);line-height:1.1;margin:0 0 16px;letter-spacing:-.025em}}
.grad{{background:linear-gradient(90deg,var(--acc),var(--acc2));-webkit-background-clip:text;background-clip:text;color:transparent}}
.hero p.lead{{font-size:19px;color:var(--mut);max-width:640px;margin:0 0 28px}}
.btns{{display:flex;gap:12px;flex-wrap:wrap}}
.btn{{display:inline-block;padding:11px 20px;border-radius:11px;font-weight:600;font-size:15px}}
.btn.p{{background:linear-gradient(135deg,var(--acc),var(--acc2));color:#fff;box-shadow:0 6px 18px rgba(47,107,255,.3)}}
.btn.s{{background:var(--panel);border:1px solid var(--line);color:var(--ink)}}.btn:hover{{text-decoration:none;transform:translateY(-1px)}}
h2.sec{{font-size:13px;letter-spacing:.09em;text-transform:uppercase;color:var(--mut);margin:44px 0 14px;border:0}}
.heads{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.head{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:var(--shadow);font-size:14.5px;line-height:1.55}}
.head b{{display:block;font-size:15px;margin-bottom:4px}}
.cards{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
.card{{display:flex;gap:14px;padding:18px;background:var(--panel);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow);color:var(--ink);transition:.15s}}
.card:hover{{transform:translateY(-2px);border-color:var(--acc);text-decoration:none}}
.card h3{{margin:0 0 4px;font-size:16.5px}}.card p{{margin:0 0 6px;color:var(--mut);font-size:14.5px;line-height:1.5}}
.cicon{{font-size:26px;width:46px;height:46px;border-radius:12px;background:var(--accbg);display:grid;place-items:center;flex:none}}
.mins{{font-size:12px;color:var(--acc);font-weight:600;background:var(--accbg);padding:2px 8px;border-radius:999px;white-space:nowrap}}
/* tutorial sections */
.tut{{margin-top:72px;padding-top:8px}}
.tuthead{{display:flex;gap:16px;align-items:center;margin-bottom:18px;padding-bottom:18px;border-bottom:1px solid var(--line)}}
.num{{width:58px;height:58px;border-radius:16px;background:linear-gradient(135deg,var(--acc),var(--acc2));color:#fff;display:grid;place-items:center;flex:none;position:relative;font-size:22px}}
.num b{{position:absolute;right:-6px;bottom:-6px;background:var(--panel);color:var(--acc);font-size:12px;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;border:2px solid var(--bg)}}
.tuthead h1{{margin:0;font-size:30px;letter-spacing:-.02em;line-height:1.2}}.tuthead p{{margin:4px 0 0;color:var(--mut)}}
.tut h2{{font-size:21px;margin:38px 0 10px;letter-spacing:-.01em}}.tut h3{{font-size:17px;margin:26px 0 8px}}
.tut p,.tut li{{color:var(--ink)}}.tut ul,.tut ol{{padding-left:22px}}.tut li{{margin:5px 0}}
code{{font:.88em ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--accbg);color:var(--acc);padding:2px 6px;border-radius:6px}}
.code{{margin:16px 0;border-radius:12px;overflow:hidden;background:var(--code);box-shadow:var(--shadow);border:1px solid #1d2840}}
.codebar{{display:flex;justify-content:space-between;align-items:center;padding:7px 12px;background:#141d30;color:#8fa0bd;font:600 11.5px ui-monospace,Menlo,monospace;text-transform:uppercase;letter-spacing:.06em}}
.copy{{background:#22304d;color:#cfd9ee;border:0;border-radius:7px;padding:4px 10px;font:600 11.5px inherit;cursor:pointer}}.copy:hover{{background:var(--acc);color:#fff}}
.code pre{{margin:0;padding:14px 16px;overflow:auto}}.code code{{background:none;color:var(--codeink);padding:0;font-size:13.5px;line-height:1.6}}
.tablewrap{{overflow:auto;margin:16px 0;border:1px solid var(--line);border-radius:12px;background:var(--panel);box-shadow:var(--shadow)}}
table{{border-collapse:collapse;width:100%;font-size:14.5px}}th,td{{padding:10px 14px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}}
th{{background:var(--accbg);font-size:12.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut)}}tr:last-child td{{border-bottom:0}}
.callout{{display:flex;gap:12px;margin:18px 0;padding:14px 16px;border-radius:12px;border:1px solid var(--line);background:var(--accbg)}}
.callout p{{margin:0}}.callout .ci{{font-size:18px;line-height:1.5}}
.callout.tip{{background:rgba(16,185,129,.1);border-color:rgba(16,185,129,.35)}}.callout.warn{{background:rgba(245,158,11,.1);border-color:rgba(245,158,11,.4)}}
li.todo{{list-style:none;margin-left:-20px}}li.todo input{{margin-right:8px;accent-color:var(--acc)}}
.foot{{margin-top:80px;padding-top:24px;border-top:1px solid var(--line);color:var(--mut);font-size:13.5px}}
@media(max-width:900px){{body{{display:block}}aside{{position:static;height:auto;width:auto;border:0;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:4px}}.brand{{width:100%;margin-bottom:8px}}.side-foot{{display:none}}.wrap{{padding:0 20px 80px}}.hero{{margin:0 -20px;padding:48px 20px 36px}}.heads,.cards{{grid-template-columns:1fr}}}}
</style></head><body>
<aside><a class="brand" href="#top"><span class="logo">☁</span>Cloudways Cookbook</a>{nav}
<div class="side-foot">Fact-checked against Cloudways docs on {updated}. Unofficial community guide.</div></aside>
<main><div class="wrap" id="top">
<div class="hero"><div class="chips"><span class="chip">Updated {updated}</span><span class="chip">API v2</span><span class="chip">MCP ready</span><span class="chip">For developers</span></div>
<h1>Ship on <span class="grad">Cloudways</span><br>in an afternoon.</h1>
<p class="lead">A hands-on cookbook for hackers: launch a server, deploy with Git, automate with the v2 API, and drive it all from an AI agent.</p>
<div class="btns"><a class="btn p" href="#t1">Start with tutorial 1</a><a class="btn s" href="#t3">Jump to the API</a></div></div>
<h2 class="sec">Three things changed in 2026</h2>
<div class="heads">
<div class="head"><b>🔑 Access Tokens, not API keys</b>The legacy email + API key flow was scheduled to end on Oct 15, 2026. Send <code>Bearer</code> tokens.</div>
<div class="head"><b>🧭 API v2 is current</b>Base URL <code>https://api.cloudways.com/api/v2</code>. v1 is sunset and some help articles still show it.</div>
<div class="head"><b>👤 Owner-only tokens</b>Only the primary account owner can create tokens. Team members can't.</div></div>
<h2 class="sec">The path</h2><div class="cards">{cards}</div>
{sections}
<section class="tut" id="resources"><header class="tuthead"><div class="num">★</div><div><h1>Resources &amp; safety</h1><p>Where to go next, and how not to get burned.</p></div></header>{extra}</section>
<div class="foot">Unofficial, community-style guide. Verify details in the <a href="https://support.cloudways.com" target="_blank" rel="noopener">Cloudways Help Center</a> and <a href="https://developers.cloudways.com/play" target="_blank" rel="noopener">API Playground</a>. Items marked <em>(verify)</em> were read from docs but not tested on a live account. Generated by <code>tools/build.py</code>.</div>
</div></main>
<script>
document.querySelectorAll('.copy').forEach(function(b){{b.addEventListener('click',function(){{
 var t=b.closest('.code').querySelector('code').innerText;
 function ok(){{b.textContent='Copied';setTimeout(function(){{b.textContent='Copy'}},1400)}}
 if(navigator.clipboard&&navigator.clipboard.writeText){{navigator.clipboard.writeText(t).then(ok,fb)}}else fb();
 function fb(){{var a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();try{{document.execCommand('copy');ok()}}catch(e){{}}a.remove()}}
}})}});
var links=[].slice.call(document.querySelectorAll('[data-spy]'));
var secs=links.map(function(l){{return document.getElementById(l.dataset.spy)}});
function spy(){{var y=window.scrollY+140,cur=0;secs.forEach(function(s,i){{if(s&&s.offsetTop<=y)cur=i}});links.forEach(function(l,i){{l.classList.toggle('on',i===cur)}})}}
window.addEventListener('scroll',spy,{{passive:true}});spy();
</script></body></html>'''

if __name__ == "__main__":
    build_guide()
    build_html()
    print("built GUIDE.md and index.html")
