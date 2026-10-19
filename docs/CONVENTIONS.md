# Conventions

Draft, finalised at gate G1 of the plan (after the three pilot pages). Everything below is what the
Sod and Taylor–Green pages use today.

## A page

`cases/<family>/<slug>/` holds `case.yaml` (data), `page.md` (prose), `<slug>.ipynb` (Colab notebook),
`golden/` (small final states, in git), `reference/` (small experimental data with provenance),
`artifacts.json` (generated manifest of the large files). Slug: kebab-case, unique across families, it is
the URL and never changes after publication. `from-examples/` is the pre-migration source material and is
removed from a page once everything useful in it has been absorbed.

Status: `stub` -> `drafted` -> `generated` -> `reviewed` -> `published`.

## case.yaml

Fields: `schemas/case.schema.json`. The ones that drive the build:

- `cases`, `solvers`, `walls`, `schemes` (the order is the colour/legend order), `unavailable` (schemes that
  cannot run the case, with the reason, shown as such).
- `reference: {kind}`: which exact solution (`sod`, `tgv`; `src/warpSPHCases/reference.py`). It is built from the
  run's own stored parameters, never re-typed.
- `runs`: the runs matrix. A row is `scheme` or `schemes` (list), `nx` (int or list), `case` (registered warpSPH
  case, default the first of `cases`), `variant`, `tier` (`demo` Colab-sized | `reference`), `spec` (CaseSpec
  overrides), `params` (case parameter overrides), `video` (default true), `golden`. Run id
  `<scheme>__<variant>__nx<N>`. Convergence sweeps set `video: false` and say so; every other run has the vispy
  video on (warpSPH's run rules).
- `figures`, `tables`: what the page shows (below). `select: {nx, variant, tier, scheme}` picks public runs.
- `origin.references`: bib keys (see Citations), `notebook`, `site: {importance, img}`.

## Figure and table kinds

| kind | for | what |
|---|---|---|
| `loop` / `loop2d` | hero | looping MP4 + poster (profiles / particle field + energy history), <= 2 MB, 720 px |
| `snapshots`, `overlay`, `scheme_grid` | profile references (Sod) | one run through time; all schemes overlaid with a zoom; scheme x field grid with error norms |
| `series`, `field_grid` | TGV-type references | kinetic energy against the exact decay; per-scheme error maps on one colour scale |
| `convergence` | any | error metric against resolution, observed order in the legend |
| `diagnostics` | any | a per-step diagnostic over time (`quantity`, `relative`, `yscale`) |
| table `errors` / `orders` | any | the reference's metrics per run / observed orders per scheme |

A reference exposes named scalar `metrics(traj)` (the table columns; the first is the primary one).

## page.md

Hand-written Markdown, sections in this order: hero + summary, Origin and purpose, Setup, Results, Solver
comparison, Reference comparison, Known limitations, Reproduce, References. Generated content goes in through
directives on a line of their own: `<<hero>>`, `<<colab>>` (badge once `notebook` is set), `<<figure:ID>>`,
`<<table:ID>>`, `<<command:RUNID>>`, `<<reproduce>>`, `<<refs>>`.

Prose carries no measured numbers: they come from the trajectories (figures, tables), so they cannot go stale.
Descriptions of a scheme come from its source docstring, not from memory.

## Citations

`{% cite key --file cases %}` and `{% bibliography --file cases --cited_in_order %}` (the `<<refs>>` directive):
the keys live in `data/references.bib`, which is rendered from `_bibliography/cases.bib` on the site so the
references do not appear on the publications page. Entries are copied from warpSPH's verified
`literature/references.bib` or fetched by DOI (warpSPH's `paper-lookup` skill), never typed from memory. The build
stops on a key that is not in the file.

## Commands

```
warpsph-cases run <slug> [--runs ID...] [--tier demo|reference] [--force]   # sequential, resumable, GPU
warpsph-cases manifest <slug>        # artifacts.json (sha256, wall time, commits, caseSpec)
warpsph-cases golden promote|compare <slug> [--strict] [--tol 1e-3]
warpsph-cases build <slug> [--skip-video]      # figures, tables, build/site/_cases/<slug>.md, build/preview/<slug>/
warpsph-cases check [<slug>]
warpsph-cases publish <slug> --site ~/dev/wi-re.github.io   # copies into the working tree; never commits or pushes
```

`build/preview/<slug>/index.html` renders the page without Jekyll (not the site's styling); the final look is
checked with the site's `-Production` build.

## Goldens

`golden/<runid>.npz` holds the last frame of a run marked `golden: true` (positions, velocities, densities,
internal energies, final time, step count). `golden compare` re-runs those rows and checks each field with a
relative L2 tolerance (default 1e-3); `--strict` demands bit equality, meaningful only on the same GPU and driver.
A golden is regenerated deliberately (`promote --force`), never silently.

## Timing

Pages show no timings (ms/step needs an idle GPU; they come from a separate benchmark study). `timing.json` is still
recorded per run, with the GPU utilisation at launch.

## Runs that fail

A scheme that blows up or does not track its reference is not shown publicly (user, 2026-10-12). Its rows go in the
page's `case.internal.yaml` (gitignored; same row format): they are run and kept, but excluded from figures, tables,
goldens and the public `artifacts.json`. The finding goes in `local/INTERNAL_FINDINGS.md` (gitignored). `build`
refuses a public run that diverged or fails `Reference.flag`, so a failing run cannot reach a page by accident. Keep
failures out of committed prose too: plans, page text, `case.yaml`, commit messages.
