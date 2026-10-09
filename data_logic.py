"""Importação e estatísticas verificáveis, independentes da interface Streamlit."""
from collections import Counter, defaultdict
from pathlib import Path
import re
import unicodedata

import pandas as pd

CATEGORIES = ("Gênero documental", "Espécie/Tipo documental", "Técnica de registro", "Forma documental")
CAT_FIELDS = {
    "Identificador local": ("cod",),
    "Título (Busca)": ("titulo descritivo",),
    "Nível de descrição": ("nivel de descricao",),
    "Data (Busca)": ("data",),
    "Tamanho / Duração": ("tamanho", "duracao"),
    "Suporte": ("suporte",), "Local": ("local",),
    "Autor / Responsável": ("autor responsavel",),
    "Catálogo temático": ("denominacao do catalogo",),
    "Localização": ("localizacao",),
    "Código de referência": ("codigo de referencia",),
    "História arquivística": ("historia arquivistica",),
    "Conteúdo (Busca)": ("conteudo assunto",),
    "Condições de acesso e reprodução": ("condicoes de acesso",),
    "Palavras-chave": ("palavras chave",),
    "Gênero declarado": ("genero",),
    "Técnica declarada": ("tecnica de registro",),
    "Legenda para publicações": ("legenda para publicacoes",),
    "Citação ABNT": ("citacao abnt",),
    "Notas (Busca)": ("notas",),
}
INI_FIELDS = {
    "Nome da iniciativa": ("nome da iniciativa", "iniciativa"),
    "Finalidade primária": ("finalidade primaria",),
    "Intervenção": ("intervencao",), "Abrangência": ("abrangencia",),
    "Modalidade": ("modalidade",), "Data": ("data",), "Ano": ("ano",),
    "Local": ("local",), "Proponente": ("proponente da iniciativa", "proponente"),
    "Título do documento": ("titulo",), "Gênero documental": ("genero documental",),
    "Técnica de registro": ("reproducao tecnica de registro",),
    "Fonte / Origem": ("fonte origem",), "Idioma": ("idioma",),
    "Chave de busca": ("entrada chave de busca",),
    "Data de acesso": ("data de acesso",), "Disponibilidade": ("disponibilidade",),
    "Link": ("link",), "Citação ABNT": ("associacao brasileira de normas tecnicas",),
}
MISSING = {"", "na", "n/a", "nan", "none", "null", "nat", "-", "--", "[titulo nao localizado]"}
EXCEL_ERRORS = {"#VALUE!", "#REF!", "#N/A", "#DIV/0!", "#NAME?", "#NUM!", "#NULL!"}


def normalize(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode().lower()).strip()


def clean(value):
    if pd.isna(value):
        return ""
    if isinstance(value, (int, float)) and float(value).is_integer():
        return str(int(value))
    text = re.sub(r"\s+", " ", str(value)).strip()
    return "" if normalize(text) in MISSING or text in EXCEL_ERRORS else text


def header(value):
    text = re.sub(r"\[[^]]*\]|\([^)]*\)", "", normalize(value))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def find_column(columns, aliases):
    """Preferência por alias, match exato, depois prefixo com limite de palavra."""
    names = {c: header(c) for c in columns}
    for alias in aliases:
        for column, name in names.items():
            if name == alias:
                return column
    for alias in aliases:
        for column, name in names.items():
            if name.startswith(alias + " "):
                return column
    return None


def reference_key(value):
    text = re.sub(r"\.[a-z0-9]+$", "", clean(value), flags=re.I)
    # F/V designam faces de uma representação, não uma nova descrição.
    text = re.sub(r"(?<=\d)[FV]$", "", text, flags=re.I)
    return re.sub(r"[^a-z0-9]", "", normalize(text))


def read_table(book, sheet, marker):
    raw = pd.read_excel(book, sheet_name=sheet, header=None, nrows=15)
    for index, row in raw.iterrows():
        names = [header(v) for v in row if pd.notna(v)]
        found = ("ano" in names and any(n in {"nome da iniciativa", "iniciativa"} for n in names)) if marker == "iniciativa" else any(n.startswith(marker) for n in names)
        if found:
            return pd.read_excel(book, sheet_name=sheet, header=index, dtype=object), index + 2
    raise ValueError(f"Cabeçalho não localizado: {sheet} ({marker})")


