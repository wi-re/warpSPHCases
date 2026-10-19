# CASE_PAGES_PLAN — every example case as a documented page on fluids.dev/cases

> Index and status: [../warpSPH/PLANS.md](../warpSPH/PLANS.md) (row "CASE_PAGES_PLAN.md"). Opened 2026-10-12 in warpSPH; moved to this repo 2026-10-12.

## Current scope agreed on 2026-10-19

The validation workflow below takes precedence over the older rollout and
all-solver sweep proposals later in this file. Existing layout and artifacts
remain useful; exact benchmark identity and reference quality now drive the work.

1. Separate the physical **case family** (the same general behaviour) from an
   **exact benchmark**, including its dimension, ICs, BCs, equations/material
   parameters, forcing, comparison times and reference version. Numerical
   realization and paper-reproduction settings are recorded alongside it.
2. Prefer references with quantitative value: analytic solutions, measured
   experiments with uncertainty, or independent converged/high-order numerical
   solutions. A visually compared CG dam break is useful demonstration material
   but need not become another reference-data target.
   Where a good reference is unavailable or would require building another
   solver, qualitative published comparisons are sufficient for the initial
   study. Keep their evidence distinct from quantitative error acceptance.
3. Initially provide **one accepted solver trajectory per exact benchmark**.
   Keep other solvers runnable and select useful comparisons, such as KH.
   Exhaustive MFM/MFV sweeps across every compressible case are deferred.
4. Work case by case: literature/setup and reference definition; reusable Python
   metrics and visualizations; a thin stored-data notebook; selected convergence
   and limitations studies; trajectory; Remote adapter; case page.
5. Remote initially receives a portable case description defining visualization
   and validation settings, followed by a user-selected **local data file**.
   Pages can supply or forward that description. HF distributes downloadable
   trajectories/datasets; direct HF-to-Remote linking is aspirational.
6. ML training-data generation is a separate research question and is outside
   this milestone. No training-split or training-pipeline work is required here.
7. Support is evidence-specific: registry presence, configuration metadata,
   frontend exposure, runtime completion and quantitative validation are separate
   claims. Keep internal findings under the existing repository policy.
8. Keep a compact set of **core dynamics builders**. Exact published experiments
   live in `reproductions/<bibkey>/paper.yaml`, with multiple studies per paper.
   Study-specific geometry/IC code lives in that paper's `specialized/` subfolder
   until actual reuse justifies extracting it. Adding a paper or variant normally
   adds a study file entry, not a new registered case.
9. Prioritize validation of the **fluid physics the solver can run now**.
   The Frontiere 2017 CRKSPH suite is the first paper target; Marrone 2011
   sections 3.1 and 3.3 follow as free-surface targets. Solid models, landslides,
   heaving/floating-body benchmarks and new physical models stay in a separate
   long-term backlog. SPHERIC is a source
   of useful references, not a catalogue-completion objective.
10. For stationary planar reflecting boundaries, use the existing reflected-IC
    realization with periodic outer bounds. Reflecting all axes gives 2/4/8
    copies in 1D/2D/3D; mixed periodic/reflecting cases need 2**k copies for k
    reflected axes. Reverse normal velocities, preserve scalar fields/material
    IDs, and measure only the physical domain. A new boundary solver is not a
    prerequisite for these studies.

The [support and target audit](docs/VALIDATION_AUDIT.md) contains the reconciled
inventory, source-linked literature relationships, proposed metrics for all
43 current pages, active paper/adapter targets and a separate long-term backlog.
The [core and paper architecture](docs/PAPER_REPRODUCTIONS.md) defines the split
and the acceptance contract. Frontiere now covers 14 dynamics families in 21
study definitions; Marrone retains two studies. These remain drafts, not
executable runner documents. The acoustic reference and local-data notebook
provide the first Python analysis component; no paper study has been executed
or accepted in this pass.
Structured records and CSV matrices live in `data/validation/`; reproducible
inventory, literature screening and matrix generation scripts live in `scripts/`.

Snapshot: **48 registered cases, 47 case modules, 43 pages**. The builder catalogue
marks **18 ready / 30 unmigrated**; installed Remote discovery advertises all 48.
These are metadata claims, not evidence that every configuration runs correctly.
The audit covers 207 local PDF files (206 unique hashes), with 204 text-screened
and three scans (55 pages) visually screened. It records 147 reviewed family-level
relationships from 39 papers and 25 online searches. The 24 SPHERIC scope checks
are retained as background. Exact setup reconciliation is a per-paper-study task;
unreviewed keyword hits are retained separately. All 56 publicly manifested
trajectory files exist locally and match their recorded checksums; their
scientific acceptance was not reassessed.

Next: build the **Frontiere 2017 CRKSPH suite** case by case, following
[its coverage and implementation order](reproductions/frontiere2017/README.md).
Start by reconciling the acoustic run protocol and checking one float64 run
against the implemented metric, then planar Sod/Sedov/Noh, Gresho and Yee before
broader instability/reference work and expensive dimensional variants. Resolve
each paper setup before generating accepted trajectories or Remote adapters.
Marrone 3.1/3.3 remain subsequent targets. No new solver runs, Remote changes,
uploads or site publication have been performed in this suite-definition pass.

## 0. Goal and what "done" means

Turn every registered case (48 in `warpSPH.runner.case._REGISTRY`, 43 family
pages with explicitly distinguished exact benchmark variants)
into one documented page on the website, `fluids.dev/cases` (today
`fluids.dev/datasets`; source `~/dev/wi-re.github.io`, Jekyll/al-folio on
GitHub Pages). A page is **done** when it has:

1. **Origin** — who introduced the case, what paper(s), what it is a test *of*.
2. **What it does / represents** — physics, governing setup, what a correct result
   looks like and which failure modes it exposes.
3. **Setup** — domain, ICs, BCs, resolution, parameters, the `warpsph-run <case>`
   line and the `CaseSpec` knobs; both particle and analytic boundaries where the
   case has both.
