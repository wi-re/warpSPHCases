"""Runs-matrix executor: page ``runs:`` rows -> warpSPH ``run()`` -> the run store.

Follows warpSPH's "Running simulations" rules: vispy video on (a row opts out
with ``video: false`` -- only for the many-small-runs convergence sweeps, and
the log says so), progress streamed row by row, the velocity alarm drawing every
step while it is active, the sim-time stall watchdog armed, and strictly one run
at a time (the GPU is kernel-launch bound).

Layout::

    results/<family>/<slug>/<runid>/{trajectory.h5, caseSpec.json, config.json,
                                     timing.json, diagnostics.csv, output.mp4, images/}
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np

from .spec import Page, RunEntry
from .store import promote

__all__ = ['execute', 'runEntry', 'selectRuns', 'commits']

#: export of the trajectory is mandatory for a page; these are the run-time knobs every run gets
_FIXED = dict(store=True, storeMode='trajectory', show=False, progress=True,
              velocityAlarmPlotInterval=1, stallProgress=1e-3)


def commits() -> Dict[str, str]:
    """Short git hash (``+dirty`` when the tree has local changes) of each warpSPH package in use."""
    import importlib
    out: Dict[str, str] = {}
    for name in ('warpSPH', 'warpSPHCore', 'warpSPHIntegrators', 'warpSPHPlotting', 'warpSPHBoundaries'):
        try:
            module = importlib.import_module(name)
        except Exception:
            continue
        folder = Path(module.__file__).resolve().parent
        try:
            head = subprocess.run(['git', '-C', str(folder), 'rev-parse', '--short', 'HEAD'],
                                  capture_output=True, text=True, check=True).stdout.strip()
            dirty = subprocess.run(['git', '-C', str(folder), 'status', '--porcelain', '--', '.'],
                                   capture_output=True, text=True, check=True).stdout.strip()
            out[name] = head + ('+dirty' if dirty else '')
        except Exception:
            out[name] = getattr(module, '__version__', 'unknown')
    return out


def selectRuns(page: Page, ids: Optional[Iterable[str]] = None, tier: Optional[str] = None) -> List[RunEntry]:
    runs = page.runs
    if ids:
        wanted = set(ids)
        missing = wanted - {r.id for r in runs}
        if missing:
            raise KeyError(f'{page.slug}: unknown run ids {sorted(missing)}')
        runs = [r for r in runs if r.id in wanted]
    if tier:
        runs = [r for r in runs if r.tier == tier]
    return runs


def _gpuName() -> Optional[str]:
    try:
        import torch
        return torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'
    except Exception:
        return None


def _gpuUtilization() -> Optional[int]:
    """Current GPU utilisation in percent (other jobs included), or None without nvidia-smi."""
    try:
        out = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
                             capture_output=True, text=True, check=True, timeout=10).stdout
        return int(out.split()[0])
    except Exception:
        return None


def _writeDiagnostics(rows: List[Dict[str, float]], path: Path) -> None:
    keys: List[str] = []
    for row in rows:
        for k in row:
            if k not in keys:
                keys.append(k)
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in keys})


def _flatten(exportRoot: Path, runDir: Path) -> None:
    """warpSPH writes into ``exportRoot/<caseName>_<timestamp>/``; hoist its contents up one level."""
    children = [p for p in exportRoot.iterdir() if p.is_dir() and (p / 'trajectory.h5').exists()]
    if len(children) != 1:
        raise RuntimeError(f'expected exactly one export in {exportRoot}, found {[c.name for c in children]}')
    for item in children[0].iterdir():
        shutil.move(str(item), str(runDir / item.name))
    children[0].rmdir()
    if exportRoot != runDir:
        exportRoot.rmdir()


def _substitute(value, pageDir: Optional[Path]):
    """Replace ``{pageDir}`` in string values (recursively) so a row can point at the page's reference files."""
    if pageDir is None:
        return value
    if isinstance(value, str):
        return value.replace('{pageDir}', str(pageDir))
    if isinstance(value, dict):
        return {k: _substitute(v, pageDir) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute(v, pageDir) for v in value]
    return value


