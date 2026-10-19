"""Named, tested derived quantities -- everything computed from a trajectory.

Functions take plain numpy so they run anywhere. Nothing here draws.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Sequence

import numpy as np

from .reference import ProfileReference
from .store import Trajectory

__all__ = ['norms', 'profileErrors', 'convergenceSlope', 'monotonePrefix', 'pairwiseOrders', 'relativeDrift',
           'finalFrameIndex']


def norms(error: np.ndarray) -> Dict[str, float]:
    """L1 (mean |e|), L2 (rms) and L-infinity of a pointwise error, NaNs ignored."""
    e = np.asarray(error, dtype=float)
    e = e[np.isfinite(e)]
    if e.size == 0:
        return {'L1': np.nan, 'L2': np.nan, 'Linf': np.nan}
    return {'L1': float(np.mean(np.abs(e))), 'L2': float(np.sqrt(np.mean(e * e))), 'Linf': float(np.max(np.abs(e)))}


def finalFrameIndex(traj: Trajectory) -> int:
    return len(traj) - 1


def profileErrors(traj: Trajectory, ref: ProfileReference, index: int = -1,
                  fields: Optional[Iterable[str]] = None) -> Dict[str, Dict[str, float]]:
    """Error norms of each field of frame ``index`` against the exact profile at that frame's time."""
    frame = traj.frame(index)
    x, measured = ref.measure(frame)
    exact = ref.evaluate(frame['t'], x)
    return {name: norms(measured[name] - exact[name]) for name in (fields or ref.fields)}


def convergenceSlope(resolution: Sequence[float], error: Sequence[float]) -> float:
    """Least-squares slope of ``log(error)`` against ``log(1/resolution)``: the observed order.

    ``resolution`` is the particle count along the resolved axis (``nx``); a first-order
    method has slope 1, a second-order one 2.
    """
    n = np.asarray(resolution, dtype=float)
    e = np.asarray(error, dtype=float)
    ok = np.isfinite(e) & (e > 0)
    if ok.sum() < 2:
        return float('nan')
    slope, _ = np.polyfit(np.log(n[ok]), np.log(e[ok]), 1)
    return float(-slope)


def monotonePrefix(error: Sequence[float]) -> int:
    """Number of leading points (resolutions in increasing order) over which the error strictly decreases."""
    e = np.asarray(error, dtype=float)
    n = 1
    while n < len(e) and e[n] < e[n - 1]:
        n += 1
    return n


def pairwiseOrders(resolution: Sequence[float], error: Sequence[float]) -> np.ndarray:
    """Observed order between each pair of consecutive resolutions: ``log(e_i / e_i+1) / log(n_i+1 / n_i)``.

    Unlike a fit over all points this shows where convergence stops (an order near zero or negative).
    """
    n = np.asarray(resolution, dtype=float)
    e = np.asarray(error, dtype=float)
    return np.log(e[:-1] / e[1:]) / np.log(n[1:] / n[:-1])


def relativeDrift(series: np.ndarray) -> np.ndarray:
    """``(q(t) - q(0)) / |q(0)|`` for a conserved scalar series."""
    q = np.asarray(series, dtype=float)
    return (q - q[0]) / abs(q[0]) if q[0] != 0 else q - q[0]
