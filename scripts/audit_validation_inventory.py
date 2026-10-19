#!/usr/bin/env python3
"""Snapshot registered cases and frontend metadata without constructing a simulation.

Run with the warp environment, from this repository. Dependencies are those of the
installed solver and PyYAML. A sibling warpSPHRemote checkout supplies the discovery
code; --remote-root selects a different checkout. This measures metadata coverage,
not runtime or scientific validity. GPU visibility is disabled before importing.
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
from datetime import date
import enum
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def serializable(value):
    if dataclasses.is_dataclass(value):
        return serializable(dataclasses.asdict(value))
    if isinstance(value, enum.Enum):
        return serializable(value.value)
    if isinstance(value, dict):
        return {str(k): serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def provenance(root):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args])
    status = git('status', '--porcelain').decode()
    return dict(commit=git('rev-parse', 'HEAD').decode().strip(),
                branch=git('branch', '--show-current').decode().strip(),
                dirty=bool(status), status=status.splitlines(),
                tracked_diff_sha256=hashlib.sha256(git('diff', 'HEAD')).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument('--remote-root', type=Path, default=root.parent / 'warpSPHRemote')
    parser.add_argument('--output', type=Path, default=root / 'data/validation')
    parser.add_argument('--date', default=date.today().isoformat(), help='Date recorded in the snapshot.')
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ.setdefault('NUMBA_CACHE_DIR', '/tmp/warpsph-audit-numba')
    os.environ.setdefault('MPLCONFIGDIR', '/tmp/warpsph-audit-mpl')
    sys.path.insert(0, str(args.remote_root / 'python'))
    import yaml
    import warpSPH
    from warpSPH.cases import importAll, CASE_MODULES
    from warpSPH.runner import getCase, listCases, configurationCatalogue
    from warpsph_remote.configuration import installed_catalogue
    importAll()
    catalogue = configurationCatalogue()
    configuration = {c['id']: c for c in catalogue['cases']}
    remote = installed_catalogue()
    remote_by_case = {c['registry']: c for c in remote if 'registry' in c}
    claims = {}
    for path in sorted((root / 'cases').glob('*/*/case.yaml')):
        spec = yaml.safe_load(path.read_text())
        for name in spec['cases']:
            if name in claims:
                raise ValueError(f'Duplicate page claim: {name}')
            notebook = spec.get('notebook')
            claims[name] = dict(page=spec['slug'], family=spec['family'],
                page_status=spec['status'], manifest=str(path.relative_to(root)),
                reference_kind=spec.get('reference', {}).get('kind'),
                notebook=str(path.parent.relative_to(root) / notebook) if notebook else None,
                notebook_exists=bool(notebook and (path.parent / notebook).is_file()),
                golden_files=len(list((path.parent / 'golden').glob('*')))
                    if (path.parent / 'golden').is_dir() else 0)
    if set(claims) != set(listCases()):
        raise ValueError(f'Page/registry mismatch: {set(claims) ^ set(listCases())}')
    records = []
    for name in listCases():
        case = getCase(name)
        frontend = remote_by_case.get(name, {})
        records.append(dict(name=name, module=case.buildSystem.__module__,
            description=case.description, default_scheme=case.scheme,
            defaults=serializable(case.defaults), params=serializable(case.params),
            supported_schemes=list(case.supportedSchemes), variants=serializable(case.variants),
            simulation_parameters=serializable(case.simulationParameters),
            parameter_definitions=serializable(case.parameterDefinitions),
            extra_fields=list(case.extraFields), builder=configuration[name],
            remote=frontend, page=claims[name],
            evidence='metadata-only; no launch or validation performed by this audit'))
    solver_root = Path(warpSPH.__file__).resolve().parents[2]
    snapshot = dict(schema_version=1, source_date=args.date,
        provenance=dict(warpSPH=provenance(solver_root),
                        warpSPHRemote=provenance(args.remote_root),
                        warpSPHCases=provenance(root)),
        module_count=len(CASE_MODULES), registered_case_count=len(records),
        page_count=len(list((root / 'cases').glob('*/*/case.yaml'))), cases=records)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'inventory.json').write_text(json.dumps(snapshot, indent=2) + '\n')
    columns = ['case', 'family', 'page', 'default_dimension', 'advertised_remote_dimensions',
        'default_scheme', 'declared_schemes', 'named_variants', 'builder_status',
        'missing_parameter_descriptors', 'remote_id', 'remote_available',
        'remote_configurable', 'reference_adapter', 'thin_notebook_exists', 'golden_files',
        'runtime_evidence', 'source_module']
    with (args.output / 'support.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in records:
            writer.writerow(dict(case=row['name'], family=row['page']['family'], page=row['page']['page'],
                default_dimension=row['defaults'].get('dim'),
                advertised_remote_dimensions=';'.join(map(str, row['remote'].get('dimensions', []))),
                default_scheme=row['default_scheme'], declared_schemes=';'.join(row['supported_schemes']),
                named_variants=';'.join(row['variants']), builder_status=row['builder']['status'],
                missing_parameter_descriptors=len(row['builder']['missingParameters']),
                remote_id=row['remote'].get('id'), remote_available=row['remote'].get('available'),
                remote_configurable=row['remote'].get('configurable'),
                reference_adapter=row['page']['reference_kind'],
                thin_notebook_exists=row['page']['notebook_exists'], golden_files=row['page']['golden_files'],
                runtime_evidence='not assessed', source_module=row['module']))
    print(f"{len(records)} cases; {snapshot['page_count']} pages; "
          f"{sum(r['builder']['status'] == 'ready' for r in records)} builder-ready; "
          f"{sum(bool(r['remote'].get('available')) for r in records)} advertised by Remote")


if __name__ == '__main__':
    main()