4. **Outputs** — at least one figure set and **at least one video** per case:
   a short looping MP4 + poster embedded on the page (no GIFs: site rule) and a
   high-quality version on YouTube.
5. **Solver comparison** — selected schemes where the comparison adds scientific
   or explanatory value, with reproducible configurations for other supported
   methods. Start with one accepted trajectory per exact benchmark.
6. **Reference comparison** — against exact/analytic values where they exist,
   otherwise against available published data or a converged reference run.
   Qualitative published comparisons are sufficient initially when a good
   reference is unavailable or would need a new solver; numerical error norms
   and convergence claims require an appropriate reference. Derived quantities
   include pressure-sensor traces, probes,
   integral quantities (energy, momentum, KE decay, wave-front position).
7. **Notebook** — a Jupyter notebook that runs the case (small demo sizes) and
   opens in Colab from a badge on the page; it installs the latest revisions from GitHub.
8. **Canonical trajectory and regression data** — an HDF5 recording of the
   accepted run(s), with provenance, used by figures and notebooks. Regression
   goldens remain distinct from independent analytic/experimental references.
9. **Evidence and limitations** — qualify support and reference applicability
   accurately; maintain internal experiment findings under the current
   repository publication policy.

Coverage must span the whole breadth: compressible (incl. walls), weakly
compressible, incompressible, and boundaries both as particles and as analytic
walls.

## 1. Where things stand (survey, 2026-10-12)

- **Cases:** 48 registered, `src/warpSPH/cases/__init__.py:CASE_MODULES`.
  16 compressible, 8 compressible-with-walls, 12 WC (free surface, rigid body,
  periodic), 4 analytic-wall WC (periodicChannel, stokesArray, taylorCouette,
  cylinderWake), 7 incompressible, 1 non-fluid (waveEquation).
- **Notebooks:** most cases already have one under `examples/**` (committed
  stripped, `nbstripout`); some are `.py` only (`compressibleWalls/*`, the
  analytic-wall four, the incompressible `.py`s). `EXAMPLES_SUMMARY.md` in
  `examples/compressible` and `examples/weaklyCompressible` are the existing
  poor man's gallery (PNG + MP4 per case, no text, no references, no comparisons).
  Old-format `examples/*/export` and `examples/sweeps/` are historic.
- **Schemes:** compressible Monaghan / CompSPH / CRKSPH / GSPH / InutsukaGSPH /
  PESPH (in progress) / MFM / MFV; WC deltaSPH (+ δ⁺, PST variants, ACSPH);
  incompressible divergenceFree / dfsphReference / iisph / omniIncompressible.
  Which scheme runs which case is **not** recorded as data anywhere — needs the
  support matrix (§4).
- **References in-repo:** exact/reference code exists case by case (Sod exact
  solution, TC10 data in `examples/sloshingTank/SPHERIC_TestCase10`, Marrone
  configs in `sweeps/dambreak/marrone*.json`, `docs/analytic_boundaries/`,
  `docs/av/`, `docs/support_solver/`), but there is **no shared
  `reference()` hook** on `Case`. `scripts/g1_*`, `scripts/probe_*`,
  `scripts/av_report` are the ad-hoc comparison harnesses to harvest.
- **Runtime plumbing exists:** `warpsph-run`, `CaseSpec` (+ `--config` yaml/json),
  vispy video via `runner/media.py`, per-run `caseSpec.json`.
- **Packaging:** PyPI is behind (`warpSPH 0.6.0`, `warpSPHCore 0.6.0` vs the
  `>=0.6.1` pin, `warpSPHBoundaries 0.1.0` vs 0.1.5), so notebooks install from
  GitHub (decided, §2); no release gate.
- **Repo weight:** `examples/` is 847 MB tracked (368 MB mp4, 222 MB avi, 212 MB
  gif) in a 1.1 GB `.git`; the existing HDF5 export (`io/hdf5.py`, `io/export.py`,
  `storeMode='trajectory'`) is the golden-trajectory format.
- **Colab reference notebook:** now in this repo (`OscillatingDroplet.ipynb`),
  read 2026-10-12. It is the **old API** (`!pip install warpSPH==0.4.5`,
  `sphWarpCore`, a hand-written integrator loop, ~130 lines of setup), which the
  `runner`/`CaseSpec` API replaces, so the new notebooks will be far shorter. What
  it shows and we keep: the plotting process (`warpPlot.visualize` with the vispy
  backend, `UniformColorMap.viridis` / `flare`, diverging `RdBu`, `Mapping.L2Norm`,
  two-panel mosaic velocity | density, live `updateQuantities`) and — importantly —
  that **headless vispy works on Colab** through `pyvirtualdisplay.Display`
  (it ran there with a T4), so the video risk below is smaller than assumed. Its
  analytic overlays (initial / extreme ellipses of the droplet) are the kind of
  reference decoration the style needs.
- **Site:** `_datasets/` holds 30 legacy pages (diffSPH-era validation cases and
  the ML training datasets `dataset_0x`, `periodic_00_dataset_ICLR`), listed by
  `_pages/datasets.md` (title already reads "cases", `permalink: /datasets/`),
  categories `periodic, closed, boundary, freesurface, simulation, compressible,
  dataset`. Site rules (`CLAUDE.md` there, `new-case` / `optimize-media` skills):
  no GIFs, MP4 + poster via `video.liquid`, `category:` must be in
  `display_categories`, no content edits during a running build, a missing
  cache-busted image fails the whole build, `related_publications: true` only
  with a `{% cite %}`. `assets/` is already 148 MB.

## 2. Decisions

**Settled (user, 2026-10-12):**

