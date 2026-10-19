"""The one plotting style every page and notebook uses.

Palette and mark rules follow the dataviz method: the eight-hue categorical order
below passed the validator (worst adjacent CVD dE 9.1, normal-vision 19.6; three
slots sit under 3:1 contrast on the light surface, so every chart carries a legend
and a second encoding -- marker shape -- as the relief rule requires). Thin marks,
recessive grid, text in ink never in series colour, reference solutions always the
same thin ink line.

Colour follows the entity: a scheme keeps its slot on every page, whatever subset
the page shows.
"""

from __future__ import annotations

import zlib
from contextlib import contextmanager
from typing import Dict, Iterable, List

import matplotlib as mpl

__all__ = ['DIVERGING', 'SURFACE', 'INK', 'INK2', 'GRID', 'REFERENCE', 'schemeStyle', 'useStyle', 'save', 'SCHEME_ORDER']

SURFACE = '#fcfcfb'
INK = '#0b0b0b'
INK2 = '#52514e'
GRID = '#e4e3df'
REFERENCE = INK

#: fixed slot per scheme (categorical order of the validated palette)
SCHEME_ORDER: List[str] = ['CompSPH', 'Monaghan', 'CRKSPH', 'GSPH', 'InutsukaGSPH', 'MFM', 'MFV', 'PESPH']
_SLOTS = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
_MARKERS = ['o', 's', '^', 'D', 'v', 'P', 'X', '*']
#: the other solver families reuse slots; they never share a chart with the compressible schemes
_OTHER = ['deltaSPH', 'sun2017DeltaSPH', 'artificialCompressible', 'divergenceFree', 'dfsphReference', 'iisph',
          'omniIncompressible', 'band2018pb']


def schemeStyle(scheme: str) -> Dict[str, object]:
    """``color`` and ``marker`` for ``scheme``; unknown names fall back to a slot by a stable hash of the name."""
    if scheme in SCHEME_ORDER:
        i = SCHEME_ORDER.index(scheme)
    elif scheme in _OTHER:
        i = _OTHER.index(scheme)
    else:
        i = zlib.crc32(scheme.encode()) % len(_SLOTS)    # deterministic across processes
    return {'color': _SLOTS[i], 'marker': _MARKERS[i]}


def _diverging():
    from matplotlib.colors import LinearSegmentedColormap
    # blue <-> red poles with the neutral grey midpoint of the dataviz palette
    return LinearSegmentedColormap.from_list('warpcases_diverging', ['#2a78d6', '#f0efec', '#e34948'])


DIVERGING = _diverging()

_RC = {
    'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE, 'savefig.facecolor': SURFACE,
    'axes.edgecolor': INK2, 'axes.labelcolor': INK2, 'text.color': INK,
    'xtick.color': INK2, 'ytick.color': INK2,
    'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.linewidth': 0.8, 'lines.linewidth': 1.4, 'lines.markersize': 3.0,
    'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.titlesize': 9.5, 'axes.titleweight': 'regular',
    'axes.labelsize': 9, 'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 8,
    'legend.frameon': False, 'figure.dpi': 100, 'savefig.dpi': 160,
    'axes.axisbelow': True,
}


@contextmanager
def useStyle():
    with mpl.rc_context(_RC):
        yield


def save(fig, path, **kwargs) -> None:
    kwargs.setdefault('bbox_inches', 'tight')
    kwargs.setdefault('pad_inches', 0.08)
    fig.savefig(path, **kwargs)
