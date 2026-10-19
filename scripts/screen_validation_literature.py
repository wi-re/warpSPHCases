#!/usr/bin/env python3
"""Screen every local PDF for benchmark aliases; matches are discovery evidence only.

Requires pdftotext. Extracted text stays in gitignored local/. Candidate CSV rows
do not claim a paper runs a case: references, discussions and ambiguous names are
retained for review. Reviewed relationships live in literature-evidence.csv.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unicodedata


def normalize(text):
    text = unicodedata.normalize('NFKC', text).lower()
    return re.sub(r'\s+', ' ', text.translate(str.maketrans('–—−', '---')))


def write_csv(path, rows, fields):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--literature-root', type=Path, default=root.parent / 'warpSPH/literature')
    parser.add_argument('--output', type=Path, default=root / 'data/validation')
    parser.add_argument('--cache', type=Path, default=root / 'local/validation-audit/text')
    args = parser.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    rules = json.loads((root / 'data/validation/search-aliases.json').read_text())
    visual_reviews = {r['sha256']: r for r in json.loads(
        (root / 'data/validation/visual-reviews.json').read_text())}
    compiled = {k: re.compile(v) for k, v in rules.items()}

    def screen(path):
        result = subprocess.run(['pdftotext', '-layout', str(path), '-'], capture_output=True)
        text = result.stdout.decode('utf-8', errors='replace')
        rel = path.relative_to(args.literature_root).as_posix()
        cache = args.cache / (rel.replace('/', '__') + '.txt')
        cache.write_text(text)
        pages = text.split('\f')
        if pages and not pages[-1].strip():
            pages.pop()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        candidates = []
        references_started = False
        for index, page in enumerate(pages, 1):
            match_page = normalize(page)
            reference_heading = re.search(r'^\s*(?:\d+[. ]+)?(?:references|bibliography)\s*$', page, re.M | re.I)
            for family, pattern in compiled.items():
                hits = sorted(set(m.group(0) for m in pattern.finditer(match_page)))
                if hits:
                    candidates.append(dict(document=rel, family=family, pdf_page=index,
                        matched_aliases=';'.join(hits),
                        bibliography_possible=references_started or bool(reference_heading),
                        relationship='unreviewed-match', exact_setup_match='not-assessed'))
            # Appendices can follow references. This flag is only a review aid.
            references_started = references_started or bool(reference_heading)
        # ADS watermarks can yield hundreds of characters across a scanned paper.
        # A total-character threshold alone incorrectly calls those searchable.
        substantive = sum(len(re.sub(r'\s', '', p)) >= 300 for p in pages)
        enough_text = (len(text) / max(1, len(pages)) >= 500
                       and substantive >= 0.6 * len(pages))
        visual = visual_reviews.get(digest)
        if visual:
            assert visual['document'] == rel and visual['reviewed_pages'] == len(pages)
            for family, page in visual['candidates']:
                assert family in rules and 1 <= page <= len(pages)
                candidates.append(dict(document=rel, family=family, pdf_page=page,
                    matched_aliases='visual discovery; see visual-reviews.json',
                    bibliography_possible=False, relationship='visual-discovery',
                    exact_setup_match='not-assessed'))
        record = dict(document=rel, sha256=digest, bytes=path.stat().st_size,
            extracted_pages=len(pages), text_characters=len(text),
            substantive_text_pages=substantive,
            text_status='extracted' if enough_text else 'visual-review-required',
            search_status='aliases-screened' if enough_text else 'not-text-searchable',
            families_with_matches=';'.join(sorted({r['family'] for r in candidates})),
            extraction_returncode=result.returncode, duplicate_of='')
        return record, candidates

    results = list(ThreadPoolExecutor(max_workers=6).map(screen, sorted(args.literature_root.rglob('*.pdf'))))
    corpus, candidates, hashes = [], [], {}
    for record, hits in results:
        record['duplicate_of'] = hashes.get(record['sha256'], '')
        hashes.setdefault(record['sha256'], record['document'])
        visual = visual_reviews.get(record['sha256'])
        if visual:
            record['search_status'] = f"visually-screened-all-{record['extracted_pages']}-pages-{visual['date']}"
        corpus.append(record)
        candidates.extend(hits)
    write_csv(args.output / 'literature-corpus.csv', corpus, list(corpus[0]))
    write_csv(args.output / 'literature-candidates.csv', candidates,
        ['document', 'family', 'pdf_page', 'matched_aliases', 'bibliography_possible',
         'relationship', 'exact_setup_match'])
    print(f'{len(corpus)} PDFs; {len(hashes)} unique hashes; {len(candidates)} page/family candidates')


if __name__ == '__main__':
    main()
