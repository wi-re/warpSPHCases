# warpSPH case support and validation targets

Snapshot: 2026-10-19. This catalogue separates physical case families, exact reference benchmarks, numerical realizations and evidence of support. Its immediate target is one accepted trajectory per exact benchmark, reusable Python validation and local-file visualization in Remote.

## Scope agreed with the user

A shared visual character establishes a family, not an exact benchmark. Quantitative targets take priority when analytic solutions, measured experiments or independent high-order references exist. Distinct dimensions, initial conditions, boundaries and reference protocols remain distinct. A CG demonstration can inform visualization without qualifying as a quantitative reference.

One solver initially supplies an accepted trajectory for each selected exact benchmark. Other solvers remain runnable; illustrative comparisons such as KH are selected deliberately. Convergence and limitations are evaluated per case. Training-data design is a separate research question. HF is initially a distribution/download location; direct HF-to-Remote streaming is deferred.

## Core dynamics and paper studies

Keep a compact set of reusable dynamics builders. Exact ICs, discretization, references and figure-level comparisons belong in files organized by paper. A study-specific setup can live in that paper’s specialized subfolder. Adding a published variant normally adds a study, not another registered factory. See [the architecture and acceptance contract](PAPER_REPRODUCTIONS.md).

The first reproduction suite is Frontiere 2017 CRKSPH: 14 dynamics families and 21 studies, starting with analytic tests before instability/reference extraction and expensive dimensional variants. See [the suite and implementation order](../reproductions/frontiere2017/README.md). Marrone 2011 sections 3.1 and 3.3 remain subsequent pressure-history targets. Paper files are definition drafts, not executable runner documents or completed validations; the acoustic density metric and local-data notebook are the first Python analysis component.

| Paper | Study | Core dynamics | Binding | Dimension | Reference targets |
| --- | --- | --- | --- | --- | --- |
| frontiere2017 | section-4-0-1-kidder | kidder | existing-builder-needs-reconciliation | 1 | 1: entropy ratio; compatible versus total energy |
| frontiere2017 | section-4-1-acoustic | linear-wave | existing-builder-needs-reconciliation | 1 | 2: density L1 convergence |
| frontiere2017 | section-4-2-hydrostatic | hydrostatic | existing-builder-needs-reconciliation | 2 | 3: initial/final density at t=7 |
| frontiere2017 | section-4-3-1-sod-1d | sod | existing-builder-needs-reconciliation | 1 | 4: density, pressure, velocity and entropy |
| frontiere2017 | section-4-3-1-sod-3d | sod | existing-builder-needs-reconciliation | 3 | 5: profiles, transverse velocities and particle positions |
| frontiere2017 | section-4-3-2-sedov-1d | sedov | existing-builder-needs-reconciliation | 1 | 6: radial profiles and symmetry; 11: planar density convergence |
| frontiere2017 | section-4-3-2-sedov-2d | sedov | existing-builder-needs-reconciliation | 2 | 6: radial profiles and symmetry |
| frontiere2017 | section-4-3-2-sedov-3d | sedov | existing-builder-needs-reconciliation | 3 | 7: radial profiles and symmetry |
| frontiere2017 | section-4-3-3-noh-1d | noh | existing-builder-needs-reconciliation | 1 | 8: radial profiles and symmetry; 11: planar density convergence |
| frontiere2017 | section-4-3-3-noh-2d | noh | existing-builder-needs-reconciliation | 2 | 8: radial profiles and symmetry |
| frontiere2017 | section-4-3-3-noh-3d | noh | existing-builder-needs-reconciliation | 3 | 9: radial profiles and symmetry |
| frontiere2017 | section-4-3-4-woodward | woodward-colella | existing-builder-needs-reconciliation | 1 | 10: density and specific thermal energy |
| frontiere2017 | section-4-4-1-gresho | gresho | existing-builder-needs-reconciliation | 2 | 12: azimuthal velocity at t=3 and 5 |
| frontiere2017 | section-4-4-2-yee | yee | existing-builder-needs-reconciliation | 2 | 13: point positions; 14: density and velocity profiles; 15: L1/L2/Linf convergence |
| frontiere2017 | section-4-4-3-kh | kelvin-helmholtz | existing-builder-needs-reconciliation | 2 | 16: density snapshots; 17: mode amplitude and maximum transverse kinetic energy; 18: viscous pressure |
| frontiere2017 | section-4-4-4-rt | rayleigh-taylor | existing-builder-needs-reconciliation | 2 | 19: density at t=4; two CRKSPH resolutions |
| frontiere2017 | section-4-4-5-shearing-noh-vs1 | shearing-noh | existing-builder-needs-reconciliation | 2 | 20: profiles for shear amplitude 1 |
| frontiere2017 | section-4-4-5-shearing-noh-vs5 | shearing-noh | existing-builder-needs-reconciliation | 2 | 20: profiles for shear amplitude 5 |
| frontiere2017 | section-4-5-1-blob-2d | blob-wind | proposed-reusable-core-builder | 2 | 21: density snapshots; 23: 2D cloud mass fraction |
| frontiere2017 | section-4-5-1-blob-3d | blob-wind | proposed-reusable-core-builder | 3 | 22: density slices; 23: 3D cloud mass fraction |
| frontiere2017 | section-4-5-2-triple-point | triple-point | existing-family-capability-gated | 2 | 24: IC regions; 25: time sequence; 26: density at t=5; 27: density at t=7 |
| marrone2011 | section-3-1-wall-impact | dam-break | existing-builder | 2 | 5: P1 and P2 pressure histories |
| marrone2011 | section-3-3-step-impact | dam-break | needs-setup-adapter-audit | 3 | 14: geometry; 16: sensor positions; 17: pressure histories |

