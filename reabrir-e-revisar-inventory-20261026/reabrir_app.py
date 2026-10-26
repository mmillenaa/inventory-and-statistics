"""Retira somente o bloqueio de manutenção conhecido de app.py, com backup."""
import ast
from datetime import datetime, timezone
from pathlib import Path
import shutil


def reopen(path):
    path=Path(path)
    source=path.read_text(encoding="utf-8")
    nodes=ast.parse(source).body
    lines=source.splitlines(keepends=True)
    remove=[]
    found=False
    for node in nodes:
        if not isinstance(node,ast.Expr) or not isinstance(node.value,ast.Call):
            continue
        call=node.value
        if not isinstance(call.func,ast.Attribute) or not isinstance(call.func.value,ast.Name) or call.func.value.id!="st":
            continue
        text=call.args[0].value if call.args and isinstance(call.args[0],ast.Constant) else ""
        maintenance=call.func.attr in {"markdown","warning"} and isinstance(text,str) and ("manutencao-tela" in text or "site em manutenção" in text.lower())
        if maintenance:
            found=True
            remove.append((node.lineno-1,node.end_lineno))
        elif found and call.func.attr=="stop":
            remove.append((node.lineno-1,node.end_lineno))
            break
    if not remove:
        print("Não há bloqueio de manutenção conhecido. Nenhum arquivo alterado.")
        return False
    if len(remove)<2:
        raise SystemExit("Bloco diferente do esperado. Nenhum arquivo alterado; conferir app.py.")
    for start,end in reversed(remove):
        del lines[start:end]
    revised="".join(lines)
    ast.parse(revised)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup=path.parent/".backup-correcoes"/stamp
    backup.mkdir(parents=True)
    shutil.copy2(path,backup/path.name)
    path.write_text(revised,encoding="utf-8")
    print("Bloqueio removido. Para publicar, execute:")
    print('git add app.py')
    print('git commit -m "Retira aviso de manutencao e reabre app"')
    print('git push origin main')
    return True


if __name__=="__main__":
    reopen(Path.cwd()/"app.py")
