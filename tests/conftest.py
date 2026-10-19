"""Synthetic fixtures: a throw-away repo root with one Sod page whose "runs" are particles sampled
from the exact solution plus noise, written in warpSPH's trajectory.h5 layout. Nothing here needs a GPU."""

import json
import shutil
from pathlib import Path

import h5py
import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]

SOD_PARAMS = dict(gamma=5 / 3, left_rho=1.0, left_pressure=1.0, left_velocity=0.0,
                  right_rho=0.25, right_pressure=0.1795, right_velocity=0.0)

CASE_YAML = {
    'slug': 'sod', 'family': 'compressible', 'title': 'Sod shock tube', 'status': 'drafted',
    'description': 'test page', 'cases': ['sod'], 'solvers': ['compressible'], 'walls': None,
    'schemes': ['CompSPH', 'Monaghan'],
    'origin': {'references': ['sod1978']},
    'reference': {'kind': 'sod'},
    'runs': [{'schemes': ['CompSPH', 'Monaghan'], 'nx': [100, 200, 400], 'golden': False}],
    'figures': [
        {'id': 'hero', 'kind': 'loop', 'run': 'CompSPH__default__nx400', 'fields': ['density', 'velocity']},
        {'id': 'overlay', 'kind': 'overlay', 'select': {'nx': 400}, 'fields': ['density', 'velocity'], 'caption': 'c'},
        {'id': 'convergence', 'kind': 'convergence', 'select': {}, 'metric': 'L1 rho', 'caption': 'c'},
    ],
    'tables': [{'id': 'comparison', 'kind': 'errors', 'select': {'nx': 400}},
               {'id': 'orders', 'kind': 'orders', 'select': {}}],
    'notebook': None,
    'site': {'importance': 1, 'img': 'hero'},
}

PAGE_MD = """<<hero>>

Intro {% cite sod1978 --file cases %}.

<<figure:overlay>>

<<table:comparison>>

<<command:CompSPH__default__nx400>>

<<figure:convergence>>

<<table:orders>>

<<reproduce>>

<<refs>>
"""


def writeRun(runDir: Path, nx: int, noise: float, seed: int = 0):
    from warpSPHCases.reference import SodReference
    ref = SodReference(SOD_PARAMS)
    rng = np.random.default_rng(seed)
    x = np.linspace(-0.995, 0.995, nx + nx // 4)
    runDir.mkdir(parents=True)
    times = [0.0, 0.075, 0.15]
    with h5py.File(runDir / 'trajectory.h5', 'w') as h:
        h.attrs['scheme'] = 'CompSPH'
        for name in ('positions', 'velocities', 'densities', 'internalEnergies', 'supports', 'times'):
            h.create_group(name)
        h.create_dataset('combinedMasses', data=np.ones_like(x))
        h.create_dataset('combinedKinds', data=np.zeros_like(x, dtype=int))
        for i, t in enumerate(times):
            key = f'frame_{i:05d}'
            e = ref.evaluate(t if t > 0 else 1e-6, np.clip(x, 0, 1))
            n = noise * rng.standard_normal(x.size)
            h['positions'].create_dataset(key, data=x[:, None])
            h['velocities'].create_dataset(key, data=(e['velocity'] + n)[:, None])
            h['densities'].create_dataset(key, data=e['density'] + n)
            h['internalEnergies'].create_dataset(key, data=e['internalEnergy'] + n)
            h['supports'].create_dataset(key, data=np.full_like(x, 0.01))
            h['times'].create_dataset(key, data=np.array([t]))
    (runDir / 'caseSpec.json').write_text(json.dumps({'nx': nx, 'dim': 1, 'params': SOD_PARAMS}))
    (runDir / 'timing.json').write_text(json.dumps(dict(
        wallTime=1.0, nSteps=10, msPerStep=1.0, msPerStepMean=1.0, commits={'warpSPH': 'abc1234'}, gpu='test')))


@pytest.fixture
def root(tmp_path):
    """A repo root with the real schema, the test page, and synthetic trajectories (error ~ 1/nx)."""
    (tmp_path / 'schemas').mkdir()
    shutil.copy(REPO / 'schemas' / 'case.schema.json', tmp_path / 'schemas')
    pageDir = tmp_path / 'cases' / 'compressible' / 'sod'
    pageDir.mkdir(parents=True)
    (pageDir / 'case.yaml').write_text(yaml.safe_dump(CASE_YAML, sort_keys=False))
    (pageDir / 'page.md').write_text(PAGE_MD)
    (tmp_path / 'data').mkdir()
    shutil.copy(REPO / 'data' / 'references.bib', tmp_path / 'data')
    for scheme, scale in (('CompSPH', 1.0), ('Monaghan', 2.0)):
        for nx in (100, 200, 400):
            writeRun(tmp_path / 'trajectories' / 'compressible' / 'sod' / f'{scheme}__default__nx{nx}',
                     nx, noise=scale * 0.2 / nx, seed=nx)
    return tmp_path