[Paper study matrix](../data/validation/paper-studies.csv). Setup matching, reference availability, metric implementation and acceptance are separate columns; every initial study remains unscored until those requirements are met.

## Current implementation coverage

The imported registry contains **48 cases** from 47 modules, mapped to **43 pages**. The configuration catalogue marks **18 ready** and **30 unmigrated**. Remote advertises all 48 through installed discovery; this does not demonstrate that a simulation launches or validates. Its seven static presets are curated entries, not the full catalogue.

Builder ready means the versioned configuration metadata is complete. Unmigrated cases retain legacy paths. Empty declared-scheme lists mean no explicit support declaration; they do not mean every alternative scheme is unsupported. Dimensions below are advertised by Remote in this snapshot. Existing notebook/golden files and reference adapters establish artifact presence only.

| Registered case | Page | Dimensions | Default scheme | Builder | Named variants | Reference adapter |
| --- | --- | --- | --- | --- | --- | --- |
| bowShock | bow-shock | 2 | Monaghan | unmigrated | default only | none declared |
| closedBox | closed-box | 1 | Monaghan | unmigrated | default only | none declared |
| columnCollapse | column-collapse | 2 | divergenceFree | unmigrated | default only | none declared |
| cylinderWake | cylinder-wake | 2 | deltaSPH | unmigrated | default only | none declared |
| dambreak | dam-break | 2 | deltaSPH | unmigrated | default only | none declared |
| drivenSquare | driven-square | 2 | deltaSPH | unmigrated | default only | none declared |
| droplet | oscillating-droplet | 2 | deltaSPH | unmigrated | default only | none declared |
| forwardStep | forward-step | 2 | Monaghan | unmigrated | default only | none declared |
| gresho | gresho | 2 | CRKSPH | ready | smoothed | none declared |
| hydrostatic | hydrostatic | 2 | CRKSPH | ready | default only | none declared |
| hydrostaticColumn | hydrostatic-column | 2 | divergenceFree | unmigrated | default only | none declared |
| impact | impact | 2 | deltaSPH | unmigrated | default only | none declared |
| kelvinHelmholtz | kelvin-helmholtz | 2 | CRKSPH | ready | smooth-density | none declared |
| kidder | kidder | 1;2;3 | CRKSPH | ready | default only | none declared |
| kolmogorov | kolmogorov-flow | 2 | deltaSPH | unmigrated | default only | none declared |
| kolmogorovIncompressible | kolmogorov-flow | 2 | divergenceFree | unmigrated | default only | none declared |
| ldc | lid-driven-cavity | 2 | deltaSPH | unmigrated | default only | none declared |
| linearWave | linear-wave | 1 | CRKSPH | ready | default only | none declared |
| movingObstacle | moving-obstacle | 2 | deltaSPH | unmigrated | default only | none declared |
| noh | noh | 1 | CRKSPH | ready | default only | none declared |
| openFlow | open-flow | 2 | deltaSPH | unmigrated | default only | none declared |
| periodicChannel | periodic-channel | 2 | deltaSPH | unmigrated | default only | none declared |
| piston | piston | 1 | Monaghan | unmigrated | default only | none declared |
| randomFlow | random-flow | 2 | deltaSPH | ready | bounded;obstacle | none declared |
| randomFlowIncompressible | random-flow | 2 | divergenceFree | unmigrated | default only | none declared |
| rayleighTaylor | rayleigh-taylor | 2 | CRKSPH | ready | default only | none declared |
| sedov | sedov | 1;2;3 | CRKSPH | ready | singular;quadrant | none declared |
| sedovWalls | sedov-walls | 2 | CRKSPH | unmigrated | default only | none declared |
| shearBox | shear-box | 2 | Monaghan | ready | default only | none declared |
| shearWave | shear-wave | 2 | divergenceFree | unmigrated | default only | none declared |
| shearingNoh | shearing-noh | 2 | CRKSPH | ready | default only | none declared |
| shockCylinder | shock-cylinder | 2 | Monaghan | unmigrated | default only | none declared |
| shockReflection | shock-reflection | 1 | Monaghan | unmigrated | default only | none declared |
| sloshingTank | sloshing-tank | 2 | deltaSPH | unmigrated | default only | tc10 |
| sod | sod | 1 | CompSPH | ready | classic;smoothed | sod |
| sod2d | sod | 2 | CompSPH | ready | classic | sod |
| sod3d | sod | 3 | CompSPH | ready | classic | sod |
| squarePatch | rotating-square-patch | 2 | deltaSPH | unmigrated | default only | none declared |
| staticBlob | static-blob | 2 | divergenceFree | unmigrated | default only | none declared |
| stokesArray | stokes-array | 2 | deltaSPH | unmigrated | default only | none declared |
| taylorCouette | taylor-couette | 2 | deltaSPH | unmigrated | default only | none declared |
| tgv | taylor-green-vortex | 2 | divergenceFree | unmigrated | default only | tgv |
| tgv-wc | taylor-green-vortex | 2 | deltaSPH | ready | analytic-pressure;no-shifting | tgv |
| triplePoint | triple-point | 2 | CRKSPH | ready | default only | none declared |
| waveEquation | wave-equation | 2 | waveEquation | unmigrated | default only | none declared |
| woodwardColella | woodward-colella | 1 | CRKSPH | ready | default only | none declared |
| woodwardColellaWalls | woodward-colella-walls | 1 | CRKSPH | unmigrated | default only | none declared |
| yee | yee | 2 | CRKSPH | ready | default only | none declared |

