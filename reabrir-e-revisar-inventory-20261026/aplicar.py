"""Aplica a revisão dos cálculos e retira o bloqueio conhecido de manutenção."""
import hashlib
import importlib.util
import json
from pathlib import Path
from datetime import datetime, timezone
import shutil
import subprocess


def main():
    package=Path(__file__).resolve().parent
    root=Path.cwd()
    result=subprocess.run(['git','rev-parse','--show-toplevel'],capture_output=True,text=True)
    if result.returncode or Path(result.stdout.strip()).resolve()!=root.resolve() or not (root/'app.py').exists():
        raise SystemExit('Execute na raiz do repositório inventory-and-statistics.')
    manifest=json.loads((package/'versoes.json').read_text())
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    for name,expected in manifest.items():
        if digest(root/name) not in {expected,digest(package/'codigo'/name)}:
            raise SystemExit(f'{name} mudou desde a versão conferida. Nenhum arquivo foi alterado; preservar e revisar essa mudança.')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup=root/'.backup-correcoes'/stamp
    backup.mkdir(parents=True)
    paths=list(manifest)+['app.py']
    for name in paths:
        if (root/name).exists():
            (backup/name).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(root/name,backup/name)
    try:
        for name in manifest:
            (root/name).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(package/'codigo'/name,root/name)
        spec=importlib.util.spec_from_file_location('reabrir_app',package/'reabrir_app.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.reopen(root/'app.py')
    except BaseException:
        for name in paths:
            if (backup/name).exists():
                shutil.copy2(backup/name,root/name)
            elif (root/name).exists():
                (root/name).unlink()
        raise
    print('Revisão aplicada com backup. Os XLSX não foram alterados.')
    print('Execute agora: python -m unittest discover -s tests -v')
    print('Depois use os comandos de commit e push em LEIA-PRIMEIRO.md.')


if __name__=='__main__':
    main()
