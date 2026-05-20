import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from docx import Document
import re
import os
import requests

st.set_page_config(layout="wide", page_title="Inventário e estatísticas do GPDVE")

# ============================================================
# CONTROLES SUPERIORES (DIREITA) E IDIOMA
# ============================================================
# Deixamos apenas a coluna de espaço vazio (8.5) e a coluna do idioma (1.5)
col_espaco, col_idioma = st.columns([8.5, 1.5])

with col_idioma:
    st.caption("Idioma / Language")
    idioma = st.selectbox(
        "Seletor de idioma", 
        ["Português", "English", "Español"], 
        label_visibility="collapsed"
    )

def traduzir(texto_pt):
    dicionario = {
        "Inventário e estatística das coleções do GPDVE": {
            "English": "Inventory and Statistics of GPDVE Collections",
            "Español": "Inventario y estadística de las colecciones del GPDVE"
        },
        "Gestão e visualização transversal de metadados arquivísticos.": {
            "English": "Management and transversal visualisation of archival metadata.",
            "Español": "Gestión y visualización transversal de metadatos archivísticos."
        },
        "O programa foi concebido para realizar análises estatísticas sobre bases de dados estruturadas e padronizadas, especificamente voltadas à catalogação e descrição arquivística de documentos, permitindo visualizações transversais de metadados e instrumentos de pesquisa.": {
            "English": "The programme was designed to perform statistical analyses on structured and standardised databases, specifically aimed at the cataloguing and archival description of documents, allowing transversal visualisations of metadata and research instruments.",
            "Español": "El programa fue diseñado para realizar análisis estadísticos sobre bases de datos estructuradas y estandarizadas, específicamente dirigidas a la catalogación y descripción archivística de documentos, permitiendo visualizaciones transversales de metadatos e instrumentos de investigación."
        },
        "Inventário do acervo catalogado": {"English": "Catalogued collection inventory", "Español": "Inventario del acervo catalogado"},
        "Visão geral do acervo": {"English": "Collection overview", "Español": "Visión general del acervo"},
        "Observatório de bases publicadas pelo GPDVE no Dataverse": {"English": "Observatory of databases published by GPDVE on Dataverse", "Español": "Observatorio de bases de datos publicadas por GPDVE en Dataverse"},
        "Busca avançada": {"English": "Advanced search", "Español": "Búsqueda avanzada"},
        "Pesquisar termo nas planilhas (ex: criança, portão, costura)": {"English": "Search term in spreadsheets (e.g., child, gate, sewing)", "Español": "Buscar término en hojas de cálculo (ej: niño, puerta, costura)"},
        "Filtros categoriais": {"English": "Categorical filters", "Español": "Filtros categóricos"},
        "Selecione as planilhas para integrar:": {"English": "Select the spreadsheets to integrate:", "Español": "Seleccione las hojas de cálculo a integrar:"},
        "Indicadores": {"English": "Metrics", "Español": "Indicadores"},
        "Itens exibidos": {"English": "Displayed items", "Español": "Elementos mostrados"},
        "Gêneros documentais": {"English": "Documentary genres", "Español": "Géneros documentales"},
        "Metadados indexados (total)": {"English": "Indexed metadata (total)", "Español": "Metadatos indexados (total)"},
        "Análises e visualizações do acervo": {"English": "Analyses and visualisations of the collection", "Español": "Análisis y visualizaciones de la colección"},
        "Escolha uma visualização ou eixo temático:": {"English": "Choose a visualisation or thematic axis:", "Español": "Elija una visualización o eje temático:"},
        "Nenhuma visualização (limpar tela)": {"English": "No visualisation (clear screen)", "Español": "Ninguna visualización (limpiar pantalla)"},
        "Linha do tempo (distribuição cronológica)": {"English": "Timeline (chronological distribution)", "Español": "Línea de tiempo (distribución cronológica)"},
        "Frequência de datas grafadas nos documentos": {"English": "Frequency of dates written in documents", "Español": "Frecuencia de fechas escritas en los documentos"},
        "Volume documental": {"English": "Documentary volume", "Español": "Volumen documental"},
        "Distribuição estatística": {"English": "Statistical distribution", "Español": "Distribución estadística"},
        "Visualização detalhada": {"English": "Detailed view", "Español": "Vista detallada"},
        "Instrumentos de pesquisa": {"English": "Research instruments", "Español": "Instrumentos de investigación"},
        "Gerar INVENTÁRIO DO ACERVO": {"English": "Generate COLLECTION INVENTORY", "Español": "Generar INVENTARIO DEL ACERVO"},
        "Acervo documental digitalizado": {"English": "Digitised documentary collection", "Español": "Colección documental digitalizada"},
        "Controle descritivo dos conjuntos documentais sob guarda ou análise do grupo.": {"English": "Descriptive control of documentary sets under custody or analysis by the group.", "Español": "Control descriptivo de los conjuntos documentales bajo custodia o análisis del grupo."},
        "Fotografia (FOT)": {"English": "Photography (FOT)", "Español": "Fotografía (FOT)"},
        "Planta cartográfica (PLN)": {"English": "Cartographic plan (PLN)", "Español": "Planta cartográfica (PLN)"},
        "Digitalizado (DGZ)": {"English": "Digitised (DGZ)", "Español": "Digitalizado (DGZ)"},
        "Iconográfico (ICO)": {"English": "Iconographic (ICO)", "Español": "Iconográfico (ICO)"},
        "Meio magnético/ótico (MTO)": {"English": "Magnetic/optical media (MTO)", "Español": "Medio magnético/óptico (MTO)"},
        "Textual (TXT)": {"English": "Textual (TXT)", "Español": "Textual (TXT)"}
    }
    if idioma == "Português" or texto_pt not in dicionario:
        return texto_pt
    return dicionario[texto_pt].get(idioma, texto_pt)

