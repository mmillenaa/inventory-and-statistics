import pandas as pd
import os

pasta = os.getcwd()
saida = []

for f in sorted(os.listdir(pasta)):
    if not f.lower().endswith(('.xlsx', '.xls')) or f.startswith('~$'):
        continue
    saida.append(f"\n{'='*90}\nARQUIVO: {f}\n{'='*90}")
    try:
        xls = pd.ExcelFile(os.path.join(pasta, f))
        saida.append(f"ABAS ({len(xls.sheet_names)}): {xls.sheet_names}")
        for aba in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=aba, header=None, nrows=6)
            saida.append(f"\n--- ABA: {aba} | shape={df.shape} ---")
            saida.append(df.to_string(max_colwidth=45))
    except Exception as e:
        saida.append(f"ERRO ao ler: {e}")

with open("estrutura_acervo.txt", "w", encoding="utf-8") as fp:
    fp.write("\n".join(saida))

print("Pronto: estrutura_acervo.txt")