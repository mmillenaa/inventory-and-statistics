"""Interface das duas áreas de análise; os cálculos ficam em data_logic."""
import re

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from wordcloud import WordCloud

from data_logic import (CAT_FIELDS, INI_FIELDS, CATEGORIES, category_options, display_table,
                        faceted_options, filter_categories, metadata_count,
                        phrase_frequency, reconcile_filters, search_matches,
                        search_records, values_of, year_frequency, record_frequency,
                        cross_frequency, clean)
from vocabulario_controlado import rotulo_curto_sigla
HTML = '<p class="source-paragraph" role="group" aria-label="Planilhas incluídas na análise"></p>'
CSS = """
.source-paragraph {
    margin: 0; padding: 0;
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: .875rem; line-height: 1.55;
    color: var(--st-text-color, #e0d8c8);
    text-align: justify;
    text-align-last: left;
    overflow-wrap: anywhere;
}
.source-paragraph label { display: inline; cursor: pointer; }
.source-paragraph input {
    width: .85rem; height: .85rem; padding: 0;
    margin: 0 .28em 0 0; vertical-align: -.08em;
    accent-color: #5ca6b8; cursor: pointer;
}
.source-paragraph input:focus-visible {
    outline: 2px solid #7bc6cc; outline-offset: 2px;
}
.source-name {
    font-family: 'IBM Plex Mono', monospace;
    font-size: .94em; font-weight: 600;
    color: #7bc6cc; overflow-wrap: anywhere;
}
.source-description { display: inline; }
"""
JS = """
export default function ({parentElement, data, setStateValue}) {
    const paragraph = parentElement.querySelector('.source-paragraph');
    const items = data.items || [];
    const signature = JSON.stringify(items);
    // Mantém os mesmos inputs nos reruns, inclusive foco e navegação pelo teclado.
    if (paragraph.dataset.items !== signature) {
        paragraph.replaceChildren();
        for (const [index, item] of items.entries()) {
            if (index) paragraph.append(document.createTextNode(' '));
            const label = document.createElement('label');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = item.name;
            checkbox.setAttribute('aria-label', item.name);
            const name = document.createElement('span');
            name.className = 'source-name';
            name.textContent = item.name;
            label.append(checkbox, name);
            paragraph.append(label);
            if (item.description) {
                const description = document.createElement('span');
                description.className = 'source-description';
                description.textContent = item.description;
                paragraph.append(document.createTextNode(' '), description);
            }
        }
        paragraph.dataset.items = signature;
    }
    const selected = new Set(data.selection || []);
    for (const checkbox of paragraph.querySelectorAll('input')) {
        checkbox.checked = selected.has(checkbox.value);
    }
    paragraph.onchange = () => {
        const names = [...paragraph.querySelectorAll('input:checked')].map(input => input.value);
        setStateValue('selection', names);
    };
    return () => { paragraph.onchange = null; };
}
"""

def render_sources(available, descriptions, prefix):
    component = st.components.v2.component(
        "inventory_inline_sources", html=HTML, css=CSS, js=JS, isolate_styles=True,
    )
    key = prefix + "source_picker"
    defaults = [name for name in available if st.session_state.get(prefix+"source_"+name, True)]
    current = st.session_state.get(key, {}).get("selection", defaults)
    if current is None:
        current = defaults
    current = [name for name in available if name in current]
    language = st.session_state.get("app_language", "Português")
    items = []
    for name in available:
        translation = descriptions.get(name, {})
        description = translation.get(language, translation.get("Português", ""))
        items.append({"name": name, "description": description})
    result = component(
        key=key, data={"items": items, "selection": current},
        default={"selection": current}, on_selection_change=lambda: None,
        width="stretch", height="content",
    )
    selected = result.selection if result.selection is not None else current
    files = [name for name in available if name in selected]
    for name in available:
        st.session_state[prefix+"source_"+name] = name in files
    return files

CATEGORY_TYPES = {**dict(zip(CATEGORIES, ("genero", "especie", "tecnica", "forma"))),
                  "Gênero declarado": "genero", "Técnica declarada": "tecnica"}
