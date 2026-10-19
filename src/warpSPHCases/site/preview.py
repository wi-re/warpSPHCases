"""Standalone HTML preview of a built page: what the Jekyll page will say, without Jekyll.

It renders the same Markdown + liquid body the site gets, mapping the three liquid
constructs the generator emits (``video.liquid`` and ``figure.liquid`` includes,
``cite`` / ``bibliography``) to plain HTML. It is a reading aid: fonts, spacing and the
navbar are not the site's, so the final look is checked on the real site build.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Dict, List

from markdown_it import MarkdownIt

from .bib import formatEntry

__all__ = ['renderPreview', 'writeIndex']

_INCLUDE = re.compile(r'\{%\s*include\s+(\S+)\s+(.*?)\s*%\}', re.S)
_ATTR = re.compile(r'([\w-]+)=("([^"]*)"|\S+)')
_CITE = re.compile(r'\{%\s*cite\s+(\S+)(?:\s+--file\s+\S+)?\s*%\}')
_BIBLIO = re.compile(r'\{%\s*bibliography[^%]*%\}')

_CSS = """
:root{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--rule:#e4e3df;--accent:#2a78d6;--code:#f2f1ee}
@media (prefers-color-scheme:dark){:root{--bg:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--rule:#363633;--accent:#6da7ec;--code:#242423}
 img.fig{filter:none}}
body{background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,sans-serif;margin:0}
main{max-width:860px;margin:0 auto;padding:24px 16px 80px}
h1{font-weight:500;margin:.2em 0 0}h2{font-weight:500;margin-top:2em;border-bottom:1px solid var(--rule);padding-bottom:.2em}
.desc{color:var(--ink2);margin-top:.2em}.banner{font-size:13px;color:var(--ink2);border:1px solid var(--rule);padding:6px 10px;border-radius:6px;margin-bottom:16px}
figure{margin:1.2em 0}figure img,figure video{max-width:100%;height:auto;border-radius:6px}
figcaption{color:var(--ink2);font-size:14px;margin-top:6px}
table{border-collapse:collapse;font-size:14px;display:block;overflow-x:auto}th,td{padding:4px 10px;border-bottom:1px solid var(--rule);text-align:left;white-space:nowrap}
code,pre{background:var(--code);border-radius:4px;font-size:13px}code{padding:1px 4px}pre{padding:10px;overflow-x:auto}pre code{padding:0}
a{color:var(--accent)}ol.refs li{margin:.4em 0;font-size:14px}
"""


def _attrs(text: str) -> Dict[str, str]:
    return {m.group(1): (m.group(3) if m.group(3) is not None else m.group(2)) for m in _ATTR.finditer(text)}


def renderPreview(page, frontMatter: Dict[str, str], body: str, bib: Dict[str, Dict[str, str]], outFile: Path) -> Path:
    cited: List[str] = []

    def cite(m):
        key = m.group(1)
        if key not in cited:
            cited.append(key)
        return f'<sup>[<a href="#ref-{key}">{cited.index(key) + 1}</a>]</sup>'

    def include(m):
        kind, a = m.group(1), _attrs(m.group(2))
        if kind == 'video.liquid':
            src = a['sources'].split(',')[0]
            return (f'<figure><video src="{src}" poster="{a.get("poster", "")}" autoplay loop muted playsinline controls>'
                    f'</video></figure>')
        if kind == 'figure.liquid':
            cap = f'<figcaption>{html.escape(a["caption"])}</figcaption>' if 'caption' in a else ''
            return f'<figure><img class="fig" src="{a["path"]}" alt="{html.escape(a.get("alt", ""))}">{cap}</figure>'
        return ''

    text = _INCLUDE.sub(include, body)
    text = _CITE.sub(cite, text)
    md = MarkdownIt('commonmark', {'html': True}).enable('table')
    content = md.render(text)
    refs = '<ol class="refs">' + ''.join(
        f'<li id="ref-{k}">{formatEntry(bib[k])}</li>' for k in cited) + '</ol>'
    content = _BIBLIO.sub(lambda _: refs, content)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(frontMatter['title'])} - preview</title><style>{_CSS}</style>
<script>window.MathJax={{tex:{{inlineMath:[['$','$']]}}}}</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"></script></head>
<body><main><div class="banner">Local preview of <code>_cases/{page.slug}.md</code> -- not the site's styling. <a href="../index.html">all pages</a></div>
<h1>{html.escape(frontMatter['title'])}</h1><p class="desc">{html.escape(frontMatter['description'])}</p>
{content}</main></body></html>"""
    outFile.parent.mkdir(parents=True, exist_ok=True)
    outFile.write_text(doc)
    return outFile


def writeIndex(previewRoot: Path) -> Path:
    cards = []
    for index in sorted(previewRoot.glob('*/index.html')):
        slug = index.parent.name
        title = re.search(r'<h1>(.*?)</h1>', index.read_text()).group(1)
        poster = next(index.parent.glob('assets/img/cases/*/hero-poster.jpg'), None)
        img = f'<img src="{slug}/{poster.relative_to(index.parent)}" width="240">' if poster else ''
        cards.append(f'<li style="margin:1em 0"><a href="{slug}/index.html">{title}</a><br>{img}</li>')
    out = previewRoot / 'index.html'
    out.write_text(f'<!doctype html><meta charset="utf-8"><title>cases preview</title><style>{_CSS}</style>'
                   f'<main><h1>Case pages (local preview)</h1><ul>{"".join(cards)}</ul></main>')
    return out