1. **New repo `warpSPHCases`** holds the generator, the per-case specs, the
   notebooks, the golden trajectories and the results. It also slims warpSPH:
   `examples/` is 847 MB of tracked files there (368 MB mp4, 222 MB avi, 212 MB
   gif; `.git` is 1.1 GB). The current `examples/**` notebooks, `.py` scripts and
   `EXAMPLES_SUMMARY.md` files migrate into it; warpSPH keeps `src/`, tests,
   `warpsph-run` and a few minimal smoke examples. Rewriting warpSPH history to drop
   the old media is a separate, outward-facing step (force-push) — not part of this
   plan unless you ask. Layout and the split of responsibilities: §4.
2. **Site structure:** `/cases/` replaces the case listing; `/datasets/` stays for
   the ML training datasets, with redirects from the old case URLs (user said the
   rename "brings up a good point" — read as: cases and datasets separate).
3. **Notebook path:** reuse and Colab-ready the existing example notebooks, one
   per page, schemes/variants as a parameter cell.
4. **Install in notebooks:** iterative — the setup cell pulls the latest
   revisions from GitHub (`pip install git+https://github.com/wi-re/<repo>@<ref>`
   for warpSPHCore, Integrators, Plotting, warpSPH, Boundaries, Cases). No PyPI
   release gate; pin a ref in the cell once a page is frozen.
5. **warpSPH is public** — Colab "open in Colab" GitHub badges work (warpSPHCases
   must be public too for its badges).