INITIATIVE_CLOUD_FIELDS = ["Nome da iniciativa", "Ano", "Fonte / Origem", "Proponente"]
FIELD_NAMES = {"Título (Busca)": "Título descritivo", "Conteúdo (Busca)": "Conteúdo / Assunto",
               "Data (Busca)": "Data", "Notas (Busca)": "Notas",
               "Arquivo_origem": "Planilha de origem", "Aba_origem": "Aba de origem",
               "Linha_origem": "Linha na planilha", "Fonte / Origem": "Fonte/Origem",
               "Gênero declarado": "Gênero na descrição documental",
               "Técnica declarada": "Técnica na descrição documental"}


def category_label(value, field, with_code=False):
    name = rotulo_curto_sigla(value, tipo=CATEGORY_TYPES.get(field))
    name = re.split(r"\s*\(ex\.?", name, maxsplit=1)[0].rstrip(" .,")
    return f"{name} — {value}" if with_code and name != value else name


def analysis_fields(kind, frame):
    fields = list(CATEGORIES) + list(CAT_FIELDS) if kind == "catalogue" else list(INI_FIELDS)
    return [field for field in fields if field in frame and category_options(frame, field)]


def labeled_fields(frame, fields):
    result = frame.copy()
    for field in fields:
        if field in CATEGORY_TYPES:
            result[field] = frame[field].map(lambda value, field=field: tuple(category_label(v, field) for v in values_of(value)))
    return result


def _reset(prefix, signature):
    if st.session_state.get(prefix + "signature") != signature:
        for key in list(st.session_state):
            if key.startswith(prefix) and key != prefix + "files" and not key.startswith(prefix + "source_"):
                del st.session_state[key]
        st.session_state[prefix + "signature"] = signature


def _sync_filters(frame, fields, prefix, preferred=None):
    searched = search_records(
        frame, st.session_state.get(prefix + "search", "")
    )

    selected = {
        field: list(st.session_state.get(prefix + field, []))
        for field in fields
    }

    # Selecionar todas as opções não deve excluir valores vazios.
    for field in fields:
        available = set(category_options(searched, field))

        if available and available.issubset(set(selected[field])):
            selected[field] = []

    # Considera também listas reduzidas pelos demais filtros.
    if preferred in fields:
        available = set(
            faceted_options(searched, fields, selected)[preferred]
        )

        if available and available.issubset(set(selected[preferred])):
            selected[preferred] = []

    valid = reconcile_filters(
        searched, fields, selected, preferred
    )

    for field in fields:
        key = prefix + field

        if key not in st.session_state or st.session_state[key] != valid[field]:
            st.session_state[key] = valid[field]


def _clear_search(frame, fields, prefix):
    st.session_state[prefix + "search"] = ""
    _sync_filters(frame, fields, prefix)


def _source_note(kind, fields, frame):
    if not fields:
        return
    if kind == "catalogue" and any(field in CATEGORIES for field in fields) and not all(field in CATEGORIES for field in fields):
        _source_note(kind, [field for field in fields if field in CATEGORIES], frame)
        _source_note(kind, [field for field in fields if field not in CATEGORIES], frame)
        return
    layouts = frame.attrs.get("source_columns", {})
    if kind == "initiatives":
        parts = []
        for filename in frame["Arquivo_origem"].unique():
            columns = layouts.get(filename, {}).get("Geral", {})
            source = "Penha" if "MSSCPENHA" in filename else "Carandiru"
            labels = ", ".join(f"{FIELD_NAMES.get(field, field)} ({columns.get(field, '?')})" for field in fields)
            parts.append(f"{source}, aba Geral: {labels}")
        st.caption("Campos de origem — " + "; ".join(parts) + ".")
        return
    positions = {field: set() for field in fields}
    for filename, sheets in layouts.items():
        for sheet, mapping in sheets.items():
            if (sheet == "Geral") != all(field in CATEGORIES for field in fields):
                continue
            for field in fields:
                if field in mapping:
                    positions[field].add(mapping[field])
    labels = ", ".join(FIELD_NAMES.get(field, field) + (" (coluna " + "/".join(sorted(positions[field])) + ")" if positions[field] else "") for field in fields)
    if kind == "catalogue" and all(field in CATEGORIES for field in fields):
        st.caption(f"Campo de origem: {labels}, na aba Geral das planilhas selecionadas. A contagem usa as descrições documentais vinculadas a essas classificações.")
    elif kind == "catalogue":
        st.caption(f"Campos de origem: {labels}, nas abas de descrição documental das planilhas selecionadas.")
    else:
        st.caption(f"Campos de origem: {labels}, na aba Geral das planilhas de mapeamento selecionadas.")
