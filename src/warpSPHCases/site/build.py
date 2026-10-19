"""Page build: ``case.yaml`` + ``page.md`` + trajectories -> ``build/``.

Outputs (all under ``build/``, gitignored)::

    build/<slug>/                        figures, loop.mp4, tables.json (raw recipe output)
    build/site/_cases/<slug>.md          the Jekyll page
    build/site/assets/img/cases/<slug>/  the files that page references
    build/preview/<slug>/index.html      standalone HTML preview (same body, no Jekyll)

``page.md`` is hand-written Markdown with generator directives on lines of their own:
``<<hero>>``, ``<<colab>>``, ``<<figure:ID>>``, ``<<table:ID>>``, ``<<command:RUNID>>``,
``<<reproduce>>`` and ``<<refs>>``. Everything measured comes from the trajectories.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from .. import figures
from ..spec import Page
from ..store import Trajectory
from .bib import bibPath, readBib
from .preview import renderPreview, writeIndex

__all__ = ['buildPage', 'checkPage', 'runCommand']

_DIRECTIVE = re.compile(r'^<<(\w+)(?::([\w\-.]+))?>>[ \t]*$', re.M)
_CITE = re.compile(r'\{%\s*cite\s+(\S+)')
#: the loop is the page's lead media; the site rule is MP4 + poster, small
LOOP_MAX_BYTES = 2_000_000
LOOP_MAX_WIDTH = 720

_CLASS = 'img-fluid rounded z-depth-1'


def runCommand(page: Page, runId: str) -> str:
    """The ``warpsph-run`` line that reproduces a run's configuration."""
    run = page.run(runId)
    parts = ['warpsph-run', run.case, '--scheme', run.scheme, '--nx', str(run.nx)]
    for k, v in {**run.spec, **run.params}.items():
        if k == 'params':
            continue
        parts += [f'--{k}', str(v)]
    parts += ['--plot', '--video', '--store', '--storeMode', 'trajectory']
    return '```bash\n' + ' '.join(parts) + '\n```'


def _assetPath(slug: str, name: str) -> str:
    return f'assets/img/cases/{slug}/{name}'


def _figureInclude(page: Page, fig: Dict[str, Any], files: List[Path]) -> str:
    slug = page.slug
    if fig['kind'] in ('loop', 'loop2d', 'loop_tank'):
        return ('{% include video.liquid '
                f'sources="{_assetPath(slug, fig["id"] + ".mp4")}" poster="{_assetPath(slug, fig["id"] + "-poster.jpg")}" '
                f'class="{_CLASS}" autoplay=true loop=true muted=true playsinline=true %}}')
    png = next(f for f in files if f.suffix == '.png')
    caption = ' '.join(str(fig.get('caption', '')).split())
    alt = fig.get('alt', caption)
    extra = f' caption="{caption}"' if caption else ''
    return ('{% include figure.liquid '
            f'path="{_assetPath(slug, png.name)}" class="{_CLASS}" zoomable=true alt="{alt}"{extra} %}}')


def _reproduce(page: Page, ctx: figures.Context) -> str:
    runs = [r for r in page.publicRuns if r.tier == 'reference']
    commits: Dict[str, str] = {}
    gpus = set()
    for r in runs:
        t = ctx.traj(r.id).timing
        if t is None:
            continue
        commits.update(t.commits or {})
        gpus.add(t.gpu or 'unknown')
    pretty = ', '.join(f'{k} `{v.replace("+dirty", "")}`' + (' (with uncommitted local changes)' if v.endswith('+dirty') else '')
                       for k, v in commits.items() if k in ('warpSPH', 'warpSPHCore'))
    precision = ctx.traj(runs[0].id).caseSpec.get('precision', 'float32')
    lines = [f'- Versions: {pretty or "not recorded"}.',
             f'- Hardware: {", ".join(sorted(gpus)) or "not recorded"}; precision {precision}.',
             f'- {len(runs)} reference runs.',
             f'- Every run is described by its `caseSpec.json` (`warpsph-run --config`); the checksums and provenance of the '
             f'trajectories are in `cases/{page.family}/{page.slug}/artifacts.json` of '
             '[warpSPHCases](https://github.com/wi-re/warpSPHCases).',
             '- Full trajectories are not stored in the repository; a download link is added here when they are published.',
             f'- Page built {date.today().isoformat()}.']
    if page.meta.get('notebook'):
        lines.insert(0, '- Notebook: see the Colab badge at the top.')
    return '\n'.join(lines)


