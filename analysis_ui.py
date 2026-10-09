"""Interface das duas áreas de análise; os cálculos ficam em data_logic."""
from html import escape
import re

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import streamlit as st
from wordcloud import WordCloud

from data_logic import (CATEGORIES, category_options, display_table,
                        faceted_options, filter_categories, metadata_count,
                        phrase_frequency, reconcile_filters, search_matches,
                        search_records, values_of, year_frequency)
from vocabulario_controlado import rotulo_curto_sigla

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


def _reset(prefix, signature):
    if st.session_state.get(prefix + "signature") != signature:
        for key in list(st.session_state):
            if key.startswith(prefix) and key != prefix + "files" and not key.startswith(prefix + "source_"):
                del st.session_state[key]
        st.session_state[prefix + "signature"] = signature


def _sync_filters(frame, fields, prefix, preferred=None):
    searched = search_records(frame, st.session_state.get(prefix + "search", ""))
    selected = {field: st.session_state.get(prefix + field, []) for field in fields}
    valid = reconcile_filters(searched, fields, selected, preferred)
    for field in fields:
        key = prefix + field
        if selected[field] != valid[field] or key not in st.session_state:
            st.session_state[key] = valid[field]


def _clear_search(frame, fields, prefix):
    st.session_state[prefix + "search"] = ""
    _sync_filters(frame, fields, prefix)


def _source_note(kind, fields, frame):
    if not fields:
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


def render_analysis(kind, available, descriptions, loader, folder, translate):
    prefix = "cat_" if kind == "catalogue" else "inic_"
    files = []
    with st.container(key=prefix+"sources"):
        for filename in available:
            if st.checkbox(filename, value=True, key=prefix+"source_"+filename):
                files.append(filename)
            translations = descriptions.get(filename, {})
            description = translations.get(st.session_state.get("app_language", "Português"), translations.get("Português", ""))
            if description:
                st.markdown(f"<div class='desc-lista'>{escape(description)}</div>", unsafe_allow_html=True)
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
            st.multiselect(translate(field), options, key=prefix+field,
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
        available_fields = [field for field in fields if category_options(filtered, field)]
        if available_fields:
            field = st.selectbox("Campo da frequência", available_fields, key=prefix+"frequency_field")
            _source_note(kind, [field], filtered)
            counts = {value: len(filter_categories(filtered, {field: [value]})) for value in category_options(filtered, field)}
            frequency = pd.DataFrame([{"Categoria": category_label(value, field) if kind == "catalogue" else value, "Registros": count} for value, count in counts.items()])
            st.caption("Cada registro conta uma vez por categoria. Um registro com várias categorias pode entrar em mais de uma barra.")
            st.dataframe(frequency, hide_index=True, width="stretch")
            st.plotly_chart(px.bar(frequency, x="Categoria", y="Registros"), width="stretch")
        else:
            st.info("Os registros deste recorte não têm classificações preenchidas para este gráfico.")
    elif visualization == views[3]:
        options = ["Título (Busca)", "Conteúdo (Busca)", "Palavras-chave"] if kind == "catalogue" else INITIATIVE_CLOUD_FIELDS
        options = [field for field in options if field in filtered]
        key = prefix+"cloud_fields"
        if key in st.session_state:
            st.session_state[key] = [field for field in st.session_state[key] if field in options]
        chosen = st.multiselect("O que deve conter?", options, default=options if key not in st.session_state else None, key=key, format_func=lambda field: FIELD_NAMES.get(field, field))
        _source_note(kind, chosen, filtered)
        combined, detail = phrase_frequency(filtered, chosen)
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
