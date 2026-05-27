import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re
import os
import requests
from bs4 import BeautifulSoup

st.set_page_config(layout="wide", page_title="Inventário e estatísticas do GPDVE")

# ============================================================
# SISTEMA DE SEGURANÇA (PORTA TRANCADA)
# ============================================================
def check_password():
    def password_entered():
        if st.session_state["input_senha"] == st.secrets["senha_porta"]:
            st.session_state["password_correct"] = True
            del st.session_state["input_senha"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h3 style='text-align: center; font-family: \"Cormorant Garamond\", serif; margin-top: 50px;'>Acesso restrito - GPDVE</h3>", unsafe_allow_html=True)
        st.text_input("Digite a senha de acesso para carregar o acervo:", type="password", on_change=password_entered, key="input_senha")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<h3 style='text-align: center; font-family: \"Cormorant Garamond\", serif; margin-top: 50px;'>Acesso restrito - GPDVE</h3>", unsafe_allow_html=True)
        st.text_input("Digite a senha de acesso para carregar o acervo:", type="password", on_change=password_entered, key="input_senha")
        st.error("Senha incorreta. Acesso negado.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ============================================================
# CONTROLES SUPERIORES E IDIOMA
# ============================================================
col_espaco, col_idioma = st.columns([8.5, 1.5])

with col_idioma:
    st.caption("Idioma / Language")
    idioma = st.selectbox("Seletor de idioma", ["Português", "English", "Español"], label_visibility="collapsed")

def traduzir(texto_pt):
    dicionario = {
        "Audiovisual (AVS)": {"English": "Audiovisual (AVS)", "Español": "Audiovisual (AVS)"},
        "Filmográfico (FLG)": {"English": "Filmographic (FLG)", "Español": "Filmográfico (FLG)"},
        "Filme (FME)": {"English": "Film (FME)", "Español": "Filme (FME)"},
        "Notícia (NOT)": {"English": "News (NOT)", "Español": "Noticia (NOT)"},
        "Relatório (REL)": {"English": "Report (REL)", "Español": "Relatorio (REL)"},
        "Nato-digital (NDG)": {"English": "Born-digital (NDG)", "Español": "Nato-digital (NDG)"},
        "Não determinado (NDT)": {"English": "Undetermined (NDT)", "Español": "No determinado (NDT)"},
        "Inventário e estatística das coleções do GPDVE": {"English": "Inventory and statistics of GPDVE collections", "Español": "Inventario y estadística de las colecciones del GPDVE"},
        "Gestão e visualização transversal de metadados arquivísticos.": {"English": "Management and transversal visualisation of archival metadata.", "Español": "Gestión y visualización transversal de metadatos archivísticos."},
        "Inventário do acervo catalogado": {"English": "Catalogued collection inventory", "Español": "Inventario del acervo catalogado"},
        "Visão geral do acervo": {"English": "Collection overview", "Español": "Visión general del acervo"},
        "Equipe e Observatório": {"English": "Team and Observatory", "Español": "Equipo y Observatorio"},
        "O programa foi concebido para realizar análises estatísticas sobre bases de dados estruturadas e padronizadas, especificamente voltadas à catalogação e descrição arquivística de documentos, permitindo visualizações transversais de metadados e instrumentos de pesquisa.": {"English": "The programme was designed to perform statistical analyses on structured and standardised databases, specifically aimed at the cataloguing and archival description of documents, allowing transversal visualisations of metadata and research instruments.", "Español": "El programa fue diseñado para realizar análisis estadísticos sobre bases de datos estructuradas y estandarizadas, específicamente dirigidas a la catalogación y descripción archivística de documentos, permitiendo visualizaciones transversales de metadatos e instrumentos de investigación."},
        "Observatório de bases publicadas pelo GPDVE no Dataverse": {"English": "Observatory of databases published by GPDVE on Dataverse", "Español": "Observatorio de bases de datos publicadas por GPDVE en Dataverse"},
        "Equipe do GPDVE": {"English": "GPDVE Team", "Español": "Equipo del GPDVE"},
        "Dados extraídos em tempo real da página oficial da FGV Direito SP.": {"English": "Data extracted in real-time from the official FGV Direito SP website.", "Español": "Datos extraídos en tiempo real de la página oficial de la FGV Direito SP."},
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
        "Gerar inventário do acervo": {"English": "Generate collection inventory", "Español": "Generar inventario del acervo"},
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
# ESTILOS (CSS BASE E RESPONSIVIDADE)
# ============================================================
css_base = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Source+Serif+4:wght@400;500;600&family=IBM+Plex+Mono:wght@500;600&display=swap');

.block-container { padding-top: 1.5rem !important; }
h1, h2, h3, .stTitle, .stSubheader { font-family: 'Cormorant Garamond', serif !important; letter-spacing: 0.3px; }
html, body, [class*="css"] { font-family: 'Source Serif 4', serif !important; }
h1 { font-size: 2.4rem !important; font-weight: 700 !important; padding-bottom: 0.4rem; border-bottom: 1px solid rgba(120,120,120,0.25); margin-bottom: 1rem; line-height: 1.2; }
div[data-testid="metric-container"] { border-radius: 18px; padding: 1rem; border: 1px solid rgba(120,120,120,0.18); background: rgba(80, 120, 160, 0.06); backdrop-filter: blur(4px); }
div[data-testid="stDataFrame"] { border-radius: 16px; overflow: hidden; border: 1px solid rgba(120,120,120,0.15); }
.stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stMultiSelect div[data-baseweb="select"] > div { border-radius: 12px !important; border: 1px solid rgba(120,120,120,0.2) !important; }
span[data-baseweb="tag"] { background-color: #2f6f8f !important; color: white !important; border-radius: 6px !important; }
span[data-baseweb="tag"] span { color: white !important; }
.stButton > button { border-radius: 999px !important; border: none !important; background: linear-gradient(135deg, #2f6f8f, #4ba3a6) !important; color: white !important; font-family: 'Source Serif 4', serif !important; font-weight: 600 !important; padding: 0.6rem 1.2rem !important; transition: all 0.2s ease; }
.stButton > button:hover { transform: translateY(-1px); filter: brightness(1.05); }

/* Estilização das Siglas e Códigos */
.sigla-codigo { font-family: 'IBM Plex Mono', monospace; color: #2F6F8F; font-weight: 600; font-size: 0.9em; background: rgba(47, 111, 143, 0.08); padding: 2px 5px; border-radius: 4px; }

/* CSS da Equipe - Ajustado para numeração e espaçamento */
.equipe-item { font-family: 'Source Serif 4', serif; letter-spacing: -0.2px; font-size: 1.05rem; line-height: 1.5; margin-bottom: 6px; }

/* Correções de Responsividade Mobile */
@media (max-width: 768px) {
    .block-container { padding-top: 1rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }
    h1 { font-size: 1.8rem !important; }
    div[data-testid="metric-container"] { padding: 0.8rem; }
    .hierarquia-grid { grid-template-columns: 1fr !important; }
}
</style>
"""
st.markdown(css_base, unsafe_allow_html=True)

# ============================================================
# FUNÇÕES DE EXTRAÇÃO, CACHE E WEBSCRAPING
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
        df_mestra['Notas (Busca)'] = ""
        
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
            col_notas = next((c for c in df_det.columns if 'nota' in c.lower()), None)
            
            for i, idx_mestra in enumerate(indices_mestra):
                if i < len(df_det):
                    r_det = df_det.iloc[i]
                    t_val = str(r_det[col_t]).strip() if col_t and pd.notna(r_det[col_t]) else "[Título não localizado]"
                    c_val = str(r_det[col_c]).strip() if col_c and pd.notna(r_det[col_c]) else ""
                    d_val = str(r_det[col_d]).strip() if col_d and pd.notna(r_det[col_d]) else ""
                    n_val = str(r_det[col_n]).strip() if col_n and pd.notna(r_det[col_n]) else df_mestra.at[idx_mestra, col_ref]
                    notas_val = str(r_det[col_notas]).strip() if col_notas and pd.notna(r_det[col_notas]) else ""
                    
                    df_mestra.at[idx_mestra, 'Título (Busca)'] = t_val if t_val.lower() != "nan" and t_val else "[Título não localizado]"
                    df_mestra.at[idx_mestra, 'Conteúdo (Busca)'] = c_val
                    df_mestra.at[idx_mestra, 'Data (Busca)'] = d_val
                    df_mestra.at[idx_mestra, 'Notação (Busca)'] = n_val
                    df_mestra.at[idx_mestra, 'Notas (Busca)'] = notas_val
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
        params = {"q": f'"{autora}"', "type": "dataset", "per_page": 100}
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

@st.cache_data(ttl=86400)
def extrair_equipe_fgv():
    url = "https://direitosp.fgv.br/grupos-de-pesquisa/grupo-pesquisa-direito-violencia-estado"
    equipe_extraida = []
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            textos = soup.stripped_strings
            capturando = False
            for text in textos:
                if text.strip().lower() == "equipe":
                    capturando = True
                    continue
                if capturando and text.strip().lower() in ["mídias", "projetos de pesquisa", "contato", "vídeo"]:
                    break
                if capturando:
                    if "(" in text and ")" in text: 
                        nome = text.split("(")[0].strip()
                        if nome and nome not in equipe_extraida:
                            equipe_extraida.append(nome)
        if not equipe_extraida:
            raise ValueError("Falha na extração de texto estruturado.")
        return equipe_extraida
    except Exception:
        return [
            "Maíra Rocha Machado", "Carolina Cutrupi Ferreira", "Luisa Moraes Abreu Ferreira",
            "Cecília Asperti", "Bianca Tavolari", "Roberta Canheo", "Ana Beatriz Passos",
            "Luisa Plastino", "Mariana Zambom", "Viviane Balbuglio", "Maria Eduarda de Castro",
            "Natalia Santana", "Luciano Pinheiro", "Iasmin Milfont", "Beatriz de Paula",
            "Cecília Moreira", "Maria Luiza Silva Oliveira", "Maurício Monteiro", "Millena Franco"
        ]

# ============================================================
# CABEÇALHO DO PROGRAMA
# ============================================================
st.title(traduzir("Inventário e estatística das coleções do GPDVE"))
st.markdown(traduzir("Gestão e visualização transversal de metadados arquivísticos."))
st.caption(traduzir("O programa foi concebido para realizar análises estatísticas sobre bases de dados estruturadas e padronizadas, especificamente voltadas à catalogação e descrição arquivística de documentos, permitindo visualizações transversais de metadados e instrumentos de pesquisa."))

# ============================================================
# CRIAÇÃO DAS ABAS
# ============================================================
aba_inventario, aba_producao, aba_equipe = st.tabs([
    traduzir("Inventário do acervo catalogado"), 
    traduzir("Visão geral do acervo"),
    traduzir("Equipe e Observatório")
])

# ============================================================
# ABA 1: INVENTÁRIO DO ACERVO
# ============================================================
with aba_inventario:
    dicionario_tematico = {
        "Família": ["mãe", "filho", "criança", "pai", "avó"],
        "Educação, artes e ofícios": ["escola", "alfabetização", "atividade cultural", "costura"],
        "Arquitetura prisional": ["grade", "cela", "janela", "parede", "portão"]
    }

    pasta_acervo = "."
    arquivos = [f for f in os.listdir(pasta_acervo) if f.lower().endswith(('.xlsx', '.xls'))]
    if not arquivos:
        st.warning("Nenhum arquivo Excel encontrado na pasta do sistema.")
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
        mask = df_filtrado['SUPER_STRING'].str.contains(rf'\b{termo}\b', case=False, regex=True)
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
        "TXT": traduzir("Textual (TXT)"),
        "AVS": traduzir("Audiovisual (AVS)"),
        "FLG": traduzir("Filmográfico (FLG)"),
        "FME": traduzir("Filme (FME)"),
        "NOT": traduzir("Notícia (NOT)"),
        "REL": traduzir("Relatório (REL)"),
        "NDG": traduzir("Nato-digital (NDG)"),
        "NDT": traduzir("Não determinado (NDT)")
    }

    filtros_selecionados = {}
    if cols_exist:
        l_cols = st.columns(len(cols_exist))
        selecoes_ativas = {c: st.session_state.get(f"f_{c}", []) for c in cols_exist}
        
        for i, col in enumerate(cols_exist):
            with l_cols[i]:
                df_opcoes = df_consolidado.copy()
                for o_col, sel_vals in selecoes_ativas.items():
                    if o_col != col and sel_vals:
                        df_opcoes = df_opcoes[df_opcoes[o_col].isin(sel_vals)]
                
                valores = [v for v in df_opcoes[col].dropna().unique() if "Unnamed" not in str(v)]
                
                filtros_selecionados[col] = st.multiselect(
                    f"{col}", 
                    sorted(valores), 
                    key=f"f_{col}",
                    format_func=lambda x: dicionario_siglas.get(str(x), str(x))
                )

    for col, sel in filtros_selecionados.items():
        if sel: 
            df_filtrado = df_filtrado[df_filtrado[col].isin(sel)]

    st.subheader(traduzir("Indicadores"))
    col1, col2, col3 = st.columns(3)
    col1.metric(traduzir("Itens exibidos"), len(df_filtrado))
    if 'Gênero documental' in df_filtrado.columns: 
        col2.metric(traduzir("Gêneros documentais"), df_filtrado['Gênero documental'].nunique())
    
    df_metricas = df_filtrado.drop(columns=['Arquivo_origem', 'SUPER_STRING'], errors='ignore')
    df_metricas = df_metricas.replace(r'^\s*$', pd.NA, regex=True).replace("[Título não localizado]", pd.NA)
    col3.metric(traduzir("Metadados indexados (total)"), df_metricas.notna().sum().sum())

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
             fig_linha = px.line(contagem_anos.sort_values(by='Ano'), x='Ano', y='Frequência', markers=True, color_discrete_sequence=['#4ba3a6'])
             fig_linha.update_layout(template='plotly_dark', font=dict(family='Source Serif 4, serif', size=15), title=dict(text=traduzir("Frequência de datas grafadas nos documentos"), font=dict(family='Cormorant Garamond, serif', size=24)), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(title='', showgrid=False), yaxis=dict(title=traduzir("Volume documental"), gridcolor='rgba(120,120,120,0.15)'))
             fig_linha.update_traces(line=dict(width=3), marker=dict(size=8))
             st.plotly_chart(fig_linha, use_container_width=True)

    elif visualizacao_selecionada != opcao_limpar:
        palavras_chave = dicionario_tematico[visualizacao_selecionada]
        texto_combinado = " ".join(df_consolidado['Conteúdo (Busca)'].dropna().astype(str).str.lower()) + " " + " ".join(df_consolidado['Título (Busca)'].dropna().astype(str).str.lower())
        
        contagem_termos = {}
        for palavra in palavras_chave:
            ocorrencias = len(re.findall(rf'\b{palavra.lower()}\b', texto_combinado))
            contagem_termos[palavra] = ocorrencias
        
        fig_tema = px.bar(pd.DataFrame(list(contagem_termos.items()), columns=['Termo', 'Frequência']), x='Termo', y='Frequência', text='Frequência', color='Frequência', color_continuous_scale=['#16324F', '#235789', '#2F6F8F', '#4BA3A6', '#7BC6CC'])
        fig_tema.update_traces(textposition='outside')
        fig_tema.update_layout(template='plotly_dark', font=dict(family='Source Serif 4, serif', size=15), title=dict(text=f"{traduzir('Distribuição estatística')} — {visualizacao_selecionada.lower()}", font=dict(family='Cormorant Garamond, serif', size=24)), coloraxis_showscale=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(title='', showgrid=False), yaxis=dict(title='', gridcolor='rgba(120,120,120,0.15)'))
        st.plotly_chart(fig_tema, use_container_width=True)

    st.subheader(traduzir("Visualização detalhada"))
    df_exibicao = df_filtrado.copy().reset_index(drop=True)
    df_exibicao.index += 1
    st.dataframe(df_exibicao, use_container_width=True, height=350)

    st.subheader(traduzir("Instrumentos de pesquisa"))
    
    tamanho_est_mb = max(0.01, len(df_filtrado['Arquivo_origem'].unique()) * 0.05)
    st.markdown(f"**Tamanho estimado do arquivo:** ~{tamanho_est_mb:.2f} MB")

    if st.button(traduzir("Gerar inventário do acervo")):
        if df_filtrado.empty:
            st.warning("Não há registros para exportar com os filtros atuais.")
        else:
            palavras_chave = dicionario_tematico[visualizacao_selecionada]
            texto_combinado = " ".join(df_consolidado['Conteúdo (Busca)'].dropna().astype(str).str.lower()) + " " + " ".join(df_consolidado['Título (Busca)'].dropna().astype(str).str.lower())
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

import streamlit_antd_components as sac

# ============================================================
# ABA 2: VISÃO GERAL DO ACERVO (SUBSTITUIÇÃO PELO COMPONENTE TREE)
# ============================================================
# O bloco HTML foi removido e substituído por estrutura nativa de árvore.
# Capitalização ajustada estritamente para PT-BR (siglas e nomes próprios).
# Emojis removidos.

with aba_producao:
    sac.tree(items=[
        sac.TreeItem('Coleção: Grupo de Pesquisa em Direito e Violência de Estado (GPDVE)', children=[
            sac.TreeItem('Série: Notícias (NOTICIAS)', children=[
                sac.TreeItem('Subsérie: Massacre do Carandiru', children=[
                    sac.TreeItem('Unidade documental: DVD original')
                ]),
                sac.TreeItem('BR-SPGPDVE_NOTICIAS-CSDTCARANDIRU_TXT-PNL-MT0_0001.xlsx') 
            ]),
            sac.TreeItem('Série: Filmes (FILMES)', children=[
                sac.TreeItem('Subsérie: Penitenciária do Estado em 1928'),
                sac.TreeItem('Subsérie: Direção de arte do filme Carandiru'),
                sac.TreeItem('Subsérie: Slideshow e charge "Recado da produção"'),
                sac.TreeItem('Subsérie: Bastidores do filme Carandiru'),
                sac.TreeItem('Subsérie: Filmes de Hector Babenco'),
                sac.TreeItem('Unidade documental: DVD original de documentários sobre o filme "Carandiru" e "Penitenciária do Estado 1928"'),
                sac.TreeItem('BR-SPGPDVE_FILMES-CSDTCARANDIRU_TXT-PNL-MT0_0001.xlsx')
            ]),
            sac.TreeItem('Série: Mapeamentos (MAPEAMENTOS)', children=[
                sac.TreeItem('Subsérie: Rememorações do massacre do Carandiru', children=[
                    sac.TreeItem('BR-SPGPDVE_MAPEAMENTOS-REMEMORA-CARANDIRU_TXT-PNL-MT0_0001.xlsx')
                ]),
                sac.TreeItem('Subsérie: Notícias massacre da Penha', children=[
                    sac.TreeItem('BR-SPGPDVE_MAPEAMENTOS-NOTICIAS-MSSCPENHA_TXT-PNL-MT0_0001.xlsx')
                ])
            ]),
            sac.TreeItem('Série: Arcoenge (ARCOENGE)', children=[
                sac.TreeItem('Subsérie: Demolição dos pavilhões 2 e 5 da Casa de Detenção do Carandiru'),
                sac.TreeItem('Subsérie: Demolição da Casa de Detenção do Carandiru (Penitenciária do Estado)', children=[
                    sac.TreeItem('Unidade documental: DVD original 2')
                ]),
                sac.TreeItem('BR-SPGPDVE_ARCOENGE-DEMOLICAO-CSDTCARANDIRU_TXT-PNL-MT0_0001.xlsx')
            ])
        ]),
        
        sac.TreeItem('Coleção: Arquivo Público do Estado de São Paulo (APESP)', children=[
            sac.TreeItem('Série: Companhia Paulista de Obras e Serviços (CPOS)', children=[
                sac.TreeItem('Subsérie: Planta do complexo do Carandiru'),
                sac.TreeItem('BR-SPAPESP_CPOS-PLNCARANDIRU_TXT-PNL-MT0_0001.xlsx')
            ]),
            sac.TreeItem('Série: Diários Associados do Estado de São Paulo (DASP)', children=[
                sac.TreeItem('Subsérie: Penitenciárias e presídios - Casa de Detenção do Carandiru'),
                sac.TreeItem('BR-SPAPESP_DASP-PENITPRE-CSDTCARANDIRU_TXT-PNL-MT0_0001.xlsx')
            ])
        ]),
        
        sac.TreeItem('Coleção: Procedimentos judiciais e administrativos (PROCJURADM)', children=[
            sac.TreeItem('Série: Tribunal de Justiça do Estado de São Paulo (TJSP)', children=[
                sac.TreeItem('Subsérie: Processo criminal contra 120 policiais militares (PROCRIM-POLMIL)'),
                sac.TreeItem('Subsérie: Sindicância da Corregedoria dos Presídios de 1992 (SINDIC-CORREGEDPRES)'),
                sac.TreeItem('Subsérie: Processos cíveis de indenização por danos materiais e morais (PROCCIVEL)')
            ]),
            sac.TreeItem('Série: Assembleia Legislativa do Estado de São Paulo (ALESP)', children=[
                sac.TreeItem('Subsérie: Comissão Parlamentar de Inquérito de 1992 (CPI)')
            ]),
            sac.TreeItem('Série: Ministério Público do Estado de São Paulo (MPSP)', children=[
                sac.TreeItem('Subsérie: Inquérito Civil Público de 1992 (INQCIVPUBLICO)')
            ]),
            sac.TreeItem('Série: Tribunal de Justiça Militar do Estado de São Paulo (TJMSP)', children=[
                sac.TreeItem('Subsérie: Sindicância Justiça Militar de 1992 (SINDIC-TJM)')
            ]),
            sac.TreeItem('Série: Ministério da Justiça (MINJUSTICA)', children=[
                sac.TreeItem('Subsérie: Relatório final do Conselho Nacional de Política Criminal e Penitenciária (RELFINAL-CNPCP)')
            ]),
            sac.TreeItem('Série: Conselho Municipal de Preservação do Patrimônio (CONPRESPSP)', children=[
                sac.TreeItem('Subsérie: Processo de tombamento (PROCTOM)')
            ])
        ])
    ], open_all=False) # Configurado como recolhido para melhor usabilidade na visualização

# ============================================================
# ABA 3: EQUIPE E OBSERVATÓRIO DATAVERSE
# ============================================================
with aba_equipe:
    st.subheader(traduzir("Equipe do GPDVE"))
    st.markdown(traduzir("Dados extraídos em tempo real da página oficial da FGV Direito SP."))
    
    with st.spinner("Extraindo informações da web..."):
        lista_equipe = extrair_equipe_fgv()
        
    # Lógica estruturada para distribuição exata de itens (6, 6, 7) e numeração sequencial
    colunas_equipe = st.columns(3)
    fatias_lista = [lista_equipe[:6], lista_equipe[6:12], lista_equipe[12:]]
    contador = 1
    
    for idx_coluna, st_col in enumerate(colunas_equipe):
        with st_col:
            for membro in fatias_lista[idx_coluna]:
                st.markdown(f"<div class='equipe-item'><strong>{contador}.</strong> {membro}</div>", unsafe_allow_html=True)
                contador += 1

    st.markdown("<br><hr>", unsafe_allow_html=True)
    
    st.subheader(traduzir("Observatório de bases publicadas pelo GPDVE no Dataverse"))
    st.markdown("Listagem automatizada das publicações institucionais das autoras do GPDVE.")
    
    meu_token_api = st.secrets["api_dataverse"]
    
    pesquisadoras_rastreadas = [
        "Machado, Maíra Rocha", 
        "Ferreira, Carolina Cutrupi",
        "Ferreira, Luisa Moraes Abreu",
        "Tavolari, Bianca",
        "Asperti, Cecília",
        "Canheo, Roberta",
        "Passos, Ana Beatriz",
        "Plastino, Luisa Mozetic",
        "Zambom, Mariana Morais",
        "Balbuglio, Balbuglio",
        "Castro, Maria Eduarda de",
        "Santos, Natália Santana dos",
        "Milfont, Iasmin",
        "Moreira, Maria Cecília",
        "Oliveira, Maria Luiza Silva",
        "Monteiro, Maurício",
        "Franco, Millena Miranda"
    ]
    
    with st.spinner("Consultando o repositório..."):
        df_producao = buscar_producao_autoras(meu_token_api, pesquisadoras_rastreadas)
    
    if not df_producao.empty:
        st.data_editor(
            df_producao,
            column_config={"Link de acesso": st.column_config.LinkColumn("Link de acesso")},
            hide_index=True,
            use_container_width=True
        )

# ============================================================
# RODAPÉ INSTITUCIONAL
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
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Grupo de pesquisa:</strong> Grupo de Pesquisa em Direito e Violência de Estado <span class="sigla-codigo">(GPDVE)</span></p>
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Fomento:</strong> Fundação de Amparo à Pesquisa do Estado de São Paulo <span class="sigla-codigo">(FAPESP)</span></p>
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Projeto:</strong> Organização e disponibilização pública de acervo documental envolvendo violência de Estado.</p>
        <p style="margin-bottom: 5px; line-height: 1.4;"><strong>Processo:</strong> 25/11544-9</p>
    </div>
    <div style="display: flex; align-items: center; justify-content: flex-end; margin-top: 30px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/c/cf/Logo_FGV_-_Funda%C3%A7%C3%A3o_Getulio_Vargas.png" height="20" style="margin-right: 5px;">
        <img src="https://fapesp.br/assets/img/logo-simple2.png" height="25">
    </div>
</div>
<hr style="border-top: 1px solid rgba(120,120,120,0.25); margin: 20px 0;">
<div style="background: rgba(80, 120, 160, 0.06); padding: 15px; border-radius: 12px; border: 1px solid rgba(120,120,120,0.18);">
    <p style="margin: 0; font-family: 'Source Serif 4', serif; font-size: 0.95rem; color: var(--text-color);">FRANCO, Millena Miranda. Inventário e estatísticas das coleções do GPDVE: gestão e visualização transversal de metadados arquivísticos. São Paulo: Escola de Direito de São Paulo, Fundação Getulio Vargas (FGV), 2026. Programa de computador. Acesso em: {data_formatada}.</p>
</div>
"""
st.markdown(rodape_html, unsafe_allow_html=True)