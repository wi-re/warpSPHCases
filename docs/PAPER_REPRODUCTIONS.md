# Core dynamics and paper reproductions

Keep a compact set of reusable dynamics builders in warpSPH. Put exact published
experiments in paper files in this repository. The unit of quantitative validation
is a named study and its comparison to a particular result, not the presence of
another registered case or an attractive animation.

## Responsibilities

| Layer | Owns | Example |
| --- | --- | --- |
| Core dynamics | Geometry/IC construction, physical controls and solver hooks shared across studies | Dam break; shock tube; blob interacting with ambient flow |
| Paper reproduction | Exact physical setup, numerical protocol, reference, measurement and figure targets | Frontiere 2017 section 4 suite; Marrone 2011 sections 3.1 and 3.3 |
| Specialized study | Geometry or setup useful only to one paper, kept under that paper | A particular step, prescribed motion or unusual IC construction |

Add a core builder when it supplies reusable dynamics using supported physics.
Adding a paper, resolution, dimension, probe arrangement or figure target normally
adds data to a paper file. Specialized code belongs beside the study until reuse
justifies extracting it. Avoid adding its controls to every core case.

## Repository organization

```text
cases/<family>/<slug>/             existing general explanations and demonstrations
reproductions/<bibkey>/paper.yaml  paper metadata and exact studies
reproductions/<bibkey>/reference/  small reference data with provenance
reproductions/<bibkey>/specialized/<study>/
                                  paper-specific setup code/data when necessary
src/warpSPHCases/                  shared metrics, references, analysis and adapters
data/validation/backlog/           targets requiring additional physical models
```

Keep existing page URLs and case manifests. General dynamics pages link to the
paper studies they support; a paper file can reference several dynamics builders
and contain several studies. One paper need not imply one new solver factory or
one website page per experiment. Store large recordings through the existing
trajectory/manifests policy.

The two `paper.yaml` files are **definition drafts** consumed by the research
matrix generator. They are not executable runner documents. The first suite is
[Frontiere 2017 CRKSPH](../reproductions/frontiere2017/README.md): 14 dynamics
families and 21 studies with explicit sampling, measurement and setup gaps. Its
acoustic reference and local-data notebook are the first Python analysis component;
no study has yet been run or accepted as a paper reproduction.
The next implementation is a Python resolver that combines a study, its core or
specialized setup and chosen numerical settings into the existing runner contract.
Remote later consumes the same resolved study/analysis settings with a local
recording. Introducing this organization does not require changing the registry.

## What a paper study must specify

Each study has a stable paper/study identifier and revision, section/figure/table
locators, dimensionality, equations/EOS, geometry, ICs, BCs, forcing and units.
Record the paper's discretization separately from an affordable demonstration
resolution. A reduced run remains labelled as a demonstration.

Specify the reference assets and their provenance, the exact measurement operator
(including probes, averaging, filtering, normalization and time alignment), and
the particular observable and time interval to compare. Set acceptance criteria
from reference uncertainty or numerical evidence before scoring a run. Until
criteria and reference extraction are complete, record an unscored comparison.

An initial qualitative comparison is sufficient when a good reference is
unavailable or generating one would require a new solver. Match published times,
views and scales, and label the result qualitative. Useful diagnostics can still
be measured without claiming an independent numerical error or pass threshold.
Reference acquisition is then an optional later improvement, not a release gate.

For stationary planar slip/symmetry walls, the accepted boundary realization is
reflected IC copies with periodic outer bounds: 2**k copies for k reflected axes.
Reflect normal velocity components and retain scalar properties/material IDs.
Plots and integrals select the original physical domain. This does not replace
the prescribed time-dependent or equilibrium boundary states of Kidder/Yee/RT.

Track definition, configuration resolution, reference availability, metric checks,
run completion and numerical agreement independently. Report reference error
separately from Python/Remote agreement: frontend parity does not establish
agreement with a paper. Use one accepted trajectory initially; choose additional
solver comparisons where they answer a useful question.

## First suite and subsequent targets

Build the Frontiere 2017 CRKSPH suite first. The paper spans smooth flow, contact
discontinuities, shocks, vortices, instabilities and combined shock/shear tests,
mostly through families already present in the solver. Its exact studies provide
an initial test of this organization before adding further papers that reuse the
same dynamics.

Begin with acoustic, planar Sod/Sedov/Noh, Gresho and Yee reference measurements.
Then reconcile Kidder, hydrostatic, Woodward, KH, RT and shearing Noh. Defer costly
dimensional variants until a small run and metric are checked. Blob needs a
reusable initializer; the exact triple-point experiment needs a per-material
gamma capability check. The [suite file](../reproductions/frontiere2017/paper.yaml)
and [coverage/implementation order](../reproductions/frontiere2017/README.md)
retain every section-4 dynamics family, even where execution is pending.

Marrone 2011 remains the next free-surface paper. Section 3.1 targets wall-pressure
histories (Fig. 5); section 3.3 targets pressure histories at P1/P3/P6 (Fig. 17).
The existing paper file retains those studies and their provenance gaps.

Marrone section 3.3 describes a three-dimensional rectangular-step experiment.
A 2D simplification must have a different study identity. The existing local
Marrone 3.1 frontend setup is traceable to
`warpSPHPlotting/examples/verify_frontends.py`, and Remote's
`reports/VERIFICATION.md` records loading its NPZ sequence. The user identifies
3.3 as another useful Remote validation; its exact local configuration remains
to be located and reconciled rather than inferred from the 3.1 setup.

The CRKSPH blob example starts a dense cloud at rest in an ambient wind; it does
not require a sustained injection boundary. General blob initialization and
relative flow are reusable controls. Actual time-dependent injection belongs in
the builder only when a selected study needs it. The paper also discusses how
unstandardized interface perturbations limit rigorous late-time comparisons;
matching a cloud-mass curve is therefore a study-specific comparison, not an
assertion of a unique exact nonlinear trajectory.

TGV remains another small analytic check of the workflow. Marrone provides a
subsequent end-to-end free-surface target using existing frontend work; the blob
builder extends the core's range without requiring a new dynamics registry entry
for each paper.

## Scope and the long-term backlog

Prioritize experiments that exercise the fluid physics the solver can run now.
Geometry/IC/reference adapters for those experiments belong in the active work.
Gate uncertain capabilities explicitly before committing to an implementation.

Solid mechanics, landslides, heaving/floating-body benchmarks and new thermal or
multiphase models are long-term targets. SPHERIC remains a useful reference
provider; completing its catalogue is not a release gate or the structure of this
project. Its complete checklist is retained in the research data as background.