# ============================================================
# ESTILOS (CSS BASE)
# ============================================================
css_base = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Source+Serif+4:wght@400;500;600&display=swap');

h1, h2, h3, .stTitle, .stSubheader {
    font-family: 'Cormorant Garamond', serif !important;
    letter-spacing: 0.3px;
}
html, body, [class*="css"] {
    font-family: 'Source Serif 4', serif !important;
}
h1 {
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(120,120,120,0.25);
    margin-bottom: 1rem;
    line-height: 1.2;
}
h2 {
    font-size: 1.8rem !important;
    font-weight: 600 !important;
    margin-top: 1.5rem !important;
}
div[data-testid="metric-container"] {
    border-radius: 18px;
    padding: 1rem;
    border: 1px solid rgba(120,120,120,0.18);
    background: rgba(80, 120, 160, 0.06);
    backdrop-filter: blur(4px);
}
div[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(120,120,120,0.15);
}
.stTextInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    border-radius: 12px !important;
    border: 1px solid rgba(120,120,120,0.2) !important;
}
span[data-baseweb="tag"] {
    background-color: #2f6f8f !important;
    color: white !important;
    border-radius: 6px !important;
}
span[data-baseweb="tag"] span {
    color: white !important;
}
.stButton > button {
    border-radius: 999px !important;
    border: none !important;
    background: linear-gradient(135deg, #2f6f8f, #4ba3a6) !important;
    color: white !important;
    font-family: 'Source Serif 4', serif !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.2rem !important;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    filter: brightness(1.05);
}
</style>
"""

st.markdown(css_base, unsafe_allow_html=True)

# ============================================================
# FUNÇÕES DE CACHE
# ============================================================
@st.cache_data
def carregar_e_cruzar_dados(lista_arquivos, pasta):
    df_consolidado = pd.DataFrame()
    for nome in lista_arquivos:
        caminho = os.path.join(pasta, nome)
        if not os.path.exists(caminho): continue
        xls = pd.ExcelFile(caminho)
        aba_mestra = 'geral' if 'geral' in xls.sheet_names else xls.sheet_names[0]
        df_mestra = pd.read_excel(xls, sheet_name=aba_mestra)
        df_mestra['Arquivo_origem'] = nome
        df_mestra['Título (Busca)'] = "[Título não localizado]"
        df_mestra['Conteúdo (Busca)'] = ""
        df_mestra['Data (Busca)'] = ""
        df_mestra['Notação (Busca)'] = ""
        
        col_ref = next((c for c in df_mestra.columns if 'código' in c.lower() or 'notação' in c.lower() or 'unidade' in c.lower()), None)
        if not col_ref: col_ref = df_mestra.columns[0]
            
        df_mestra[col_ref] = df_mestra[col_ref].astype(str).str.strip()
        abas_detalhe = [aba for aba in xls.sheet_names if aba.lower() not in ['geral', 'classificação']]
        
        for aba in abas_detalhe:
            aba_norm = re.sub(r'[\s\-_]', '', aba).lower()
            indices_mestra = []
            for idx, row in df_mestra.iterrows():
                cod_norm = re.sub(r'[\s\-_]', '', str(row[col_ref])).lower()
                if aba_norm in cod_norm or cod_norm in aba_norm:
                    indices_mestra.append(idx)
            
            if not indices_mestra: continue
                
            df_det = pd.read_excel(xls, sheet_name=aba)
            df_det = df_det.dropna(how='all')
            col_t = next((c for c in df_det.columns if 'título' in c.lower() or 'titulo' in c.lower()), None)
            col_c = next((c for c in df_det.columns if 'conteúdo' in c.lower() or 'assunto' in c.lower()), None)
            col_d = next((c for c in df_det.columns if 'data' in c.lower()), None)
            col_n = next((c for c in df_det.columns if 'referência' in c.lower() or 'notação' in c.lower() or 'código' in c.lower()), None)
            
            for i, idx_mestra in enumerate(indices_mestra):
                if i < len(df_det):
                    r_det = df_det.iloc[i]
                    t_val = str(r_det[col_t]).strip() if col_t and pd.notna(r_det[col_t]) else "[Título não localizado]"
                    c_val = str(r_det[col_c]).strip() if col_c and pd.notna(r_det[col_c]) else ""
                    d_val = str(r_det[col_d]).strip() if col_d and pd.notna(r_det[col_d]) else ""
                    n_val = str(r_det[col_n]).strip() if col_n and pd.notna(r_det[col_n]) else df_mestra.at[idx_mestra, col_ref]
                    if t_val == "" or t_val.lower() == "nan": t_val = "[Título não localizado]"
                    df_mestra.at[idx_mestra, 'Título (Busca)'] = t_val
                    df_mestra.at[idx_mestra, 'Conteúdo (Busca)'] = c_val
                    df_mestra.at[idx_mestra, 'Data (Busca)'] = d_val
                    df_mestra.at[idx_mestra, 'Notação (Busca)'] = n_val
                else:
                    df_mestra.at[idx_mestra, 'Notação (Busca)'] = df_mestra.at[idx_mestra, col_ref]

        df_consolidado = pd.concat([df_consolidado, df_mestra], ignore_index=True)
        
    if not df_consolidado.empty:
        df_consolidado = df_consolidado.loc[:, ~df_consolidado.columns.str.contains('^Unnamed')]
    return df_consolidado

@st.cache_data(ttl=3600)
def buscar_producao_autoras(api_token, lista_autoras):
    url_busca = "https://dataverse.fgv.br/api/search"
    headers = {"X-Dataverse-key": api_token} if api_token else {}
    resultados_unicos = {} 
    
    for autora in lista_autoras:
        params = {"q": f'authorName:"{autora}"', "type": "dataset", "per_page": 50}
        try:
            resposta = requests.get(url_busca, headers=headers, params=params)
            if resposta.status_code == 200:
                itens = resposta.json().get('data', {}).get('items', [])
                for item in itens:
                    identificador = item.get('global_id')
                    if identificador not in resultados_unicos:
                        resultados_unicos[identificador] = {
                            "Título da base": item.get('name', '[sem título]'),
                            "Autores": "; ".join(item.get('authors', [])),
                            "Identificador": identificador,
                            "Link de acesso": item.get('url')
                        }
        except Exception:
            continue
    return pd.DataFrame(list(resultados_unicos.values()))

# ============================================================
# CABEÇALHO DO PROGRAMA
# ============================================================
st.title(traduzir("Inventário e estatística das coleções do GPDVE"))
st.markdown(traduzir("Gestão e visualização transversal de metadados arquivísticos."))

st.caption(traduzir("O programa foi concebido para realizar análises estatísticas sobre bases de dados estruturadas e padronizadas, especificamente voltadas à catalogação e descrição arquivística de documentos, permitindo visualizações transversais de metadados e instrumentos de pesquisa."))

# ============================================================
# CRIAÇÃO DAS ABAS
# ============================================================
aba_inventario, aba_producao = st.tabs([traduzir("Inventário do acervo catalogado"), traduzir("Visão geral do acervo")])

# ============================================================
# ABA 1: INVENTÁRIO DO ACERVO
# ============================================================
with aba_inventario:
    
    dicionario_tematico = {
        "Família": ["mãe", "filho", "criança", "pai", "avó"],
        "Educação, artes e ofícios": ["escola", "alfabetização", "atividade cultural", "costura"],
        "Arquitetura prisional": ["grade", "cela", "janela", "parede", "portão"]
    }

    pasta_acervo = r"C:\Users\mille\OneDrive\Área de Trabalho\inventario_acervo"
    if not os.path.exists(pasta_acervo):
        st.error(f"Pasta não encontrada: {pasta_acervo}")
        st.stop()

    arquivos = [f for f in os.listdir(pasta_acervo) if f.lower().endswith(('.xlsx', '.xls'))]
    if not arquivos:
        st.error("Nenhum arquivo Excel encontrado na pasta.")
        st.stop()

    selecionados = st.multiselect(traduzir("Selecione as planilhas para integrar:"), arquivos, default=arquivos)
    if not selecionados:
        st.stop()

    df_consolidado = carregar_e_cruzar_dados(selecionados, pasta_acervo)

    st.subheader(traduzir("Busca avançada"))
    termo = st.text_input(traduzir("Pesquisar termo nas planilhas (ex: criança, portão, costura)"))
    df_filtrado = df_consolidado.copy()

    if termo:
        df_filtrado['SUPER_STRING'] = df_filtrado.apply(lambda row: ' '.join(row.dropna().astype(str)), axis=1)
        mask = df_filtrado['SUPER_STRING'].str.contains(termo, case=False, regex=False)
        df_filtrado = df_filtrado[mask].drop(columns=['SUPER_STRING'])

    st.subheader(traduzir("Filtros categoriais"))
    cols_int = ['Gênero documental', 'Espécie/Tipo documental', 'Técnica de registro', 'Arquivo_origem']
    cols_exist = [c for c in cols_int if c in df_consolidado.columns]

    dicionario_siglas = {
        "FOT": traduzir("Fotografia (FOT)"),
        "PLN": traduzir("Planta cartográfica (PLN)"),
        "DGZ": traduzir("Digitalizado (DGZ)"),
        "ICO": traduzir("Iconográfico (ICO)"),
        "MTO": traduzir("Meio magnético/ótico (MTO)"),
        "TXT": traduzir("Textual (TXT)")
    }

    filtros_selecionados = {}
    if cols_exist:
        l_cols = st.columns(len(cols_exist))
        for i, col in enumerate(cols_exist):
            with l_cols[i]:
                valores = [v for v in df_consolidado[col].dropna().unique() if "Unnamed" not in str(v)]
                filtros_selecionados[col] = st.multiselect(
                    f"{col}", 
                    sorted(valores), 
                    key=f"f_{col}",
                    format_func=lambda x: dicionario_siglas.get(str(x), str(x))
                )

    for col, sel in filtros_selecionados.items():
        if sel: df_filtrado = df_filtrado[df_filtrado[col].isin(sel)]

    st.subheader(traduzir("Indicadores"))
    col1, col2, col3 = st.columns(3)
    col1.metric(traduzir("Itens exibidos"), len(df_filtrado))
    if 'Gênero documental' in df_filtrado.columns: 
        col2.metric(traduzir("Gêneros documentais"), df_filtrado['Gênero documental'].nunique())
    
    df_metricas = df_filtrado.drop(columns=['Arquivo_origem', 'SUPER_STRING'], errors='ignore')
    df_metricas = df_metricas.replace(r'^\s*$', pd.NA, regex=True).replace("[Título não localizado]", pd.NA)
    total_metadados = df_metricas.notna().sum().sum()
    
    col3.metric(traduzir("Metadados indexados (total)"), total_metadados)

    st.subheader(traduzir("Análises e visualizações do acervo"))

    opcao_limpar = traduzir("Nenhuma visualização (limpar tela)")
    opcao_timeline = traduzir("Linha do tempo (distribuição cronológica)")
    opcoes_menu = [opcao_limpar, opcao_timeline] + list(dicionario_tematico.keys())

    visualizacao_selecionada = st.selectbox(traduzir("Escolha uma visualização ou eixo temático:"), opcoes_menu, index=1)

    if visualizacao_selecionada == opcao_timeline:
        df_datas = df_filtrado.copy()
        df_datas['Ano_Extraido'] = df_datas['Data (Busca)'].astype(str).str.extract(r'((?:18|19|20)\d{2})')
        df_anos = df_datas.dropna(subset=['Ano_Extraido'])

        if not df_anos.empty:
            contagem_anos = df_anos['Ano_Extraido'].value_counts().reset_index()
            contagem_anos.columns = ['Ano', 'Frequência']
            contagem_anos = contagem_anos.sort_values(by='Ano')
            
            fig_linha = px.line(
                contagem_anos, x='Ano', y='Frequência', markers=True, 
                color_discrete_sequence=['#4ba3a6']
            )
            fig_linha.update_layout(
                template='plotly_dark', 
                font=dict(family='Source Serif 4, serif', size=15),
                title=dict(text=traduzir("Frequência de datas grafadas nos documentos"), font=dict(family='Cormorant Garamond, serif', size=24)),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(title='', showgrid=False), yaxis=dict(title=traduzir("Volume documental"), gridcolor='rgba(120,120,120,0.15)')
            )
            fig_linha.update_traces(line=dict(width=3), marker=dict(size=8))
            st.plotly_chart(fig_linha, use_container_width=True)

    elif visualizacao_selecionada == opcao_limpar:
        pass 

    else:
        palavras_chave = dicionario_tematico[visualizacao_selecionada]
        texto_combinado = " ".join(df_filtrado['Conteúdo (Busca)'].dropna().astype(str).str.lower()) + " " + " ".join(df_filtrado['Título (Busca)'].dropna().astype(str).str.lower())
        contagem_termos = {palavra: texto_combinado.count(palavra.lower()) for palavra in palavras_chave}
        
        df_estatistica = pd.DataFrame(list(contagem_termos.items()), columns=['Termo do eixo', 'Frequência'])
        fig_tema = px.bar(
            df_estatistica, x='Termo do eixo', y='Frequência', text='Frequência',
            color='Frequência', color_continuous_scale=['#16324F', '#235789', '#2F6F8F', '#4BA3A6', '#7BC6CC']
        )
        fig_tema.update_traces(textposition='outside', marker_line_width=0)
        fig_tema.update_layout(
            template='plotly_dark', 
            font=dict(family='Source Serif 4, serif', size=15),
            title=dict(text=f"{traduzir('Distribuição estatística')} — {visualizacao_selecionada.lower()}", font=dict(family='Cormorant Garamond, serif', size=24)),
            coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title='', showgrid=False), yaxis=dict(title='', gridcolor='rgba(120,120,120,0.15)')
        )
        st.plotly_chart(fig_tema, use_container_width=True)

    st.subheader(traduzir("Visualização detalhada"))
    
    df_exibicao = df_filtrado.copy()
    df_exibicao.reset_index(drop=True, inplace=True)
    df_exibicao.index += 1
    
    st.dataframe(df_exibicao, use_container_width=True, height=350)

    st.subheader(traduzir("Instrumentos de pesquisa"))
    if st.button(traduzir("Gerar INVENTÁRIO DO ACERVO")):
        if df_filtrado.empty:
            st.warning("Não há registros para exportar com os filtros atuais.")
        else:
            doc = Document()
            doc.add_heading('INVENTÁRIO DO ACERVO', 0)
            doc.add_heading('Coleção: Arquivo Público do Estado de São Paulo (APESP)', level=1)
            grupos_arquivos = df_filtrado.groupby('Arquivo_origem')
            
            for arquivo_origem, df_grupo in grupos_arquivos:
                if "CPOS" in arquivo_origem.upper():
                    nome_sub, sub_tipo = "CPOS (Plantas e Obras Públicas)", "Acervo iconográfico"
                elif "DASP" in arquivo_origem.upper():
                    nome_sub, sub_tipo = "DASP (Fotografias)", "Acervo fotográfico"
                else:
                    nome_sub, sub_tipo = "Subconjunto documental", "Acervo iconográfico"
                    
                doc.add_heading(f'Subconjunto: {nome_sub}', level=1)
                col_h = next((c for c in df_grupo.columns if 'história' in c.lower() or 'historico' in c.lower()), None)
                if col_h and len(df_grupo[col_h].dropna().unique()) > 0:
                    hist_txt = str(df_grupo[col_h].dropna().unique()[0]).strip()
                    if hist_txt and hist_txt.lower() != "nan":
                        doc.add_heading('História arquivística', level=2)
                        doc.add_paragraph(hist_txt)
                
                doc.add_heading(sub_tipo, level=2)
                for idx, row in df_grupo.iterrows():
                    doc.add_heading(str(row.get('Título (Busca)', '[Título não localizado]')), level=3)
                    table = doc.add_table(rows=1, cols=2)
                    cells = table.rows[0].cells
                    c1 = cells[0].paragraphs[0]
                    c1.add_run("Características:\n").bold = True
                    c1.add_run(f"Gênero: {row.get('Gênero documental', '')}\nEspécie: {row.get('Espécie/Tipo documental', '')}\nTécnica: {row.get('Técnica de registro', '')}")
                    
                    c2 = cells[1].paragraphs[0]
                    cont_final, data_final = row.get('Conteúdo (Busca)', ''), row.get('Data (Busca)', '')
                    if cont_final: 
                        c2.add_run("Conteúdo:\n").bold = True
                        c2.add_run(str(cont_final) + "\n\n")
                    if data_final: 
                        c2.add_run("Data: ").bold = True
                        c2.add_run(str(data_final))
                    
                    p_not = doc.add_paragraph()
                    p_not.add_run("Notação: ").bold = True
                    p_not.add_run(str(row.get('Notação (Busca)', '')))
                    doc.add_paragraph("-" * 40)
                doc.add_page_break()
            doc.save("inventario_gpdve_final.docx")
            st.success("Documento exportado com sucesso.")

# ============================================================
# ABA 2: PRODUÇÃO INSTITUCIONAL E DADOS
# ============================================================
with aba_producao:
    st.subheader(traduzir("Observatório de bases publicadas pelo GPDVE no Dataverse"))
    st.markdown(traduzir("Listagem automatizada das publicações do GPDVE no FGV Dataverse."))
    
    meu_token_api = ""
    pesquisadoras_rastreadas = ["Machado, Maíra Rocha", "Ferreira, Carolina Cutrupi", "Tavolari, Bianca"]
    
    with st.spinner("Consultando o repositório... / Querying repository..."):
        df_producao = buscar_producao_autoras(meu_token_api, pesquisadoras_rastreadas)
    
    if not df_producao.empty:
        st.data_editor(
            df_producao,
            column_config={"Link de acesso": st.column_config.LinkColumn("Link de acesso")},
            hide_index=True,
            use_container_width=True
        )
    
    st.markdown("---")
    st.subheader(traduzir("Acervo documental digitalizado"))
    st.markdown(traduzir("Controle descritivo dos conjuntos documentais sob guarda ou análise do grupo."))
    
    dados_digitalizados = {
        "Fundo/coleção": ["APESP - cpos", "APESP - dasp", "outros documentos"],
        "Natureza do acervo": ["iconográfico (plantas)", "fotográfico", "textual"],
        "Formato digital": ["PDF / TIFF", "JPEG", "PDF"],
        "Status da digitalização": ["concluído", "em andamento", "pendente"]
    }
    st.dataframe(pd.DataFrame(dados_digitalizados), hide_index=True, use_container_width=True)

# ============================================================
# 7. RODAPÉ INSTITUCIONAL (FORA DAS ABAS)
# ============================================================
meses = ["jan.", "fev.", "mar.", "abr.", "maio", "jun.", "jul.", "ago.", "set.", "out.", "nov.", "dez."]
data_atual = datetime.now()
data_formatada = f"{data_atual.day} {meses[data_atual.month - 1]} {data_atual.year}"

rodape_html = f"""
<hr style="border-top: 1px solid rgba(120,120,120,0.25); margin: 40px 0 20px 0;">
<div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; font-family: 'Source Serif 4', serif; font-size: 0.95rem; color: var(--text-color);">
    <div style="flex: 1; min-width: 300px;">
        <h3 style="font-family: 'Cormorant Garamond', serif; font-weight: 700; font-size: 1.4rem; margin-bottom: 15px; border-bottom: none;">Créditos e equipe</h3>
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Autora:</strong> <a href="http://lattes.cnpq.br/3848824456283762" target="_blank" style="color: #4ba3a6; text-decoration: none;"><strong>Millena Miranda Franco</strong></a> | <a href="https://orcid.org/0000-0002-0292-0797" target="_blank" style="color: #4ba3a6;">ORCID</a> | <a href="https://bv.fapesp.br/pt/pesquisador/743339/millena-miranda-franco/" target="_blank" style="color: #4ba3a6;">BV FAPESP</a></p>
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Orientadora:</strong> <a href="http://lattes.cnpq.br/0553760669855058" target="_blank" style="color: #4ba3a6; text-decoration: none;"><strong>Maíra Rocha Machado</strong></a> | <a href="https://orcid.org/0000-0003-1303-5790" target="_blank" style="color: #4ba3a6;">ORCID</a> | <a href="https://bv.fapesp.br/pt/pesquisador/90750/maira-rocha-machado/" target="_blank" style="color: #4ba3a6;">BV FAPESP</a></p>
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Instituição-sede:</strong> Escola de Direito de São Paulo. Fundação Getulio Vargas (FGV). São Paulo, SP, Brasil</p>
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Grupo de pesquisa:</strong> Grupo de Pesquisa em Direito e Violência de Estado (GPDVE)</p>
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Fomento:</strong> Fundação de Amparo à Pesquisa do Estado de São Paulo (FAPESP)</p>
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Projeto:</strong> Organização e disponibilização pública de acervo documental envolvendo violência de Estado.</p>
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Processo:</strong> 25/11544-9</p>
    </div>
    <div style="display: flex; align-items: center; justify-content: flex-end; margin-top: 30px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/c/cf/Logo_FGV_-_Funda%C3%A7%C3%A3o_Getulio_Vargas.png" height="20" style="margin-right: 5px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Logo_fapesp_em_preto.svg/1280px-Logo_fapesp_em_preto.svg.png" height="25">
    </div>
</div>
<hr style="border-top: 1px solid rgba(120,120,120,0.25); margin: 20px 0;">
<div style="background: rgba(80, 120, 160, 0.06); padding: 15px; border-radius: 12px; border: 1px solid rgba(120,120,120,0.18);">
    <p style="margin: 0; font-family: 'Source Serif 4', serif; font-size: 0.95rem; color: var(--text-color);">FRANCO, Millena Miranda. Inventário e estatísticas das coleções do GPDVE: gestão e visualização transversal de metadados arquivísticos. São Paulo: Escola de Direito de São Paulo, Fundação Getulio Vargas (FGV), 2026. Programa de computador. Acesso em: {data_formatada}.</p>
</div>
"""
st.markdown(rodape_html, unsafe_allow_html=True)