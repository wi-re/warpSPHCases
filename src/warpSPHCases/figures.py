"""Figure and table recipes, driven by a page's ``figures:`` / ``tables:`` lists.

Every recipe reads trajectories (never a live run), so a page re-renders without
simulating and a new scheme added to the runs matrix shows up in every comparison
without touching the others. A recipe returns the files it wrote.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from . import derived
from .reference import ProfileReference, buildReference
from .spec import Page, RunEntry
from .store import Trajectory, readDiagnostics
from .style import DIVERGING, GRID, INK, INK2, REFERENCE, SURFACE, SCHEME_ORDER, save, schemeStyle, useStyle

__all__ = ['Context', 'render', 'renderTable', 'selectRuns']


def selectRuns(page: Page, select: Optional[Dict[str, Any]] = None) -> List[RunEntry]:
    """Rows of the runs matrix matching ``select`` (``nx``, ``variant``, ``tier``, ``scheme`` -- scalar or list),
    ordered by the page's scheme order, then resolution."""
    select = select or {}
    out = []
    for run in page.publicRuns:      # internal rows never reach a figure or table
        ok = True
        for key, want in select.items():
            have = getattr(run, key)
            ok &= (have in want) if isinstance(want, list) else (have == want)
        if ok:
            out.append(run)
    order = page.meta.get('schemes') or SCHEME_ORDER
    rank = {s: i for i, s in enumerate(order)}
    return sorted(out, key=lambda r: (rank.get(r.scheme, 99), r.nx))


@dataclass
class Context:
    """Per-build cache of open trajectories and references, and where outputs go."""

    page: Page
    outDir: Path
    _traj: Dict[str, Trajectory] = field(default_factory=dict)
    _ref: Dict[str, Any] = field(default_factory=dict)

    def traj(self, runId: str) -> Trajectory:
        if runId not in self._traj:
            self._traj[runId] = Trajectory(self.page.runDir(runId))
        return self._traj[runId]

    def reference(self, runId: str):
        if runId not in self._ref:
            self._ref[runId] = buildReference(self.page.meta['reference']['kind'], self.traj(runId),
                                              pageDir=self.page.dir)
        return self._ref[runId]

    def close(self) -> None:
        for t in self._traj.values():
            t.close()


def _axisLabel(ref: ProfileReference, name: str) -> str:
    return ref.fields[name][0]


def _legendHandles(runs: Sequence[RunEntry]):
    from matplotlib.lines import Line2D
    handles = [Line2D([], [], color=REFERENCE, lw=1.0, label='exact')]
    for scheme in dict.fromkeys(r.scheme for r in runs):
        s = schemeStyle(scheme)
        handles.append(Line2D([], [], color=s['color'], marker=s['marker'], lw=0, markersize=4.5, label=scheme))
    return handles


