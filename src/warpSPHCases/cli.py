"""``warpsph-cases``: run | build | publish | list | check."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog='warpsph-cases', description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('list', help='list pages with status and run counts')

    p = sub.add_parser('run', help='execute the runs matrix of a page (sequential, resumable)')
    p.add_argument('slug')
    p.add_argument('--runs', nargs='*', help='run ids (default: all)')
    p.add_argument('--tier', choices=['demo', 'reference'])
    p.add_argument('--force', action='store_true', help='re-run rows whose trajectory already exists')

    p = sub.add_parser('build', help='render figures, tables, videos and the page into build/')
    p.add_argument('slug')
    p.add_argument('--skip-video', action='store_true', help='reuse existing loop.mp4 / poster')
    p.add_argument('--allow-missing', action='store_true', help='interim build: leave out runs that have no trajectory yet')

    p = sub.add_parser('publish', help='copy the built page into the website repo working tree (no commit, no push)')
    p.add_argument('slug')
    p.add_argument('--site', required=True, help='path to the website checkout')

    p = sub.add_parser('golden', help='promote final states of golden runs into git, or compare a fresh re-run with them')
    p.add_argument('action', choices=['promote', 'compare'])
    p.add_argument('slug')
    p.add_argument('--force', action='store_true', help='promote: overwrite an existing golden (a deliberate decision)')
    p.add_argument('--strict', action='store_true', help='compare: bit-identical (same machine and driver only)')
    p.add_argument('--tol', type=float, default=1e-3, help='compare: relative L2 tolerance per field')
    p.add_argument('--no-rerun', action='store_true', help='compare the stored runs, do not re-simulate')

    p = sub.add_parser('manifest', help='write cases/<family>/<slug>/artifacts.json from the promoted trajectories')
    p.add_argument('slug')

    p = sub.add_parser('check', help='validate case.yaml, citations, referenced runs and artifacts')
    p.add_argument('slug', nargs='?')

    args = parser.parse_args(argv)

    from .spec import allPages, loadPage

    if args.command == 'list':
        for page in allPages():
            runs = page.runs
            have = sum((page.trajectoryDir(r.id) / 'trajectory.h5').exists() or
                       (page.resultsDir(r.id) / 'trajectory.h5').exists() for r in runs)
            print(f'{page.family:20s} {page.slug:28s} {page.meta["status"]:9s} runs {have}/{len(runs)}')
        return 0

    page = loadPage(args.slug)
    if args.command == 'run':
        from .runs import execute
        execute(page, ids=args.runs, tier=args.tier, force=args.force)
    elif args.command == 'golden':
        from .golden import compareGolden, promoteGolden
        if args.action == 'promote':
            promoteGolden(page, force=args.force)
        else:
            return 0 if compareGolden(page, tol=args.tol, strict=args.strict, rerun=not args.no_rerun) else 1
    elif args.command == 'manifest':
        from .store import writeManifest
        print(writeManifest(page))
    elif args.command == 'build':
        from .site.build import buildPage
        buildPage(page, skipVideo=args.skip_video, allowMissing=args.allow_missing)
    elif args.command == 'publish':
        from .site.publish import publishPage
        publishPage(page, args.site)
    elif args.command == 'check':
        from .site.build import checkPage
        return 0 if checkPage(page) else 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
