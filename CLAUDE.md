# warpSPHCases — working rules for Claude

Plan and status: `CASE_PAGES_PLAN.md` (here). The index of all plans is
`~/dev/warpSPH/PLANS.md` — when you work on this plan, update its row there
(*Last worked* = today, one-phrase *Where it stands*), as warpSPH's CLAUDE.md requires.

## Layout (do not reinvent)

`cases/<family>/<slug>/` per page; families are physical regimes, not solver
families (plan §4–§5). Prose is hand-written (`page.md`), everything measured is
generated from trajectories. Notebooks are thin: logic lives in `src/warpSPHCases`.
Slugs are URLs and never change once published.

Paper-specific validation lives in `reproductions/<bibkey>/paper.yaml` (user,
2026-10-19), with multiple studies per paper and a `specialized/` subfolder for
study-specific setup. Keep the solver's core dynamics registry compact; do not
register every paper preset as a factory. See `docs/PAPER_REPRODUCTIONS.md`.
Prioritize current fluid capabilities; additional-physics benchmarks and the
full SPHERIC catalogue remain long-term background rather than release gates.

## Runs

Every run follows warpSPH's CLAUDE.md "Running simulations" rules: video on
(vispy), stream progress, watch for the velocity alarm and stalls, one GPU run at a
time, report wall time and ms/step. Python: `/home/lu26029/miniconda3/envs/warp/bin/python`.

## Storage

Nothing large in git. `trajectories/`, `results/`, `build/`, `local/` are gitignored.
Large artifacts are described by `cases/*/*/artifacts.json` (sha256, HF path once
uploaded). Uploading to Hugging Face, publishing to the website repo and pushing
are the user's call — do not do them unprompted.

## Failures stay internal

A scheme that blows up or does not track its reference on a case is **not** shown or mentioned publicly (pages,
plans, `case.yaml`, commits): its rows go in the page's gitignored `case.internal.yaml`, the finding in gitignored
`local/INTERNAL_FINDINGS.md`. Pages show no timings (a separate benchmark study comes later).

## Notebooks

`nbstripout --install` in every clone before committing a notebook. Notebooks
install the latest warpSPH stack from GitHub (see plan §2); pin a ref only when
a page is frozen.

## Website (`~/dev/wi-re.github.io`)

Follow its CLAUDE.md: no GIFs (MP4 + poster), `category:` must be in the listing's
`display_categories`, never edit content while a site build runs, a missing
cache-busted image fails the whole build, `{% cite %}` only with real bib keys
(use the `paper-lookup` skill; never cite from memory).

## Commits

No co-author / Claude trailers. Commit only when asked.
