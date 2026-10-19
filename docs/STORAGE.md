# Storage tiers

| Tier | Holds |
|---|---|
| git (this repo) | code, `case.yaml`, prose, stripped notebooks, `reference/`, `data/literature/`, small `golden/`, `artifacts.json` manifests |
| `trajectories/` (gitignored) | curated per-run HDF5, `<family>/<slug>/<runid>/trajectory.h5`; what pages are built from; uploaded to Hugging Face by hand when pages are done |
| `results/`, `build/` (gitignored) | scratch run store (frames, raw videos), generated figures, site staging |
| `local/` (gitignored) | third-party data not redistributed (SPHERIC experiment videos, raw TC10 sensor series, `local/spheric-tc10/`) |
| Hugging Face dataset | full trajectories, heavy goldens, high-res videos (not used yet) |
| YouTube | full-quality videos, id in `case.yaml: media.youtube` |
| website repo | looping MP4 (<= ~2 MB) + poster, PNG figures |

`artifacts.json` per page (generated): for each large artifact its run id, sha256,
bytes, `caseSpec.json`, warpSPH/Core commits, dtype, device, wall time, ms/step and
(after upload) the HF path. Until uploaded, artifacts are `local` and `check` does not fail on them.
