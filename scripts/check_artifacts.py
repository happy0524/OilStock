"""Check local links, notebook execution state, and generated output completeness."""
from pathlib import Path
import json
import re
import nbformat

ROOT = Path(__file__).resolve().parents[1]


def main():
    checked = 0
    missing = []
    for path in [ROOT / 'README.md', *sorted((ROOT / 'docs').glob('*.md')), *sorted((ROOT / 'reports').glob('*.md'))]:
        for url in re.findall(r'\]\(([^\s]+)\)',path.read_text(encoding='utf-8')):
            if url.startswith(('https://','http://','#','mailto:')):
                continue
            checked += 1
            if not (path.parent / url.split('#')[0]).exists():
                missing.append(f'{path.relative_to(ROOT)} -> {url}')
    notebook = nbformat.read(ROOT / 'notebooks/01_exploration.ipynb',as_version=4)
    nbformat.validate(notebook)
    cells = [c for c in notebook.cells if c.cell_type == 'code']
    assert [c.execution_count for c in cells] == list(range(1,len(cells)+1)), 'Notebook execution order incomplete'
    assert not any(o.output_type == 'error' for c in cells for o in c.outputs), 'Notebook contains errors'
    run = json.loads((ROOT / 'data/processed/run_manifest.json').read_text(encoding='utf-8'))
    for fig in run['figures']:
        if fig['generated']:
            assert (ROOT / 'reports/figures' / fig['file']).stat().st_size > 1000
    assert not missing, '\n'.join(missing)
    print(f'Artifact checks passed: {checked} local links; {len(cells)} executed notebook cells; {sum(f["generated"] for f in run["figures"])} figures')


if __name__ == '__main__':
    main()