def texto_controle(pt, en, es):
    idioma = st.session_state.get("app_language", "Português")

    return {
        "Português": pt,
        "English": en,
        "Español": es,
    }.get(idioma, pt)


def multiselect_traduzido(
    label,
    options,
    *,
    key,
    format_func=str,
    on_change=None,
    args=None,
    kwargs=None,
    **config,
):
    options = list(options)
    todos = "__ui_selecionar_todos__"

    # Os filtros usam seleção vazia para representar ausência de restrição.
    filtro_categorial = key in {
        "cat_Gênero documental",
        "cat_Espécie/Tipo documental",
        "cat_Técnica de registro",
        "cat_Forma documental",
        "inic_Nome da iniciativa",
        "inic_Intervenção",
        "inic_Abrangência",
        "inic_Modalidade",
    }

    if not options:
        st.text_input(
            label,
            value="",
            placeholder=texto_controle(
                "Nenhuma opção disponível neste recorte",
                "No options available for this selection",
                "No hay opciones disponibles para esta selección",
            ),
            disabled=True,
            key=key + "__sem_opcoes",
        )
        return []

    def ao_mudar():
        selecionados = list(st.session_state.get(key, []))

        if todos in selecionados:
            st.session_state[key] = (
                [] if filtro_categorial else list(options)
            )

        if callable(on_change):
            on_change(*(args or ()), **(kwargs or {}))

    def rotulo(valor):
        if valor == todos:
            return texto_controle(
                "Selecionar todos",
                "Select all",
                "Seleccionar todos",
            )

        return format_func(valor)

    config.pop("placeholder", None)
    config.pop("select_all", None)

    return st.multiselect(
        label,
        [todos, *options],
        key=key,
        format_func=rotulo,
        placeholder=texto_controle(
            "Selecione opções",
            "Choose options",
            "Seleccione opciones",
        ),
        select_all=False,
        on_change=ao_mudar,
        **config,
    )