def runEntry(entry: RunEntry, runDir: Path, pageDir: Optional[Path] = None) -> Dict[str, object]:
    """Run one matrix row into ``runDir`` (bootstrap and case registration are the caller's job).

    Leaves ``trajectory.h5``, ``caseSpec.json``, ``config.json``, ``timing.json``, ``diagnostics.csv`` and,
    with video on, ``output.mp4`` in ``runDir``; returns the timing dict.
    """
    from warpSPH.runner import getCase, run
    if runDir.exists():
        shutil.rmtree(runDir)
    runDir.mkdir(parents=True)
    overrides = dict(_FIXED)
    overrides.update(_substitute(entry.caseSpecOverrides(), pageDir))
    overrides['plot'] = bool(entry.video)
    overrides['video'] = bool(entry.video)
    if entry.video:
        overrides.setdefault('plotBackend', 'vispy')
    overrides['exportRoot'] = str(runDir / '_export')
    busyBefore = _gpuUtilization()     # a shared GPU makes ms/step unreliable; recorded so the page can say so
    started = time.perf_counter()
    result = run(getCase(entry.case), **overrides)
    wall = time.perf_counter() - started

    _flatten(runDir / '_export', runDir)
    rows = result.trajectory
    step = np.array([r['stepTime_ms'] for r in rows if 'stepTime_ms' in r])
    steady = step[1:] if len(step) > 1 else step
    timing = dict(
        wallTime=float(result.wallTime or wall), nSteps=int(result.nSteps),
        msPerStep=float(np.median(steady)) if len(steady) else float('nan'),
        msPerStepMean=float(np.mean(steady)) if len(steady) else float('nan'),
        diverged=bool(result.diverged), stopReason=result.stopReason,
        velocityAlarms=len(result.velocityAlarms), video=bool(entry.video),
        gpu=_gpuName(), commits=commits(), gpuUtilBefore=busyBefore,
    )
    (runDir / 'timing.json').write_text(json.dumps(timing, indent=1) + '\n')
    _writeDiagnostics(rows, runDir / 'diagnostics.csv')
    return timing


def execute(page: Page, ids: Optional[Iterable[str]] = None, tier: Optional[str] = None,
            force: bool = False, promoteRuns: bool = True, resultsRoot: Optional[Path] = None) -> List[str]:
    """Run the selected rows of ``page`` one after another; returns the ids that ran.

    A row whose ``trajectory.h5`` already exists is skipped unless ``force``, so an
    interrupted overnight chain resumes where it stopped.
    """
    where = (lambda rid: Path(resultsRoot) / page.slug / rid) if resultsRoot else page.resultsDir
    runs = selectRuns(page, ids, tier)
    todo = [r for r in runs if force or not (where(r.id) / 'trajectory.h5').exists()]
    if not todo:
        print(f'[{page.slug}] nothing to run ({len(runs)} selected, all present)')
        return []

    precisions = {r.spec.get('precision', 'float32') for r in todo}
    if len(precisions) > 1:
        raise ValueError(f'{page.slug}: mixed precisions {precisions} cannot share a process; run them separately')
    from warpSPHBootstrap import bootstrap
    bootstrap(precision=precisions.pop())

    from warpSPH import cases as warpCases
    warpCases.importAll()    # importing a case module registers it
    ran: List[str] = []
    for n, entry in enumerate(todo, 1):
        runDir = where(entry.id)
        print(f'\n[{page.slug}] run {n}/{len(todo)}: {entry.id}  '
              f'(case {entry.case}, scheme {entry.scheme}, nx {entry.nx}, tier {entry.tier}, '
              f'video {"on" if entry.video else "OFF (sweep run)"})', flush=True)
        timing = runEntry(entry, runDir, pageDir=page.dir)
        flag = ' DIVERGED' if timing['diverged'] else ''
        print(f'[{page.slug}] {entry.id}: {timing["wallTime"]:.1f} s wall, {timing["nSteps"]} steps, '
              f'{timing["msPerStep"]:.2f} ms/step (median), {timing["velocityAlarms"]} velocity alarms{flag}',
              flush=True)
        if promoteRuns:
            promote(runDir, page.trajectoryDir(entry.id))
        ran.append(entry.id)
    return ran
