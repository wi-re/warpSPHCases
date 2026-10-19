# warpSPHCases

Documented example and validation cases for [warpSPH](https://github.com/wi-re/warpSPH):
one page per case at <https://fluids.dev/cases> (origin, setup, results, solver
comparison, reference comparison), each with a Colab-ready notebook.

```
cases/<family>/<slug>/   one folder per page (case.yaml, page.md, <slug>.ipynb, reference/, golden/)
reproductions/<bibkey>/  paper.yaml studies; reference/ and specialized/ setup when needed
src/warpSPHCases/        the installable package the notebooks and the site build both use
data/literature/         digitised reference curves shared by several pages
migration/ scripts/      one-off: examples/ -> cases/ migration from warpSPH
legacy/                  old-API material kept for reference, not published
docs/                    architecture, conventions and storage policy
trajectories/ results/ build/ local/   gitignored (see docs/STORAGE.md)
```

Families: `compressible`, `compressible-walls`, `free-surface`, `periodic`,
`wall-bounded`, `boundaries`, `demos`. The plan, decisions and status:
[CASE_PAGES_PLAN.md](CASE_PAGES_PLAN.md).

The [validation support and target audit](docs/VALIDATION_AUDIT.md) lists every
registered case and builder status, maps reviewed literature to case families,
and identifies exact benchmark/reference targets. Machine-readable matrices,
source locators and the search record live in [data/validation/](data/validation/).
The current workflow starts with Python validation and one accepted trajectory
per exact benchmark; Remote consumes a case description and a local data file.
Keep reusable dynamics in the core and exact published setups in paper files;
adding a paper does not require another registered case. See
[core dynamics and paper reproductions](docs/PAPER_REPRODUCTIONS.md). The first suite is
[Frontiere 2017 CRKSPH](reproductions/frontiere2017/README.md), with 14 dynamics
families / 21 study definitions and an acoustic-wave analysis pilot. Marrone
3.1/3.3 follow as free-surface targets. Benchmarks requiring
additional physical models remain in a separate long-term backlog.

Use a case page's notebook in Colab, or locally:

```bash
pip install git+https://github.com/wi-re/warpSPHCases
```
