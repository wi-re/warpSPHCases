"""The notebook-facing API: run one configuration, look at it, compare it with the exact solution.

A page's notebook is install -> parameters -> ``run`` -> ``profiles`` / ``errors`` -> optionally
``compareWithGolden``, using the same functions as the site build, so a reader reproduces the page's
numbers with the same method. Nothing here needs the warpSPHCases repository layout.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import matplotlib.pyplot as plt
import numpy as np

from . import derived
from .reference import buildReference
from .spec import RunEntry
from .store import Trajectory
from .style import REFERENCE, schemeStyle, useStyle

__all__ = ['run', 'profiles', 'errors', 'compareWithGolden', 'fetchPage', 'sensor']

_RAW_URL = 'https://raw.githubusercontent.com/wi-re/warpSPHCases/main/cases/{family}/{slug}/{path}'
_GOLDEN_URL = 'https://raw.githubusercontent.com/wi-re/warpSPHCases/main/cases/{family}/{slug}/golden/{runId}.npz'


def run(case: str, scheme: str, nx: int, workdir: str = 'warpsph_runs', video: bool = True,
        precision: str = 'float32', spec: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None) -> Trajectory:
    """Run a registered warpSPH case and return its trajectory.

    Same fixed settings as the page runs (trajectory export, progress rows, velocity alarm, stall
    watchdog); ``video=True`` also writes ``output.mp4`` next to the trajectory. If the video backend
    cannot start (no display, no GL), the run is repeated once without it.
    """
    from warpSPHBootstrap import bootstrap
    bootstrap(precision=precision)
    from warpSPH import cases as warpCases
    warpCases.importAll()
    from .runs import runEntry

    entry = RunEntry(id=f'{scheme}__notebook__nx{nx}', case=case, scheme=scheme, nx=nx, variant='notebook',
                     spec={**(spec or {}), 'precision': precision}, params=dict(params or {}), video=video)
    runDir = Path(workdir) / entry.id
    try:
        runEntry(entry, runDir)
    except Exception as exc:      # headless GL is the usual failure; the physics must not depend on it
        if not video:
            raise
        print(f'video backend failed ({type(exc).__name__}: {exc}); repeating without video')
        entry.video = False
        runEntry(entry, runDir)
    return Trajectory(runDir)


def fetchPage(family: str, slug: str, files: Iterable[str], workdir: str = 'warpsph_page') -> Path:
    """Download files of a page folder (e.g. ``reference/...``) from GitHub, keeping their relative paths.

    Returns the local folder that then plays the role of the page directory (``pageDir``). Files that are
    already there (a local checkout, a previous call) are not fetched again.
    """
    root = Path(workdir)
    for rel in files:
        target = root / rel
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(_RAW_URL.format(family=family, slug=slug, path=rel), target)
    return root


def sensor(traj: Trajectory, kind: str, pageDir, zoom: float = 0.25):
    """Sensor pressure of the run against the experiment (``tc10``): the trace and a zoom on each impact."""
    ref = buildReference(kind, traj, pageDir=pageDir)
    t, p = ref.simulatedSeries(traj.dir)
    style = schemeStyle(traj.scheme)
    n = len(ref.impactTimes)
    with useStyle():
        fig, axes = plt.subplots(1, n + 1, figsize=(3.0 * (n + 1), 2.8), squeeze=False)
        for k, ax in enumerate(axes[0]):
            ax.fill_between(ref.t, 0, ref.pMax, color='#e4e3df', lw=0)
            ax.plot(ref.t, ref.pMean, color='#52514e', lw=0.7, label='experiment')
            ax.plot(t, p, color=style['color'], lw=0.9, label=traj.scheme)
            if k:
                te = ref.impactTimes[k - 1]
                ax.errorbar([te], [ref.repeatMean[k - 1]], yerr=[ref.repeatStd[k - 1]], color='k', marker='_', ms=7)
                ax.set_xlim(te - zoom, te + zoom)
                ax.set_title(f'impact {k}')
            else:
                ax.set_xlim(0, t.max())
                ax.set_ylabel('pressure (mbar)')
            ax.set_xlabel('time (s)')
        axes[0, 0].legend()
        fig.tight_layout()
    return fig, ref.metrics(traj)


def profiles(traj: Trajectory, kind: str, fields: Optional[Iterable[str]] = None, index: int = -1):
    """The run's particles against the exact profile at frame ``index`` (default: the last)."""
    ref = buildReference(kind, traj)
    fields = list(fields or ['density', 'velocity', 'pressure'])
    frame = traj.frame(index)
    x, measured = ref.measure(frame)
    xs = np.linspace(x.min(), x.max(), 4001)
    exact = ref.evaluate(frame['t'], xs)
    style = schemeStyle(traj.scheme)
    with useStyle():
        fig, axes = plt.subplots(1, len(fields), figsize=(3.2 * len(fields), 2.8), squeeze=False)
        for ax, name in zip(axes[0], fields):
            ax.plot(xs, exact[name], color=REFERENCE, lw=0.9, label='exact')
            ax.plot(x, measured[name], ls='none', marker=style['marker'], ms=2.6, mfc=style['color'], mec='none',
                    label=traj.scheme)
            ax.set_title(ref.fields[name][0])
            ax.set_xlabel(ref.xlabel)
        axes[0, 0].legend()
        fig.suptitle(f'{traj.scheme}, nx {traj.caseSpec.get("nx")}, t = {frame["t"]:.3f}', fontsize=9)
        fig.tight_layout()
    return fig


def errors(traj: Trajectory, kind: str, index: int = -1) -> Dict[str, Dict[str, float]]:
    """L1 / L2 / Linf error of every field of the exact solution at frame ``index``."""
    return derived.profileErrors(traj, buildReference(kind, traj), index=index)


def compareWithGolden(traj: Trajectory, family: str, slug: str, runId: str, tol: float = 1e-3) -> Optional[bool]:
    """Compare the last frame with the golden stored in the repository for ``runId`` (same nx, scheme).

    Runs are deterministic on one GPU and driver but not across hardware, so the check is a relative L2
    tolerance per field, not bit equality.
    """
    url = _GOLDEN_URL.format(family=family, slug=slug, runId=runId)
    try:
        with urllib.request.urlopen(url) as response:
            import io
            gold = np.load(io.BytesIO(response.read()))
    except OSError as exc:        # offline, or the repository does not publish this golden (yet)
        print(f'golden not reachable at {url} ({exc}); skipping the comparison')
        return None
    frame = traj.frame(-1)
    ok = True
    for key in ('positions', 'velocities', 'densities', 'internalEnergies'):
        if key not in gold.files or key not in frame:
            continue
        a, b = gold[key], frame[key]
        rel = np.linalg.norm(a - b) / (np.linalg.norm(a) + 1e-30) if a.shape == b.shape else np.inf
        print(f'{key:18s} relative L2 difference {rel:.3g}  {"ok" if rel <= tol else "DIFFERS"}')
        ok &= rel <= tol
    return bool(ok)
