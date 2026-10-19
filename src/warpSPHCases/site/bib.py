"""The cases bibliography (``data/references.bib``): a small BibTeX reader and a plain formatter.

Entries are never typed from memory: they are copied from warpSPH's verified
``literature/references.bib`` or fetched by DOI (see the header of the file). The
build refuses a ``{% cite %}`` whose key is not here.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict

__all__ = ['readBib', 'formatEntry', 'bibPath']


def bibPath(root: Path) -> Path:
    return root / 'data' / 'references.bib'


def readBib(path: Path) -> Dict[str, Dict[str, str]]:
    text = path.read_text()
    entries: Dict[str, Dict[str, str]] = {}
    for m in re.finditer(r'@(\w+)\s*\{\s*([^,\s]+)\s*,', text):
        depth, i = 1, m.end()
        while depth and i < len(text):
            depth += {'{': 1, '}': -1}.get(text[i], 0)
            i += 1
        body = text[m.end():i - 1]
        fields: Dict[str, str] = {'_type': m.group(1).lower()}
        for f in re.finditer(r'(\w+)\s*=\s*', body):
            j = f.end()
            if body[j] == '{':
                d, k = 1, j + 1
                while d:
                    d += {'{': 1, '}': -1}.get(body[k], 0)
                    k += 1
                value = body[j + 1:k - 1]
            elif body[j] == '"':
                k = body.index('"', j + 1)
                value = body[j + 1:k]
            else:
                value = re.match(r'[^,\s]+', body[j:]).group(0)
            fields[f.group(1).lower()] = re.sub(r'\s+', ' ', value).strip()
        entries[m.group(2)] = fields
    return entries


_ACCENTS = {"'": '\u0301', '`': '\u0300', '"': '\u0308', '^': '\u0302', '~': '\u0303', 'c': '\u0327'}


def _tex(text: str) -> str:
    """BibTeX/LaTeX markup in a field -> plain Unicode (greek letters, accents; braces and math dollars dropped)."""
    import unicodedata
    text = text.replace('\\delta', '\u03b4').replace('\\alpha', '\u03b1').replace('\\nu', '\u03bd')
    text = re.sub(r"\\(['`\"^~c])\s*\{?(\w)\}?", lambda m: unicodedata.normalize('NFC', m.group(2) + _ACCENTS[m.group(1)]), text)
    return re.sub(r'[{}$]', '', text)


def _authors(raw: str) -> str:
    names = [a.strip() for a in raw.split(' and ')]
    out = []
    for n in names:
        if ',' in n:
            last, first = [p.strip() for p in n.split(',', 1)]
        else:
            parts = n.split()
            last, first = parts[-1], ' '.join(parts[:-1])
        initials = ' '.join(p[0] + '.' for p in re.split(r'[\s-]+', first) if p)
        out.append(f'{last}, {initials}'.strip(', '))
    return out[0] if len(out) == 1 else ', '.join(out[:-1]) + ' & ' + out[-1]


def formatEntry(e: Dict[str, str]) -> str:
    """One reference as an HTML string (authors, year, title, venue, doi link)."""
    parts = [f'{_authors(_tex(e["author"]))} ({e.get("year", "")}). {_tex(e["title"])}.']
    venue = _tex(e.get('journal') or e.get('booktitle') or '')
    if venue:
        vol = e.get('volume', '')
        if vol and e.get('number'):
            vol += f'({e["number"]})'
        pages = e.get('pages', '').replace('--', '–')
        parts.append(f'<i>{venue}</i>' + (f', {vol}' if vol else '') + (f', {pages}' if pages else '') + '.')
    if e.get('doi'):
        parts.append(f'<a href="https://doi.org/{e["doi"]}">doi:{e["doi"]}</a>')
    return ' '.join(parts).replace('--', '–')