def load_collection(files, folder):
    catalogue, initiatives, representations, issues = [], [], [], []
    for filename in sorted(set(files)):
        path = Path(folder) / filename
        try:
            with pd.ExcelFile(path) as book:
                general = next((s for s in book.sheet_names if header(s) == "geral"), None)
                if not general:
                    raise ValueError("Aba Geral ausente")
                if "MAPEAMENTOS" in filename.upper():
                    table, start = read_table(book, general, "iniciativa")
                    mapping = {field: find_column(table.columns, aliases) for field, aliases in INI_FIELDS.items()}
                    required = ["Nome da iniciativa", "Ano", "Título do documento"]
                    absent = [f for f in required if mapping[f] is None]
                    if absent:
                        raise ValueError("Campos ausentes: " + ", ".join(absent))
                    for index, row in table.iterrows():
                        record = {field: clean(row[c]) if c is not None else "" for field, c in mapping.items()}
                        if not record["Nome da iniciativa"]:
                            if any(clean(v) for v in row):
                                issues.append({"Arquivo": filename, "Aba": general, "Linha": start + index, "Problema": "Linha incompleta sem categoria de iniciativa; não incluída nas estatísticas"})
                            continue
                        record.update(Arquivo_origem=filename, Aba_origem=general, Linha_origem=start + index, Registro_ID=f"{filename}:{general}:{start+index}")
                        initiatives.append(record)
                    continue

                master, master_start = read_table(book, general, "genero documental")
                class_cols = {field: find_column(master.columns, (header(field),)) for field in CATEGORIES}
                if any(c is None for c in class_cols.values()):
                    raise ValueError("Geral sem as quatro classificações documentais")
                for index, row in master.iterrows():
                    if not any(clean(row[c]) for c in class_cols.values()):
                        continue
                    pieces = []
                    for pos, value in enumerate(row.iloc[1:], start=1):
                        token = clean(value)
                        if pos == 19 and token.isdigit():
                            token = token.zfill(3)
                        pieces.append(token)
                    ref = "".join(pieces)
                    representations.append({"Arquivo_origem": filename, "Aba_origem": general, "Linha_origem": master_start+index, "Representação_ID": f"{filename}:{general}:{master_start+index}", "Referência do arquivo": ref, "Chave": reference_key(ref), **{field: clean(row[c]).upper() for field, c in class_cols.items()}})

                for sheet in book.sheet_names:
                    if header(sheet) in {"geral", "classificacao", "controle"}:
                        continue
                    try:
                        table, start = read_table(book, sheet, "titulo descritivo")
                    except ValueError:
                        continue
                    mapping = {field: find_column(table.columns, aliases) for field, aliases in CAT_FIELDS.items()}
                    for index, row in table.iterrows():
                        record = {field: clean(row[c]) if c is not None else "" for field, c in mapping.items()}
                        if not record["Título (Busca)"]:
                            issues.append({"Arquivo": filename, "Aba": sheet, "Linha": start+index, "Problema": "Descrição sem título; não incluída nas estatísticas"})
                            continue
                        record.update(Arquivo_origem=filename, Aba_origem=sheet, Linha_origem=start+index, Registro_ID=f"{filename}:{sheet}:{start+index}")
                        catalogue.append(record)
        except (ValueError, OSError) as exc:
            issues.append({"Arquivo": filename, "Aba": "", "Linha": "", "Problema": str(exc)})

    keys = Counter((r["Arquivo_origem"], reference_key(r["Código de referência"])) for r in catalogue if r["Código de referência"])
    rep_index = defaultdict(list)
    for rep in representations:
        rep_index[(rep["Arquivo_origem"], rep["Chave"])].append(rep)
    matched = set()
    for record in catalogue:
        key = (record["Arquivo_origem"], reference_key(record["Código de referência"]))
        conflict = bool(key[1] and keys[key] > 1)
        matches = [] if conflict else rep_index.get(key, [])
        record["Conflito de código"] = conflict
        record["Representações vinculadas"] = len(matches)
        record["Representações_ID"] = tuple(r["Representação_ID"] for r in matches)
        for field in CATEGORIES:
            record[field] = tuple(sorted({r[field] for r in matches if r[field]}))
        matched.update(record["Representações_ID"])
        if conflict or not matches:
            issues.append({"Arquivo": record["Arquivo_origem"], "Aba": record["Aba_origem"], "Linha": record["Linha_origem"], "Problema": "Código repetido em descrições diferentes; classificação não atribuída" if conflict else "Descrição sem correspondência na Geral"})
    for rep in representations:
        if rep["Representação_ID"] not in matched:
            issues.append({"Arquivo": rep["Arquivo_origem"], "Aba": rep["Aba_origem"], "Linha": rep["Linha_origem"], "Problema": "Representação sem descrição vinculada"})
    for field in ("Nome da iniciativa", "Finalidade primária", "Intervenção", "Abrangência", "Modalidade"):
        labels = {}
        for record in initiatives:
            key = normalize(record[field])
            labels.setdefault(key, record[field])
            record[field] = labels[key]
    cat = pd.DataFrame(catalogue, columns=list(CAT_FIELDS)+list(CATEGORIES)+["Arquivo_origem", "Aba_origem", "Linha_origem", "Registro_ID", "Conflito de código", "Representações vinculadas", "Representações_ID"])
    ini = pd.DataFrame(initiatives, columns=list(INI_FIELDS)+["Arquivo_origem", "Aba_origem", "Linha_origem", "Registro_ID"])
    cat.attrs["representations"] = representations
    cat.attrs["issues"] = issues
    return cat, ini