# ---------------------------------------------------------------------------- overlay
def overlay(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    """Every selected run's particles at its final time against the exact profile; full range on top,
    a zoom on the contact and the shock below (where the schemes differ)."""
    runs = selectRuns(ctx.page, fig.get('select'))
    fields = fig['fields']
    first = ctx.traj(runs[0].id)
    ref = ctx.reference(runs[0].id)
    t = first.frame(-1)['t']
    marks = ref.landmarks(t)
    zoom = (marks['contact'] - 0.05, marks['shock'] + 0.05)
    with useStyle():
        f, axes = plt.subplots(2, len(fields), figsize=(2.55 * len(fields), 4.5), squeeze=False)
        xs = np.linspace(0, 1, 4001)
        exact = ref.evaluate(t, xs)
        for c, name in enumerate(fields):
            for r in range(2):
                ax = axes[r, c]
                ax.plot(xs, exact[name], color=REFERENCE, lw=0.9, zorder=1)
                for run in runs:
                    traj = ctx.traj(run.id)
                    x, m = ref.measure(traj.frame(-1))
                    s = schemeStyle(run.scheme)
                    ax.plot(x, m[name], ls='none', marker=s['marker'], ms=2.6 if r == 0 else 3.6,
                            mfc=s['color'], mec='none', alpha=0.85, zorder=2)
                if r == 1:
                    ax.set_xlim(*zoom)
                    sel = (xs > zoom[0]) & (xs < zoom[1])
                    lo, hi = exact[name][sel].min(), exact[name][sel].max()
                    pad = 0.12 * (hi - lo + 1e-9)
                    ax.set_ylim(lo - pad, hi + pad)
                    ax.set_xlabel(ref.xlabel)
                else:
                    ax.set_xlim(0, 1)
                    ax.set_title(_axisLabel(ref, name))
                    ax.tick_params(labelbottom=False)
        axes[0, 0].set_ylabel('full tube')
        axes[1, 0].set_ylabel('contact and shock')
        f.legend(handles=_legendHandles(runs), loc='lower center', ncol=len(runs) + 1, bbox_to_anchor=(0.5, -0.02))
        f.suptitle(f'nx {runs[0].nx}, t = {t:.3f}', fontsize=9, color=INK2, y=0.995)
        f.tight_layout(rect=(0, 0.05, 1, 0.98))
        path = ctx.outDir / f'{fig["id"]}.png'
        save(f, path)
        plt.close(f)
    return [path]


# ---------------------------------------------------------------------------- scheme_grid
def schemeGrid(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    """Scheme (rows) x field (columns), one shared y-range per column, error norm in each panel."""
    runs = selectRuns(ctx.page, fig.get('select'))
    fields = fig['fields']
    ref = ctx.reference(runs[0].id)
    t = ctx.traj(runs[0].id).frame(-1)['t']
    xs = np.linspace(0, 1, 4001)
    exact = ref.evaluate(t, xs)
    with useStyle():
        f, axes = plt.subplots(len(runs), len(fields), figsize=(2.6 * len(fields), 1.15 * len(runs) + 0.5),
                               squeeze=False, sharex=True)
        for r, run in enumerate(runs):
            traj = ctx.traj(run.id)
            x, m = ref.measure(traj.frame(-1))
            errs = derived.profileErrors(traj, ref)
            s = schemeStyle(run.scheme)
            for c, name in enumerate(fields):
                ax = axes[r, c]
                ax.plot(xs, exact[name], color=REFERENCE, lw=0.8, zorder=1)
                ax.plot(x, m[name], ls='none', marker=s['marker'], ms=2.4, mfc=s['color'], mec='none', zorder=2)
                lo, hi = exact[name].min(), exact[name].max()
                pad = 0.12 * (hi - lo)
                ax.set_ylim(lo - pad, hi + pad)
                ax.set_xlim(0, 1)
                ax.text(1.0, 1.03, f'L1 {errs[name]["L1"]:.2g}', transform=ax.transAxes, ha='right', va='bottom',
                        fontsize=7.5, color=INK2)
                if r == 0:
                    ax.set_title(_axisLabel(ref, name), loc='left', pad=14)
                if r == len(runs) - 1:
                    ax.set_xlabel(ref.xlabel)
            axes[r, 0].set_ylabel(run.scheme, rotation=0, ha='right', va='center', labelpad=6, color=INK)
        f.suptitle(f'nx {runs[0].nx}, t = {t:.3f}; line: exact, markers: particles', fontsize=8.5, color=INK2)
        f.tight_layout(rect=(0, 0, 1, 0.985))
        path = ctx.outDir / f'{fig["id"]}.png'
        save(f, path)
        plt.close(f)
    return [path]


# ---------------------------------------------------------------------------- snapshots
def snapshots(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    traj = ctx.traj(fig['run'])
    ref = ctx.reference(fig['run'])
    run = ctx.page.run(fig['run'])
    name = fig['field']
    times = fig['times']
    s = schemeStyle(run.scheme)
    xs = np.linspace(0, 1, 4001)
    with useStyle():
        f, axes = plt.subplots(1, len(times), figsize=(2.3 * len(times), 2.3), squeeze=False, sharey=True)
        for ax, t in zip(axes[0], times):
            index = traj.frameAt(t)
            frame = traj.frame(index)
            x, m = ref.measure(frame)
            ax.plot(xs, ref.evaluate(frame['t'], xs)[name], color=REFERENCE, lw=0.9)
            ax.plot(x, m[name], ls='none', marker=s['marker'], ms=2.4, mfc=s['color'], mec='none')
            ax.set_title(f't = {frame["t"]:.3f}')
            ax.set_xlabel(ref.xlabel)
            ax.set_xlim(0, 1)
        axes[0, 0].set_ylabel(_axisLabel(ref, name))
        f.tight_layout()
        path = ctx.outDir / f'{fig["id"]}.png'
        save(f, path)
        plt.close(f)
    return [path]


# ---------------------------------------------------------------------------- convergence
def _metricsByScheme(ctx: Context, runs: Sequence[RunEntry], metric: str) -> Dict[str, Dict[int, float]]:
    out: Dict[str, Dict[int, float]] = {}
    for run in runs:
        out.setdefault(run.scheme, {})[run.nx] = ctx.reference(run.id).metrics(ctx.traj(run.id))[metric]
    return out


# ---------------------------------------------------------------------------- convergence
def convergence(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    runs = selectRuns(ctx.page, fig.get('select'))
    metric = fig['metric']
    errors = _metricsByScheme(ctx, runs, metric)
    with useStyle():
        f, ax = plt.subplots(figsize=(5.2, 4.2))
        allN, allE = [], []
        for scheme, byN in errors.items():
            n = np.array(sorted(byN))
            e = np.array([byN[k] for k in n])
            k = derived.monotonePrefix(e)
            slope = derived.convergenceSlope(n[:k], e[:k]) if k > 1 else float('nan')
            note = f'order {slope:.2f}' if k == len(n) else (
                f'order {slope:.2f} up to nx {int(n[k - 1])}, then not converging' if k > 1 else 'not converging')
            s = schemeStyle(scheme)
            ax.plot(n, e, color=s['color'], marker=s['marker'], ms=4.5, lw=1.2, label=f'{scheme}  ({note})')
            allN += list(n)
            allE += list(e)
        n0 = min(allN)
        e0 = 0.5 * min(byN[n0] for byN in errors.values())      # guide lines start below the data
        grid = np.array([n0, max(allN)], dtype=float)
        for order, ls in ((1, '--'), (2, ':')):
            ax.plot(grid, e0 * (grid / n0) ** (-order), color=INK2, lw=0.8, ls=ls)
        ax.text(grid[-1], e0 * (grid[-1] / n0) ** -1 * 0.8, 'order 1', fontsize=7.5, color=INK2, ha='right', va='top')
        ax.text(grid[-1] / 2, e0 * (grid[-1] / 2 / n0) ** -2 * 1.3, 'order 2', fontsize=7.5, color=INK2, ha='left', va='bottom')
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel(fig.get('xlabel', 'resolution nx'))
        ax.set_ylabel(fig.get('ylabel', metric))
        ax.set_xticks(sorted(set(allN)))
        ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        longest = max(len(label) for label in ax.get_legend_handles_labels()[1])
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=1 if longest > 32 else 2, fontsize=7.5)
        f.tight_layout()
        path = ctx.outDir / f'{fig["id"]}.png'
        save(f, path)
        plt.close(f)
    return [path]


# ---------------------------------------------------------------------------- diagnostics
def diagnostics(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    runs = selectRuns(ctx.page, fig.get('select'))
    key = fig['quantity']
    with useStyle():
        f, ax = plt.subplots(figsize=(4.6, 3.0))
        for run in runs:
            d = readDiagnostics(ctx.page.runDir(run.id))
            if key not in d:
                continue
            y = derived.relativeDrift(d[key]) if fig.get('relative') else d[key]
            s = schemeStyle(run.scheme)
            ax.plot(d['t'], y, color=s['color'], lw=1.2, label=run.scheme)
        if fig.get('relative'):
            ax.set_yscale('symlog', linthresh=1e-7)
        elif fig.get('yscale'):
            ax.set_yscale(fig['yscale'])
        ax.set_xlabel('simulated time')
        ax.set_ylabel(fig.get('ylabel', key))
        ax.legend(fontsize=7.5, ncol=4, loc='lower center', bbox_to_anchor=(0.5, 1.0), columnspacing=1.0, handlelength=1.4)
        f.tight_layout()
        path = ctx.outDir / f'{fig["id"]}.png'
        save(f, path)
        plt.close(f)
    return [path]


# ---------------------------------------------------------------------------- loop (hero video)
def loop(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    """Looping hero: the profile fields of one run through time against the exact solution -> MP4 + poster."""
    from PIL import Image
    traj = ctx.traj(fig['run'])
    ref = ctx.reference(fig['run'])
    run = ctx.page.run(fig['run'])
    fields = fig['fields']
    s = schemeStyle(run.scheme)
    xs = np.linspace(0, 1, 2001)
    frames = [traj.frame(i) for i in range(len(traj))]
    measured = [ref.measure(fr) for fr in frames]
    exact = [ref.evaluate(fr['t'], xs) for fr in frames]
    width, height = 720, 304
    with useStyle():
        f, axes = plt.subplots(1, len(fields), figsize=(width / 100, height / 100), dpi=100, squeeze=False)
        lines, dots = [], []
        for ax, name in zip(axes[0], fields):
            vals = np.concatenate([e[name] for e in exact] + [m[1][name][np.isfinite(m[1][name])] for m in measured])
            lo, hi = vals.min(), vals.max()
            pad = 0.08 * (hi - lo)
            ax.set_ylim(lo - pad, hi + pad)
            ax.set_xlim(0, 1)
            ax.set_title(_axisLabel(ref, name))
            ax.set_xlabel(ref.xlabel)
            lines.append(ax.plot(xs, exact[0][name], color=REFERENCE, lw=0.9)[0])
            dots.append(ax.plot(*measured[0][:1], measured[0][1][name], ls='none', marker=s['marker'], ms=2.4,
                                mfc=s['color'], mec='none')[0])
        label = f.suptitle('', fontsize=9, color=INK2, y=0.995)
        f.tight_layout(rect=(0, 0, 1, 0.94))
        outFrames = []
        for i, fr in enumerate(frames):
            x, m = measured[i]
            for k, name in enumerate(fields):
                lines[k].set_ydata(exact[i][name])
                dots[k].set_data(x, m[name])
            label.set_text(f'{run.scheme}, nx {run.nx}   t = {fr["t"]:.3f}   (line: exact)')
            f.canvas.draw()
            outFrames.append(np.asarray(f.canvas.buffer_rgba())[..., :3].copy())
        plt.close(f)
    return _encode(ctx, fig, outFrames, Image)


# ---------------------------------------------------------------------------- series (kinetic energy)
def series(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    """Kinetic energy of every selected run against the exact decay: the curves (log axis) and the
    deviation from the exact value, side by side. Needs a reference with ``kineticEnergy(t)``.

    The axes are limited to ``deviationLimit`` (relative, default 0.15) around the exact decay so the
    schemes that track it can be told apart; a run that leaves that band is still drawn, its legend entry
    says "(off scale)".
    """
    runs = selectRuns(ctx.page, fig.get('select'))
    ref = ctx.reference(runs[0].id)
    limit = float(fig.get('deviationLimit', 0.15))
    with useStyle():
        f, (a, b) = plt.subplots(1, 2, figsize=(7.6, 3.2))
        tmax = 0.0
        for run in runs:
            d = readDiagnostics(ctx.page.runDir(run.id))
            t, ke = d['t'], d['kineticEnergy']
            tmax = max(tmax, t.max())
            s = schemeStyle(run.scheme)
            deviation = ke / ref.kineticEnergy(t) - 1.0
            off = bool(np.nanmax(np.abs(deviation)) > limit)
            a.plot(t, ke / ref.kineticEnergy0, color=s['color'], lw=1.2,
                   label=run.scheme + (' (off scale)' if off else ''))
            b.plot(t, deviation, color=s['color'], lw=1.2)
        tt = np.linspace(0, tmax, 200)
        a.plot(tt, ref.kineticEnergy(tt) / ref.kineticEnergy0, color=REFERENCE, lw=0.9, ls='--', label='exact')
        a.set_yscale('log')
        a.set_ylim(float(ref.kineticEnergy(tmax) / ref.kineticEnergy0) * (1 - limit), 1 + limit)
        a.set_xlabel('simulated time')
        a.set_ylabel(r'$E_k / E_k^{\mathrm{exact}}(0)$')
        b.axhline(0, color=REFERENCE, lw=0.8, ls='--')
        b.set_ylim(-limit, limit)
        b.set_xlabel('simulated time')
        b.set_ylabel('relative deviation from the exact decay')
        f.tight_layout(rect=(0, 0.2, 1, 1))
        handles, labels = a.get_legend_handles_labels()
        f.legend(handles, labels, loc='lower center', ncol=3, fontsize=7.5, bbox_to_anchor=(0.5, -0.01))
        path = ctx.outDir / f'{fig["id"]}.png'
        save(f, path)
        plt.close(f)
    return [path]


# ---------------------------------------------------------------------------- field_grid (2D error maps)
def fieldGrid(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    """One panel per run: the signed speed error ``|v| - |v_exact|`` (in units of the exact amplitude) at
    each particle, final frame, one symmetric colour scale shared by all panels."""
    runs = selectRuns(ctx.page, fig.get('select'))
    ref = ctx.reference(runs[0].id)
    panels = []
    for run in runs:
        frame = ctx.traj(run.id).frame(-1)
        speed = np.linalg.norm(frame['velocities'], axis=1)
        exact = np.linalg.norm(ref.velocity(frame['t'], frame['positions']), axis=1)
        scale = ref.U * float(ref.amplitude(frame['t']))
        panels.append((run, np.mod(frame['positions'], ref.L), (speed - exact) / scale, frame['t']))   # periodic wrap
    limit = float(fig.get('limit') or np.percentile(np.abs(np.concatenate([p[2] for p in panels])), 99))
    n = len(panels)
    cols = min(4, n)
    rows = int(np.ceil(n / cols))
    with useStyle():
        f, axes = plt.subplots(rows, cols, figsize=(2.5 * cols + 0.6, 2.6 * rows), squeeze=False)
        for ax in axes.flat:
            ax.set_visible(False)
        for ax, (run, pos, err, t) in zip(axes.flat, panels):
            ax.set_visible(True)
            im = ax.scatter(pos[:, 0], pos[:, 1], c=err, s=fig.get('markersize', 1.2), cmap=DIVERGING,
                            vmin=-limit, vmax=limit, linewidths=0, rasterized=True)
            ax.set_aspect('equal')
            ax.set_title(run.scheme, fontsize=9)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)
            for sp in ax.spines.values():
                sp.set_visible(False)
        cbar = f.colorbar(im, ax=axes, shrink=0.8, pad=0.02)
        cbar.set_label(r'$(|v| - |v_{\mathrm{exact}}|)\,/\,U(t)$', fontsize=8)
        cbar.ax.tick_params(labelsize=7)
        f.suptitle(f'nx {runs[0].nx}, t = {panels[0][3]:.2f}', fontsize=9, color=INK2)
        path = ctx.outDir / f'{fig["id"]}.png'
        save(f, path)
        plt.close(f)
    return [path]


# ---------------------------------------------------------------------------- loop2d (hero video)
def loop2d(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    """Looping hero for 2D runs: particles coloured by speed next to the kinetic-energy history with a
    moving time marker -> MP4 + poster."""
    from PIL import Image
    traj = ctx.traj(fig['run'])
    ref = ctx.reference(fig['run'])
    run = ctx.page.run(fig['run'])
    d = readDiagnostics(ctx.page.runDir(fig['run']))
    frames = [traj.frame(i) for i in range(len(traj))]
    speeds = [np.linalg.norm(fr['velocities'], axis=1) for fr in frames]
    vmax = float(max(s.max() for s in speeds[:1]))
    width, height = 720, 330
    with useStyle():
        f, (ax, kx) = plt.subplots(1, 2, figsize=(width / 100, height / 100), dpi=100,
                                   gridspec_kw={'width_ratios': [1, 1.15]})
        pos = np.mod(frames[0]['positions'], ref.L)
        sc = ax.scatter(pos[:, 0], pos[:, 1], c=speeds[0], s=fig.get('markersize', 1.4), cmap='viridis',
                        vmin=0, vmax=vmax, linewidths=0)
        ax.set_aspect('equal')
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title('speed $|v|$', fontsize=9)
        tt = np.linspace(0, d['t'].max(), 200)
        kx.plot(tt, ref.kineticEnergy(tt) / ref.kineticEnergy0, color=REFERENCE, lw=0.9, ls='--', label='exact')
        s = schemeStyle(run.scheme)
        kx.plot(d['t'], d['kineticEnergy'] / ref.kineticEnergy0, color=s['color'], lw=1.3, label=run.scheme)
        marker = kx.plot([0], [1], 'o', color=INK, ms=4)[0]
        kx.set_xlabel('simulated time')
        kx.set_ylabel(r'$E_k / E_k^{\mathrm{exact}}(0)$')
        kx.legend(fontsize=7.5, loc='lower left')
        label = f.suptitle('', fontsize=9, color=INK2, y=0.995)
        f.tight_layout(rect=(0, 0, 1, 0.94))
        outFrames = []
        for fr, speed in zip(frames, speeds):
            sc.set_offsets(np.mod(fr['positions'], ref.L))
            sc.set_array(speed)
            ke = np.interp(fr['t'], d['t'], d['kineticEnergy']) / ref.kineticEnergy0
            marker.set_data([fr['t']], [ke])
            label.set_text(f'{run.scheme}, nx {run.nx}   t = {fr["t"]:.2f}')
            f.canvas.draw()
            outFrames.append(np.asarray(f.canvas.buffer_rgba())[..., :3].copy())
        plt.close(f)
    return _encode(ctx, fig, outFrames, Image)


def _encode(ctx: Context, fig: Dict[str, Any], outFrames, Image) -> List[Path]:
    outFrames = list(outFrames) + [outFrames[-1]] * 10   # hold the end before the loop restarts
    h, w = outFrames[0].shape[:2]
    mp4 = ctx.outDir / f'{fig["id"]}.mp4'
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
           '-r', str(fig.get('fps', 12)), '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24',
           '-pix_fmt', 'yuv420p', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-movflags', '+faststart', str(mp4)]
    proc = subprocess.run(cmd, input=b''.join(fr.tobytes() for fr in outFrames), capture_output=True)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode())
    poster = ctx.outDir / f'{fig["id"]}-poster.jpg'
    Image.fromarray(outFrames[-1]).save(poster, quality=88)
    return [mp4, poster]


# ---------------------------------------------------------------------------- sloshing (TC10-type references)
_VARIANT_LINES = ['-', '--', ':', '-.']


def _groups(runs: Sequence[RunEntry]):
    """Runs grouped by (scheme, variant) with a stable colour (scheme) and line style (variant)."""
    keys = list(dict.fromkeys((r.scheme, r.variant) for r in runs))
    variants = list(dict.fromkeys(v for _, v in keys))
    out = {}
    for scheme, variant in keys:
        st = dict(schemeStyle(scheme))
        st['ls'] = _VARIANT_LINES[variants.index(variant) % len(_VARIANT_LINES)]
        st['label'] = next(r.legend for r in runs if (r.scheme, r.variant) == (scheme, variant))
        out[(scheme, variant)] = st
    return out


def sensorTrace(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    """Wall pressure at the sensor, simulation against experiment smoothed the same way (10 ms Gaussian): the whole
    record on top, one zoom per experimental impact below. Behind the smoothed experiment (black) the recorded 1 ms
    mean (light grey); the dotted vertical lines mark the experimental impact times."""
    runs = selectRuns(ctx.page, fig.get('select'))
    ref = ctx.reference(runs[0].id)
    groups = _groups(runs)
    tmax = max(ctx.traj(r.id).times.max() for r in runs)
    n = len(ref.impactTimes)
    half = float(fig.get('zoom', 0.25))
    sim = {r.id: ref.smoothedSimulated(ctx.page.runDir(r.id)) for r in runs}
    top_ = max([np.nanmax(p) for _, p in sim.values()] + [np.nanmax(ref.pSmooth)])
    ymax = float(fig.get('ymax', 1.12 * top_))
    with useStyle():
        f = plt.figure(figsize=(7.4, 5.9))
        grid = f.add_gridspec(2, n, height_ratios=[1.0, 1.05], hspace=0.42, wspace=0.28, bottom=0.2, top=0.97)
        top = f.add_subplot(grid[0, :])
        zooms = [f.add_subplot(grid[1, k]) for k in range(n)]
        for ax in [top] + zooms:
            ax.plot(ref.t, ref.pMean, color='#c9c8c2', lw=0.6, zorder=1)
            for rid, (t, p) in sim.items():
                run = ctx.page.run(rid)
                st = groups[(run.scheme, run.variant)]
                ax.plot(t, p, color=st['color'], ls=st['ls'], lw=1.0 if ax is top else 1.3, alpha=0.95, zorder=3)
            ax.plot(ref.tSmooth, ref.pSmooth, color=INK, lw=1.5, zorder=5)
            ax.set_ylim(-0.04 * ymax, ymax)
        top.set_xlim(0, tmax)
        top.set_ylabel('smoothed pressure (mbar)')
        top.set_xlabel('time (s)')
        for k, (ax, te) in enumerate(zip(zooms, ref.impactTimes)):
            ax.set_xlim(te - half, te + half)
            top.axvline(te, color=GRID, lw=0.7, ls=':', zorder=0)
            ax.axvline(te, color=GRID, lw=0.7, ls=':', zorder=0)
            ax.set_title(f'impact {k + 1}', fontsize=8.5)
            ax.set_xlabel('time (s)')
            if k == 0:
                ax.set_ylabel('smoothed pressure (mbar)')
        from matplotlib.lines import Line2D
        handles = [Line2D([], [], color=INK, lw=1.5, label='experiment, smoothed'),
                   Line2D([], [], color='#c9c8c2', lw=1.0, label='experiment, recorded 1 ms mean')]
        handles += [Line2D([], [], color=st['color'], ls=st['ls'], lw=1.3, label=st['label']) for st in groups.values()]
        f.legend(handles=handles, loc='lower center', ncol=2, fontsize=7.5, bbox_to_anchor=(0.5, 0.0))
        path = ctx.outDir / f'{fig["id"]}.png'
        save(f, path)
        plt.close(f)
    return [path]


def sweep(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    """Metrics against resolution, one panel per metric, one line per (scheme, variant); if the reference has
    ``bands()`` the experimental mean ± std is drawn as a band."""
    runs = selectRuns(ctx.page, fig.get('select'))
    groups = _groups(runs)
    ref = ctx.reference(runs[0].id)
    metrics = fig['metrics']
    bands = getattr(ref, 'bands', lambda: {})()
    cols = min(len(metrics), fig.get('columns', 4))
    rows = int(np.ceil(len(metrics) / cols))
    with useStyle():
        f, axes = plt.subplots(rows, cols, figsize=(2.4 * cols + 0.4, 2.5 * rows + 0.6), squeeze=False)
        for ax, name in zip(axes.flat, metrics):
            if name in bands:
                m, sd = bands[name]
                ax.axhspan(m - sd, m + sd, color=GRID, lw=0, zorder=0)
                ax.axhline(m, color=INK, lw=0.8, zorder=1)
            for key, st in groups.items():
                mine = sorted((r for r in runs if (r.scheme, r.variant) == key), key=lambda r: r.nx)
                ax.plot([r.nx for r in mine], [ctx.reference(r.id).metrics(ctx.traj(r.id))[name] for r in mine],
                        color=st['color'], ls=st['ls'], marker=st['marker'], ms=4.5, lw=1.1, zorder=3)
            ax.set_title(name, fontsize=8.5)
            ax.set_xlabel(fig.get('xlabel', 'resolution nx'))
            ax.set_xscale('log')
            nxs = sorted({r.nx for r in runs})
            ax.set_xticks(nxs)
            ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
            ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            ax.tick_params(axis='x', labelsize=7)
        for ax in list(axes.flat)[len(metrics):]:
            ax.set_visible(False)
        from matplotlib.lines import Line2D
        handles = [Line2D([], [], color=st['color'], ls=st['ls'], marker=st['marker'], ms=4.5, lw=1.1, label=st['label'])
                   for st in groups.values()]
        if bands:
            handles.append(Line2D([], [], color=INK, lw=0.8, label='experiment (recorded trace, smoothed)'))
        f.tight_layout(rect=(0, 0.08, 1, 1))
        f.legend(handles=handles, loc='lower center', ncol=3, fontsize=7.5, bbox_to_anchor=(0.5, -0.01))
        path = ctx.outDir / f'{fig["id"]}.png'
        save(f, path)
        plt.close(f)
    return [path]


def _tankOutline(ax, traj: Trajectory) -> None:
    """The tank walls as a thin outline (analytic-wall runs have no wall particles to draw)."""
    from matplotlib.patches import Rectangle
    width, height = float(traj.caseSpec['L']), float(traj.params['tankHeight'])
    ax.add_patch(Rectangle((-width / 2, 0.0), width, height, fill=False, ec=INK2, lw=0.8, zorder=4))
    ax.set_xlim(-width / 2 - 0.02, width / 2 + 0.02)
    ax.set_ylim(-0.02, height + 0.02)


def _tankFrame(traj: Trajectory, index: int):
    frame = traj.frame(index)
    kinds = frame['kinds']
    fluid, wall = kinds == 0, kinds == 1
    return frame, fluid, wall


def tankSnapshots(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    """Particles (coloured by speed) at the given times, in the tank-fixed frame: walls grey."""
    traj = ctx.traj(fig['run'])
    ref = ctx.reference(fig['run'])
    times = fig.get('times') or list(ref.impactTimes)
    frames = [traj.frameAt(t) for t in times]
    speeds = [np.linalg.norm(traj.frame(i)['velocities'][traj.frame(i)['kinds'] == 0], axis=1) for i in frames]
    vmax = float(np.percentile(np.concatenate(speeds), 99.5))
    with useStyle():
        f, axes = plt.subplots(1, len(frames), figsize=(2.6 * len(frames) + 0.5, 1.9), squeeze=False)
        for ax, i, sp in zip(axes[0], frames, speeds):
            frame, fluid, wall = _tankFrame(traj, i)
            pos = frame['positions']
            ax.scatter(pos[wall, 0], pos[wall, 1], s=0.8, c=GRID, linewidths=0, rasterized=True)
            im = ax.scatter(pos[fluid, 0], pos[fluid, 1], s=fig.get('markersize', 1.6), c=sp, cmap='viridis', vmin=0,
                            vmax=vmax, linewidths=0, rasterized=True)
            _tankOutline(ax, traj)
            ax.set_aspect('equal')
            ax.set_title(f't = {frame["t"]:.2f} s', fontsize=8.5)
            ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
            for sp_ in ax.spines.values():
                sp_.set_visible(False)
        cbar = f.colorbar(im, ax=axes, shrink=0.85, pad=0.01)
        cbar.set_label('speed (m/s)', fontsize=8)
        cbar.ax.tick_params(labelsize=7)
        path = ctx.outDir / f'{fig["id"]}.png'
        save(f, path)
        plt.close(f)
    return [path]


def loopTank(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    """Hero loop: the tank (tank-fixed frame, particles coloured by speed) next to the sensor pressure with a moving
    time marker, simulation against experiment -> MP4 + poster."""
    from PIL import Image
    traj = ctx.traj(fig['run'])
    ref = ctx.reference(fig['run'])
    run = ctx.page.run(fig['run'])
    t, p = ref.smoothedSimulated(ctx.page.runDir(fig['run']))
    stride = int(fig.get('stride', 3))
    indices = list(range(0, len(traj), stride)) + ([len(traj) - 1] if (len(traj) - 1) % stride else [])
    first = traj.frame(0)
    vmax = float(fig.get('vmax', 1.5))
    width, height = 720, 330
    st = schemeStyle(run.scheme)
    with useStyle():
        f, (ax, kx) = plt.subplots(1, 2, figsize=(width / 100, height / 100), dpi=100, gridspec_kw={'width_ratios': [1.25, 1]})
        wall = first['kinds'] == 1
        ax.scatter(first['positions'][wall, 0], first['positions'][wall, 1], s=0.8, c=GRID, linewidths=0, zorder=1)
        _tankOutline(ax, traj)
        sc = ax.scatter([], [], s=fig.get('markersize', 1.8), c=[], cmap='viridis', vmin=0, vmax=vmax, linewidths=0, zorder=2)
        ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title('speed (m/s), tank frame', fontsize=9)
        kx.plot(ref.tSmooth, ref.pSmooth, color=INK, lw=1.3, label='experiment')
        kx.plot(t, p, color=st['color'], lw=1.0, label=run.legend)
        marker = kx.axvline(0, color=INK, lw=0.8)
        kx.set_xlim(0, traj.times.max())
        kx.set_xlabel('time (s)'); kx.set_ylabel('smoothed sensor pressure (mbar)')
        kx.legend(fontsize=7.5, loc='upper left')
        label = f.suptitle('', fontsize=9, color=INK2, y=0.995)
        f.tight_layout(rect=(0, 0, 1, 0.94))
        outFrames = []
        for i in indices:
            frame = traj.frame(i)
            fluid = frame['kinds'] == 0
            sc.set_offsets(frame['positions'][fluid])
            sc.set_array(np.linalg.norm(frame['velocities'][fluid], axis=1))
            marker.set_xdata([frame['t'], frame['t']])
            label.set_text(f'{run.legend}, nx {run.nx}   t = {frame["t"]:.2f} s')
            f.canvas.draw()
            outFrames.append(np.asarray(f.canvas.buffer_rgba())[..., :3].copy())
        plt.close(f)
    return _encode(ctx, fig, outFrames, Image)


RECIPES = {'overlay': overlay, 'scheme_grid': schemeGrid, 'snapshots': snapshots,
           'convergence': convergence, 'diagnostics': diagnostics, 'loop': loop,
           'series': series, 'field_grid': fieldGrid, 'loop2d': loop2d,
           'sensor_trace': sensorTrace, 'sweep': sweep, 'tank_snapshots': tankSnapshots, 'loop_tank': loopTank}


def render(ctx: Context, fig: Dict[str, Any]) -> List[Path]:
    if fig['kind'] not in RECIPES:
        raise KeyError(f'figure {fig["id"]!r}: unknown kind {fig["kind"]!r}; known: {sorted(RECIPES)}')
    return RECIPES[fig['kind']](ctx, fig)


# ---------------------------------------------------------------------------- tables
def _fmt(v: float) -> str:
    if v is None or not np.isfinite(v):
        return '--'
    return f'{v:.3g}'


def renderTable(ctx: Context, table: Dict[str, Any]) -> Dict[str, Any]:
    """Returns ``{'id', 'columns', 'rows', 'markdown'}``; the numbers come from the trajectories."""
    runs = selectRuns(ctx.page, table.get('select'))
    first = ctx.reference(runs[0].id).metrics(ctx.traj(runs[0].id))
    names = list(first)
    if table['kind'] == 'errors':
        # no timing columns: ms/step needs an idle GPU and lives in the separate benchmark study
        columns = ['scheme', 'nx'] + names + ['steps']
        rows = []
        for run in runs:
            traj = ctx.traj(run.id)
            m = ctx.reference(run.id).metrics(traj)
            tm = traj.timing
            rows.append([run.legend, run.nx] + [_fmt(m[k]) for k in names] + [tm.nSteps if tm else '--'])
        extra = getattr(ctx.reference(runs[0].id), 'referenceRows', None)
        if extra:
            rows = [r + ['--'] * (len(columns) - len(r)) for r in extra(names)] + rows
    elif table['kind'] == 'orders':
        primary = (table.get('metrics') or names)[0]
        ns = sorted({r.nx for r in runs})
        columns = (['scheme'] + [f'{primary} at nx {n}' for n in ns]
                   + [f'order {a}-{b}' for a, b in zip(ns[:-1], ns[1:])])
        rows = []
        for scheme in dict.fromkeys(r.scheme for r in runs):
            per = {r.nx: ctx.reference(r.id).metrics(ctx.traj(r.id))[primary] for r in runs if r.scheme == scheme}
            have = sorted(per)
            e = [per[n] for n in have]
            pair = dict(zip(zip(have[:-1], have[1:]), derived.pairwiseOrders(have, e))) if len(have) > 1 else {}
            rows.append([scheme] + [_fmt(per.get(n)) for n in ns] +
                        [_fmt(pair.get((a, b))) for a, b in zip(ns[:-1], ns[1:])])
    else:
        raise KeyError(f'table {table["id"]!r}: unknown kind {table["kind"]!r}')
    md = ['| ' + ' | '.join(columns) + ' |', '|' + '|'.join(['---'] * len(columns)) + '|']
    md += ['| ' + ' | '.join(str(c) for c in row) + ' |' for row in rows]
    return {'id': table['id'], 'columns': columns, 'rows': rows, 'markdown': '\n'.join(md)}
