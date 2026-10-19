# Frontiere 2017 CRKSPH reproduction suite

This is the first paper suite for warpSPHCases: **14 dynamics families and 21
studies** from section 4 of Frontiere, Raskin & Owen, *CRKSPH – A Conservative
Reproducing Kernel Smoothed Particle Hydrodynamics Scheme*.
[Paper DOI](https://doi.org/10.1016/j.jcp.2016.12.004).

[`paper.yaml`](paper.yaml) records the published setups, discretizations,
measurements, figure targets, existing builder candidates and remaining gaps.
Its source checksum pins the locally reviewed PDF. PDF page numbers are physical
pages starting at 1. These are definition drafts: **none is yet a resolved,
executed or accepted paper reproduction**. The existing solver implementation and
its tests provide a starting point; selecting its CRKSPH enum is not evidence of
paper-level agreement.

## Coverage

| Family | Studies | Candidate builder | Paper target | Remaining work before execution/comparison |
| --- | ---: | --- | --- | --- |
| Kidder | 1 | `kidder` | §4.0.1, Fig. 1, entropy | Pressures, gamma, active/boundary counts; compatible versus total-energy updates |
| Acoustic wave | 1 | `linearWave` | §4.1, Fig. 2, density convergence | B7/support protocol, timestep, viscosity, float64 and initial sampling check |
| Hydrostatic square | 1 | `hydrostatic` | §4.2, Fig. 3, stationary contact | Gamma 1.5, density contrast 4, uniform lattice with varying masses, volume/density rule |
| Sod | 2: 1D, 3D | `sod`, `sod3d` | §4.3.1, Figs. 4–5; planar convergence Fig. 11 | Smoothed ICs, equal-mass counts, mirror/wall mapping; 3D smoothing adapter |
| Sedov | 3: 1D, 2D, 3D | `sedov` | §4.3.2, Figs. 6–7; planar convergence Fig. 11 | Single-particle energy, symmetry-sector normalization, boundary mapping, exact final time |
| Noh | 3: 1D, 2D, 3D | `noh` | §4.3.3, Figs. 8–9; planar convergence Fig. 11 | Inflow/shock-speed convention and boundaries; registry currently advertises only 1D |
| Interacting blastwaves | 1 | `woodwardColella` | §4.3.4, Fig. 10 | Physical tube mapping; qualitative Fig. 10 first, ATHENA data later; text/caption time discrepancy |
| Gresho | 1 | `gresho` | §4.4.1, Fig. 12 at t=3,5 | Published 64² lattice, exact cusps, center and periodic-coordinate diagnostics |
| Yee vortex | 1 | `yee` | §4.4.2, Figs. 13–15 | Radial-ring resolution/masses, fixed ghost rings, norm convention |
| Kelvin–Helmholtz | 1 | `kelvinHelmholtz` | §4.4.3, Figs. 16–18 | Smooth density, box-wide 0.01 perturbation; qualitative first, McNally measurement/reference later |
| Rayleigh–Taylor | 1 | `rayleighTaylor` | §4.4.4, Fig. 19 | Perturbation 0.025, physical aspect, prescribed pressure and boundary rows |
| Shearing Noh | 2: shear 1,5 | `shearingNoh` | §4.4.5, Fig. 20 | Physical 20×100 lattice, boundaries and shear amplitude convention |
| Blob/wind | 2: 2D,3D | shared builder needed | §4.5.1, Figs. 21–23 | Equal-mass clipped lattices and mass/temperature criterion; qualitative first, reference extraction later |
| Triple point | 1 | `triplePoint` family; capability gated | §4.5.2, Figs. 24–27 | Per-region gamma (1.5,1.5,1.4), regional lattices and reflecting geometry |

Convergence is a study protocol, not a separate registered case. The two Sod
dimensions reproduce the paper's 1D and 3D experiments; a 2D extension would be
labelled separately. The Kidder total-energy comparison remains pending until
that update can be selected and verified. Section 4.6 reuses Noh for performance
analysis; appendix interpolation/operator tests belong in a separate solver
unit-test track rather than expanding this dynamics catalogue.

## Implementation order

1. **Analytic baseline:** acoustic wave, planar Sod/Sedov/Noh, Gresho and Yee.
   For each, reconcile IC/BC/sampling and numerical configuration, implement the
   analytic measurement, verify it on manufactured data, then run one inexpensive
   CRKSPH configuration. Build the stored-data notebook before a resolution sweep.
   Use acoustic and Yee for smooth convergence and planar shocks for first-order
   convergence after extracting the Fig. 11 resolution points.
2. **Broader dynamics:** Kidder and the hydrostatic contact; Woodward and KH
   initially against published figures, adding independent data and McNally
   mode/energy comparisons when feasible; RT
   and both shearing Noh strengths. Prefer existing builders plus explicit paper
   presets. Put a paper-only setup adapter under `specialized/` if needed.
3. **Dimensional and capability extensions:** 2D/3D Sedov/Noh and 3D Sod, then a
   reusable blob/wind initializer and its 2D/3D studies. Gate the exact triple
   point on per-material EOS support. Scale to published resolution only after
   the setup, metric and a small trajectory have been checked.
4. **Delivery:** record one defensible CRKSPH trajectory per selected study,
   with provenance and analysis settings. Add selected solver comparisons later.
   Once Python measurement is established, adapt Remote to the same study and a
   user-selected local recording, then build the case/paper page. HF initially
   distributes downloadable files; training-data design is separate work.

For each resolved setup, record the solver commit, input/source hashes, precision,
support statistics and reference version. Where useful, inspect the authors'
Spheral test inputs as a setup cross-check and pin their revision; agreement with
another implementation is separate from agreement with an analytic or independent
reference. Do not assume current test defaults reproduce the 2017 configuration.

Marrone 2011 sections 3.1/3.3 remain the next free-surface reproduction targets.
No exhaustive cross-solver or 3D resolution product is part of the first pass.

## First Python component

[`acoustic.ipynb`](acoustic.ipynb) reads local `trajectory.h5` recordings with their
resolved `caseSpec.json` sidecars. It uses the shared
`FrontiereAcousticReference` through `buildReference('frontiere2017-acoustic', ...)`.
The density L1 is the particle-unweighted Eq. (95), evaluated at current positions
and actual stored time. L2, Linf and amplitude-normalized L1 are supplementary.
The reference checks the paper's recorded physical parameters, rejects missing
or nonfinite particles, and has manufactured HDF5 tests that distinguish current
positions from initial positions and particle weighting from mass weighting.

The notebook does not execute the unresolved paper presets. It remains an
analysis pilot, without solver results or fitted convergence claims. Acceptance
criteria are deliberately unset. A checked metric is independent of a checked
solver trajectory.

## Issues to resolve before claiming reproduction

- Numerical identity includes the density/volume estimator, support adaptation,
  viscosity limiter and energy update. B7, RK2 and CRKSPH labels alone are not
  enough. Paper `n_h=1` and warpSPH's candidate `n_h=4` use different conventions;
  compare the actual support/neighbor distribution.
- The acoustic amplitude is only 10⁻⁶. Initialization error, storage precision,
  timestepping and roundoff can dominate a convergence plot. The reference is a
  linear wave; do not mistake its finite-amplitude approximation for exact Euler
  evolution at arbitrary amplitude.
- Paper Woodward text uses t=0.038, while the Fig. 10 caption prints 0.38. The
  definition retains this discrepancy and uses the text time provisionally.
  Independent reference data must confirm the alignment.
- Audit formulas against the defining sources before coding them. In particular,
  the printed Noh pre-shock expression needs a sign check; the physical inflow
  compression cannot be inferred from a transcription alone.
- The paper triple point is a mixed-gamma experiment. Uniform-gamma versions
  remain useful dynamics demonstrations with a different exact-study identity.
- Quantitative KH reference errors need the independent McNally data and its
  measurement operator; Woodward errors need an independent reference such as
  the paper's ATHENA trace. Initial qualitative comparisons are sufficient.
  Building a new reference solver is not a prerequisite.
- RT, blob and triple-point figures do not establish unique exact late-time
  trajectories or scalar tolerances. Compare them qualitatively initially;
  additional metrics and uncertainty can support later quantitative work.
  Nonlinear interface details depend on perturbations.
- A published particle count is not necessarily the builder's `nx`. Check active
  particles, ghosts, mirrored domains, regional spacing and mass normalization
  before running at paper scale.

## Boundary and comparison decisions

For stationary planar reflecting walls, use the existing brute-force reflected
IC construction with periodic outer bounds. Each reflected axis doubles the
sampled domain: 2/4/8 copies when all axes reflect in 1D/2D/3D, or 2**k for a
subset of k reflected axes. Normal velocity components change sign; scalars and
material/origin IDs retain their values. Compare profiles, mass and energy in
the original physical paper domain, and report physical versus full particle
counts separately. Triple point uses four copies. This is an accepted numerical
realization; no dedicated wall solver needs to be developed for this milestone.
Prescribed analytic/equilibrium boundaries in Kidder, Yee and RT keep their own
protocols.

When good reference data are unavailable, or would require developing another
solver, an initial qualitative comparison is sufficient. Match times, slices,
coordinates and color scales; retain useful scalar diagnostics where available.
The paper file keeps the reference used in the original publication separately
from our initial comparison mode. Qualitative evidence does not acquire a
numerical error tolerance, and need not block a documented comparison page.

## Materials and species

Within this suite, **only the paper's triple point needs multiple EOS parameter
sets**: regions I/II have gamma=1.5 and III has gamma=1.4. Three initial regions
therefore need two EOS entries; region identity can be tracked separately.
The hydrostatic square, KH, RT and blob use one ideal-gas gamma within each
published test. A density or entropy contrast alone does not require different
material thermodynamics. Their origin labels remain useful for entrainment,
interface and mixing diagnostics; the blob's published retained-mass criterion
still selects all gas satisfying its density/temperature conditions.

Separate the following capabilities rather than bundling them into one feature:

| Capability | Minimal representation | Uses |
| --- | --- | --- |
| Origin tracking | Immutable particle origin ID; optionally reconstructed concentration | Tagged KH/RT fluid, cloud entrainment, material-specific plots |
| Multiple material EOS | Particle material ID selects gamma/EOS parameters | Exact triple point, different-gas shock/contact and shock/bubble problems |
| Mixture composition | Species mass fractions with a mixture EOS and optional diffusion/reactions | Gas mixing, reacting jets/combustion, composition-dependent cooling or burning |
| Multiple phases | Distinct constitutive/interface treatment as needed | Water-air impact, gas bubbles in liquid, cavitation, oil-water interfaces |

The third and fourth rows are broader physics projects. Particle labels do not
model molecular diffusion; several gamma values do not supply surface tension,
phase change or liquid-gas interface mechanics.

Practical extensions closest to the present suite are shock transmission through
a different gas and shock interaction with a helium/air bubble (including
Richtmyer–Meshkov deformation). A primary
[shock–bubble study](https://fti.neep.wisc.edu/fti.neep.wisc.edu/pdf/fdm1334.pdf),
section 3.1.4 / PDF pp. 105–106, assigns separate gas properties and fixed gamma
values. The broader roles are illustrated by
[FLASH's per-species property model](https://flash.rochester.edu/site/flashcode/user_support/flash_ug_devel/node87.html),
[OpenFOAM reacting-flow equations](https://www.sciencedirect.com/science/article/pii/S0045793019301847),
and [MFC's multiphase applications](https://arxiv.org/abs/1907.10512).
The existing warpSPH `shockCylinder` is a shock striking a solid cylinder, not a
gas bubble, and does not itself require multiple gas EOS parameters. Standard
single-water dam-break/sloshing setups also do not require simulated air; adding
an explicit air phase would be a separate study.

The current code already carries `CompressibleState.materials`. A per-material
EOS dispatch helper exists in `modules/eos/gas.py`, but the active CRKSPH step
calls `idealGasEOS(..., gamma=schemeConfig.gamma)` and the triple-point sampler
also initializes with that global gamma. These are building blocks, not verified
end-to-end support.

A scoped candidate extension is to reuse the particle material ID for a small
EOS table, initially fixed-gamma ideal gases, and retain it through mirrored ICs,
reordering and recording. Audit all EOS/sound-speed, energy/entropy and relevant
signal-speed paths before enabling it. Begin checks with a pressure-equilibrium
contact, then shock/interface interaction and the existing single-gamma cases.
Species fractions, diffusion and chemistry need not accompany this extension.
This is a proposed solver direction, not an implemented feature or a prerequisite
for progressing through the remaining single-EOS suite.