6. **Media tiers.** (a) Short looping embeds on the site (≤ ~2 MB each, ≤ 720 px,
   MP4+poster, per the site's no-GIF rule; "gif" in the sense of an autoplay loop),
   committed to the site repo. (b) High-quality full videos on YouTube, embedded or
   linked from the page; the YouTube id lives in the case spec.
7. **Compute tiers.** Notebook/Colab demo runs are small (low `nx`, short `tLimit`,
   few seconds on a T4). Site/video/reference runs may be as expensive as needed —
   overnight chains, sequential, no ceiling.
8. **Large videos and trajectories may live on Hugging Face** (user, same day):
   a public HF dataset repo is the home for full trajectories, heavy goldens and
   high-res videos; git holds only manifests and small goldens (§4.4).
9. **The plan lives in this repo** (`~/dev/warpSPHCases/CASE_PAGES_PLAN.md`);
   warpSPH's PLANS.md keeps the index row. **Step 1 is the repo layout** (§4), which
   is a proposal to approve before anything is scaffolded.
10. **Layout amendments (user, same day):** grouped by family, not flat (§4.1, §5);
    trajectories live in a gitignored `trajectories/` folder for now and are
    uploaded to HF by hand when things are done; SPHERIC TC10: small data in the
    repo with attribution, the experiment videos link-only/local.

**Still open:**

- ~~Approve layout and family split~~ — **approved 2026-10-12** (user: "sounds good"),
  including no top-level incompressible grouping (a `solvers:` tag and filter instead).
- **Hugging Face account/repo name** for later (placeholder `<hf-user>/warpSPHCases`);
  not needed until you upload.
- Legacy diffSPH pages: replace each with a warpSPH page + redirect, or keep as
  "legacy" until replaced.

## 3. Page template (frozen after the pilot, §6 Phase 1)

Front matter per `new-case` skill (`layout: page`, `title`, `description` one-line
physics summary, `img`, `importance`, `category`, `related_publications` only
with cites) plus case metadata (`family`, `dimension`, `schemes`, `notebook`,
`colab`, `status`). Body sections, always in this order:

1. Hero video (`video.liquid`), one-paragraph summary, Colab badge, "run it" line.
2. **Origin and purpose** — citations via `{% cite %}` (keys into
   `_bibliography/papers.bib`, adding entries via the `paper-lookup` skill, never
   from memory).
3. **Setup** — table (domain, ICs, BCs, N, parameters) + the exact `warpsph-run`
   command and `CaseSpec` snippet; boundary-representation variants.
4. **Results** — particle snapshots at stated times, then derived quantities.
5. **Solver comparison** — scheme × field grid, one shared colour scale, plus a
   compact table (error, wall time, ms/step, status).
6. **Reference comparison** — overlay plots + error numbers + convergence if run.
7. **Known limitations** — public-language notes, linked to the repo issues.
8. **Reproduce** — notebook, CaseSpec json, warpSPH commit/tag, GPU, wall time.

## 4. Repo layout and data model (this is what makes ~43 pages tractable)

### 4.1 Principles

1. **One folder per page, grouped by family:** `cases/<family>/<slug>/`
   (user, 2026-10-12: a flat folder with compressible and free-surface problems
   side by side is too unstructured). Families are physical regimes (§5), not
   solver families, because the solver is the comparison axis inside a page and
   several pages cross solver families (the Taylor–Green vortex runs on weakly
   compressible *and* incompressible schemes). A page lives in exactly one
   family; the slug is unique across families and is the site URL
   (`/cases/<slug>/`) and the Colab path, so it never changes once published; the
   family folder name is the site category.
2. **Prose is hand-written, everything measured is generated.** Origin, meaning,
   setup text and limitation notes are Markdown in the repo; figures, tables,
   error numbers, timings and videos are produced from run data and never pasted.
3. **Notebooks are thin.** All logic (derived quantities, reference loading, plot
   style, golden comparison) lives in an installable package, so a Colab notebook
   is: install → parameters → `run` → plot with the same functions the site build
   uses → compare to reference. This keeps notebooks short, stripped
   (`nbstripout`, as in warpSPH) and identical in method to the page.
4. **Four storage tiers, by size** (§4.4): git, Hugging Face, YouTube, the website repo.
   Git holds everything that is text or small; large data is referenced through a
   committed manifest with checksums, so a page is reproducible and auditable
   without the bytes being in git.
5. **Dependency direction:** `warpSPHCases → warpSPH (+Core/Integrators/Plotting)`,
   never the reverse. The case definitions and their exact solutions
   (`Case.reference()`) stay in warpSPH; the *documentation, experimental
   reference data, goldens and notebooks* live here.
6. **No hosted GPU CI**, same as warpSPH. A GitHub Action may validate YAML
   against the schema and lint notebooks (no GPU needed); runs and golden checks
   happen locally.

### 4.2 Proposed tree

```
warpSPHCases/
  CLAUDE.md                  working rules (inherits warpSPH's run rules: video on, progress, sequential, perf)
  CASE_PAGES_PLAN.md         this plan (index row stays in warpSPH/PLANS.md)
  README.md  LICENSE  pyproject.toml  .gitattributes (nbstripout)
  src/warpSPHCases/          the installable package (Colab: pip install git+https://github.com/wi-re/warpSPHCases)
    spec.py                  case.yaml loader + JSON-schema validation
    runs.py                  runs-matrix executor: spec -> warpSPH CaseSpec -> run store (tiers: demo | reference)
    store.py                 trajectory I/O, run-store layout, golden promote/compare, HF fetch/upload via manifest
    derived.py               named, tested derived quantities (pressure sensors, profiles, norms, convergence, budgets, front position, ...)
    reference.py             exact solutions registry (calls warpSPH Case.reference) + loaders for data/literature
    style.py                 the one plotting style (harvested from the Colab notebook) + figure recipes (snapshot grid, scheme x field, overlay, convergence)
    support.py               case x scheme support matrix generator
    site/                    build + publish to the website repo (optional extra "[site]": needs ffmpeg, not on Colab)
    cli.py                   `warpsph-cases` : support | run | build | golden | fetch | publish | check
  cases/<family>/<slug>/     ~43 pages, 7 families: compressible, compressible-walls, free-surface, periodic, wall-bounded, boundaries, demos
    case.yaml                metadata, citations, runs matrix, figure/probe/quantity list, reference spec, media ids (YouTube), site fields
    page.md                  hand-written prose with generator directives (figure/table/run-table slots)
    <slug>.ipynb             the Colab notebook (stripped)
    reference/               small experimental/digitised data (csv/npz) + provenance.yaml per file
    artifacts.json           GENERATED, committed: manifest of every large artifact (path in HF, sha256, bytes, caseSpec, warpSPH/Core commits, dtype, device, wall time, ms/step)
    golden/                  small goldens in git (<= ~5 MB total per page): probe series, profiles, final-state fields downsampled
  data/literature/           digitised curves shared by several pages (Ghia, Marrone, Lobovsky, ...) with provenance + bib key
  schemas/case.schema.json   the case.yaml schema
  docs/                      CONVENTIONS.md (how to add a page, style guide, golden policy), PAGE_TEMPLATE.md, STORAGE.md
  tests/                     package tests (CPU, no GPU) + marked `gpu` golden regression
  legacy/                    OscillatingDroplet_0.4.5.ipynb (the old-API Colab notebook, kept for reference, not published)
  trajectories/              GITIGNORED (user, 2026-10-12): the curated per-run HDF5 the pages are built from, <family>/<slug>/<runid>/trajectory.h5;
                             uploaded to Hugging Face by hand when a page is done, then recorded in artifacts.json
  results/  build/           GITIGNORED: scratch run store (frames, raw videos, non-promoted runs); generated figures + site staging
```

Runs matrix entry (sketch): `scheme`, `variant` (wall representation, shape,
dimension…), `nx`, `tier`, `spec` (overrides on the case defaults), `golden: true|false`.
Run id = `<scheme>__<variant>__nx<N>`; a page's figures name runs by id only.

### 4.3 Generated vs hand-written, and the build flow

```
case.yaml ──runs.py──▶ results/<family>/<slug>/<runid>/{caseSpec.json, trajectory.h5, frames/, video.mp4, timing.json}
                                   │ store.py promote ─▶ trajectories/<family>/<slug>/<runid>/ (gitignored)  [+ golden/ small, git]
                                   │ later, by hand: HF upload ─▶ HF dataset + artifacts.json (sha256, HF path)
trajectory.h5 + reference ──derived.py / style.py──▶ build/<slug>/{*.png, tables.json, loop.mp4, poster.jpg, master.mp4}
page.md + tables.json ──site──▶ build/site/_cases/<slug>.md  ──publish──▶ ~/dev/wi-re.github.io (_cases/, assets/img/cases/<slug>/)
master.mp4 ─▶ YouTube (id written back into case.yaml)
```

Figures and derived quantities are computed **from the trajectories**, never
from the live run, so they re-render without re-simulating and a new scheme can be
added to a page without touching the others. `publish` never runs while the site's
build is running; it checks `ffmpeg`, image caps (loop ≤ ~2 MB, §2.6) and that
every referenced file exists (a missing cache-busted image fails the whole Jekyll build).

### 4.4 Storage tiers

| Tier | Holds | Why |
|---|---|---|
| **warpSPHCases (git)** | code, `case.yaml`, prose, stripped notebooks, `reference/` and `data/literature/` (small), `golden/` (small), `artifacts.json` manifests (checksums; HF path filled in when you upload) | text + small; diffable; reviewable |
| **Hugging Face dataset repo** (`<hf-user>/warpSPHCases`, public) | full HDF5 trajectories, heavy goldens, high-res/raw videos, anything > ~5 MB | big files without LFS quota worries; Colab notebooks can fetch a golden by URL without cloning (`hf_hub_download`); mirrors `<family>/<slug>/<runid>/`; **not used yet** — until a page is finished its trajectories sit in the gitignored `trajectories/` folder and you upload them in one go |
| **YouTube** | full-quality videos | embed/link from the page; id in `case.yaml` |
| **Website repo** (`assets/img/cases/<slug>/`) | looping MP4 + poster, PNG figures | what the page displays; per the site's no-GIF/size rules |
| **local `trajectories/` + `results/`** (gitignored) | `trajectories/`: curated runs the pages use; `results/`: everything else, incl. frames and non-promoted runs | working store; 406 GB of `results/` exists in warpSPH today, this is the same pattern |

Rule: nothing large is in git; every large artifact a page depends on is listed in
`artifacts.json` with a checksum, and `warpsph-cases fetch <slug>` restores it
(local first, then HF once uploaded). Before the upload, a page's artifacts are
local-only and `check` reports them as `local` instead of failing.

### 4.5 Golden HDF5 trajectories (user, 2026-10-12)

Each page has, locally at least, one **HDF5 trajectory per (scheme, resolution) run
the page uses**, written by warpSPH's existing `storeMode='trajectory'` (single
growing `trajectory.h5`, `exportInterval` in simulated time; the `io/` format, not a
new one). They serve:

1. the data behind every figure/derived quantity (4.3);
2. a **golden-output set**: `warpsph-cases golden compare` re-runs the demo tier and
   compares per field against the stored golden with explicit tolerances, so a
   solver change that moves a documented result is caught;
3. a download for readers (HF link on the page).

Phase-1 requirements: the file must carry `caseSpec.json`, warpSPH/Core commits,
dtype and device; a downsample policy (full fields at a few times, probes at every
step) keeps light goldens small; goldens are compared **with tolerances** (bit-exact
only on the same GPU/driver, so it is a separate strict mode). A golden is
regenerated deliberately (a logged decision), never silently.

### 4.6 What the package gets from the existing code

- `Case.reference()` hook (new, small, in warpSPH): Sod exact Riemann,
  Noh/Sedov/Kidder self-similar, Gresho, TGV/Couette/Poiseuille/Taylor–Couette/
  shear-wave analytics, hydrostatic p(z).
- Harvest `scripts/g1_*`, `scripts/probe_*`, `scripts/av_report`, the `docs/av/`,
  `docs/support_solver/` and `docs/analytic_boundaries/` evidence for derived
  quantities and reference comparisons.
- Plot style, colour maps and the vispy/headless recipe from `legacy/OscillatingDroplet_0.4.5.ipynb`
  (see §1: warpPlot `visualize` with `UniformColorMap.viridis/flare`, diverging
  RdBu, `Mapping.L2Norm`, `backend='vispy'`, `pyvirtualdisplay.Display` for Colab).

### 4.7 Migration of `examples/` from warpSPH

`examples/` (847 MB tracked) moves into `cases/<family>/<slug>/` by mapping (one table,
generated in Phase 0 from the registry + `EXAMPLES_SUMMARY.md`): notebook → 
`<slug>.ipynb`, the `.py` twin → absorbed into the runs matrix, sweep configs that
serve a page → its `case.yaml`, previews/mp4/avi/gif → **not** migrated (regenerated).
The SPHERIC TC10 experimental data (user: handle as proposed): the small
txt/figures go to `cases/free-surface/sloshing-tank/reference/` with attribution;
the 222 MB of experiment `.avi` are SPHERIC's and stay out of git and public hosting
(link to SPHERIC, keep locally in a gitignored folder). warpSPH then deletes
`examples/` except a few smoke examples (a deliberate change there, with its own
commit and a README pointer); rewriting its git history to shed the old media
is separate and not part of this plan unless asked.

## 5. Families and page inventory

Pages are grouped by **physical regime**, not by solver family: the solver is the
comparison axis *inside* a page (compressible schemes, deltaSPH, DFSPH-style
incompressible, particle vs analytic walls), so a page like Taylor–Green vortex
holds all the solvers that can run it. Each page lives in exactly one family
folder `cases/<family>/<slug>/`; its `case.yaml` lists the registered cases it
covers and carries `solvers:` tags (`compressible`, `weakly-compressible`,
`incompressible`; `walls: particle|analytic|both`) so the listing can still filter
"show me everything incompressible". Slugs are unique across families (they are the
URL, `/cases/<slug>/`); the family is the site `category:`.

Variants merge into one page. "Ref" = what the reference comparison is.

| Family folder (site category) | Pages (slug) | Registered cases |
|---|---|---|
| `compressible/` (14) | sod, linear-wave, kidder, noh, shearing-noh, woodward-colella, sedov, hydrostatic, gresho, yee, shear-box, kelvin-helmholtz, rayleigh-taylor, triple-point | sod/sod2d/sod3d, linearWave, kidder, noh, shearingNoh, woodwardColella, sedov, hydrostatic, gresho, yee, shearBox, kelvinHelmholtz, rayleighTaylor, triplePoint |
| `compressible-walls/` (8) | closed-box, piston, shock-reflection, woodward-colella-walls, sedov-walls, shock-cylinder, bow-shock, forward-step | the same-named cases |
| `free-surface/` (6) | dam-break, sloshing-tank, oscillating-droplet, rotating-square-patch, impact, column-collapse | dambreak, sloshingTank, droplet, squarePatch (WC + incompressible), impact, columnCollapse |
| `periodic/` (5) | taylor-green-vortex, kolmogorov-flow, random-flow, shear-wave, static-blob | tgv-wc + tgv, kolmogorov + kolmogorovIncompressible, randomFlow + randomFlowIncompressible, shearWave, staticBlob |
| `wall-bounded/` (4) | lid-driven-cavity, moving-obstacle, driven-square, open-flow | ldc, movingObstacle, drivenSquare, openFlow |
| `boundaries/` (5+) | periodic-channel, stokes-array, taylor-couette, cylinder-wake, hydrostatic-column (+ a wall-representation page: particle vs analytic on dam break) | periodicChannel, stokesArray, taylorCouette, cylinderWake, hydrostaticColumn |
| `demos/` (1) | wave-equation | waveEquation (non-fluid, exact solution) |

About 43 pages for 48 registered cases (variants and the same physics under
different solver families share a page).

**References per page** (what "compared against reference values" means)

