#!/usr/bin/env python3
"""Build the research matrices from the inventory and reviewed source records.

Requires PyYAML. Does not run simulations, download reference data or publish.
Every local reviewed relationship is checked against the corpus checksum index
and the referenced physical PDF page. Discovery matches remain separate.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/validation'


def read_csv(name):
    with (DATA / name).open() as stream:
        return list(csv.DictReader(stream))


def write_csv(name, rows, fields=None):
    with (DATA / name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def table(headers, rows):
    def cell(v):
        return str(v).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join('---' for _ in headers) + ' |',
                      *['| ' + ' | '.join(cell(v) for v in row) + ' |' for row in rows]])


def main():
    inventory = json.loads((DATA / 'inventory.json').read_text())
    corpus = read_csv('literature-corpus.csv')
    candidates = read_csv('literature-candidates.csv')
    reviewed = yaml.safe_load((DATA / 'reviewed-literature.yaml').read_text())
    external = yaml.safe_load((DATA / 'external-references.yaml').read_text())
    goals = yaml.safe_load((DATA / 'case-targets.yaml').read_text())
    extra = yaml.safe_load((DATA / 'additional-targets.yaml').read_text())
    backlog = yaml.safe_load((DATA / 'backlog/long-term-targets.yaml').read_text())
    spheric = yaml.safe_load((DATA / 'spheric-coverage.yaml').read_text())
    aliases = json.loads((DATA / 'search-aliases.json').read_text())
    pages = {r['page']['page'] for r in inventory['cases']}
    assert pages == {r['family'] for r in goals}, 'Case targets must cover every page exactly once'
    assert len(goals) == len(pages), 'Duplicate case target'
    assert len({r['id'] for r in extra}) == len(extra), 'Duplicate additional target'
    evidence = []
    bib_path = ROOT.parent / 'warpSPH/literature/references.bib'
    bibliography = bib_path.read_text()
    source_metadata = {}
    for match in re.finditer(r'@\w+\{([^,]+),', bibliography):
        end = bibliography.find('\n@', match.end())
        body = bibliography[match.end():end if end >= 0 else len(bibliography)]
        doi = re.search(r'\bdoi\s*=\s*[{\"]([^}\"]+)', body, re.I)
        source_metadata[match.group(1)] = 'https://doi.org/' + doi.group(1) if doi else ''
    known_sources = set(source_metadata) | {r['paper'] for r in reviewed} | {r['id'] for r in external}
    assert all(r['reference'] in known_sources for r in extra), 'Unresolved target reference'
    assert all(r['reference'] in known_sources for r in backlog), 'Unresolved backlog reference'
    study_rows = []
    corpus_by_document = {r['document']: r for r in corpus}
    for path in sorted((ROOT / 'reproductions').glob('*/paper.yaml')):
        paper = yaml.safe_load(path.read_text())
        assert paper['format'] == 'research-draft-v1'
        assert paper['paper'] in known_sources
        assert paper['source']['sha256'] == corpus_by_document[paper['source']['document']]['sha256']
        assert len({s['id'] for s in paper['studies']}) == len(paper['studies'])
        if paper['paper'] == 'frontiere2017':
            assert len({s['core_family'] for s in paper['studies']}) == paper['scope']['families']
            study_ids = {s['id'] for s in paper['studies']}
            policy = paper['execution_policy']
            assert policy['status'] == 'not-executable-yet'
            assert set(policy['first_wave']).isdisjoint(policy['second_wave'])
            assert set(policy['first_wave'] + policy['second_wave']) <= study_ids
            for study in paper['studies']:
                assert study['setup_gaps'] and study['measurement'] and study['reference']['kind']
                assert study['comparison_mode'] in ('qualitative-initial', 'quantitative-analytic-target')
                if study.get('boundary_realization'):
                    realization = study['boundary_realization']
                    assert realization['method'] == 'reflected-initial-conditions-periodic'
                    assert len(set(realization['reflected_axes'])) == len(realization['reflected_axes'])
                    assert set(realization['reflected_axes']) <= set('xyz'[:study['dimension']])
                    assert realization['domain_copies'] == 2 ** len(realization['reflected_axes'])
                if study.get('setup_group'):
                    assert study['setup_group'] in paper['study_groups']
        for study in paper['studies']:
            assert study['registry_case'] is None or study['registry_case'] in {r['name'] for r in inventory['cases']}
            assert all(1 <= p <= int(corpus_by_document[paper['source']['document']]['extracted_pages']) for p in study['source_pdf_pages'])
            assert study['acceptance_status'] == 'unscored' and study['acceptance_criteria'] is None
            study_rows.append(dict(paper=paper['paper'], study=study['id'], section=study['section'],
                core_family=study['core_family'], registry_case=study['registry_case'] or '',
                binding=study['binding'], priority=study['priority'], dimension=study['dimension'],
                figure_targets='; '.join(study['figure_targets']), setup_status=study['setup_status'],
                reference_status=study['reference_status'], metric_status=study['metric_status'],
                reference_kind=study.get('reference', {}).get('kind', ''),
                comparison_mode=study.get('comparison_mode', 'not-yet-classified'),
                boundary_realization=study.get('boundary_realization', {}).get('method', ''),
                reflected_domain_copies=study.get('boundary_realization', {}).get('domain_copies', ''),
                material_model=study.get('material_model', ''),
                setup_gaps='; '.join(study.get('setup_gaps', [])),
                acceptance_status=study['acceptance_status'], paper_file=str(path.relative_to(ROOT))))
    write_csv('paper-studies.csv', study_rows)
    for paper in reviewed:
        key = paper['paper']
        choices = [r for r in corpus if Path(r['document']).name.startswith(key + '_')]
        if paper.get('document'):
            choices = [r for r in corpus if r['document'] == paper['document']]
        assert len(choices) == 1, (key, choices)
        document = choices[0]
        assert paper['sha256'] == document['sha256'], f'Reviewed source changed: {key}'
        for family, page, locator, relationship, reference in paper['entries']:
            assert family in aliases, family
            assert 1 <= page <= int(document['extracted_pages']), (key, page)
            evidence.append(dict(paper=key, family=family, document=document['document'],
                sha256=document['sha256'], pdf_page=page, locator=locator,
                relationship=relationship, reference_kind=reference,
                exact_warpsph_setup_match='not-established',
                source_url=source_metadata.get(key, ''),
                review_scope='benchmark section/caption; exact setup reconciliation is a per-case task'))
    write_csv('literature-evidence.csv', evidence)
    write_csv('case-targets.csv', goals)
    write_csv('additional-targets.csv', extra)
    write_csv('backlog/long-term-targets.csv', backlog)
    assert [r[0] for r in spheric] == list(range(1, 25))
    write_csv('spheric-coverage.csv', [dict(test=r[0], title=r[1], related_page=r[2],
        assessment=r[3], source='https://www.spheric-sph.org/validation-tests',
        definition_review='individual-page' if r[0] in (1,2,3,6,8,10,16,22,23) else 'index-only')
        for r in spheric])
    by_family = defaultdict(list)
    for row in evidence:
        by_family[row['family']].append(row)
    family_rows = []
    for family in sorted(set(by_family) | pages):
        rows = by_family[family]
        family_rows.append(dict(family=family, registered_page=family in pages,
            reviewed_papers=';'.join(sorted({r['paper'] for r in rows})),
            reviewed_paper_count=len({r['paper'] for r in rows}),
            external_sources=';'.join(r['id'] for r in external if r['family'] == family),
            exact_setup_status='not-established'))
    write_csv('literature-by-case.csv', family_rows)
    support = read_csv('support.csv')
    schemes = sorted({s for r in inventory['cases'] for s in [r['default_scheme'], *r['supported_schemes']]})
    write_csv('scheme-support.csv', [dict(case=r['name'], **{
        scheme: 'declared' if scheme in r['supported_schemes'] else
        'default-only' if scheme == r['default_scheme'] else 'not-declared'
        for scheme in schemes}) for r in inventory['cases']])
    artifacts = []
    for manifest in sorted((ROOT / 'cases').glob('*/*/artifacts.json')):
        content = json.loads(manifest.read_text())
        for run_id, artifact in content.get('artifacts', {}).items():
            path = (ROOT / artifact['path']).resolve()
            assert path.is_relative_to((ROOT / 'trajectories').resolve()), path
            digest = None
            if path.is_file():
                sha = hashlib.sha256()
                with path.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        sha.update(chunk)
                digest = sha.hexdigest()
            artifacts.append(dict(page=manifest.parent.name, run_id=run_id,
                path=artifact['path'], exists=path.is_file(),
                bytes=path.stat().st_size if path.is_file() else '',
                manifest_bytes=artifact.get('bytes'), sha256=digest or '',
                manifest_sha256=artifact.get('sha256'),
                checksum_matches=bool(digest and digest == artifact.get('sha256')),
                hf=artifact.get('hf') or '', scientific_acceptance='not-reassessed'))
    write_csv('trajectory-availability.csv', artifacts,
        ['page', 'run_id', 'path', 'exists', 'bytes', 'manifest_bytes', 'sha256',
         'manifest_sha256', 'checksum_matches', 'hf', 'scientific_acceptance'])
    ready = sum(r['builder_status'] == 'ready' for r in support)
    references = Counter(r['reference_adapter'] for r in support if r['reference_adapter'])
    keywords_docs = len({r['document'] for r in candidates})
    summary = dict(date=inventory['source_date'], modules=inventory['module_count'],
        registered_cases=len(support), pages=len(pages), builder_ready=ready,
        remote_advertised=sum(r['remote_available'] == 'True' for r in support),
        corpus_files=len(corpus), unique_pdf_hashes=len({r['sha256'] for r in corpus}),
        text_searchable=sum(r['text_status'] == 'extracted' for r in corpus),
        visually_screened=sum(r['search_status'].startswith('visually-screened') for r in corpus),
        candidate_documents=keywords_docs, page_family_candidates=len(candidates),
        reviewed_papers=len(reviewed), reviewed_relationships=len(evidence),
        external_reference_records=len(external), additional_targets=len(extra),
        long_term_targets=len(backlog), paper_files=len({r['paper'] for r in study_rows}), paper_studies=len(study_rows),
        manifested_trajectories=len(artifacts),
        local_manifested_trajectories=sum(r['exists'] for r in artifacts),
        matching_trajectory_checksums=sum(r['checksum_matches'] for r in artifacts),
        search_queries=len(json.loads((DATA / 'web-queries.json').read_text())['queries']))
    (DATA / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    paper_rows = []
    for paper in reviewed:
        rows = [r for r in evidence if r['paper'] == paper['paper']]
        url = rows[0]['source_url']
        label = f"[{paper['paper']}]({url})" if url else paper['paper']
        paper_rows.append([label, ', '.join(dict.fromkeys(r['family'] for r in rows)),
            '; '.join(f"{r['family']}: p{r['pdf_page']} ({r['locator']})" for r in rows)])
    parts = [
        '# warpSPH case support and validation targets',
        f"Snapshot: {inventory['source_date']}. This catalogue separates physical case families, exact reference benchmarks, numerical realizations and evidence of support. Its immediate target is one accepted trajectory per exact benchmark, reusable Python validation and local-file visualization in Remote.",
        '## Scope agreed with the user',
        'A shared visual character establishes a family, not an exact benchmark. Quantitative targets take priority when analytic solutions, measured experiments or independent high-order references exist. Distinct dimensions, initial conditions, boundaries and reference protocols remain distinct. A CG demonstration can inform visualization without qualifying as a quantitative reference.',
        'One solver initially supplies an accepted trajectory for each selected exact benchmark. Other solvers remain runnable; illustrative comparisons such as KH are selected deliberately. Convergence and limitations are evaluated per case. Training-data design is a separate research question. HF is initially a distribution/download location; direct HF-to-Remote streaming is deferred.',
        '## Core dynamics and paper studies',
        'Keep a compact set of reusable dynamics builders. Exact ICs, discretization, references and figure-level comparisons belong in files organized by paper. A study-specific setup can live in that paper’s specialized subfolder. Adding a published variant normally adds a study, not another registered factory. See [the architecture and acceptance contract](PAPER_REPRODUCTIONS.md).',
        'The first reproduction suite is Frontiere 2017 CRKSPH: 14 dynamics families and 21 studies, starting with analytic tests before instability/reference extraction and expensive dimensional variants. See [the suite and implementation order](../reproductions/frontiere2017/README.md). Marrone 2011 sections 3.1 and 3.3 remain subsequent pressure-history targets. Paper files are definition drafts, not executable runner documents or completed validations; the acoustic density metric and local-data notebook are the first Python analysis component.',
        table(['Paper', 'Study', 'Core dynamics', 'Binding', 'Dimension', 'Reference targets'],
              [[r['paper'], r['study'], r['core_family'], r['binding'], r['dimension'], r['figure_targets']] for r in study_rows]),
        '[Paper study matrix](../data/validation/paper-studies.csv). Setup matching, reference availability, metric implementation and acceptance are separate columns; every initial study remains unscored until those requirements are met.',
        '## Current implementation coverage',
        f"The imported registry contains **{len(support)} cases** from {inventory['module_count']} modules, mapped to **{len(pages)} pages**. The configuration catalogue marks **{ready} ready** and **{len(support)-ready} unmigrated**. Remote advertises all {len(support)} through installed discovery; this does not demonstrate that a simulation launches or validates. Its seven static presets are curated entries, not the full catalogue.",
        'Builder ready means the versioned configuration metadata is complete. Unmigrated cases retain legacy paths. Empty declared-scheme lists mean no explicit support declaration; they do not mean every alternative scheme is unsupported. Dimensions below are advertised by Remote in this snapshot. Existing notebook/golden files and reference adapters establish artifact presence only.',
        table(['Registered case', 'Page', 'Dimensions', 'Default scheme', 'Builder', 'Named variants', 'Reference adapter'],
            [[r['case'], r['page'], r['advertised_remote_dimensions'], r['default_scheme'],
              r['builder_status'], r['named_variants'] or 'default only', r['reference_adapter'] or 'none declared'] for r in support]),
        '[Full metadata and provenance](../data/validation/inventory.json) · [Support CSV](../data/validation/support.csv). All source checkouts and their dirty state are recorded; a commit alone does not reproduce a dirty checkout. This audit constructs no particle systems and runs no solver steps.',
        '[Case by scheme declaration matrix](../data/validation/scheme-support.csv): declared and default-only are metadata evidence, not runtime validation; not-declared is unknown rather than unsupported. Variant-specific compatibility still needs per-case assessment.',
        f"[Trajectory availability](../data/validation/trajectory-availability.csv): {len(artifacts)} entries in public artifact manifests; {summary['local_manifested_trajectories']} local files exist and {summary['matching_trajectory_checksums']} checksums match. These are stored artifacts from earlier work, not newly certified references. Raw scratch runs and internal experiment records are outside this inventory.",
        '## Benchmark identity and reference quality',
        'Use a family identifier for browsing. Assign a versioned benchmark identifier only after specifying the governing equations/EOS, dimension, domain and geometry, physical initial fields, boundary and forcing histories, material parameters, units/nondimensionalization, comparison times and reference version. Record equivalent coordinate/unit transformations explicitly.',
        'Keep the numerical realization alongside that identity: particle mass/spacing policy, lattice/glass/jitter and seed, kernel and support/neighbour policy, operator corrections, integration and timestep policy, solver tolerance, precision and scheme. These choices are comparison axes; matching the continuum setup alone does not reproduce a paper’s numerical experiment.',
        'Reference types are descriptive, not a universal ranking. An analytic solution has an applicability interval and modelling assumptions; an experiment has measurement/filtering uncertainty; a converged numerical reference has a discretization/solver error budget. A stored solver golden supports regression and does not become independent scientific truth.',
        'Reflected IC copies with periodic outer bounds are an accepted initial realization of stationary planar reflecting boundaries: use 2**k copies for k reflected axes, transform normal velocities, preserve material IDs, and measure only the physical paper domain. No dedicated reflecting-wall solver is required. Where good reference data are unavailable or would require a new solver, start with clearly labelled qualitative published comparisons; quantitative reference-error acceptance remains separate.',
        'Concrete distinctions from the snapshot and primary definitions:',
        '- Sod defaults to gamma 5/3 and right state (rho,p)=(0.25,0.1795). Its classic variant uses gamma 1.4 and (0.125,0.1). The 1D classic variant also changes samplingRatio; extruded 2D/3D slabs have their own transverse/equal-mass sampling. Preserve these identities.',
        '- LinearWave is advertised as 1D, with amplitude 1e-6, wavelength and sound speed 1, gamma 5/3 and a unit domain. This is a strong first convergence target; the travelling-wave reference is a small-amplitude approximation whose validity must be checked when changing amplitude.',
        '- Classical incompressible TGV and [SPHERIC TC22](https://www.spheric-sph.org/tests/test-22) use different references. The latter supplies a weakly compressible expansion. Audit the existing analytic-pressure variant before declaring an exact match.',
        '- The current drivenSquare oscillates sinusoidally. [SPHERIC TC6](https://www.spheric-sph.org/tests/test-06) supplies acceleration to steady translation. The body shape alone does not establish the benchmark.',
        '- The current cylinderWake uses a periodic pinned frame. [DFG 2D-1](https://wwwold.mathematik.tu-dortmund.de/~featflow/en/benchmarks/cfdbenchmarking/flow/dfg_benchmark1_re20.html) specifies a confined inlet/outlet channel; it needs a separate target.',
        '- staticBlob is a rest-state null test. [SPHERIC TC23](https://www.spheric-sph.org/tests/test-23) is wind-driven cloud disruption. Central-force oscillation, unforced drop expansion and capillary oscillation also need separate identities.',
        '## Local literature and online search coverage',
        f"The corpus contains **{len(corpus)} PDF files**, representing **{summary['unique_pdf_hashes']} unique hashes**. Text extraction screened {summary['text_searchable']} files against {len(aliases)} benchmark alias groups. Three scans (Gingold 1977, Monaghan 1992 and Monaghan 1994; 55 pages total) were visually screened, with checksum-bound records in [visual reviews](../data/validation/visual-reviews.json). A page-level text-coverage check distinguishes genuine text from scanned-paper watermarks. The duplicate Tube Maps downloads remain recorded rather than counted as independent papers.",
        f"The search produces {len(candidates)} page/family candidates across {keywords_docs} documents. A match can occur in a bibliography or discussion; it is not a claim of benchmark use. The reviewed evidence table contains **{len(evidence)} relationships across {len(reviewed)} papers**, with physical PDF pages and section/figure/table locators. Online expansion records **{summary['search_queries']} queries** and {len(external)} selected primary reference/provider records.",
        '**Coverage limit:** file enumeration covers the complete local PDF corpus; searchable papers were screened for aliases and the three scans were screened visually. Benchmark-section review is selective and exact warpSPH-to-paper setup equivalence is not established by those family associations. Online search is a bounded expansion, not a claim to enumerate every paper ever published. Unreviewed matches remain visible for subsequent case work; no absence claim is inferred from a failed search.',
        '[Corpus checksums](../data/validation/literature-corpus.csv) · [Unreviewed matches](../data/validation/literature-candidates.csv) · [Reviewed relationships](../data/validation/literature-evidence.csv) · [Case-to-paper index](../data/validation/literature-by-case.csv) · [Online queries](../data/validation/web-queries.json). Copyrighted PDFs and extracted text stay outside tracked research outputs.',
        '## Papers and the case families they use',
        'Locators refer to physical PDF pages, starting at one. The CSV distinguishes benchmark sections, quantitative comparisons, demonstrations with internal metrics and related variants. None of these family-level associations automatically certifies an exact setup match.',
        table(['Paper', 'Case families', 'Evidence locators'], paper_rows),
        '## Validation targets for every existing page',
        'P0 identifies the first reusable workflow; P1 follows with strong references or complementary physics; P2 needs more setup/reference work. These are scientific targets, not measured performance claims. Exact setup requirements and proposed metrics are in the CSV/YAML.',
        table(['Page family', 'Priority', 'Reference strategy', 'Primary metrics'],
              [[r['family'], r['priority'], r['reference_strategy'], r['primary_metrics']] for r in goals]),
        '[Existing-page targets and setup requirements](../data/validation/case-targets.csv). Wall representation and discretization belong in each applicable study; an analytic pre-wall-contact reference cannot be used after reflected waves invalidate it.',
        '## Active paper and adapter targets',
        'Current-fluid-physics identifies studies using the present equation/model families; it does not assert that a preset or initializer is implemented. Capability-check requires a targeted dimension/boundary/adapter audit before scheduling runs. The delivery column distinguishes a paper study, specialized adapter and genuinely reusable builder. None implies one factory per paper.',
        table(['Target', 'Priority', 'Scope', 'Delivery', 'Prerequisite'],
              [[r['id'], r['priority'], r['scope'], r['delivery'], r['prerequisite']] for r in extra]),
        '[Active target details](../data/validation/additional-targets.csv) · [Primary reference definitions](../data/validation/external-references.yaml).',
        '## Long-term directions',
        'Solid/elastic models, landslides, heaving/floating bodies and additional physical-model work remain [long-term targets](../data/validation/backlog/long-term-targets.csv). SPHERIC is a useful source, not a catalogue-completion goal. Its [background checklist](backlog/SPHERIC_COVERAGE.md) is retained separately from active validation.',
        '## Case workflow and completion criteria',
        'Build Frontiere 2017 CRKSPH as the first paper suite. Start with a reconciled float64 acoustic configuration and its implemented density measurement, then planar Sod/Sedov/Noh, Gresho and Yee. Reconcile the broader contact/shock/shear/instability studies next; gate costly dimensional variants and mixed-gamma triple point explicitly. Add Remote adapters after Python measurements and a checked local trajectory. Marrone 3.1/3.3 remain subsequent free-surface targets. See the suite for the complete study order and setup/reference gaps.',
        'For each exact benchmark, complete: source-linked setup; reference and measurement operator; Python metrics verified on controlled inputs; a thin stored-data notebook; selected convergence/limitations evidence; one accepted local trajectory with resolved configuration, source revisions and checksums; then Remote plot parity and the page. Reference quality determines acceptance tolerances; visual similarity alone cannot qualify a quantitative benchmark.',
        'Remote initially consumes a portable case description and a separately selected local trajectory. The description should version the benchmark and analysis definitions, declare required fields/units, list probes/profiles/time windows and reference assets, and specify camera/colour/plot settings. Validate compatibility when the user selects the data file. Use declarative built-in analysis identifiers rather than executable notebook code. Existing URL/view presets are useful starting points, but do not yet establish this complete portable validation-file contract.',
        'Use Python as the initial analysis implementation. For expensive or complex metrics, export versioned measurement series that Remote can plot; for calculations also implemented in the browser, compare both implementations on the same stored frames. Case pages may forward the case description; file selection remains local. HF download/distribution can be added without changing the measurement definitions. No direct HF streaming or ML training-data pipeline is required for this milestone.',
        '## Reproduce the audit',
        'From the cases checkout, with the warp environment and pdftotext installed:',
        '```bash\nPYTHONDONTWRITEBYTECODE=1 /home/lu26029/miniconda3/envs/warp/bin/python scripts/audit_validation_inventory.py --date 2026-10-19\npython scripts/screen_validation_literature.py\n/home/lu26029/miniconda3/envs/warp/bin/python scripts/build_validation_matrices.py\n```',
        'The inventory uses the installed warpSPH checkout and sibling Remote checkout. Screening uses the sibling literature directory by default; both scripts accept explicit source/output paths. Reviewed YAML records are curated input. Generated CSV/JSON and this report must be refreshed together. The scripts check page claims, target coverage, source identity and PDF page bounds; these checks establish catalogue consistency rather than solver correctness.',
    ]
    appendix = ROOT / 'docs/backlog/SPHERIC_COVERAGE.md'
    appendix.parent.mkdir(exist_ok=True)
    appendix.write_text('# SPHERIC background coverage\n\nThe [SPHERIC index](https://www.spheric-sph.org/validation-tests) is a long-term discovery checklist, not an active validation requirement. Prioritize studies that exercise the solver’s current fluid physics. Related pages do not establish exact benchmark equivalence. Individual definitions were reviewed for tests 1, 2, 3, 6, 8, 10, 16, 22 and 23; the remainder are index-level scope notes.\n\n' + table(['Test', 'Benchmark', 'Related page', 'Assessment'], spheric) + '\n')
    (ROOT / 'docs/VALIDATION_AUDIT.md').write_text('\n\n'.join(parts) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
