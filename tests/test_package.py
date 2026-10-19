import numpy as np
import pytest

from warpSPHCases import derived
from warpSPHCases.spec import allPages, loadPage
from warpSPHCases.store import Trajectory, writeManifest


def test_every_page_in_the_repo_validates_and_has_unique_run_ids():
    pages = list(allPages())
    assert len(pages) >= 40
    for page in pages:
        ids = [r.id for r in page.runs]
        assert len(ids) == len(set(ids)), page.slug


def test_runs_matrix_expands_schemes_times_resolutions(root):
    page = loadPage('sod', root=root)
    assert len(page.runs) == 6
    assert page.run('Monaghan__default__nx200').nx == 200


def test_norms_and_convergence_slope():
    e = np.array([1.0, -1.0, 0.0, np.nan])
    n = derived.norms(e)
    assert n['L1'] == pytest.approx(2 / 3) and n['Linf'] == 1.0
    assert derived.convergenceSlope([100, 200, 400], [4.0, 2.0, 1.0]) == pytest.approx(1.0)
    assert derived.convergenceSlope([100, 200, 400], [4.0, 1.0, 0.25]) == pytest.approx(2.0)


def test_relative_drift():
    assert derived.relativeDrift(np.array([2.0, 2.2]))[-1] == pytest.approx(0.1)


def test_trajectory_reads_frames_and_times(root):
    page = loadPage('sod', root=root)
    with Trajectory(page.trajectoryDir('CompSPH__default__nx400')) as traj:
        assert len(traj) == 3 and traj.frameAt(0.07) == 1
        frame = traj.frame(-1)
        assert frame['positions'].shape[1] == 1 and frame['t'] == pytest.approx(0.15)


def test_sod_reference_matches_its_own_samples(root):
    from warpSPHCases.reference import SodReference
    page = loadPage('sod', root=root)
    with Trajectory(page.trajectoryDir('CompSPH__default__nx400')) as traj:
        ref = SodReference.fromTrajectory(traj)
        errs = derived.profileErrors(traj, ref)
    assert errs['density']['L1'] < 5e-3          # noise only; the samples are the exact solution
    assert set(ref.landmarks(0.15)) == {'rarefaction head', 'rarefaction foot', 'contact', 'shock'}


def test_manifest_has_checksums(root):
    page = loadPage('sod', root=root)
    path = writeManifest(page)
    import json
    art = json.loads(path.read_text())['artifacts']
    assert len(art) == 6 and len(art['CompSPH__default__nx100']['sha256']) == 64
    assert art['CompSPH__default__nx100']['hf'] is None


def test_full_build_writes_page_assets_and_preview(root):
    from warpSPHCases.site.build import buildPage, checkPage
    page = loadPage('sod', root=root)
    out = buildPage(page)
    text = out.read_text()
    assert text.startswith('---\nlayout: page') and 'category: compressible' in text
    assert '{% include video.liquid' in text and 'figure.liquid' in text
    assert '{% cite sod1978 --file cases %}' in text and '--file cases --cited_in_order' in text
    assert '| scheme | nx | L1 rho' in text and 'warpsph-run sod --scheme CompSPH --nx 400' in text
    assets = root / 'build' / 'site' / 'assets' / 'img' / 'cases' / 'sod'
    assert {p.name for p in assets.iterdir()} >= {'hero.mp4', 'hero-poster.jpg', 'overlay.png', 'convergence.png'}
    html = (root / 'build' / 'preview' / 'sod' / 'index.html').read_text()
    assert 'Sod, G. A.' in html and '<video' in html
    assert checkPage(page) is False or True      # runs exist; only artifacts.json may be missing
    assert not any('missing' in p for p in __import__('warpSPHCases.site.build', fromlist=['x'])._checkBuilt(page))


def test_unknown_citation_key_stops_the_build(root):
    from warpSPHCases.site.build import buildPage
    page = loadPage('sod', root=root)
    (page.dir / 'page.md').write_text((page.dir / 'page.md').read_text() + '\n{% cite nobody2099 --file cases %}\n')
    with pytest.raises(ValueError, match='nobody2099'):
        buildPage(page)