- `compressible/`: Sod exact Riemann; linear wave exact phase/damping; Kidder,
  Noh, Sedov self-similar exact; hydrostatic exact p(r); Gresho exact steady v_φ
  and KE drift; Yee exact advection; shear box steady shear; KH mode growth;
  RT growth rate; Woodward–Colella and triple point against a converged
  high-resolution reference (own run or a mesh code, digitised with provenance).
- `compressible-walls/`: closedBox rest state; piston and shockReflection exact;
  WC-walls and Sedov-walls against their mirror twins; bow-shock standoff
  distance; forward step against Woodward–Colella 1984.
- `free-surface/`: dam break — Lobovsky, Marrone 2011 front/pressure,
  Martin–Moyce; sloshing — SPHERIC TC10 pressure sensors and wave elevation;
  droplet — analytic period; rotating patch — Colagrossi ω decay, p_min;
  impact — Marrone/Antuono impact pressure; column collapse — front position.
- `periodic/`: TGV exact decay; Kolmogorov laminar profile/decay; random flow
  energy decay and spectrum; shear wave exact decay; static blob null test.
- `wall-bounded/`: LDC — Ghia et al. 1982 centreline profiles; obstacle pages —
  force/torque, Strouhal/drag.
- `boundaries/`: Poiseuille exact, Sangani–Acrivos drag, Taylor–Couette exact,
  wake Strouhal/drag, hydrostatic p(z). The point of these pages is *particle vs
  analytic walls on the same case*.

**New site categories** the listing page must add to `display_categories` (or the
pages render nowhere): `compressible-walls`, `free-surface`, `wall-bounded`,
`boundaries`, `demos` (existing `compressible`, `periodic` are reused; the legacy
`closed`/`freesurface`/`simulation`/`boundary` and the ML `dataset` stay for the
old pages until they are replaced).

## 6. Phases