def render_analysis(kind, available, descriptions, loader, folder, translate):
    prefix = "cat_" if kind == "catalogue" else "inic_"
    files = render_sources(available, descriptions, prefix)
    st.session_state[prefix+"files"] = files
    _reset(prefix, tuple(sorted(files)))
    if not files:
        st.info("Selecione ao menos uma planilha nesta aba.")
        return
    cat, ini = loader(files, folder)
    frame = cat if kind == "catalogue" else ini
    fields = list(CATEGORIES) if kind == "catalogue" else ["Nome da iniciativa", "Intervenção", "Abrangência", "Modalidade"]
    _sync_filters(frame, fields, prefix)
    st.subheader(translate("Busca avançada"))
    search_column, clear_column = st.columns([12, 1], vertical_alignment="bottom")
    with search_column:
        term = st.text_input("Pesquisar palavra, número ou frase inteira", key=prefix+"search",
                             on_change=_sync_filters, args=(frame, fields, prefix))
    with clear_column:
        st.button("Limpar", key=prefix+"clear_search", type="tertiary", help="Limpar somente a busca avançada",
                  on_click=_clear_search, args=(frame, fields, prefix))
    searched = search_records(frame, term)
    selections = {field: st.session_state[prefix + field] for field in fields}
    options_by_field = faceted_options(searched, fields, selections)
    st.subheader(translate("Filtros categoriais"))
    for column, field in zip(st.columns(4), fields):
        with column:
            options = options_by_field[field]
            multiselect_traduzido(translate(field), options, key=prefix+field,
                           format_func=(lambda value, field=field: category_label(value, field, True)) if kind == "catalogue" else str,
                           on_change=_sync_filters, args=(frame, fields, prefix, field),
                           disabled=not options,
                           help='Este campo é o detalhamento do campo "Abrangência".' if field == "Modalidade" else None)
    filtered = filter_categories(searched, selections)
    if term.strip():
        matches = search_matches(filtered, term).sum()
        origin = "; ".join(f"{FIELD_NAMES.get(field, field)} ({int(count)} registros)" for field, count in matches.items() if count)
        if origin:
            st.caption(f'Busca por “{term}”: correspondências nos campos {origin}. Um registro pode corresponder em mais de um campo.')
    st.subheader(translate("Indicadores"))
    metrics = st.columns(3)
    metrics[0].metric("Registros exibidos", len(filtered))
    if kind == "catalogue":
        metrics[1].metric("Gêneros documentais", len(category_options(filtered, "Gênero documental")))
    else:
        metrics[1].metric("Bases selecionadas", len(files))
    metrics[2].metric("Metadados preenchidos no recorte", metadata_count(filtered, kind))
    st.caption("Metadados preenchidos contam os campos de origem, uma vez por registro.")
    st.subheader(translate("Análises e visualizações do acervo"))
    views = ["Nenhuma visualização (limpar tela)", "Linha do tempo (distribuição cronológica)", "Frequências categoriais", "Nuvem de palavras"]
    if kind == "catalogue":
        views.append("Frequências temáticas")
    views.append("Cruzar dois campos")
    visualization = st.selectbox("Escolha uma visualização", views, key=prefix+"view")
    if filtered.empty:
        st.info("Nenhum registro corresponde à busca. Limpe ou ajuste o termo pesquisado.")
    elif visualization == views[1]:
        field = "Data (Busca)" if kind == "catalogue" else "Ano"
        _source_note(kind, [field], filtered)
        frequency, dated, undated = year_frequency(filtered, field)
        st.caption(f"Registros com ano: {dated}. Sem ano extraível: {undated}. Anos sem registros no intervalo aparecem com zero.")
        if not frequency.empty:
            fig = px.line(frequency, x="Ano", y="Frequência", markers=True)
            fig.update_layout(yaxis_title="Registros", xaxis_title="Ano")
            st.plotly_chart(fig, width="stretch")
            st.dataframe(frequency, hide_index=True, width="stretch")
    elif visualization == views[2]:
        available_fields = analysis_fields(kind, filtered)
        if available_fields:
            field = st.selectbox("Campo da frequência", available_fields, key=prefix+"frequency_field", format_func=lambda value: FIELD_NAMES.get(value,value))
            _source_note(kind, [field], filtered)
            frequency = record_frequency(labeled_fields(filtered, [field]), field)
            missing = int(filtered[field].map(lambda value: not any(clean(v) for v in values_of(value))).sum())
            st.caption("Cada registro conta uma vez por categoria. Um registro com várias categorias pode entrar em mais de uma barra.")
            st.caption(f"Registros sem valor neste campo: {missing}. Campos textuais contam o conteúdo de cada célula como uma categoria.")
            st.dataframe(frequency, hide_index=True, width="stretch")
            if len(frequency)>30:
                st.caption("O gráfico mostra as 30 categorias mais frequentes. A tabela e o CSV incluem todas.")
            st.plotly_chart(px.bar(frequency.head(30), x="Categoria", y="Registros"), width="stretch")
            st.download_button("Baixar frequências CSV",frequency.to_csv(index=False).encode("utf-8-sig"),"frequencias.csv","text/csv",key=prefix+"frequency_csv")
        else:
            st.info("Os registros deste recorte não têm classificações preenchidas para este gráfico.")
    elif visualization == views[3]:
        options = analysis_fields(kind, filtered)
        defaults = ["Título (Busca)", "Conteúdo (Busca)", "Palavras-chave"] if kind == "catalogue" else INITIATIVE_CLOUD_FIELDS
        key = prefix+"cloud_fields"
        if key in st.session_state:
            st.session_state[key] = [field for field in st.session_state[key] if field in options]
        chosen = multiselect_traduzido("O que deve conter?", options, default=[f for f in defaults if f in options] if key not in st.session_state else None, key=key, format_func=lambda field: FIELD_NAMES.get(field, field))
        _source_note(kind, chosen, filtered)
        combined, detail = phrase_frequency(labeled_fields(filtered, chosen), chosen)
        st.caption("Frequência somada nos campos selecionados. Vírgulas separam termos; espaços preservam nomes e expressões completas.")
        if combined:
            try:
                cloud = WordCloud(width=1000, height=450, background_color="rgba(0,0,0,0)", mode="RGBA", collocations=False, max_words=150, random_state=7).generate_from_frequencies(combined)
                fig, ax = plt.subplots(figsize=(12, 5))
                ax.imshow(cloud, interpolation="bilinear")
                ax.axis("off")
                st.pyplot(fig)
                plt.close(fig)
            except ValueError:
                st.info("Os termos não couberam na nuvem. As frequências completas continuam disponíveis na tabela.")
            detail["Campo"] = detail["Campo"].map(lambda field: FIELD_NAMES.get(field, field))
            st.dataframe(detail.sort_values("Frequência", ascending=False), hide_index=True, width="stretch")
        else:
            st.info("Selecione campos com termos preenchidos para gerar a nuvem.")
    elif visualization == "Cruzar dois campos":
        available_fields = analysis_fields(kind, filtered)
        if len(available_fields)<2:
            st.info("Este recorte precisa ter pelo menos dois campos preenchidos para o cruzamento.")
        else:
            left,right = st.columns(2)
            row_field = left.selectbox("Campo das linhas",available_fields,key=prefix+"cross_rows",format_func=lambda value:FIELD_NAMES.get(value,value))
            column_fields = [f for f in available_fields if f!=row_field]
            if st.session_state.get(prefix+"cross_columns") not in column_fields:
                st.session_state[prefix+"cross_columns"] = column_fields[0]
            column_field = right.selectbox("Campo das colunas",column_fields,key=prefix+"cross_columns",format_func=lambda value:FIELD_NAMES.get(value,value))
            _source_note(kind,[row_field,column_field],filtered)
            frequency = cross_frequency(labeled_fields(filtered,[row_field,column_field]),row_field,column_field)
            complete = sum(bool(values_of(a)) and bool(values_of(b)) for a,b in zip(filtered[row_field],filtered[column_field]))
            st.caption(f"Registros com os dois campos preenchidos: {complete}. Sem um dos campos: {len(filtered)-complete}. Cada registro conta uma vez por combinação; múltiplas categorias podem produzir mais de uma combinação.")
            frequency = frequency.rename(columns=FIELD_NAMES)
            st.dataframe(frequency,hide_index=True,width="stretch")
            st.download_button("Baixar cruzamento CSV",frequency.to_csv(index=False).encode("utf-8-sig"),"cruzamento.csv","text/csv",key=prefix+"cross_csv")
    elif visualization == "Frequências temáticas":
        themes = {"Família":["mãe", "filho", "criança", "pai", "avó"], "Educação, artes e ofícios":["escola", "alfabetização", "atividade cultural", "costura"], "Arquitetura prisional":["grade", "cela", "pavilhão", "parede", "portão"]}
        theme = st.selectbox("Tema", list(themes), key=prefix+"theme")
        _source_note(kind, ["Título (Busca)", "Conteúdo (Busca)"], filtered)
        frequency = pd.DataFrame([{"Termo": value, "Registros": len(search_records(filtered[["Título (Busca)", "Conteúdo (Busca)"]], value))} for value in themes[theme]])
        st.caption("Documentos contendo cada termo, independentemente do número de repetições. Um documento pode conter vários termos.")
        st.plotly_chart(px.bar(frequency, x="Termo", y="Registros"), width="stretch")
        st.dataframe(frequency, hide_index=True)
    if visualization != views[0] and not filtered.empty:
        with st.expander("Conferir registros e exportar"):
            view = display_table(filtered)
            for field in CATEGORY_TYPES:
                if field in view:
                    view[field] = filtered[field].map(lambda value, field=field: ", ".join(category_label(v, field) for v in values_of(value)))
            view = view.rename(columns=FIELD_NAMES)
            st.dataframe(view, hide_index=True, width="stretch")
            st.download_button("Baixar CSV", view.to_csv(index=False).encode("utf-8-sig"), "inventario-filtrado.csv", "text/csv", key=prefix+"csv")