[Full metadata and provenance](../data/validation/inventory.json) · [Support CSV](../data/validation/support.csv). All source checkouts and their dirty state are recorded; a commit alone does not reproduce a dirty checkout. This audit constructs no particle systems and runs no solver steps.

[Case by scheme declaration matrix](../data/validation/scheme-support.csv): declared and default-only are metadata evidence, not runtime validation; not-declared is unknown rather than unsupported. Variant-specific compatibility still needs per-case assessment.

[Trajectory availability](../data/validation/trajectory-availability.csv): 56 entries in public artifact manifests; 56 local files exist and 56 checksums match. These are stored artifacts from earlier work, not newly certified references. Raw scratch runs and internal experiment records are outside this inventory.

## Benchmark identity and reference quality

Use a family identifier for browsing. Assign a versioned benchmark identifier only after specifying the governing equations/EOS, dimension, domain and geometry, physical initial fields, boundary and forcing histories, material parameters, units/nondimensionalization, comparison times and reference version. Record equivalent coordinate/unit transformations explicitly.

Keep the numerical realization alongside that identity: particle mass/spacing policy, lattice/glass/jitter and seed, kernel and support/neighbour policy, operator corrections, integration and timestep policy, solver tolerance, precision and scheme. These choices are comparison axes; matching the continuum setup alone does not reproduce a paper’s numerical experiment.

Reference types are descriptive, not a universal ranking. An analytic solution has an applicability interval and modelling assumptions; an experiment has measurement/filtering uncertainty; a converged numerical reference has a discretization/solver error budget. A stored solver golden supports regression and does not become independent scientific truth.

Reflected IC copies with periodic outer bounds are an accepted initial realization of stationary planar reflecting boundaries: use 2**k copies for k reflected axes, transform normal velocities, preserve material IDs, and measure only the physical paper domain. No dedicated reflecting-wall solver is required. Where good reference data are unavailable or would require a new solver, start with clearly labelled qualitative published comparisons; quantitative reference-error acceptance remains separate.

Concrete distinctions from the snapshot and primary definitions:

- Sod defaults to gamma 5/3 and right state (rho,p)=(0.25,0.1795). Its classic variant uses gamma 1.4 and (0.125,0.1). The 1D classic variant also changes samplingRatio; extruded 2D/3D slabs have their own transverse/equal-mass sampling. Preserve these identities.

- LinearWave is advertised as 1D, with amplitude 1e-6, wavelength and sound speed 1, gamma 5/3 and a unit domain. This is a strong first convergence target; the travelling-wave reference is a small-amplitude approximation whose validity must be checked when changing amplitude.

