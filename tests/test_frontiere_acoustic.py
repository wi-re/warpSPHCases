"""Manufactured stored data tests the paper's measurement, without a solver run."""
import json

import h5py
import numpy as np
import pytest

from warpSPHCases.reference import FrontiereAcousticReference, buildReference
from warpSPHCases.store import Trajectory


def test_paper_norm_uses_current_positions_and_equal_particle_weights(tmp_path):
    x0 = np.array([0.03, 0.18, 0.29, 0.55, 0.81])
    x = np.array([0.08, 0.21, 0.32, 0.60, 0.85])
    error = np.array([1, -2, 3, -4, 5]) * 1e-8
    with h5py.File(tmp_path / 'trajectory.h5', 'w') as h:
        h.attrs['scheme'] = 'CRKSPH'
        h['combinedMasses'] = [1, 10, 100, 1000, 10000]
        # At a quarter period the traveling sine is -cos(2*pi*x).
        for i, (t, xx, rho) in enumerate([
            (0, x0, 1 + 1e-6 * np.sin(2 * np.pi * x0)),
            (0.25, x, 1 - 1e-6 * np.cos(2 * np.pi * x) + error),
        ]):
            key = f'frame_{i:05d}'
            for name, values in {'times': [t], 'positions': xx[:, None], 'densities': rho,
                                 'velocities': np.zeros((len(x), 1))}.items():
                h.create_dataset(f'{name}/{key}', data=values)
    (tmp_path / 'caseSpec.json').write_text(json.dumps({
        'dim': 1, 'params': FrontiereAcousticReference.expectedParams}))
    with Trajectory(tmp_path) as traj:
        ref = buildReference('frontiere2017-acoustic', traj)
        assert ref.metrics(traj, 0)['L1 rho'] == pytest.approx(0, abs=1e-15)
        metrics = ref.metrics(traj)
    assert metrics['L1 rho'] == pytest.approx(3e-8, abs=2e-16)
    assert metrics['L2 rho'] == pytest.approx(np.sqrt(11) * 1e-8, abs=2e-16)
    assert metrics['Linf rho'] == pytest.approx(5e-8, abs=2e-16)
    assert metrics['L1 rho / A'] == pytest.approx(0.03, abs=2e-10)


def test_paper_reference_rejects_missing_or_different_initial_conditions():
    params = dict(FrontiereAcousticReference.expectedParams)
    params.pop('A')
    with pytest.raises(ValueError, match='recorded parameter'):
        FrontiereAcousticReference(params)
    for value in (1e-3, np.nan):
        with pytest.raises(ValueError, match='expected'):
            FrontiereAcousticReference({**FrontiereAcousticReference.expectedParams, 'A': value})


def test_paper_norm_never_silently_discards_particles():
    ref = FrontiereAcousticReference(FrontiereAcousticReference.expectedParams)
    with pytest.raises(ValueError, match='Nonfinite'):
        ref.measure({'positions': np.array([[0.1], [0.2]]), 'densities': np.array([1, np.nan])})
    with pytest.raises(ValueError, match='only evolving'):
        ref.measure({'positions': np.array([[0.1]]), 'densities': np.array([1.0]), 'kinds': [1]})
    with pytest.raises(ValueError, match='nonempty'):
        ref.measure({'positions': np.empty((0, 1)), 'densities': np.empty(0)})
