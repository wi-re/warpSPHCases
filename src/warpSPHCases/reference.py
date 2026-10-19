"""Reference solutions: what a run is compared against.

Two shapes of reference, both built *from a trajectory* so the parameters are the
ones the run actually used (never re-typed):

* :class:`ProfileReference` -- exact fields as a function of position at a given
  time (Sod's Riemann solution); ``measure`` pulls the matching quantities out of
  a stored frame so a run and its reference are evaluated at the same points.
* :class:`SeriesReference` -- an exact scalar as a function of time (TGV kinetic
  energy decay).

``REFERENCES`` maps the ``reference.kind`` of a page's ``case.yaml`` to the class.
Exact solutions themselves stay in warpSPH (``caseUtils``); this module only adapts
them. Digitised experimental data lives under ``data/literature`` and the page's
``reference/`` folder with provenance (loaders land with the pages that need them).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

from .store import Trajectory

__all__ = ['gaussianSmooth', 'Reference', 'ProfileReference', 'TGVReference', 'SodReference', 'TC10Reference', 'FrontiereAcousticReference', 'REFERENCES',
           'buildReference']


class Reference:
    """What every reference offers: named scalar ``metrics`` of a run against the exact solution.

    The metric names are the column names of the pages' error tables and the ``metric`` of the
    convergence figure; the first one is the *primary* metric (the one the orders table lists per
    resolution).
    """

    kind = ''

    def metrics(self, traj: Trajectory, index: int = -1) -> Dict[str, float]:
        raise NotImplementedError

    def flag(self, metrics: Dict[str, float]) -> str:
        """A short failure label when the metrics say the run does not track the reference, else ``''``.

        The runner's velocity alarm only fires at 100x the expected velocity, so a run can grow
        tenfold in energy without it; the page must still call that a failure.
        """
        return ''

    @classmethod
    def fromTrajectory(cls, traj: Trajectory, **options):
        raise NotImplementedError


class ProfileReference(Reference):
    """Exact fields along one axis. Subclasses fill ``fields`` and implement the two methods."""

    kind = ''
    #: field name -> (axis label, short name for tables)
    fields: Dict[str, Tuple[str, str]] = {}
    xlabel = 'x'

    def measure(self, frame: Dict[str, np.ndarray]) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """Sorted positions and the measured fields of the particles the reference covers."""
        raise NotImplementedError

    def evaluate(self, t: float, x: np.ndarray) -> Dict[str, np.ndarray]:
        raise NotImplementedError

    def landmarks(self, t: float) -> Dict[str, float]:
        """Named x-positions (waves, fronts) at time ``t`` for annotations; may be empty."""
        return {}


class FrontiereAcousticReference(ProfileReference):
    """Frontiere 2017 section 4.1, Eqs. (94)-(95), in the paper's units.

    This is the linear traveling-wave reference, not an exact finite-amplitude
    Euler solution. Its density norm weights particles equally. Restricting the
    parameters prevents a different acoustic setup being silently scored as this
    study. No simulation imports or reference downloads are needed.
    """

    kind = 'frontiere2017-acoustic'
    fields = {'density': (r'density $\rho$', 'rho')}
    xlabel = '$x$'
    expectedParams = {'gamma': 5 / 3, 'rho0': 1.0, 'A': 1e-6, 'lamda': 1.0, 'c_s': 1.0}

    def __init__(self, params: Dict[str, Any]):
        for key, expected in self.expectedParams.items():
            if key not in params:
                raise ValueError(f'Frontiere acoustic reference requires recorded parameter {key!r}')
            actual = float(params[key])
            if not np.isfinite(actual) or not np.isclose(actual, expected, rtol=1e-12, atol=0):
                raise ValueError(f'Frontiere acoustic parameter {key}={actual}; expected {expected}')

    @classmethod
    def fromTrajectory(cls, traj: Trajectory, **_):
        if traj.dim != 1:
            raise ValueError('Frontiere acoustic study requires a 1D trajectory')
        return cls(traj.params)

    def evaluate(self, t: float, x: np.ndarray) -> Dict[str, np.ndarray]:
        if not np.isfinite(t):
            raise ValueError('Acoustic reference time must be finite')
        return {'density': 1.0 + 1e-6 * np.sin(2 * np.pi * (np.asarray(x, dtype=float) - t))}

    def measure(self, frame: Dict[str, np.ndarray]):
        positions = np.asarray(frame['positions'])
        rho = np.asarray(frame['densities'])
        if positions.ndim != 2 or positions.shape[1] != 1 or rho.shape != (len(positions),) or not len(rho):
            raise ValueError('Expected nonempty 1D positions and one density per particle')
        if not np.all(np.isfinite(positions)) or not np.all(np.isfinite(rho)):
            raise ValueError('Nonfinite particles cannot be dropped from the published acoustic norm')
        if 'kinds' in frame and np.any(np.asarray(frame['kinds']) != 0):
            raise ValueError('Periodic acoustic study expects only evolving fluid particles')
        order = np.argsort(positions[:, 0])
        return positions[order, 0], {'density': rho[order]}

    def metrics(self, traj: Trajectory, index: int = -1) -> Dict[str, float]:
        from . import derived
        errs = derived.profileErrors(traj, self, index, fields=['density'])['density']
        return {'L1 rho': errs['L1'], 'L2 rho': errs['L2'], 'Linf rho': errs['Linf'],
                'L1 rho / A': errs['L1'] / 1e-6}


class SodReference(ProfileReference):
    """Exact Riemann solution of the Sod tube on ``0 < x < 1`` with the diaphragm at ``x = 0.5``.

    The warpSPH case lays the tube out in a periodic box ``[-1, 1]`` together with its
    mirror image (so the box has no walls); only the physical tube ``0 < x < 1`` is
    compared, and no wave reaches the box ends before ``tLimit``.
    """

    kind = 'sod'
    fields = {
        'density': (r'density $\rho$', 'rho'),
        'velocity': (r'velocity $v_x$', 'v'),
        'pressure': (r'pressure $p$', 'p'),
        'internalEnergy': (r'internal energy $u$', 'u'),
    }
    xlabel = '$x$'

    def __init__(self, params: Dict[str, Any], diaphragm: float = 0.5, samples: int = 8001):
        self.gamma = float(params['gamma'])
        self.left = (float(params['left_pressure']), float(params['left_rho']), float(params['left_velocity']))
        self.right = (float(params['right_pressure']), float(params['right_rho']), float(params['right_velocity']))
        self.diaphragm = diaphragm
        self.samples = samples
        self._cache: Dict[float, Tuple[Dict[str, float], Dict[str, np.ndarray]]] = {}

    @classmethod
    def fromTrajectory(cls, traj: Trajectory, **_) -> 'SodReference':
        return cls(traj.params)

    def metrics(self, traj: Trajectory, index: int = -1) -> Dict[str, float]:
        from . import derived
        errs = derived.profileErrors(traj, self, index)
        return {f'L1 {self.fields[k][1]}': errs[k]['L1'] for k in self.fields}

    def _solve(self, t: float):
        key = round(float(t), 12)
        if key not in self._cache:
            from warpSPH.caseUtils.compressible.sod.sodSolution import solve
            positions, _, values = solve(left_state=self.left, right_state=self.right,
                                         geometry=(0., 1., self.diaphragm), t=float(t), gamma=self.gamma,
                                         npts=self.samples, dustFrac=0.0)
            self._cache[key] = ({k: float(v) for k, v in positions.items()}, values)
        return self._cache[key]

    def evaluate(self, t: float, x: np.ndarray) -> Dict[str, np.ndarray]:
        _, values = self._solve(t)
        return {'density': np.interp(x, values['x'], values['rho']),
                'velocity': np.interp(x, values['x'], values['u']),
                'pressure': np.interp(x, values['x'], values['p']),
                'internalEnergy': np.interp(x, values['x'], values['energy'])}

    def landmarks(self, t: float) -> Dict[str, float]:
        positions, _ = self._solve(t)
        return {'rarefaction head': positions['Head of Rarefaction'],
                'rarefaction foot': positions['Foot of Rarefaction'],
                'contact': positions['Contact Discontinuity'],
                'shock': positions['Shock']}

    def measure(self, frame: Dict[str, np.ndarray]):
        x = frame['positions'][:, 0]
        keep = (x > 0.0) & (x < 1.0)
        order = np.argsort(x[keep])
        x = x[keep][order]
        rho = frame['densities'][keep][order]
        v = frame['velocities'][keep][order][:, 0]
        if 'internalEnergies' in frame:
            u = frame['internalEnergies'][keep][order]
        else:
            u = np.full_like(x, np.nan)
        p = (self.gamma - 1.0) * rho * u
        return x, {'density': rho, 'velocity': v, 'pressure': p, 'internalEnergy': u}


class TGVReference(Reference):
    """Taylor-Green vortex on the periodic box ``[0, L]^2``: the exact decaying velocity field.

    ``v = U A(t) (cos(kx + p) sin(ky + p), -sin(kx + p) cos(ky + p))`` with ``k = k_param / 2``,
    ``A(t) = exp(-2 nu k^2 t)`` and the quarter-period shift ``p`` the case stamps (even ``k_param``:
    ``pi/2``). The kinetic energy decays as ``A^2``, i.e. at rate ``4 nu k^2``. The field is
    evaluated at the particles' current positions (it is an Eulerian solution).
    """

    kind = 'tgv'
    xlabel = '$x$'

    def __init__(self, params: Dict[str, Any], L: float):
        self.nu = float(params['nu'])
        self.k = float(params['k']) / 2.0
        self.U = float(params['uMag'])
        self.rho0 = float(params['rho0'])
        self.L = float(L)
        explicit = params.get('phase')
        self.phase = float(explicit) if explicit is not None else (np.pi / 2 if params['k'] % 2 == 0 else 0.0)

    @classmethod
    def fromTrajectory(cls, traj: Trajectory, **_) -> 'TGVReference':
        return cls(traj.params, traj.caseSpec['L'])

    @property
    def rate(self) -> float:
        """Exponential decay rate of the kinetic energy."""
        return 4.0 * self.nu * self.k ** 2

    def amplitude(self, t):
        return np.exp(-0.5 * self.rate * np.asarray(t))

    @property
    def kineticEnergy0(self) -> float:
        return 0.25 * self.U ** 2 * self.rho0 * self.L ** 2

    def kineticEnergy(self, t):
        return self.kineticEnergy0 * np.exp(-self.rate * np.asarray(t))

    def velocity(self, t: float, positions: np.ndarray) -> np.ndarray:
        x, y = positions[:, 0], positions[:, 1]
        a = self.U * float(self.amplitude(t))
        return np.stack([a * np.cos(self.k * x + self.phase) * np.sin(self.k * y + self.phase),
                         -a * np.sin(self.k * x + self.phase) * np.cos(self.k * y + self.phase)], axis=1)

    def effectiveViscosity(self, t: np.ndarray, kinetic: np.ndarray) -> float:
        """``nu`` that reproduces the measured kinetic-energy decay (least-squares slope of ``log KE``)."""
        ok = (t > 0) & (kinetic > 0)
        slope = np.polyfit(t[ok], np.log(kinetic[ok] / kinetic[0]), 1)[0]
        return float(-slope / (4.0 * self.k ** 2))

    def flag(self, metrics: Dict[str, float]) -> str:
        if metrics.get('nu_eff/nu', 1.0) < 0:
            return 'kinetic energy grows instead of decaying'
        if metrics.get('KE error', 0.0) > 0.5 or metrics.get('L2 v', 0.0) > 1.0:
            return 'does not track the exact solution (energy error above 50 %)'
        return ''

    def metrics(self, traj: Trajectory, index: int = -1) -> Dict[str, float]:
        from .store import readDiagnostics
        frame = traj.frame(index)
        err = frame['velocities'] - self.velocity(frame['t'], frame['positions'])
        scale = self.U * float(self.amplitude(frame['t']))
        out = {'L2 v': float(np.sqrt(np.mean(np.sum(err * err, axis=1))) / scale)}
        d = readDiagnostics(traj.dir)
        t, ke = d['t'], d['kineticEnergy']
        out['KE error'] = float(abs(ke[-1] - self.kineticEnergy(t[-1])) / self.kineticEnergy(t[-1]))
        out['nu_eff/nu'] = self.effectiveViscosity(t, ke) / self.nu
        return out


def gaussianSmooth(t, p, sigma: float = 0.01, dt: float = 1e-3):
    """Gaussian smoothing on a 1 ms grid, NaN-aware, as in warpSPH's ``scripts/plot_sloshingOverlay.py`` (the method of the
    2026-10-09 sloshing validation): a record with gaps (the fluid probe is undefined with fewer than three particles near
    it) is averaged over its valid samples only (kernel-weighted mean; where less than 20 % of the kernel weight is valid
    the result stays NaN) instead of being interpolated across, which would stretch an edge spike over the gap."""
    t = np.asarray(t, dtype=float)
    p = np.asarray(p, dtype=float)
    grid = np.arange(0.0, float(np.nanmax(t)), dt)
    ok = np.isfinite(p)
    tv = t[ok]
    y = np.interp(grid, tv, p[ok])
    gapStep = np.diff(tv)
    pos = np.searchsorted(tv, grid)
    nearest = np.abs(grid - tv[np.clip(pos, 0, len(tv) - 1)])
    prev = np.abs(grid - tv[np.clip(pos - 1, 0, len(tv) - 1)])
    valid = (np.minimum(nearest, prev) <= max(2.0 * dt, 1.5 * float(np.median(gapStep)))).astype(float)
    n = int(4 * sigma / dt)
    k = np.exp(-0.5 * (np.arange(-n, n + 1) * dt / sigma) ** 2)
    k /= k.sum()
    num = np.convolve(np.pad(y * valid, n, mode='edge'), k, mode='valid')
    den = np.convolve(np.pad(valid, n, mode='edge'), k, mode='valid')
    return grid, np.where(den > 0.2, num / np.maximum(den, 1e-12), np.nan)


class TC10Reference(Reference):
    """SPHERIC test case 10, lateral water impact (18 % filling): the wall pressure at sensor 1 against the
    experiment.

    The data are the page's ``reference/spheric-tc10`` files (see ``PROVENANCE.md`` there): the recorded trace
    (1 ms block mean and maximum) and the repeatability register of the first four impacts (peak pressure of each of
    ~100 repeated experiments, 20 kHz raw peaks).

    **Like with like.** A sharp raw peak and a smoothed one are not comparable, and a particle simulation's raw sensor
    reading is a noisy few-millisecond event. Simulation and recorded trace are therefore smoothed the same way
    (``sigma`` = 10 ms Gaussian, NaN-aware, :func:`gaussianSmooth`) before their peaks are compared; the peak of an
    impact is the maximum of the smoothed trace within ``window`` seconds of the experimental impact. The four impacts of
    the recorded trace are the isolated raw pressure maxima above ``impactThreshold`` mbar. The repeatability register
    (raw peaks) is context for the scatter between repetitions, not a comparison value.
    """

    kind = 'tc10'
    sensorColumn = 'sensorPressureProbe'      # Gaussian-smoothed fluid probe at the sensor, Pa; defined for every scheme
    impactThreshold = 15.0
    window = 0.15
    sigma = 0.01
    impulseWindow = 0.1

    def __init__(self, pageDir):
        from pathlib import Path as _Path
        folder = _Path(pageDir) / 'reference' / 'spheric-tc10'
        raw = np.loadtxt(folder / 'lateral_water_1kHz.txt', skiprows=1)
        self.t = raw[:, 0]
        self.pMean = raw[:, 1]            # mbar, 1 ms block mean
        self.pMax = raw[:, 6]             # mbar, 1 ms block maximum
        self.rollDeg = raw[:, 2]
        reps = np.genfromtxt(folder / 'Repeatability_Files' / 'Water_4first_peak_lateral_impact_tto_0_85_H93_B1X.txt',
                             skip_header=2)
        self.repeats = reps                # (experiments, 4), mbar, raw peaks
        self.repeatMean = reps.mean(0)
        self.repeatStd = reps.std(0, ddof=1)
        from scipy.signal import find_peaks
        idx, _ = find_peaks(self.pMax, height=self.impactThreshold, distance=1000)   # >= 1 s apart (1 kHz samples)
        self.impactTimes = self.t[idx[:4]]
        self.tSmooth, self.pSmooth = gaussianSmooth(self.t, self.pMean, self.sigma)
        self.expPeaks, self.expPeakTimes = self._peaksOf(self.tSmooth, self.pSmooth)

    @classmethod
    def fromTrajectory(cls, traj: Trajectory, pageDir=None, **_) -> 'TC10Reference':
        return cls(pageDir)

    @property
    def peakNames(self):
        return [f'peak {k + 1} (mbar)' for k in range(len(self.impactTimes))]

    def _peaksOf(self, t, p):
        out, when = [], []
        for te in self.impactTimes:
            sel = (t >= te - self.window) & (t <= te + self.window) & np.isfinite(p)
            if not sel.any():
                out.append(float('nan')); when.append(float('nan'))
                continue
            i = np.argmax(np.where(sel, p, -np.inf))
            out.append(float(p[i])); when.append(float(t[i]))
        return np.array(out), np.array(when)

    def simulatedSeries(self, runDir):
        """Raw sensor pressure of the run in mbar (NaN where the probe has no fluid)."""
        from .store import readDiagnostics
        d = readDiagnostics(runDir, ['t', self.sensorColumn])
        return d['t'], d[self.sensorColumn] / 100.0          # Pa -> mbar

    def smoothedSimulated(self, runDir):
        t, p = self.simulatedSeries(runDir)
        return gaussianSmooth(t, p, self.sigma)

    def peaks(self, runDir):
        """Smoothed peaks (mbar) and their times within ``window`` of each experimental impact."""
        return self._peaksOf(*self.smoothedSimulated(runDir))

    def impulseRatio(self, runDir) -> float:
        """Mean over the impacts of (simulated / recorded) pressure impulse within ``impulseWindow`` seconds of the impact.

        Raw traces; a sensor with no fluid around it counts as zero pressure."""
        t, p = self.simulatedSeries(runDir)
        p = np.nan_to_num(p)
        ratios = []
        for te in self.impactTimes:
            sim = (t >= te - self.impulseWindow) & (t <= te + self.impulseWindow)
            exp = (self.t >= te - self.impulseWindow) & (self.t <= te + self.impulseWindow)
            if sim.sum() < 2:
                continue
            ratios.append(np.trapezoid(p[sim], t[sim]) / np.trapezoid(self.pMean[exp], self.t[exp]))
        return float(np.mean(ratios)) if ratios else float('nan')

    def metrics(self, traj: Trajectory, index: int = -1) -> Dict[str, float]:
        peaks, when = self.peaks(traj.dir)
        out = {name: float(v) for name, v in zip(self.peakNames, peaks)}
        out['impulse / exp'] = self.impulseRatio(traj.dir)
        out['mean |dt| (ms)'] = float(np.nanmean(np.abs(when - self.expPeakTimes)) * 1000.0)
        return out

    def bands(self) -> Dict[str, tuple]:
        """The recorded trace's smoothed peak of each impact as (value, 0), for the sweep figure's reference lines."""
        return {name: (float(v), 0.0) for name, v in zip(self.peakNames, self.expPeaks)}

    def referenceRows(self, names):
        """Rows to prepend to an errors table: the recorded trace's own numbers for the metrics it has."""
        b = self.bands()
        row = ['experiment (recorded trace, smoothed)', ''] + [f'{b[n][0]:.3g}' if n in b else ('1' if n == 'impulse / exp' else '--')
                                                              for n in names]
        return [row]


REFERENCES = {
    'frontiere2017-acoustic': FrontiereAcousticReference,
    'sod': SodReference,
    'tgv': TGVReference,
    'tc10': TC10Reference,
}


def buildReference(kind: str, traj: Trajectory, **options):
    """``options`` (e.g. ``pageDir``) go to the reference's ``fromTrajectory``; references ignore what they do not need."""
    if kind not in REFERENCES:
        raise KeyError(f'unknown reference kind {kind!r}; known: {sorted(REFERENCES)}')
    return REFERENCES[kind].fromTrajectory(traj, **options)