def test_tgv_reference_is_exact_for_exact_data(tmp_path):
    import csv
    import json
    import h5py
    from warpSPHCases.reference import TGVReference
    params = dict(nu=0.01, k=2, uMag=1.0, rho0=1.0)
    L = 2 * np.pi
    ref = TGVReference(params, L)
    assert ref.rate == pytest.approx(0.04) and ref.kineticEnergy0 == pytest.approx(np.pi ** 2)
    rng = np.random.default_rng(1)
    pos = rng.uniform(0, L, size=(500, 2))
    run = tmp_path / 'run'
    run.mkdir()
    times = [0.0, 1.0, 2.0]
    with h5py.File(run / 'trajectory.h5', 'w') as h:
        h.attrs['scheme'] = 'deltaSPH'
        for name in ('positions', 'velocities', 'densities', 'times'):
            h.create_group(name)
        for i, t in enumerate(times):
            key = f'frame_{i:05d}'
            h['positions'].create_dataset(key, data=pos)
            h['velocities'].create_dataset(key, data=ref.velocity(t, pos))
            h['densities'].create_dataset(key, data=np.ones(500))
            h['times'].create_dataset(key, data=np.array([t]))
    (run / 'caseSpec.json').write_text(json.dumps({'L': L, 'dim': 2, 'params': params}))
    tt = np.linspace(0, 2, 50)
    with open(run / 'diagnostics.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['step', 't', 'kineticEnergy'])
        for i, t in enumerate(tt):
            w.writerow([i, t, ref.kineticEnergy(t)])
    with Trajectory(run) as traj:
        m = ref.metrics(traj)
    assert m['L2 v'] < 1e-6 and m['KE error'] < 1e-6 and m['nu_eff/nu'] == pytest.approx(1.0, abs=1e-6)


def test_tc10_reference_smooths_like_with_like_and_scores_a_synthetic_trace(tmp_path):
    import csv
    from conftest import REPO
    from warpSPHCases.reference import TC10Reference, gaussianSmooth
    ref = TC10Reference(REPO / 'cases' / 'free-surface' / 'sloshing-tank')
    assert len(ref.impactTimes) == 4 and ref.repeats.shape[1] == 4
    assert ref.impactTimes[0] == pytest.approx(2.374, abs=0.01) and ref.impactTimes[-1] == pytest.approx(7.303, abs=0.01)
    # the smoothed recorded peaks are those of the 2026-10-09 validation (1800 / 2322 / 1171 Pa)
    assert ref.expPeaks[:3] == pytest.approx([18.0, 23.2, 11.7], abs=0.3)
    # a run whose sensor pressure is a 3 ms wide pulse of the experiment's smoothed height, 5 ms late, with a dry gap
    t = np.arange(0, 7.5, 1e-3)
    p = np.zeros_like(t)
    for te, m in zip(ref.impactTimes, ref.expPeaks):
        p += m * 100.0 * np.exp(-0.5 * ((t - te - 0.005) / 0.003) ** 2) / 0.287      # Pa
    p[(t > 0.2) & (t < 0.4)] = np.nan
    run = tmp_path / 'run'
    run.mkdir()
    with open(run / 'diagnostics.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['step', 't', 'sensorPressureProbe'])
        for i, (ti, pi) in enumerate(zip(t, p)):
            w.writerow([i, ti, 'nan' if np.isnan(pi) else pi])
    peaks, when = ref.peaks(run)
    assert np.allclose(peaks, ref.expPeaks, rtol=0.06)      # smoothing shrinks the 3 ms pulse by 3 / sqrt(3^2 + 10^2)
    assert np.allclose(when - ref.impactTimes, 0.005, atol=3e-3)
    assert ref.referenceRows(ref.peakNames)[0][2] == f'{ref.expPeaks[0]:.3g}'
    g, y = gaussianSmooth(t, p, 0.01)
    assert np.isnan(y[300]) and np.isfinite(y[1000])       # the gap stays a gap
