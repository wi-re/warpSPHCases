"""case.yaml loading, schema validation and the runs matrix.

A page is a folder ``cases/<family>/<slug>/`` with a ``case.yaml``; everything
else in the package (runs, derived quantities, figures, the site build) starts
from the :class:`Page` this module returns.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import yaml

__all__ = ['Page', 'RunEntry', 'findRoot', 'loadPage', 'allPages', 'validatePage']


def findRoot(start: Optional[os.PathLike] = None) -> Path:
    """The warpSPHCases checkout: ``$WARPSPHCASES_ROOT``, else the nearest parent holding ``cases/``."""
    env = os.environ.get('WARPSPHCASES_ROOT')
    if env:
        return Path(env).resolve()
    here = Path(start).resolve() if start else Path.cwd().resolve()
    for candidate in [here, *here.parents]:
        if (candidate / 'cases').is_dir() and (candidate / 'schemas').is_dir():
            return candidate
    # editable install: src/warpSPHCases/spec.py -> checkout root
    root = Path(__file__).resolve().parents[2]
    if (root / 'cases').is_dir():
        return root
    raise FileNotFoundError('No warpSPHCases checkout found (set WARPSPHCASES_ROOT).')


@dataclass
class RunEntry:
    """One row of a page's runs matrix. ``id`` names the run on disk and in the figures."""

    id: str
    case: str                       # registered warpSPH case name
    scheme: str
    nx: int
    variant: str = 'default'
    tier: str = 'reference'         # demo (Colab-sized) | reference (site / golden)
    spec: Dict[str, Any] = field(default_factory=dict)      # CaseSpec overrides
    params: Dict[str, Any] = field(default_factory=dict)    # Case.params overrides
    video: bool = True
    label: Optional[str] = None
    golden: bool = False
    #: False for rows from ``case.internal.yaml`` (gitignored): run and kept, never shown, built into the page,
    #: promoted to a golden or listed in the public manifest
    public: bool = True

    @property
    def legend(self) -> str:
        return self.label or self.scheme

    def caseSpecOverrides(self) -> Dict[str, Any]:
        overrides = dict(self.spec)
        overrides['scheme'] = self.scheme
        overrides['nx'] = self.nx
        if self.params:
            overrides['params'] = dict(self.params)
        return overrides


def runId(scheme: str, variant: str, nx: int) -> str:
    return f'{scheme}__{variant}__nx{nx}'


@dataclass
class Page:
    """A loaded ``case.yaml`` together with where it lives."""

    root: Path
    dir: Path
    meta: Dict[str, Any]
    #: run ids left out of figures and tables (an interim build while a sweep is still running)
    exclude: set = field(default_factory=set)

    @property
    def slug(self) -> str:
        return self.meta['slug']

    @property
    def family(self) -> str:
        return self.meta['family']

    @property
    def title(self) -> str:
        return self.meta['title']

    @property
    def runs(self) -> List[RunEntry]:
        """The runs matrix, public rows first, then the internal ones (``case.internal.yaml``).

        A row may give ``scheme``/``nx`` or ``schemes``/``nx`` as lists (cartesian product).
        """
        entries = self._expandRows(self.meta.get('runs') or [], public=True)
        internal = self.dir / 'case.internal.yaml'
        if internal.exists():
            rows = (yaml.safe_load(internal.read_text()) or {}).get('runs') or []
            entries += self._expandRows(rows, public=False)
        ids = [e.id for e in entries]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f'{self.slug}: duplicate run ids {sorted(dupes)}')
        return entries

    @property
    def publicRuns(self) -> List[RunEntry]:
        return [r for r in self.runs if r.public and r.id not in self.exclude]

    def _expandRows(self, rows, public: bool) -> List[RunEntry]:
        entries: List[RunEntry] = []
        for raw in rows:
            raw = dict(raw)
            schemes = raw.pop('schemes', None) or [raw.pop('scheme')]
            raw.pop('scheme', None)
            resolutions = raw.pop('nx')
            resolutions = resolutions if isinstance(resolutions, list) else [resolutions]
            variant = raw.pop('variant', 'default')
            raw.setdefault('case', self.meta['cases'][0])
            for scheme in schemes:
                for nx in resolutions:
                    entry = dict(raw)
                    entry['id'] = f'{raw["id"]}' if len(schemes) * len(resolutions) == 1 and 'id' in raw \
                        else runId(scheme, variant, nx)
                    entries.append(RunEntry(scheme=scheme, nx=nx, variant=variant, public=public, **entry))
        return entries

    def run(self, runId_: str) -> RunEntry:
        for entry in self.runs:
            if entry.id == runId_:
                return entry
        raise KeyError(f'{self.slug}: no run {runId_!r}; have {[r.id for r in self.runs]}')

    # -- where things live ---------------------------------------------------
    def resultsDir(self, run: Optional[str] = None) -> Path:
        base = self.root / 'results' / self.family / self.slug
        return base / run if run else base

    def trajectoryDir(self, run: Optional[str] = None) -> Path:
        base = self.root / 'trajectories' / self.family / self.slug
        return base / run if run else base

    def buildDir(self) -> Path:
        return self.root / 'build' / self.slug

    def runDir(self, run: str) -> Path:
        """The promoted trajectory directory when present, else the scratch run dir."""
        promoted = self.trajectoryDir(run)
        return promoted if (promoted / 'trajectory.h5').exists() else self.resultsDir(run)


def validatePage(meta: Dict[str, Any], root: Path) -> None:
    import jsonschema
    schema = json.loads((root / 'schemas' / 'case.schema.json').read_text())
    jsonschema.validate(meta, schema)


def loadPage(slug: str, root: Optional[os.PathLike] = None, validate: bool = True) -> Page:
    """Load ``cases/*/<slug>/case.yaml`` (``slug`` may also be a path to the page folder)."""
    base = Path(root).resolve() if root else findRoot()
    path = Path(slug)
    if path.is_dir() and (path / 'case.yaml').exists():
        pageDir = path.resolve()
    else:
        matches = sorted((base / 'cases').glob(f'*/{slug}/case.yaml'))
        if not matches:
            raise FileNotFoundError(f'No page {slug!r} under {base / "cases"}')
        pageDir = matches[0].parent
    meta = yaml.safe_load((pageDir / 'case.yaml').read_text())
    if validate:
        validatePage(meta, base)
    return Page(root=base, dir=pageDir, meta=meta)


def allPages(root: Optional[os.PathLike] = None, status: Optional[str] = None) -> Iterator[Page]:
    base = Path(root).resolve() if root else findRoot()
    for caseYaml in sorted((base / 'cases').glob('*/*/case.yaml')):
        page = loadPage(str(caseYaml.parent), root=base)
        if status is None or page.meta.get('status') == status:
            yield page