def _expand(page: Page, text: str, ctx: figures.Context, made: Dict[str, List[Path]], tables: Dict[str, Dict]) -> str:
    figs = {f['id']: f for f in page.meta.get('figures', [])}

    def sub(m):
        kind, arg = m.group(1), m.group(2)
        if kind == 'hero':
            hero = next(f for f in page.meta['figures'] if f['kind'] in ('loop', 'loop2d', 'loop_tank'))
            return _figureInclude(page, hero, made[hero['id']])
        if kind == 'figure':
            return _figureInclude(page, figs[arg], made[arg])
        if kind == 'table':
            return tables[arg]['markdown']
        if kind == 'command':
            return runCommand(page, arg)
        if kind == 'colab':
            nb = page.meta.get('notebook')
            if not nb:
                return ''
            url = f'https://colab.research.google.com/github/wi-re/warpSPHCases/blob/main/cases/{page.family}/{page.slug}/{nb}'
            return f'[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})'
        if kind == 'reproduce':
            return _reproduce(page, ctx)
        if kind == 'refs':
            return '{% bibliography --file cases --cited_in_order %}'
        raise KeyError(f'{page.slug}/page.md: unknown directive <<{kind}>>')

    return _DIRECTIVE.sub(sub, text)


def _refuseFailingRuns(page: Page, ctx: figures.Context) -> None:
    """A page shows only runs that track their reference: failing ones belong in ``case.internal.yaml``."""
    bad = []
    for run in page.publicRuns:
        traj = ctx.traj(run.id)
        if traj.timing is not None and traj.timing.diverged:
            bad.append(f'{run.id}: diverged')
            continue
        try:
            reason = ctx.reference(run.id).flag(ctx.reference(run.id).metrics(traj))
        except Exception:
            reason = ''
        if reason:
            bad.append(f'{run.id}: {reason}')
    if bad:
        raise ValueError(f'{page.slug}: public runs that fail their reference (move them to case.internal.yaml, '
                         'track them in local/INTERNAL_FINDINGS.md):\n  ' + '\n  '.join(bad))


def _frontMatter(page: Page, ctx: figures.Context) -> Dict[str, Any]:
    site = page.meta.get('site', {})
    img = site.get('img', 'hero')
    return {
        'layout': 'page',
        'title': page.title,
        'description': ' '.join(page.meta['description'].split()),
        'img': _assetPath(page.slug, f'{img}-poster.jpg'),
        'importance': site.get('importance', 5),
        'category': page.family,
        'solvers': ', '.join(page.meta.get('solvers', [])),
        'schemes': ', '.join(page.meta.get('schemes', [])),
        'status': page.meta['status'],
    }


def _yamlValue(v: Any) -> str:
    """Plain scalars where YAML allows them (the site's front matter is unquoted), JSON-quoted otherwise."""
    if isinstance(v, str) and (not v or re.search(r'[:#\'"{}\[\],&*!|>%@`]|^\s|\s$|^[-?]', v)):
        return json.dumps(v)
    return str(v)


