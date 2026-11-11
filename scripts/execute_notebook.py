"""Execute the delivered notebook using this interpreter, without registering a user kernel."""
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = ROOT / 'notebooks/01_exploration.ipynb'
    notebook = nbformat.read(path, as_version=4)
    with TemporaryDirectory(prefix='oilstock-kernel-') as temporary:
        kernel = Path(temporary) / 'oilstock'
        kernel.mkdir()
        (kernel / 'kernel.json').write_text(json.dumps({
            'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
            'display_name':'Python (OilStock)', 'language':'python'}),encoding='utf-8')
        manager = KernelManager(kernel_name='oilstock',kernel_spec_manager=KernelSpecManager(kernel_dirs=[temporary]))
        NotebookClient(notebook,km=manager,timeout=120,
                       resources={'metadata':{'path':str(ROOT)}}).execute()
    code = [cell for cell in notebook.cells if cell.cell_type == 'code']
    assert [cell.execution_count for cell in code] == list(range(1,len(code)+1))
    assert not any(output.output_type == 'error' for cell in code for output in cell.outputs)
    nbformat.write(notebook,path)
    print(f'Notebook executed: {len(code)} cells, no errors')


if __name__ == '__main__':
    main()
