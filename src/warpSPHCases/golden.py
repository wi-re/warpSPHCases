"""Golden outputs: small final-state references kept in git, and the regression check against them.

``promote`` stores, for each run marked ``golden: true``, the final frame's fields
(``golden/<runid>.npz``). ``compare`` re-runs those rows, writes them under ``results/_golden/``
and compares field by field with an explicit tolerance. Runs are deterministic on one GPU and
driver but not across hardware, so the default tolerance is loose (relative L2 of the difference,
1e-3) and ``strict`` demands exact equality for same-machine checks. A golden is regenerated
deliberately (``promote --force``), never silently.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from .spec import Page
from .store import Trajectory

__all__ = ['promoteGolden', 'compareGolden', 'goldenPath']

_FIELDS = ('positions', 'velocities', 'densities', 'internalEnergies')


def goldenPath(page: Page, runId: str) -> Path:
    return page.dir / 'golden' / f'{runId}.npz'


def _final(traj: Trajectory) -> Dict[str, np.ndarray]:
    frame = traj.frame(-1)
    out = {k: frame[k] for k in _FIELDS if k in frame}
    out['t'] = np.array(frame['t'])
    out['nSteps'] = np.array(traj.timing.nSteps if traj.timing else -1)
    return out


def promoteGolden(page: Page, force: bool = False) -> List[Path]:
    written = []
    for run in page.publicRuns:      # internal runs get no golden in git
        if not run.golden:
            continue
        dest = goldenPath(page, run.id)
        if dest.exists() and not force:
            print(f'[{page.slug}] golden {run.id} exists (use --force to regenerate deliberately)')
            continue
        with Trajectory(page.runDir(run.id)) as traj:
            dest.parent.mkdir(exist_ok=True)
            np.savez_compressed(dest, **_final(traj))
        print(f'[{page.slug}] golden {run.id} -> {dest} ({dest.stat().st_size / 1e3:.0f} kB)')
        written.append(dest)
    return written


def compareGolden(page: Page, tol: float = 1e-3, strict: bool = False, rerun: bool = True,
                  ids: Optional[List[str]] = None) -> bool:
    """Re-run the golden rows (GPU) and compare with the stored finals; True if all within ``tol``."""
    runs = [r for r in page.publicRuns if r.golden and (not ids or r.id in ids)]
    if rerun:
        from .runs import execute
        scratch = page.root / 'results' / '_golden'
        execute(page, ids=[r.id for r in runs], force=True, promoteRuns=False, resultsRoot=scratch)
        source = lambda rid: scratch / page.slug / rid
    else:
        source = page.runDir
    ok = True
    for run in runs:
        gold = np.load(goldenPath(page, run.id))
        with Trajectory(source(run.id)) as traj:
            now = _final(traj)
        problems = []
        for key in _FIELDS:
            if key not in gold.files:
                continue
            a, b = gold[key], now[key]
            if a.shape != b.shape:
                problems.append(f'{key}: shape {a.shape} vs {b.shape}')
                continue
            if strict:
                if not np.array_equal(a, b):
                    problems.append(f'{key}: not bit-identical (max |d| {np.abs(a - b).max():.3g})')
            else:
                rel = np.linalg.norm(a - b) / (np.linalg.norm(a) + 1e-30)
                if rel > tol:
                    problems.append(f'{key}: relative L2 difference {rel:.3g} > {tol:g}')
        if int(gold['nSteps']) > 0 and abs(int(now['nSteps']) - int(gold['nSteps'])) > max(2, 0.02 * int(gold['nSteps'])):
            problems.append(f'step count {int(now["nSteps"])} vs golden {int(gold["nSteps"])}')
        print(f'[{page.slug}] golden {run.id}: ' + ('ok' if not problems else '; '.join(problems)))
        ok &= not problems
    return ok