def buildPage(page: Page, skipVideo: bool = False, allowMissing: bool = False) -> Path:
    if allowMissing:     # interim page: leave out runs that have not finished yet (never for a publish)
        page.exclude = {r.id for r in page.publicRuns if not (page.runDir(r.id) / 'trajectory.h5').exists()}
        if page.exclude:
            print(f'[{page.slug}] INTERIM build, left out: {sorted(page.exclude)}')
    outDir = page.buildDir()
    outDir.mkdir(parents=True, exist_ok=True)
    ctx = figures.Context(page, outDir)
    made: Dict[str, List[Path]] = {}
    try:
        _refuseFailingRuns(page, ctx)
        for fig in page.meta.get('figures', []):
            if skipVideo and fig['kind'] in ('loop', 'loop2d', 'loop_tank') and (outDir / f'{fig["id"]}.mp4').exists():
                made[fig['id']] = [outDir / f'{fig["id"]}.mp4', outDir / f'{fig["id"]}-poster.jpg']
                continue
            print(f'[{page.slug}] figure {fig["id"]} ({fig["kind"]})', flush=True)
            made[fig['id']] = figures.render(ctx, fig)
        tables = {}
        for table in page.meta.get('tables', []):
            print(f'[{page.slug}] table {table["id"]}', flush=True)
            tables[table['id']] = figures.renderTable(ctx, table)
        (outDir / 'tables.json').write_text(json.dumps(tables, indent=1))

        body = _expand(page, (page.dir / 'page.md').read_text(), ctx, made, tables)
        unknown = sorted({k for k in _CITE.findall(body) if k not in readBib(bibPath(page.root))})
        if unknown:
            raise ValueError(f'{page.slug}: {{% cite %}} keys without an entry in data/references.bib: {unknown} '
                             '(add them from a verified lookup, never from memory)')
        front = _frontMatter(page, ctx)

        siteRoot = page.root / 'build' / 'site'
        assets = siteRoot / 'assets' / 'img' / 'cases' / page.slug
        if assets.exists():
            shutil.rmtree(assets)
        assets.mkdir(parents=True)
        for files in made.values():
            for f in files:
                shutil.copy2(f, assets / f.name)
        (siteRoot / '_cases').mkdir(parents=True, exist_ok=True)
        header = '---\n' + '\n'.join(f'{k}: {_yamlValue(v)}' for k, v in front.items()) + '\n---\n\n'
        pagePath = siteRoot / '_cases' / f'{page.slug}.md'
        pagePath.write_text(header + body)

        bib = readBib(bibPath(page.root))
        previewDir = page.root / 'build' / 'preview' / page.slug
        if previewDir.exists():
            shutil.rmtree(previewDir)
        (previewDir / 'assets' / 'img' / 'cases').mkdir(parents=True)
        shutil.copytree(assets, previewDir / 'assets' / 'img' / 'cases' / page.slug)
        preview = renderPreview(page, front, body, bib, previewDir / 'index.html')
        writeIndex(page.root / 'build' / 'preview')
        print(f'[{page.slug}] page   -> {pagePath}\n[{page.slug}] preview -> {preview}', flush=True)
    finally:
        ctx.close()
    problems = _checkBuilt(page)
    for p in problems:
        print(f'[{page.slug}] WARNING: {p}')
    return pagePath


def _checkBuilt(page: Page) -> List[str]:
    problems: List[str] = []
    siteRoot = page.root / 'build' / 'site'
    pagePath = siteRoot / '_cases' / f'{page.slug}.md'
    if not pagePath.exists():
        return [f'{pagePath} missing -- run build']
    text = pagePath.read_text()
    bib = readBib(bibPath(page.root))
    for key in _CITE.findall(text):
        if key not in bib:
            problems.append(f'{{% cite {key} %}} has no entry in data/references.bib')
    for ref in re.findall(r'(?:path|sources|poster|img)[=:]\s*"?(assets/img/cases/[^"\s,]+)', text):
        if not (siteRoot / ref).exists():
            problems.append(f'referenced file missing: {ref}')
    for mp4 in (siteRoot / 'assets' / 'img' / 'cases' / page.slug).glob('*.mp4'):
        if mp4.stat().st_size > LOOP_MAX_BYTES:
            problems.append(f'{mp4.name} is {mp4.stat().st_size / 1e6:.1f} MB (limit {LOOP_MAX_BYTES / 1e6:.0f} MB)')
    if page.meta.get('notebook') is None and '<<colab>>' in (page.dir / 'page.md').read_text():
        pass  # the badge simply is not rendered until a notebook exists
    return problems


def checkPage(page: Page) -> bool:
    """Static checks: runs present, artifacts manifest, built page references. Prints problems; True if none."""
    problems = _checkBuilt(page)
    for run in page.publicRuns:
        if not (page.runDir(run.id) / 'trajectory.h5').exists():
            problems.append(f'run {run.id}: no trajectory (run `warpsph-cases run {page.slug}`)')
    manifest = page.dir / 'artifacts.json'
    if not manifest.exists():
        problems.append('artifacts.json missing')
    for p in problems:
        print(f'[{page.slug}] {p}')
    print(f'[{page.slug}] {"OK" if not problems else f"{len(problems)} problem(s)"}')
    return not problems
