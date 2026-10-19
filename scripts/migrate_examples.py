#!/usr/bin/env python
"""Copy warpSPH/examples/ source material into cases/<family>/<slug>/from-examples/.

Reads migration/examples_map.yaml. Copies tracked source files only (the glob is
applied to `git ls-files` of the warpSPH repo, so outputs/export/media are never
picked up), writes a skeleton case.yaml per page, and checks that every
registered warpSPH case is claimed by exactly one page. Does NOT touch warpSPH.

    python scripts/migrate_examples.py [--warpsph ~/dev/warpSPH] [--dry-run]
"""
import argparse
import fnmatch
import os
import shutil
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPHERIC_SRC = 'sloshingTank/SPHERIC_TestCase10'
#: small SPHERIC TC10 material copied into the page's reference/ (user, 2026-10-12);
#: the experiment videos (Video_Files/*.avi) are deliberately not listed.
SPHERIC_COPY = ['Repeatability_Files', 'data_files', '*.png', '*.pdf', '*.doc']


def trackedExamples(warpsph):
    out = subprocess.run(['git', '-C', warpsph, 'ls-files', 'examples'], capture_output=True, text=True, check=True).stdout
    return [l[len('examples/'):] for l in out.splitlines()]


def match(files, pattern):
    return [f for f in files if fnmatch.fnmatchcase(f, pattern)]


def copy(src, dst, dry):
    if dry:
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--warpsph', default=os.path.expanduser('~/dev/warpSPH'))
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    mapping = yaml.safe_load(open(os.path.join(ROOT, 'migration', 'examples_map.yaml')))
    files = trackedExamples(args.warpsph)
    exdir = os.path.join(args.warpsph, 'examples')
    claimed, used = {}, set()

    for family, pages in mapping.items():
        if family == 'unmapped':
            continue
        for slug, page in pages.items():
            pageDir = os.path.join(ROOT, 'cases', family, slug)
            copied = []
            for pattern in page['sources']:
                hits = match(files, pattern)
                if not hits:
                    print(f'WARNING {family}/{slug}: no tracked file matches {pattern}')
                for f in hits:
                    copy(os.path.join(exdir, f), os.path.join(pageDir, 'from-examples', os.path.basename(f)), args.dry_run)
                    copied.append(f)
                    used.add(f)
            if slug == 'sloshing-tank':
                for f in files:
                    if f.startswith(SPHERIC_SRC + '/') and '/Video_Files/' not in f and not f.endswith('.avi'):
                        rel = os.path.relpath(f, SPHERIC_SRC)
                        # the raw sensor series are 34 MB of text: gitignored local/, not reference/
                        dst = (os.path.join(ROOT, 'local', 'spheric-tc10', rel) if rel.startswith('data_files/')
                               else os.path.join(pageDir, 'reference', 'spheric-tc10', rel))
                        copy(os.path.join(exdir, f), dst, args.dry_run)
                        used.add(f)
            for c in page['cases']:
                claimed.setdefault(c, []).append(f'{family}/{slug}')
            skeleton = {
                'slug': slug, 'family': family, 'title': page['title'], 'status': 'stub',
                'description': '', 'cases': page['cases'], 'solvers': page['solvers'],
                'walls': None, 'origin': {'references': []}, 'runs': [],
                'media': {'youtube': None}, 'notebook': None,
                'migrated_from': copied,
            }
            path = os.path.join(pageDir, 'case.yaml')
            if not args.dry_run and not os.path.exists(path):
                os.makedirs(pageDir, exist_ok=True)
                with open(path, 'w') as fh:
                    fh.write('# Skeleton written by scripts/migrate_examples.py -- fill in (see docs/CONVENTIONS.md)\n')
                    yaml.safe_dump(skeleton, fh, sort_keys=False, allow_unicode=True)

    for f in mapping['unmapped']:
        copy(os.path.join(exdir, f), os.path.join(ROOT, 'legacy', 'unmapped-examples', os.path.basename(f)), args.dry_run)
        used.add(f)

    dup = {c: p for c, p in claimed.items() if len(p) > 1}
    if dup:
        print('ERROR cases claimed by several pages:', dup)
        sys.exit(1)
    try:
        sys.path.insert(0, os.path.join(args.warpsph, 'src'))
        from warpSPH.cases import importAll
        from warpSPH.runner import case as c
        importAll()
        registry = set(c._REGISTRY)
        print(f'registry: {len(registry)} cases; claimed: {len(claimed)}')
        print('unclaimed registered cases:', sorted(registry - set(claimed)) or 'none')
        print('claimed but not registered:', sorted(set(claimed) - registry) or 'none')
    except Exception as e:  # registry check needs the warp env
        print('registry check skipped:', e)
    skipped = [f for f in files if f not in used and f.endswith(('.ipynb', '.py', '.yaml'))]
    print('tracked source files not migrated:', len(skipped))
    for f in skipped:
        print('   ', f)
    print(f'{len(used)} files migrated' + (' (dry run)' if args.dry_run else ''))


if __name__ == '__main__':
    main()