def metadata_count(frame, kind):
    """Conta células preenchidas de metadados de origem, sem campos técnicos ou cópias derivadas."""
    fields = CAT_FIELDS if kind == "catalogue" else INI_FIELDS
    return sum(bool(clean(v)) for field in fields if field in frame for v in frame[field])


def values_of(value):
    return value if isinstance(value, (tuple, list)) else ((value,) if clean(value) else ())


def category_options(frame, field):
    return sorted({v for value in frame[field] for v in values_of(value) if v}, key=normalize)


def filter_categories(frame, selections):
    result = frame.copy()
    for field, selected in selections.items():
        if selected and field in result:
            wanted = set(selected)
            result = result[result[field].map(lambda value: bool(wanted.intersection(values_of(value))))]
    return result


def search_records(frame, term):
    query = normalize(term)
    if not query or frame.empty:
        return frame.copy()
    fields = [f for f in dict.fromkeys(list(CAT_FIELDS)+list(INI_FIELDS)) if f in frame]
    pattern = re.compile(r"(?<!\w)" + re.escape(query) + r"(?!\w)")
    # Cada campo é pesquisado separadamente, impedindo frases artificiais entre colunas.
    mask = frame.apply(lambda row: any(pattern.search(normalize(row[f])) for f in fields), axis=1)
    return frame.loc[mask.astype(bool)].copy()


def year_frequency(frame, field):
    years = frame[field].map(clean).str.extract(r"(?<!\d)((?:18|19|20)\d{2})(?!\d)")[0]
    count = years.dropna().value_counts().sort_index()
    table = pd.DataFrame({"Ano": count.index.astype(int), "Frequência": count.values})
    if not table.empty:
        first, last = int(table["Ano"].min()), int(table["Ano"].max())
        table = table.set_index("Ano").reindex(range(first, last+1), fill_value=0).rename_axis("Ano").reset_index()
    return table, int(years.notna().sum()), int(years.isna().sum())


def phrase_frequency(frame, fields):
    counts, labels, per_field = Counter(), {}, Counter()
    for field in fields:
        for value in frame[field]:
            for part in re.split(r"[,;\n\r]+", clean(value)):
                label = clean(part).strip(" .-")
                key = normalize(label)
                if not label or key in {"de", "a", "o", "e", "do", "da", "em", "para"}:
                    continue
                labels.setdefault(key, label)
                counts[key] += 1
                per_field[(field, key)] += 1
    combined = {labels[k]: v for k, v in counts.items()}
    detail = pd.DataFrame([{"Campo": field, "Termo": labels[key], "Frequência": n} for (field, key), n in per_field.items()], columns=["Campo", "Termo", "Frequência"])
    return combined, detail


def display_table(frame):
    view = frame.copy()
    for field in CATEGORIES:
        if field in view:
            view[field] = view[field].map(lambda value: ", ".join(values_of(value)))
    return view.drop(columns=["Representações_ID"], errors="ignore")