**Phase 0 — Layout, repo skeleton, inventory (0.5–1 wk). Status 2026-10-12:
(a) done, (b) done, (c) done as a copy (warpSPH's `examples/` is untouched),
(d) and (e) open.**
(a) **Settle the layout (§4) with you — the first step.** (b) Scaffold the tree
(`CLAUDE.md`, `pyproject.toml`, `schemas/`, `docs/`, `legacy/`, package stubs, the
gitignored `trajectories/` and `results/`), move `OscillatingDroplet.ipynb` to
`legacy/`, set up `nbstripout`.
(c) Generate the examples → slug mapping and move `examples/` in (§4.7).
(d) Harvest the old Colab notebook's plotting into `style.py`. (e) Support-matrix
generator; list which cases have/lack notebooks and references; put the scheme × case
table into the plan.

**Phase 0 (f) — Same layout in the front end (user, 2026-10-12).** warpSPH's
`src/warpSPH/cases/` is itself 52 flat modules — the example of why flat does not
work. Regroup it into the same families as subpackages (`compressible`,
`compressibleWalls`, `freeSurface`, `periodic`, `wallBounded`, `boundaries`,
`demos`; camelCase because they are Python packages and match the repo's module
style; the cases repo uses the hyphenated spelling for the same families), with the
shared helpers (`weaklyCompressible`, `plotting`, and the compressible / walls
settings) in `common`. Constraints: registry names (`warpsph-run sod`,
`caseSpec.json`) do not change; old import paths keep working through an alias
finder (≈ 280 files import `warpSPH.cases.<module>`, plus pickled/dill exports and
external notebooks), the in-repo imports are rewritten to the new paths; `python -m`
paths and `CASE_MODULES` change. Gate: registry identical before/after, full test
suite and `check_imports.py` pass. Done = see the log.

**Phase 1 — Pilot, three pages (1 wk). Status 2026-10-12: generator, Sod and Taylor–Green built (see the log);
the third page (dam break or sloshing) waits on the reference-data decision.** One per hardest axis so the template
survives contact: **Sod** (compressible, exact reference, 1D-3D, many schemes),
**dambreak or sloshingTank** (WC free surface, pressure sensors, particle vs
analytic walls, known limitations), **TGV** (WC vs incompressible, exact, convergence).
Build the generator, `Case.reference()`, derived library, run store, golden
trajectory format + a first regression check, publisher, Colab-ready notebook
(GitHub install cell), the site collection + `/cases/` listing + redirect stubs,
and look at it with the site's `-Production` build; settle the HF/git split (§4.4). **Gate G1:** you approve the
look and template; nothing proceeds before.

**Phase 2 — Compressible (2 wk).** 14 + 8 pages. Mostly exact references, so the
quickest to make rigorous. Reuses E2 battery output (`COMPRESSIBLE_SPH_PLAN` Track E)
for MFM/MFV/CRK comparisons rather than re-running.

**Phase 3 — Weakly compressible (2–3 wk).** 11 pages. Needs digitised literature
data (Lobovsky, Ghia, Marrone) — via the `paper-lookup` skill, data recorded with
provenance. Pages about wall-contact cases will show ACSPH failing honestly
(`WALL_CONTACT_PLAN`), not hide it.

**Phase 4 — Boundaries and incompressible (1–2 wk).** Analytic-wall pages (use
`docs/analytic_boundaries/` evidence), incompressible pages, wave equation.

**Phase 5 — Site migration and polish (1 wk).** `/datasets` → `/cases`, redirects,
legacy page disposition, home page link (`_pages/about.md` mentions
`/datasets/`), nav label, listing cards, cite keys, accessibility/Lighthouse,
broken-link workflow. **Gate G2:** you approve going live.

Estimate: 8–10 weeks wall-clock if worked at the pace of the other plans; the
compute is overnight chains, the writing and reference work is the long pole.
Pages can go live incrementally after G1 (collection is additive).

## 7. Risks and how they are handled

- **A scheme does not work on a case.** (User decision 2026-10-12: tracked internally, **not** shown publicly.) Its
  runs go in the page's gitignored `case.internal.yaml`, the finding in the gitignored `local/INTERNAL_FINDINGS.md`;
  the build refuses a public run that diverges or fails its reference. Not mentioned in the public repos or on the site.
- **Headless video on Colab.** The old Colab notebook ran vispy under
  `pyvirtualdisplay.Display` (Xvfb), so this is expected to work; verify with the
  new runner in Phase 1 (`apt install xvfb` cell if the image lacks it). Fallback:
  matplotlib plots in the notebook; site videos are produced locally anyway.
- **Colab hardware.** Free T4, 16 GB, no persistent disk: notebooks default to a
  small `nx` and short `tLimit` (the page says what the full run uses); full-res
  stays on the site as stored output.
- **Version drift.** Each page records the warpSPH commit/tag and `CaseSpec` json it
  was generated with; `warpsph-cases check` verifies the stored specs still resolve
  (catches renamed parameters) and flags stale pages.
- **Reference data licensing / digitisation.** Only own digitisations of published
  curves with citation; no copied figures.
- **Site size/build time.** Looping embeds ≤ ~2 MB, full quality on YouTube (§2 item 6); `jekyll-imagemagick` handles png/jpg;
  videos are not re-encoded by the build.
- **Scope creep into solver fixes.** A page exposing a solver defect gets an
  `OPEN_PROBLEMS.md` entry (CLAUDE.md rule 3), not a detour into fixing it here.

## 8. First steps once approved

1. You: approve or amend the layout (§4) and answer the three open items in §2.
2. Phase 0 (b)–(e): scaffold, move `examples/`, support matrix.
3. Start the Phase 1 pilot with Sod.

## Log

- 2026-10-12 — plan opened from the user's request; survey of the 48 cases, the
  existing example notebooks, packaging state on PyPI and the site repo done.
  No code yet.
- 2026-10-12 — user decisions: new repo `warpSPHCases` (also slims warpSPH);
  HDF5 trajectory per page as reference and golden set; `/cases` + `/datasets`
  separate; reuse existing notebooks; notebooks install latest from GitHub; warpSPH
  public; looping embeds on the site, full-quality video on YouTube; demo runs small,
  site/video/reference runs unconstrained. Plan updated (§2, §4); Colab link was
  not readable (sign-in).
- 2026-10-12 — plan moved from warpSPH to `~/dev/warpSPHCases`. Read the Colab
  notebook now in the repo (`OscillatingDroplet.ipynb`, old 0.4.5 API; plotting =
  warpPlot/vispy, headless via pyvirtualdisplay on Colab). User: large videos and
  trajectories can live on Hugging Face; first step is the repo layout. §4 rewritten
  as a layout proposal (`cases/<family>/<slug>/`, `warpSPHCases` package, thin notebooks,
  manifests + four storage tiers, golden policy, `examples/` migration); awaiting
  approval. No scaffolding done.
- 2026-10-12 — user: cases are grouped by family rather than one flat folder;
  trajectories in a gitignored folder until uploaded; SPHERIC handled as proposed.
  §4.1/4.2/4.4/4.7 and §5 rewritten (7 families, ~43 pages, slug table, new site
  categories); HF no longer needed in Phase 0.
- 2026-10-12 — layout approved by the user; Phase 0 (a)-(c) executed, nothing committed:
  scaffold (`CLAUDE.md`, `README.md`, `pyproject.toml`, `.gitattributes` nbstripout,
  `.gitignore` for `trajectories/ results/ build/ local/ *.h5`, `docs/{CONVENTIONS,STORAGE}.md`,
  `schemas/case.schema.json`, package stubs under `src/warpSPHCases/`, `data/literature/`);
  `OscillatingDroplet.ipynb` -> `legacy/OscillatingDroplet_0.4.5.ipynb`;
  `migration/examples_map.yaml` + `scripts/migrate_examples.py` (idempotent, git-ls-files
  driven, so no media/export/outputs): 43 page skeletons `cases/<family>/<slug>/case.yaml`
  (all validate against the schema), 109 source files copied to
  `cases/.../from-examples/` (the pre-migration notebooks/scripts, to be adapted per page
  and removed when the thin `<slug>.ipynb` lands), 4 unmapped notebooks to
  `legacy/unmapped-examples/`. The registry check passes: all 48 registered cases are
  claimed by exactly one page, none unclaimed. 8 pages have no example source at all
  (shear-box, column-collapse, shear-wave, static-blob, periodic-channel, stokes-array,
  taylor-couette, cylinder-wake) and the 8 compressible-walls pages have a `.py` only:
  their notebooks are written new. SPHERIC TC10: figures, repeatability files and the
  description go to `free-surface/sloshing-tank/reference/spheric-tc10/`; the 34 MB raw
  sensor series went to gitignored `local/spheric-tc10/data_files/` (too big for git);
  the experiment `.avi` were not copied. Goldens in git will be `.npz`/`.csv` (`*.h5` is
  gitignored). Not done: nbstripout is not installed in the warp env, so the migrated
  notebooks still carry their old committed outputs (6 MB total) until they are staged
  after `nbstripout --install`.
- 2026-10-12 — Phase 0 (f) executed in warpSPH (`dev`, uncommitted, staged renames):
  `src/warpSPH/cases/` regrouped by `git mv` into `compressible/` (15 case modules +
  `common`), `compressibleWalls/` (8 + `common`), `freeSurface/` (6), `periodic/` (8),
  `wallBounded/` (3), `boundaries/` (6 incl. `channelFlow`), `demos/` (1) and `common/`
  (`plotting`, `weaklyCompressible`). Relative imports rewritten by a script;
  `CASE_MODULES` is now `'<family>.<module>'`; the old flat paths keep working through
  an alias finder in `cases/__init__.py` (`LEGACY_MODULES`, DeprecationWarning, same
  module object), `cases.compressible` / `cases.compressibleWalls` forward the old
  helper names to their `common`. 277 + 15 tracked files rewritten to the new
  `warpSPH.cases.<family>.<module>` paths (scripts, tests, notebooks, benchmarks, docs;
  `docs/historic_plans/` and the two already-modified plan files left alone). Two
  `__file__`-relative paths (`sloshingTank` -> the SPHERIC data, `plotting` -> git hash)
  needed one more `dirname`. Checks: registry (names, scheme, defaults, params,
  descriptions) identical before/after; `scripts/check_imports.py` clean (4407
  first-party imports incl. notebooks); full test run — see below.
  Findings to keep: (1) `dambreak.py` also declares `openFlow` (the wall-bounded page's
  case): split it into `wallBounded/openFlow.py` later; (2) `sloshingTank` *needs*
  `examples/sloshingTank/SPHERIC_TestCase10/data_files/lateral_water_1x.txt` as its
  default input motion, which this repo moved to gitignored `local/`: before warpSPH's
  `examples/` can be deleted the roll-motion input must get a home the case can reach
  (ship a light copy with warpSPH or fetch it) -- not decided yet.
- 2026-10-12 — Phase 1 started (nothing committed). **Package** (`src/warpSPHCases/`): `spec` (case.yaml + schema + runs
  matrix expansion), `runs` (sequential resumable executor following warpSPH's run rules, `runEntry` shared with the
  notebooks, `timing.json` incl. the GPU utilisation at launch), `store` (h5py/numpy trajectory reader, promote,
  `artifacts.json` with sha256), `reference` (Sod exact Riemann via warpSPH's solver, TGV exact decaying field;
  named `metrics`, `flag` for failing runs), `derived`, `style` (dataviz palette, validated; fixed scheme colours),
  `figures` (loop/loop2d hero MP4+poster, snapshots, overlay+zoom, scheme grid, convergence, series, error maps,
  diagnostics, error/order tables), `golden` (promote/compare), `quick` (notebook API), `site/` (page build from
  `page.md` directives, standalone HTML preview, publish into the website working tree). CLI `warpsph-cases`
  (run, manifest, golden, build, check, publish, list). `docs/CONVENTIONS.md` rewritten from what the pages use.
  10 CPU tests on synthetic trajectories pass. `data/references.bib` holds the cited entries (verified sources only).
  **Sod page** (`cases/compressible/sod/`): 36 runs (7 schemes at nx 400 with video, 4 more resolutions video off, 1 demo),
  all clean (no velocity alarms), exact-solution errors, observed orders ~1 for every scheme (expected with a shock),
  goldens (56 kB) re-run and passing, thin notebook `sod.ipynb` executed headless with papermill (Colab itself not
  tried; the golden fetch 404s until the repo is public). **TGV page** (`cases/periodic/taylor-green-vortex/`): five schemes at nx 128 plus a resolution sweep, errors against the
  exact decay. Further schemes that were run and do not track the reference are tracked internally
  (`local/INTERNAL_FINDINGS.md`, gitignored), not on the page. Two warpSPH export
  bugs fixed on the way (`io/export.py`: `None` and device-tensor case params broke `storeMode='trajectory'`).
  Findings: the GPU is shared with other jobs (70-95 % utilisation), so timings are contended; (user, 2026-10-12) the pages show no
  timings, they come from a separate benchmark study later (`timing.json` is still recorded per run); a real Jekyll build is not possible on this machine (no docker, no Ruby
  headers), so pages are checked through `build/preview/` and the site check is still open; jekyll-scholar's `--file`
  option (read in the gem source, not run) is what lets the pages cite from `_bibliography/cases.bib` instead of
  polluting the publications page.
- 2026-10-12 — user decisions: **navbar** gets `cases` (new listing, `nav_order: 3`); `datasets` stays for actual
  datasets (the old listing is relabelled `datasets`, `nav_order: 3.5`, its legacy case pages stay until a warpSPH page
  replaces each; `publish` does both, idempotent, tested on a scratch copy of the site config, float `nav_order` not
  yet seen in a real build); YouTube uploads and Hugging Face come later; the third pilot page is the sloshing tank
  (SPHERIC TC10 lateral water: reference = recorded sensor 1 trace + the repeatability register of the first four
  impacts); nx-convergence stalls are acceptable on the pages (float32 floor), timings come from a separate later
  benchmark study (pages show none); runs that blow up are tracked internally and not shown or mentioned publicly.
- 2026-10-12 — sloshing-tank page (`cases/free-surface/sloshing-tank/`): reference `tc10` (recorded sensor-1 trace reduced to
  1 kHz in `reference/spheric-tc10/lateral_water_1kHz.txt` + repeatability register of the first four impacts, provenance in
  `PROVENANCE.md`), metrics = peak of the sensor probe pressure within 0.15 s of each impact, impulse ratio, timing offset;
  runs at nx 200 (deltaSPH with boundary particles / analytic walls) to 7.5 s done; deltaSPH resolution sweep
  (nx 100/150/300, both wall types) and the Colab-sized demo run in the background chain (`build/logs/slosh_sweep.log`);
  thin notebook written, not yet executed; interim page built with `build --allow-missing`. Finding: the weakly compressible
  peak pressures are several times the measured ones (single phase, numerical sound speed 20 m/s), impulse ~3x; shown on the
  page as a limitation. Third warpSPH export fix: rigid-body ghost datasets reused the body's dataset names, so every run
  with analytic walls failed to open its trajectory (`io/export.py`).
- 2026-10-12 — sloshing page revised (user review): the incompressible comparator is `omniIncompressible` (analytic walls and
  boundary particles at n_h 2.57, analytic walls at n_h 4), the scheme that runs this case well, not `divergenceFree`; and
  simulation and recorded trace are compared smoothed the same way (10 ms Gaussian, NaN-aware, the method of warpSPH's
  2026-10-09 sloshing validation), not raw simulated peaks against the raw repeatability register. The deltaSPH runs of
  the first version were re-scored with the new metric (still several times the smoothed measurement); the omni runs and
  the sweeps have to be run (GPU released to the user at the time).
