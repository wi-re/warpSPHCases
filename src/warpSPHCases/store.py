"""Reading trajectories back, and moving runs through the storage tiers.

Reading uses plain ``h5py`` + numpy, no torch and no warpSPH, so figures
re-render on a laptop or on Colab without a GPU stack. The file layout is
warpSPH's ``storeMode='trajectory'`` export (``io/export.py``): one dataset per
frame under ``positions/``, ``velocities/``, ``densities/``, ``times/`` and
whichever of the case's ``extraFields`` were written, static per-particle
arrays under ``combined*``, and the run configuration under ``config/``.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import h5py
import numpy as np

__all__ = ['Trajectory', 'Timing', 'promote', 'sha256', 'writeManifest', 'readDiagnostics']

#: per-frame datasets read when present; positions/velocities/densities/times always exist
_FRAME_FIELDS = ('positions', 'velocities', 'densities', 'internalEnergies', 'supports', 'pressures')

#: files a promoted run keeps (the rest -- frames, gif -- stays in results/)
_PROMOTED = ('trajectory.h5', 'caseSpec.json', 'config.json', 'timing.json', 'diagnostics.csv')


@dataclass
class Timing:
    wallTime: float
    nSteps: int
    msPerStep: float            # median step time, first (JIT warm-up) step excluded
    msPerStepMean: float
    diverged: bool = False
    stopReason: Optional[str] = None
    velocityAlarms: int = 0
    video: bool = False
    gpu: Optional[str] = None
    commits: Optional[Dict[str, str]] = None
    gpuUtilBefore: Optional[int] = None     # GPU utilisation (%) at launch: >~30 means timing is contended

    @classmethod
    def load(cls, runDir: Path) -> 'Timing':
        return cls(**json.loads((Path(runDir) / 'timing.json').read_text()))


class Trajectory:
    """One run's ``trajectory.h5``: frame times, per-frame fields, run attributes."""

    def __init__(self, runDir: Path):
        self.dir = Path(runDir)
        self.path = self.dir / 'trajectory.h5'
        self._file = h5py.File(self.path, 'r')
        self.keys: List[str] = sorted(self._file['positions'].keys())
        self.times = np.array([float(self._file['times'][k][0]) for k in self.keys])
        self.attrs: Dict[str, Any] = {k: (v.item() if hasattr(v, 'item') else v)
                                      for k, v in self._file.attrs.items()}
        self.scheme: str = str(self.attrs['scheme'])
        self.fields = [f for f in _FRAME_FIELDS if f in self._file]
        specPath = self.dir / 'caseSpec.json'
        self.caseSpec: Dict[str, Any] = json.loads(specPath.read_text()) if specPath.exists() else {}
        self.params: Dict[str, Any] = dict(self.caseSpec.get('params', {}))
        self.timing: Optional[Timing] = None
        if (self.dir / 'timing.json').exists():
            self.timing = Timing.load(self.dir)

    def __len__(self) -> int:
        return len(self.keys)

    def close(self) -> None:
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def frameAt(self, t: float) -> int:
        """Index of the stored frame closest to simulated time ``t``."""
        return int(np.argmin(np.abs(self.times - t)))

    def frame(self, index: int) -> Dict[str, np.ndarray]:
        """All per-frame fields at ``index`` (negative indices count from the end) plus ``t``."""
        key = self.keys[index]
        out = {name: self._file[name][key][...] for name in self.fields}
        out['t'] = float(self.times[index])
        # static arrays (the trajectory is particle-ordered, not re-sorted)
        for name, src in (('masses', 'combinedMasses'), ('kinds', 'combinedKinds')):
            if src in self._file:
                out[name] = self._file[src][...]
        return out

    def static(self, name: str) -> np.ndarray:
        return self._file[name][...]

    @property
    def dim(self) -> int:
        return int(self.caseSpec.get('dim', self._file['positions'][self.keys[0]].shape[-1]))

    def series(self, field: str) -> np.ndarray:
        """``field`` for every frame, as a list of arrays stacked when the particle count is constant."""
        return np.stack([self._file[field][k][...] for k in self.keys])


def readDiagnostics(runDir: Path, columns: Optional[List[str]] = None) -> Dict[str, np.ndarray]:
    """The per-step diagnostics written by the run (``diagnostics.csv``) as columns (all, or just ``columns``)."""
    path = Path(runDir) / 'diagnostics.csv'
    with open(path, newline='') as f:
        reader = csv.reader(f)
        header = next(reader)
        keep = [i for i, name in enumerate(header) if columns is None or name in columns]
        data = [[row[i] for i in keep] for row in reader]
    names = [header[i] for i in keep]
    table = np.array([[float(v) if v != '' else np.nan for v in row] for row in data]) if data else np.empty((0, len(keep)))
    return {name: table[:, j] for j, name in enumerate(names)}


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def promote(sourceDir: Path, destDir: Path, files=_PROMOTED) -> Path:
    """Copy a finished run's curated files from ``results/`` to ``trajectories/``."""
    destDir.mkdir(parents=True, exist_ok=True)
    for name in files:
        src = Path(sourceDir) / name
        if src.exists():
            shutil.copy2(src, destDir / name)
    return destDir


def writeManifest(page, runIds: Optional[List[str]] = None) -> Path:
    """``cases/<family>/<slug>/artifacts.json``: checksum, size and provenance of each promoted run.

    Large files are not in git; this manifest is. ``hf`` stays ``null`` until the
    trajectories are uploaded by hand (docs/STORAGE.md).
    """
    path = page.dir / 'artifacts.json'
    manifest = json.loads(path.read_text()) if path.exists() else {'slug': page.slug, 'artifacts': {}}
    for run in page.publicRuns:        # internal runs are not listed in the public manifest
        if runIds and run.id not in runIds:
            continue
        runDir = page.trajectoryDir(run.id)
        if not (runDir / 'trajectory.h5').exists():
            continue
        h5 = runDir / 'trajectory.h5'
        entry: Dict[str, Any] = {
            'path': f'trajectories/{page.family}/{page.slug}/{run.id}/trajectory.h5',
            'sha256': sha256(h5),
            'bytes': h5.stat().st_size,
            'hf': manifest['artifacts'].get(run.id, {}).get('hf'),
        }
        if (runDir / 'timing.json').exists():
            timing = json.loads((runDir / 'timing.json').read_text())
            entry.update(wallTime=round(timing['wallTime'], 2), msPerStep=round(timing['msPerStep'], 3),
                         nSteps=timing['nSteps'], gpu=timing.get('gpu'), commits=timing.get('commits'))
        if (runDir / 'caseSpec.json').exists():
            # absolute paths of this machine do not belong in a public manifest
            entry['caseSpec'] = json.loads((runDir / 'caseSpec.json').read_text().replace(str(page.dir), '{pageDir}'))
        manifest['artifacts'][run.id] = entry
    path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + '\n')
    return path