- Classical incompressible TGV and [SPHERIC TC22](https://www.spheric-sph.org/tests/test-22) use different references. The latter supplies a weakly compressible expansion. Audit the existing analytic-pressure variant before declaring an exact match.

- The current drivenSquare oscillates sinusoidally. [SPHERIC TC6](https://www.spheric-sph.org/tests/test-06) supplies acceleration to steady translation. The body shape alone does not establish the benchmark.

- The current cylinderWake uses a periodic pinned frame. [DFG 2D-1](https://wwwold.mathematik.tu-dortmund.de/~featflow/en/benchmarks/cfdbenchmarking/flow/dfg_benchmark1_re20.html) specifies a confined inlet/outlet channel; it needs a separate target.

- staticBlob is a rest-state null test. [SPHERIC TC23](https://www.spheric-sph.org/tests/test-23) is wind-driven cloud disruption. Central-force oscillation, unforced drop expansion and capillary oscillation also need separate identities.

## Local literature and online search coverage

The corpus contains **207 PDF files**, representing **206 unique hashes**. Text extraction screened 204 files against 61 benchmark alias groups. Three scans (Gingold 1977, Monaghan 1992 and Monaghan 1994; 55 pages total) were visually screened, with checksum-bound records in [visual reviews](../data/validation/visual-reviews.json). A page-level text-coverage check distinguishes genuine text from scanned-paper watermarks. The duplicate Tube Maps downloads remain recorded rather than counted as independent papers.

The search produces 3017 page/family candidates across 181 documents. A match can occur in a bibliography or discussion; it is not a claim of benchmark use. The reviewed evidence table contains **147 relationships across 39 papers**, with physical PDF pages and section/figure/table locators. Online expansion records **25 queries** and 15 selected primary reference/provider records.

**Coverage limit:** file enumeration covers the complete local PDF corpus; searchable papers were screened for aliases and the three scans were screened visually. Benchmark-section review is selective and exact warpSPH-to-paper setup equivalence is not established by those family associations. Online search is a bounded expansion, not a claim to enumerate every paper ever published. Unreviewed matches remain visible for subsequent case work; no absence claim is inferred from a failed search.

[Corpus checksums](../data/validation/literature-corpus.csv) · [Unreviewed matches](../data/validation/literature-candidates.csv) · [Reviewed relationships](../data/validation/literature-evidence.csv) · [Case-to-paper index](../data/validation/literature-by-case.csv) · [Online queries](../data/validation/web-queries.json). Copyrighted PDFs and extracted text stay outside tracked research outputs.

## Papers and the case families they use

Locators refer to physical PDF pages, starting at one. The CSV distinguishes benchmark sections, quantitative comparisons, demonstrations with internal metrics and related variants. None of these family-level associations automatically certifies an exact setup match.

| Paper | Case families | Evidence locators |
| --- | --- | --- |
| [frontiere2017](https://doi.org/10.1016/j.jcp.2016.12.004) | kidder, linear-wave, hydrostatic, sod, sedov, noh, woodward-colella, gresho, yee, kelvin-helmholtz, rayleigh-taylor, shearing-noh, blob-wind, triple-point | kidder: p13 (4.0.1); linear-wave: p15 (4.1); hydrostatic: p15 (4.2); sod: p17 (4.3.1); sedov: p17 (4.3.2); noh: p20 (4.3.3); woodward-colella: p21 (4.3.4); gresho: p24 (4.4.1); yee: p24 (4.4.2; continuation p25); kelvin-helmholtz: p25 (4.4.3); rayleigh-taylor: p29 (4.4.4); shearing-noh: p30 (4.4.5); blob-wind: p31 (4.5.1; cloud mass fraction Fig 23 p34); triple-point: p34 (4.5.2) |
| [hopkins2015](https://doi.org/10.1093/mnras/stv195) | linear-wave, hydrostatic, gresho, keplerian-disc, sod, woodward-colella, sedov, noh, kelvin-helmholtz, rayleigh-taylor, blob-wind, random-flow, evrard-collapse | linear-wave: p13 (4.2.1; convergence Fig 2 p14); hydrostatic: p14 (4.2.2); gresho: p16 (4.2.3); keplerian-disc: p19 (4.2.4); sod: p23 (4.3.1); woodward-colella: p23 (4.3.2); sedov: p25 (4.3.3); noh: p26 (4.3.4); kelvin-helmholtz: p28 (4.4.1); rayleigh-taylor: p32 (4.4.2); blob-wind: p33 (4.4.3); random-flow: p34 (4.4.4 driven turbulence; related family with different forcing); evrard-collapse: p37 (4.5.1) |
| [owen2014](https://doi.org/10.1002/fld.3912) | sod, noh, sedov | sod: p10 (4.1 planar Sod); noh: p11 (4.2 planar; 4.3 cylindrical p13); sedov: p15 (4.4 planar; 4.5 cylindrical p18) |
| [borrow2022](https://doi.org/10.1093/mnras/stab3166) | sod, sedov, gresho, noh, hydrostatic, kelvin-helmholtz, blob-wind, evrard-collapse | sod: p7 (5.1); sedov: p8 (5.2); gresho: p9 (5.3); noh: p9 (5.4); hydrostatic: p10 (5.5 square test); kelvin-helmholtz: p11 (5.6; continuation p12); blob-wind: p13 (5.7); evrard-collapse: p14 (5.8) |
| [cabezon2017](https://doi.org/10.1051/0004-6361/201630208) | hydrostatic, shock-reflection, kelvin-helmholtz, rayleigh-taylor, gresho, triple-point | hydrostatic: p8 (5.2 static square); shock-reflection: p11 (5.3.2 wall-shock; not proven identical to shockReflection); kelvin-helmholtz: p11 (5.4 fluid instabilities); rayleigh-taylor: p16 (Fig 14; quantitative profiles Fig 17 p17); gresho: p16 (5.5); triple-point: p21 (5.7) |
| [sandnes2025](https://doi.org/10.1016/j.jcp.2025.113907) | hydrostatic, sod, kelvin-helmholtz, rayleigh-taylor, blob-wind | hydrostatic: p17 (4.1 square test); sod: p19 (4.2; 3D tube); kelvin-helmholtz: p20 (4.3 ideal gas; smooth and discontinuous ICs; material variant 4.4 p26); rayleigh-taylor: p28 (4.5 ideal gas; material variant 4.6 p29); blob-wind: p30 (4.7; dense and mixed gas mass Fig 14 p31) |
| [groth2023](https://doi.org/10.1093/mnras/stad2717) | keplerian-disc, hydrostatic, blob-wind, sod, sedov, random-flow | keplerian-disc: p9 (4.2.2); hydrostatic: p11 (4.3.3); blob-wind: p11 (4.3.4); sod: p11 (4.4.1); sedov: p13 (4.4.2); random-flow: p17 (4.6 decaying subsonic turbulence; not same random IC generator) |
| [gao2023](https://doi.org/10.1016/j.jcp.2023.112270) | rayleigh-taylor, kelvin-helmholtz, triple-point, double-mach | rayleigh-taylor: p14 (4.3); kelvin-helmholtz: p16 (4.4); triple-point: p18 (4.5 multi-material variant); double-mach: p19 (4.6) |
| [puri2014](https://doi.org/10.1016/j.jcp.2014.03.055) | linear-wave, sjogreen, woodward-colella, noh | linear-wave: p13 (5.1 acoustic diffusion; accuracy tests 5.2 and 5.3); sjogreen: p15 (5.4); woodward-colella: p16 (5.5); noh: p19 (5.6 cylindrical) |
| [cha2003](https://doi.org/10.1046/j.1365-8711.2003.06266.x) | linear-wave, sod, sjogreen, shear-box | linear-wave: p7 (5.1 isothermal wave; different EOS); sod: p7 (5.2); sjogreen: p10 (5.5); shear-box: p14 (5.7 velocity shear; exact IC match unassessed) |
| [cha2010](https://doi.org/10.1111/j.1365-2966.2010.16200.x) | kelvin-helmholtz, blob-wind | kelvin-helmholtz: p5 (4.1 density ratio 2; 4.2 ratio 10 p6; 4.3 diagonal p7); blob-wind: p7 (4.4) |
| [dehnen2012](https://doi.org/10.1111/j.1365-2966.2012.21439.x) | linear-wave, gresho | linear-wave: p9 (3.3 numerical resolution of sound waves); gresho: p10 (4.2) |
| [cullen2010](https://doi.org/10.1111/j.1365-2966.2010.17158.x) | sod, shearing-noh, keplerian-disc, evrard-collapse | sod: p9 (5.1); shearing-noh: p10 (5.3 shearing shock; exact match unassessed); keplerian-disc: p7 (4.3 Keplerian ring); evrard-collapse: p11 (5.4) |
| [morris1997](https://doi.org/10.1006/jcph.1997.5776) | planar-couette, periodic-channel, stokes-array | planar-couette: p6 (3.1); periodic-channel: p6 (3.2); stokes-array: p7 (3.3; FEM comparison) |
| [adami2012](https://doi.org/10.1016/j.jcp.2012.05.005) | periodic-channel, planar-couette, backward-step, stokes-array, hydrostatic-column, dam-break | periodic-channel: p6 (5.1 Poiseuille); planar-couette: p6 (5.1 Couette); backward-step: p7 (5.2); stokes-array: p8 (5.3); hydrostatic-column: p9 (6.1; complex geometry 6.2 p10); dam-break: p13 (7.2; geometry changed for wall impact p14) |
| [adami2013](https://doi.org/10.1016/j.jcp.2013.01.043) | taylor-green-vortex, lid-driven-cavity, rayleigh-taylor | taylor-green-vortex: p8 (3.3; lattice and relaxed starts); lid-driven-cavity: p10 (3.4; Re100/1000/10000); rayleigh-taylor: p13 (3.6; multiphase and 3D variants) |
| [ghia1982](https://doi.org/10.1016/0021-9991(82)90058-4) | lid-driven-cavity | lid-driven-cavity: p12 (Table I p12 and Table II p13; tabulated centreline profiles) |
| [marrone2011](https://doi.org/10.1016/j.cma.2010.12.016) | dam-break | dam-break: p3 (3.1 vertical wall; 3.2 tall structure p7; 3.3 3D step p8) |
| [marrone2015](https://doi.org/10.1016/j.jfluidstructs.2015.01.014) | impact | impact: p8 (5.1 1D jets; 5.2 2D equal jets p9; unequal/oblique 5.3 and 5.4 p13/15) |
| [decourcy2024](https://doi.org/10.1016/j.cma.2023.116700) | hydrostatic-column, rotating-square-patch, oscillating-droplet, impact, dam-break | hydrostatic-column: p14 (4.1.1 rigid base; elastic base 4.1.2 is a separate target); rotating-square-patch: p18 (4.2; BEM comparisons Fig 15 and 16 p23); oscillating-droplet: p23 (4.3 central force); impact: p28 (4.4 normal water-jet impact); dam-break: p29 (4.5) |
| [sun2017](https://doi.org/10.1016/j.cma.2016.10.028) | rotating-square-patch, oscillating-droplet, impact, cylinder-wake | rotating-square-patch: p10 (4.1); oscillating-droplet: p12 (4.2 central force); impact: p14 (4.3 rectangular patches); cylinder-wake: p15 (4.4 inclined ellipse; 4.5 square/rectangle p17; 4.6 sector-cut circle p20) |
| [sun2019](https://doi.org/10.1016/j.cma.2019.01.045) | taylor-green-vortex, cylinder-wake, rotating-square-patch, sloshing-tank | taylor-green-vortex: p7 (3.1; Re100/1000); cylinder-wake: p12 (3.2 inclined ellipse Re1000); rotating-square-patch: p15 (3.3); sloshing-tank: p18 (3.4 shallow-water Series experiment; 3D extension p20; not TC10) |
| [oger2016](https://doi.org/10.1016/j.jcp.2016.02.039) | taylor-green-vortex, lid-driven-cavity, rotating-square-patch, dam-break | taylor-green-vortex: p9 (6.2); lid-driven-cavity: p12 (6.3 Re1000); rotating-square-patch: p15 (6.4); dam-break: p20 (6.5) |
| [lind2012](https://doi.org/10.1016/j.jcp.2011.10.027) | taylor-green-vortex, dam-break, wet-bed-dam-break, regular-wave | taylor-green-vortex: p13 (4.1.1); dam-break: p17 (4.2.2.1 dry bed); wet-bed-dam-break: p18 (4.2.2.2); regular-wave: p20 (4.3) |
| [ramachandran2021](https://doi.org/10.1016/j.compfluid.2021.105031) | taylor-green-vortex, lid-driven-cavity, rotating-square-patch, expanding-drop, dam-break | taylor-green-vortex: p11 (4.1); lid-driven-cavity: p13 (4.2; steady 4.2.1 p14); rotating-square-patch: p14 (4.3); expanding-drop: p15 (4.4 elliptical drop; do not identify with central-force droplet); dam-break: p16 (4.5 2D; 4.6 3D) |
| [english2022](https://doi.org/10.1007/s40571-021-00403-3) | hydrostatic-column, sloshing-tank, dam-break, open-flow | hydrostatic-column: p5 (4.1 wedge bed); sloshing-tank: p5 (4.2 SPHERIC TC10; sensor plots p7); dam-break: p7 (4.3 3D cuboid obstacle; elevations and pressure p10); open-flow: p8 (4.4 fish pass; not generic openFlow geometry) |
| [ferrand2013](https://doi.org/10.1002/fld.3666) | periodic-channel, hydrostatic-column, dam-break | periodic-channel: p17 (4.1 laminar channel); hydrostatic-column: p19 (4.2.1 wedge tank); dam-break: p20 (4.2.2 wedge tank) |
| [leroy2014](https://doi.org/10.1016/j.jcp.2013.12.035) | lid-driven-cavity, stokes-array, dam-break | lid-driven-cavity: p21 (4.1); stokes-array: p24 (4.2 infinite cylinder array in a channel; periodic geometry check needed); dam-break: p28 (4.3 wedge) |
| [yildiz2009](https://doi.org/10.1002/nme.2458) | lid-driven-cavity, cylinder-wake | lid-driven-cavity: p12 (3); cylinder-wake: p13 (4; impulsive cylinder experiment; not DFG inflow benchmark) |
| [monaghan2013](https://doi.org/10.1002/fld.3671) | oscillating-droplet, rayleigh-taylor | oscillating-droplet: p8 (4; two-layer extension 5 p12); rayleigh-taylor: p16 (7; multiphase variant) |
| monaghan1994 | expanding-drop, dam-break, regular-wave | expanding-drop: p4 (6; analytic ODE and Table I p4/5); dam-break: p5 (7; Martin and Moyce comparison Table II p6); regular-wave: p6 (9 wave maker; snapshots p7) |
| [colagrossi2003](https://doi.org/10.1016/S0021-9991(03)00324-3) | dam-break | dam-break: p7 (Fig 3 geometry; front evolution Fig 16 p19; pressure Fig 22 p24) |
| [bender2015](https://doi.org/10.1145/2786784.2786796) | dam-break | dam-break: p6 (4; Fig 3 breaking dam model) |
| [ihmsen2014](https://doi.org/10.1109/TVCG.2013.105) | dam-break | dam-break: p6 (Fig 5 breaking dam) |
| [bender2026](https://doi.org/10.1111/cgf.70559) | dam-break, rayleigh-taylor | dam-break: p5 (4; Fig 2; error metrics Fig 3 p6); rayleigh-taylor: p8 (Fig 7 and 8; multiphase high-density-ratio variants) |
| [winchenbach2025diffsph](https://doi.org/10.1016/j.jcp.2026.114769) | sod, rayleigh-taylor, taylor-green-vortex, lid-driven-cavity, oscillating-droplet | sod: p40 (E.2; Fig 19); rayleigh-taylor: p41 (Fig 20); taylor-green-vortex: p42 (Fig 21; diagnostic plots p43); lid-driven-cavity: p44 (Fig 23); oscillating-droplet: p45 (Fig 24 and 25) |
| [cornelis2019](https://doi.org/10.1007/s00371-018-1488-8) | shear-wave | shear-wave: p5 (5.1; amplitude and density plots p5/6) |
| [king2022](https://doi.org/10.1016/j.jcp.2021.110760) | taylor-green-vortex, periodic-channel | taylor-green-vortex: p14 (8.1; L2 convergence Fig 9 p15); periodic-channel: p15 (8.2; convergence Fig 10 p16) |
| winchenbach2024pmac | taylor-green-vortex | taylor-green-vortex: p1 (Cross-validation setup and generalized randomized family) |

## Validation targets for every existing page

P0 identifies the first reusable workflow; P1 follows with strong references or complementary physics; P2 needs more setup/reference work. These are scientific targets, not measured performance claims. Exact setup requirements and proposed metrics are in the CSV/YAML.

| Page family | Priority | Reference strategy | Primary metrics |
| --- | --- | --- | --- |
| sod | P0 | Exact Riemann solution | density/velocity/pressure L1,L2; shock/contact positions |
| linear-wave | P0 | Small-amplitude travelling-wave solution | phase/amplitude; density L1,L2; observed order |
| kidder | P1 | Kidder isentropic compression | entropy error; density/velocity norms; boundary work |
| noh | P1 | Noh similarity solution | shock radius; post-shock density; wall-heating integral |
| shearing-noh | P2 | Published shearing-shock comparison | shock location; transverse velocity; energy budget |
| woodward-colella | P1 | Independent converged Euler solution | density L1; shock/contact locations |
| sedov | P1 | Sedov similarity solution | shock radius; radial profiles; symmetry; energy |
| hydrostatic | P1 | Stationary pressure-equilibrium density contact | spurious velocity/acceleration; interface distortion; pressure drift |
| gresho | P1 | Stationary Gresho profile | azimuthal-velocity L1; radial velocity; angular momentum |
| yee | P1 | Smooth isentropic vortex | field L1,L2; phase/advection error; observed order |
| shear-box | P1 | Steady inviscid sinusoidal shear | mode decay; artificial dissipation; transverse velocity |
| kelvin-helmholtz | P1 | Setup-specific mode-growth/reference solution | mode amplitude; mixing width; density/vorticity maps |
| rayleigh-taylor | P2 | Setup-specific independent numerical reference | bubble/spike height; mixing width; energy |
| triple-point | P2 | Independent high-order Euler reference | interface/shock locations; density profiles; conservation |
| closed-box | P1 | Uniform stationary gas | maximum velocity; pressure/density drift; conservation |
| piston | P2 | Rankine-Hugoniot piston shock | shock speed; post-shock pressure/density; wall work |
| shock-reflection | P2 | Wall Riemann/reflected shock solution | shock speed and state; wall pressure |
| woodward-colella-walls | P2 | Independent converged blast interaction | density L1; wave positions; wall load |
| sedov-walls | P2 | Similarity solution only before wall contact; later numerical reference | pre-contact radial error; reflected wave positions; conservation |
| shock-cylinder | P2 | Geometry-specific independent shock/body solution | shock geometry; surface pressure/load |
| bow-shock | P2 | Geometry-specific independent compressible reference | stand-off distance; pressure profile; drag |
| forward-step | P2 | Woodward-Colella Mach-3 step reference | shock positions; contours; pressure profiles |
| dam-break | P1 | Named experiment per geometry; Lobovsky/MARIN/Marrone separately | front/run-up; pressure impulse and arrival; uncertainty-normalized error |
| sloshing-tank | P1 | SPHERIC TC10 lateral water measurements | pressure impulse/peak/time; repeatability; surface height |
| oscillating-droplet | P1 | Central-force drop ODE | semi-axes; period; energy/volume drift |
| rotating-square-patch | P1 | Published BEM/reference evolution | surface geometry; pressure probes; angular momentum |
| impact | P1 | Named rectangular-jet analytic/numerical reference | kinetic-energy loss; impulse; pressure; shape |
| column-collapse | P2 | Named column-collapse experiment | front and height; energy; pressure |
| taylor-green-vortex | P0 | Classical incompressible exact field; separate WC approximation | velocity L2; kinetic energy; pressure; effective viscosity |
| kolmogorov-flow | P2 | Laminar forced-shear solution below instability; numerical reference otherwise | forcing/mode balance; energy/enstrophy; spectrum |
| random-flow | P2 | Specified deterministic IC and independent numerical/statistical reference | energy/enstrophy; spectra; divergence; long-time statistics |
| shear-wave | P0 | Analytic viscous sinusoidal decay | mode decay; velocity L2; inferred viscosity |
| static-blob | P1 | Rest-state null solution | spurious velocity/acceleration; density drift |
| lid-driven-cavity | P1 | Ghia tables; SPHERIC TC3 | centreline u/v; vortex centres; steady residual |
| moving-obstacle | P2 | Named rotating-body experiment/numerical reference | drag/lift; circulation; wake and torque |
| driven-square | P1 | SPHERIC TC6 only after prescribed-motion matching | pressure/viscous drag; vorticity; body work |
| open-flow | P2 | Named channel/obstacle reference | mass flux; drag; inlet/outlet reflection |
| periodic-channel | P0 | Steady and startup Poiseuille solution | velocity L2; wall shear/load; flux |
| stokes-array | P1 | Published periodic-cylinder-array reference | permeability/drag; pressure/viscous force; force balance |
| taylor-couette | P1 | Laminar annular analytic velocity and torque | azimuthal velocity L2; torque; radial leakage |
| cylinder-wake | P1 | Geometry-specific wake reference; DFG as separate target | drag/lift; Strouhal; pressure difference; recirculation |
| hydrostatic-column | P1 | Hydrostatic pressure and rest-state solution | pressure-depth norm; spurious motion; force balance |
| wave-equation | P2 | Analytic/manufactured scalar wave | amplitude/phase; propagation speed; energy; order |

[Existing-page targets and setup requirements](../data/validation/case-targets.csv). Wall representation and discretization belong in each applicable study; an analytic pre-wall-contact reference cannot be used after reflected waves invalidate it.

## Active paper and adapter targets

Current-fluid-physics identifies studies using the present equation/model families; it does not assert that a preset or initializer is implemented. Capability-check requires a targeted dimension/boundary/adapter audit before scheduling runs. The delivery column distinguishes a paper study, specialized adapter and genuinely reusable builder. None implies one factory per paper.

| Target | Priority | Scope | Delivery | Prerequisite |
| --- | --- | --- | --- | --- |
| marrone2011-section-3-1 | P0 | current-fluid-physics | paper-study | Reconcile solver probe and Plotting configs; extract reference traces and define acceptance criteria. |
| marrone2011-section-3-3 | P0 | capability-check | paper-study-with-specialized-geometry | Locate the user-identified Remote setup and audit dimensionality/geometry/probes; do not promote a 2D proxy to the 3D paper benchmark. |
| wc-tgv-spheric22 | P1 | current-fluid-physics | paper-study-or-specialized-adapter | Audit existing analytic-pressure variant against the full expansion; setting initial pressure alone does not prove equivalence. |
| vortices-3d-spheric16 | P2 | capability-check | paper-study-or-specialized-adapter | New or extended sampler and reference; extruded 2D TGV is insufficient. |
| kh-smooth-explicit-diffusion | P1 | capability-check | paper-study-or-specialized-adapter | Match profiles, diffusion and diagnostics; audit physical-model support before implementation. |
| dambreak-lobovsky-030-060 | P1 | capability-check | paper-study-or-specialized-adapter | Acquire reference tables and provenance; audit 3D setup support; document 2D approximation separately. |
| dambreak-marin-spheric02 | P2 | capability-check | paper-study-or-specialized-adapter | Match provider geometry and probes; inspect supplied description/data rather than substitute a generic obstacle. |
| sloshing-tc10-roof-oil | P2 | capability-check | paper-study-or-specialized-adapter | Check air effects and physical model suitability; current lateral-water adapter is not general TC10 support. |
| translating-square-spheric06 | P1 | current-fluid-physics | paper-study-or-specialized-adapter | Add motion-record adapter and exact geometry; existing sinusoidal drivenSquare is a related family. |
| cylinder-dfg-2d1 | P2 | capability-check | paper-study-or-specialized-adapter | Audit inlet/outlet capabilities; pinned periodic frame cannot be labelled DFG. |
| cylinder-dfg-2d2 | P2 | capability-check | paper-study-or-specialized-adapter | Establish 2D-1 setup and startup/transient handling first. |
| blob-ambient-flow-core | P1 | current-fluid-physics | shared-core-builder-with-paper-presets | Implement or reuse a general initial-condition builder; Frontiere 2017 section 4.5.1 supplies separate 2D and 3D study definitions; no factory per paper. |
| planar-couette-startup | P1 | current-fluid-physics | paper-study-or-specialized-adapter | Check reuse of channel geometry; prescribed wall velocity and analytic series adapter. |
| expanding-unforced-drop | P2 | current-fluid-physics | paper-study-or-specialized-adapter | Explicit force-free setup and analytic ODE adapter. |
| wet-bed-dambreak | P2 | current-fluid-physics | paper-study-or-specialized-adapter | Acquire original experiment specification/data and assess gate-removal effects. |
| backward-facing-step | P2 | capability-check | paper-study-or-specialized-adapter | Reconstruct exact channel, inflow and Reynolds definition. |
| sjogreen-rarefaction | P2 | current-fluid-physics | paper-study-or-specialized-adapter | Audit whether existing Sod state knobs express the exact setup before adding a factory. |
| shu-osher | P2 | current-fluid-physics | paper-study-or-specialized-adapter | New IC profile and independently verified high-order reference. |
| double-mach-reflection | P2 | capability-check | paper-study-or-specialized-adapter | Distinguish from registered one-dimensional shockReflection; match corner/boundary protocol. |
| manufactured-operators | P1 | current-fluid-physics | paper-study-or-specialized-adapter | Export operator inputs/outputs and define boundary contribution; no long trajectory needed. |

[Active target details](../data/validation/additional-targets.csv) · [Primary reference definitions](../data/validation/external-references.yaml).

## Long-term directions

Solid/elastic models, landslides, heaving/floating bodies and additional physical-model work remain [long-term targets](../data/validation/backlog/long-term-targets.csv). SPHERIC is a useful source, not a catalogue-completion goal. Its [background checklist](backlog/SPHERIC_COVERAGE.md) is retained separately from active validation.

## Case workflow and completion criteria

Build Frontiere 2017 CRKSPH as the first paper suite. Start with a reconciled float64 acoustic configuration and its implemented density measurement, then planar Sod/Sedov/Noh, Gresho and Yee. Reconcile the broader contact/shock/shear/instability studies next; gate costly dimensional variants and mixed-gamma triple point explicitly. Add Remote adapters after Python measurements and a checked local trajectory. Marrone 3.1/3.3 remain subsequent free-surface targets. See the suite for the complete study order and setup/reference gaps.

For each exact benchmark, complete: source-linked setup; reference and measurement operator; Python metrics verified on controlled inputs; a thin stored-data notebook; selected convergence/limitations evidence; one accepted local trajectory with resolved configuration, source revisions and checksums; then Remote plot parity and the page. Reference quality determines acceptance tolerances; visual similarity alone cannot qualify a quantitative benchmark.

Remote initially consumes a portable case description and a separately selected local trajectory. The description should version the benchmark and analysis definitions, declare required fields/units, list probes/profiles/time windows and reference assets, and specify camera/colour/plot settings. Validate compatibility when the user selects the data file. Use declarative built-in analysis identifiers rather than executable notebook code. Existing URL/view presets are useful starting points, but do not yet establish this complete portable validation-file contract.

Use Python as the initial analysis implementation. For expensive or complex metrics, export versioned measurement series that Remote can plot; for calculations also implemented in the browser, compare both implementations on the same stored frames. Case pages may forward the case description; file selection remains local. HF download/distribution can be added without changing the measurement definitions. No direct HF streaming or ML training-data pipeline is required for this milestone.

## Reproduce the audit

From the cases checkout, with the warp environment and pdftotext installed:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/lu26029/miniconda3/envs/warp/bin/python scripts/audit_validation_inventory.py --date 2026-10-19
python scripts/screen_validation_literature.py
/home/lu26029/miniconda3/envs/warp/bin/python scripts/build_validation_matrices.py
```

The inventory uses the installed warpSPH checkout and sibling Remote checkout. Screening uses the sibling literature directory by default; both scripts accept explicit source/output paths. Reviewed YAML records are curated input. Generated CSV/JSON and this report must be refreshed together. The scripts check page claims, target coverage, source identity and PDF page bounds; these checks establish catalogue consistency rather than solver correctness.
