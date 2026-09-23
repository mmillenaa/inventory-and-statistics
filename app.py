import os
import re
import unicodedata
from datetime import datetime

import matplotlib.pyplot as plt
import nltk
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
import streamlit_antd_components as sac  # noqa: F401  (mantido conforme original)
from bs4 import BeautifulSoup
from nltk.stem import RSLPStemmer
from wordcloud import WordCloud


# ============================================================
# RECURSOS CACHEADOS E FUNÇÕES UTILITÁRIAS
# ============================================================
@st.cache_resource
def get_stemmer():
    """Baixa o recurso RSLP uma única vez e devolve o stemmer."""
    nltk.download("rslp", quiet=True)
    return RSLPStemmer()


def normalizar_texto(texto, stemmer):
    """Remove acentos, converte para minúsculo e aplica stemming."""
    if not isinstance(texto, str):
        return ""
    texto = (
        unicodedata.normalize("NFKD", texto)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )
    texto = texto.lower()
    palavras = re.findall(r"\b[a-zA-Záéíóúâêôãõç]+\b", texto)
    palavras_stem = [stemmer.stem(p) for p in palavras]
    return " ".join(palavras_stem)


def norm_nome_arquivo(nome):
    """Normaliza nomes de arquivo para matching tolerante a variações.

    Remove: caracteres invisíveis (LTR/RTL marks, ZWSP, BOM), acentos,
    extensões, espaços, hífens e underscores.
    """
    if not isinstance(nome, str):
        return ""
    # Remove caracteres invisíveis de controle de direção / largura zero
    nome = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]", "", nome)
    # Remove acentos
    nome = (
        unicodedata.normalize("NFKD", nome)
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )
    nome = nome.lower().strip()
    # Remove extensão .xls / .xlsx
    nome = re.sub(r"\.xlsx?$", "", nome)
    # Remove separadores
    nome = re.sub(r"[\s\-_]+", "", nome)
    return nome


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    layout="wide",
    page_title="Inventário e estatísticas de coleções",
)


# ============================================================
# SISTEMA DE SEGURANÇA (PORTA TRANCADA)
# ============================================================
def check_password():
    def password_entered():
        if st.session_state.get("input_senha") == st.secrets["senha_porta"]:
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    titulo_login = (
        "<h3 style='text-align: center; "
        "font-family: \"Cormorant Garamond\", serif; margin-top: 50px;'>"
        "Acesso restrito - GPDVE</h3>"
    )

    if "password_correct" not in st.session_state:
        st.markdown(titulo_login, unsafe_allow_html=True)
        st.text_input(
            "Digite a senha de acesso para carregar o acervo:",
            type="password",
            on_change=password_entered,
            key="input_senha",
        )
        return False

    if not st.session_state["password_correct"]:
        st.markdown(titulo_login, unsafe_allow_html=True)
        st.text_input(
            "Digite a senha de acesso para carregar o acervo:",
            type="password",
            on_change=password_entered,
            key="input_senha",
        )
        st.error("Senha incorreta. Acesso negado.")
        return False

    return True


# ============================================================
# CONTROLES SUPERIORES E IDIOMA
# ============================================================
col_espaco, col_idioma = st.columns([8.5, 1.5])

with col_idioma:
    st.caption("Idioma / Language")
    idioma = st.selectbox(
        "Seletor de idioma",
        ["Português", "English", "Español"],
        label_visibility="collapsed",
    )


def traduzir(texto_pt):
    dicionario = {
        "Audiovisual (AVS)": {
            "English": "Audiovisual (AVS)",
            "Español": "Audiovisual (AVS)",
        },
        "Filmográfico (FLG)": {
            "English": "Filmographic (FLG)",
            "Español": "Filmográfico (FLG)",
        },
        "Filme (FME)": {"English": "Film (FME)", "Español": "Filme (FME)"},
        "Notícia (NOT)": {"English": "News (NOT)", "Español": "Noticia (NOT)"},
        "Relatório (REL)": {"English": "Report (REL)", "Español": "Relatorio (REL)"},
        "Nato-digital (NDG)": {
            "English": "Born-digital (NDG)",
            "Español": "Nato-digital (NDG)",
        },
        "Não determinado (NDT)": {
            "English": "Undetermined (NDT)",
            "Español": "No determinado (NDT)",
        },
        "Inventário e estatística de coleções em Direito e Violência de Estado": {
            "English": (
                "Inventory and statistics of collections about Law and state violence"
            ),
            "Español": (
                "Inventario y estadística de las colecciones en derecho "
                "y violencia de estado"
            ),
        },
        "Gestão e visualização transversal de metadados arquivísticos.": {
            "English": (
                "Management and transversal visualisation of archival metadata."
            ),
            "Español": (
                "Gestión y visualización transversal de metadatos archivísticos."
            ),
        },
        "Inventário do acervo catalogado": {
            "English": "Catalogued collection inventory",
            "Español": "Inventario del acervo catalogado",
        },
        "Iniciativas de Rememoração": {
            "English": "Remembrance Initiatives",
            "Español": "Iniciativas de Rememoración",
        },
        "Visão geral do acervo": {
            "English": "Collection overview",
            "Español": "Visión general del acervo",
        },
        "Equipe e observatório": {
            "English": "Team and Observatory",
            "Español": "Equipo y Observatorio",
        },
        "O programa foi concebido para realizar análises estatísticas sobre bases de dados estruturadas e padronizadas, especificamente voltadas à catalogação e descrição arquivística de documentos, permitindo visualizações transversais de metadados e instrumentos de pesquisa.": {
            "English": (
                "The programme was designed to perform statistical analyses "
                "on structured and standardised databases, specifically aimed "
                "at the cataloguing and archival description of documents, "
                "allowing transversal visualisations of metadata and research "
                "instruments."
            ),
            "Español": (
                "El programa fue diseñado para realizar análisis estadísticos "
                "sobre bases de datos estructuradas y estandarizadas, "
                "específicamente dirigidas a la catalogación y descripción "
                "archivística de documentos, permitiendo visualizaciones "
                "transversales de metadatos e instrumentos de investigación."
            ),
        },
        "Observatório de bases publicadas pelo GPDVE no Dataverse": {
            "English": "Observatory of databases published by GPDVE on Dataverse",
            "Español": (
                "Observatorio de bases de datos publicadas por GPDVE en Dataverse"
            ),
        },
        "Equipe do GPDVE": {"English": "GPDVE Team", "Español": "Equipo del GPDVE"},
        "Dados extraídos em tempo real da página oficial da FGV Direito SP.": {
            "English": (
                "Data extracted in real-time from the official FGV Direito SP "
                "website."
            ),
            "Español": (
                "Datos extraídos en tiempo real de la página oficial de la "
                "FGV Direito SP."
            ),
        },
        "Busca avançada": {"English": "Advanced search", "Español": "Búsqueda avanzada"},
        "Pesquisar termo nas planilhas (ex: criança, portão, costura)": {
            "English": (
                "Search term in spreadsheets (e.g., child, gate, sewing)"
            ),
            "Español": (
                "Buscar término en hojas de cálculo (ej: niño, puerta, costura)"
            ),
        },
        "Busca avançada por termo (ex: podcast, exposição, filme)": {
            "English": (
                "Advanced search by term (e.g.: podcast, exhibition, film)"
            ),
            "Español": (
                "Búsqueda avanzada por término (ej: podcast, exposición, película)"
            ),
        },
        "Filtros categoriais": {
            "English": "Categorical filters",
            "Español": "Filtros categóricos",
        },
        "Selecione as planilhas do acervo para integrar:": {
            "English": "Select the collection spreadsheets to integrate:",
            "Español": "Seleccione las hojas de la colección a integrar:",
        },
        "Selecione as planilhas de rememoração:": {
            "English": "Select the remembrance spreadsheets:",
            "Español": "Seleccione las hojas de rememoración:",
        },
        "Indicadores": {"English": "Metrics", "Español": "Indicadores"},
        "Itens exibidos": {
            "English": "Displayed items",
            "Español": "Elementos mostrados",
        },
        "Gêneros documentais": {
            "English": "Documentary genres",
            "Español": "Géneros documentales",
        },
        "Metadados indexados (total)": {
            "English": "Indexed metadata (total)",
            "Español": "Metadatos indexados (total)",
        },
        "Total de iniciativas mapeadas": {
            "English": "Total mapped initiatives",
            "Español": "Total de iniciativas mapeadas",
        },
        "Análises e visualizações do acervo": {
            "English": "Analyses and visualisations of the collection",
            "Español": "Análisis y visualizaciones de la colección",
        },
        "Escolha uma visualização ou eixo temático:": {
            "English": "Choose a visualisation or thematic axis:",
            "Español": "Elija una visualización o eje temático:",
        },
        "Nenhuma visualização (limpar tela)": {
            "English": "No visualisation (clear screen)",
            "Español": "Ninguna visualización (limpiar pantalla)",
        },
        "Linha do tempo (distribuição cronológica)": {
            "English": "Timeline (chronological distribution)",
            "Español": "Línea de tiempo (distribución cronológica)",
        },
        "Linha do tempo": {
            "English": "Timeline",
            "Español": "Línea de tiempo",
        },
        "Frequência de datas grafadas nos documentos": {
            "English": "Frequency of dates written in documents",
            "Español": "Frecuencia de fechas escritas en los documentos",
        },
        "Volume documental": {
            "English": "Documentary volume",
            "Español": "Volumen documental",
        },
        "Distribuição estatística": {
            "English": "Statistical distribution",
            "Español": "Distribución estadística",
        },
        "Visualização detalhada": {
            "English": "Detailed view",
            "Español": "Vista detallada",
        },
        "Instrumentos de pesquisa": {
            "English": "Research instruments",
            "Español": "Instrumentos de investigación",
        },
        "Acervo documental digitalizado": {
            "English": "Digitised documentary collection",
            "Español": "Colección documental digitalizada",
        },
        "Controle descritivo dos conjuntos documentais sob guarda ou análise do grupo.": {
            "English": (
                "Descriptive control of documentary sets under custody or "
                "analysis by the group."
            ),
            "Español": (
                "Control descriptivo de los conjuntos documentales bajo "
                "custodia o análisis del grupo."
            ),
        },
        "Fotografia (FOT)": {"English": "Photography (FOT)", "Español": "Fotografía (FOT)"},
        "Planta cartográfica (PLN)": {
            "English": "Cartographic plan (PLN)",
            "Español": "Planta cartográfica (PLN)",
        },
        "Digitalizado (DGZ)": {"English": "Digitised (DGZ)", "Español": "Digitalizado (DGZ)"},
        "Iconográfico (ICO)": {
            "English": "Iconographic (ICO)",
            "Español": "Iconográfico (ICO)",
        },
        "Meio magnético/ótico (MTO)": {
            "English": "Magnetic/optical media (MTO)",
            "Español": "Medio magnético/óptico (MTO)",
        },
        "Textual (TXT)": {"English": "Textual (TXT)", "Español": "Textual (TXT)"},
        "Descrição não disponível para esta planilha.": {
            "English": "Description not available for this spreadsheet.",
            "Español": "Descripción no disponible para esta hoja de cálculo.",
        },
        "Nenhum arquivo Excel encontrado na pasta do sistema.": {
            "English": "No Excel file found in the system folder.",
            "Español": "No se encontró ningún archivo Excel en la carpeta del sistema.",
        },
        "Não há vocabulário útil suficiente nos itens filtrados para gerar a nuvem de palavras. Tente remover alguns filtros.": {
            "English": (
                "There is not enough useful vocabulary in the filtered items "
                "to generate the word cloud. Try removing some filters."
            ),
            "Español": (
                "No hay vocabulario útil suficiente en los elementos filtrados "
                "para generar la nube de palabras. Intente eliminar algunos "
                "filtros."
            ),
        },
        "Listagem automatizada das publicações institucionais das autoras do GPDVE.": {
            "English": (
                "Automated listing of institutional publications by GPDVE "
                "researchers."
            ),
            "Español": (
                "Listado automatizado de las publicaciones institucionales de "
                "las autoras del GPDVE."
            ),
        },
        "Extraindo informações da web...": {
            "English": "Extracting information from the web...",
            "Español": "Extrayendo información de la web...",
        },
        "Consultando o repositório...": {
            "English": "Querying the repository...",
            "Español": "Consultando el repositorio...",
        },
        "Acesso restrito - GPDVE": {
            "English": "Restricted access - GPDVE",
            "Español": "Acceso restringido - GPDVE",
        },
        "Digite a senha de acesso para carregar o acervo:": {
            "English": "Enter the access password to load the collection:",
            "Español": "Introduzca la contraseña de acceso para cargar el acervo:",
        },
        "Senha incorreta. Acesso negado.": {
            "English": "Incorrect password. Access denied.",
            "Español": "Contraseña incorrecta. Acceso denegado.",
        },
        "Nuvem de palavras (título e conteúdo)": {
            "English": "Word cloud (title and content)",
            "Español": "Nube de palabras (título y contenido)",
        },
        "Nuvem de palavras": {
            "English": "Word cloud",
            "Español": "Nube de palabras",
        },
        "Família": {"English": "Family", "Español": "Familia"},
        "Educação, artes e ofícios": {
            "English": "Education, arts and crafts",
            "Español": "Educación, artes y oficios",
        },
        "Arquitetura prisional": {
            "English": "Prison architecture",
            "Español": "Arquitectura penitenciaria",
        },
        "Gênero documental": {
            "English": "Documentary genre",
            "Español": "Género documental",
        },
        "Espécie/Tipo documental": {
            "English": "Documentary species/type",
            "Español": "Especie/Tipo documental",
        },
        "Técnica de registro": {
            "English": "Recording technique",
            "Español": "Técnica de registro",
        },
        "Arquivo_origem": {"English": "Source file", "Español": "Archivo de origen"},
        "Sem descrição cadastrada para:": {
            "English": "No description registered for:",
            "Español": "Sin descripción registrada para:",
        },
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
h1, h2, h3, .stTitle, .stSubheader {
    font-family: 'Cormorant Garamond', serif !important;
    letter-spacing: 0.3px;
}
html, body, [class*="css"] { font-family: 'Source Serif 4', serif !important; }
h1 {
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    padding-bottom: 0.4rem;
    border-bottom: 1px solid rgba(120,120,120,0.25);
    margin-bottom: 1rem;
    line-height: 1.2;
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
span[data-baseweb="tag"] span { color: white !important; }
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
.stButton > button:hover { transform: translateY(-1px); filter: brightness(1.05); }

/* Estilização das Siglas e Códigos */
.sigla-codigo {
    font-family: 'IBM Plex Mono', monospace;
    color: #2F6F8F;
    font-weight: 600;
    font-size: 0.9em;
    background: rgba(47, 111, 143, 0.08);
    padding: 2px 5px;
    border-radius: 4px;
}

/* CSS da Equipe */
.equipe-item {
    font-family: 'Source Serif 4', serif;
    letter-spacing: -0.2px;
    font-size: 1.05rem;
    line-height: 1.5;
    margin-bottom: 6px;
}

/* Correções de Responsividade Mobile */
@media (max-width: 768px) {
    .block-container {
        padding-top: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    h1 { font-size: 1.8rem !important; }
    div[data-testid="metric-container"] { padding: 0.8rem; }
    .hierarquia-grid { grid-template-columns: 1fr !important; }
}

/* Descrições inline das planilhas selecionadas */
.desc-lista {
    font-family: 'Source Serif 4', serif;
    font-size: 0.875rem;
    line-height: 1.55;
    margin-top: 2px;
    margin-bottom: 18px;
    color: rgba(250, 250, 250, 0.72);
    text-align: justify;
}
.desc-nome {
    font-family: 'IBM Plex Mono', monospace;
    color: #7BC6CC;
    font-weight: 600;
    font-size: 0.94em;
}
</style>
"""
st.markdown(css_base, unsafe_allow_html=True)


# ============================================================
# FUNÇÕES DE EXTRAÇÃO E CACHE (Acervo e Iniciativas)
# ============================================================
@st.cache_data
def carregar_e_cruzar_dados(lista_arquivos, pasta):
    """Consolida planilhas Excel cruzando a aba mestra com as abas de detalhe."""
    # MANTIDO 100% INTACTO CONFORME O SEU CÓDIGO ORIGINAL
    def norm_col(texto):
        return (
            unicodedata.normalize("NFKD", str(texto))
            .encode("ASCII", "ignore")
            .decode("utf-8")
            .lower()
        )

    df_consolidado = pd.DataFrame()

    for nome in lista_arquivos:
        caminho = os.path.join(pasta, nome)
        if not os.path.exists(caminho):
            continue

        xls = pd.ExcelFile(caminho)
        aba_mestra = "geral" if "geral" in xls.sheet_names else xls.sheet_names[0]
        df_mestra = pd.read_excel(xls, sheet_name=aba_mestra)
        df_mestra["Arquivo_origem"] = nome
        df_mestra["Título (Busca)"] = "[Título não localizado]"
        df_mestra["Conteúdo (Busca)"] = ""
        df_mestra["Data (Busca)"] = ""
        df_mestra["Notação (Busca)"] = ""
        df_mestra["Notas (Busca)"] = ""

        col_ref = next(
            (
                c
                for c in df_mestra.columns
                if "codigo" in norm_col(c)
                or "notacao" in norm_col(c)
                or "unidade" in norm_col(c)
            ),
            None,
        )
        if not col_ref:
            col_ref = df_mestra.columns[0]

        df_mestra[col_ref] = df_mestra[col_ref].astype(str).str.strip()
        df_mestra[col_ref] = df_mestra[col_ref].str.replace(
            r"^[\=\-\+\@]\s*", "", regex=True
        )
        df_mestra[col_ref] = df_mestra[col_ref].replace("#NOME?", "")

        abas_detalhe = []
        for aba in xls.sheet_names:
            aba_sem_acento = norm_col(aba)
            if aba_sem_acento not in ["geral", "classificacao"]:
                abas_detalhe.append(aba)

        for aba in abas_detalhe:
            aba_norm = re.sub(r"[\s\-_]", "", aba).lower()

            indices_mestra = []
            for idx, row in df_mestra.iterrows():
                cod_norm = re.sub(r"[\s\-_]", "", str(row[col_ref])).lower()
                if aba_norm in cod_norm or cod_norm in aba_norm:
                    indices_mestra.append(idx)

            if not indices_mestra:
                continue

            df_det = pd.read_excel(xls, sheet_name=aba)
            df_det = df_det.dropna(how="all")

            col_t = next((c for c in df_det.columns if "titulo" in norm_col(c)), None)
            col_c = next((c for c in df_det.columns if "conteudo" in norm_col(c) or "assunto" in norm_col(c)), None)
            col_d = next((c for c in df_det.columns if "data" in norm_col(c)), None)
            col_n = next((c for c in df_det.columns if "referencia" in norm_col(c) or "notacao" in norm_col(c) or "codigo" in norm_col(c) or "cod" in norm_col(c)), None)
            col_notas = next((c for c in df_det.columns if "nota" in norm_col(c) or "condicoes" in norm_col(c) or "observacao" in norm_col(c)), None)

            for i, idx_mestra in enumerate(indices_mestra):
                if i < len(df_det):
                    r_det = df_det.iloc[i]
                    t_val = str(r_det[col_t]).strip() if col_t and pd.notna(r_det[col_t]) else "[Título não localizado]"
                    c_val = str(r_det[col_c]).strip() if col_c and pd.notna(r_det[col_c]) else ""
                    d_val = str(r_det[col_d]).strip() if col_d and pd.notna(r_det[col_d]) else ""
                    n_val = str(r_det[col_n]).strip() if col_n and pd.notna(r_det[col_n]) else df_mestra.at[idx_mestra, col_ref]
                    notas_val = str(r_det[col_notas]).strip() if col_notas and pd.notna(r_det[col_notas]) else ""

                    df_mestra.at[idx_mestra, "Título (Busca)"] = t_val if t_val.lower() != "nan" and t_val else "[Título não localizado]"
                    df_mestra.at[idx_mestra, "Conteúdo (Busca)"] = c_val
                    df_mestra.at[idx_mestra, "Data (Busca)"] = d_val
                    df_mestra.at[idx_mestra, "Notação (Busca)"] = n_val
                    df_mestra.at[idx_mestra, "Notas (Busca)"] = notas_val
                else:
                    df_mestra.at[idx_mestra, "Notação (Busca)"] = df_mestra.at[idx_mestra, col_ref]

        df_consolidado = pd.concat([df_consolidado, df_mestra], ignore_index=True)

    if not df_consolidado.empty:
        df_consolidado = df_consolidado.loc[:, ~df_consolidado.columns.str.contains("^Unnamed")]

    return df_consolidado


@st.cache_data
def carregar_iniciativas(lista_arquivos, pasta):
    """Novo leitor leve, focado exclusivamente nas colunas de iniciativas."""
    linhas = []
    
    def clean_col(c):
        if pd.isna(c): return ""
        return unicodedata.normalize('NFKD', str(c)).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

    for nome in lista_arquivos:
        caminho = os.path.join(pasta, nome)
        if not os.path.exists(caminho): continue
        
        xls = pd.ExcelFile(caminho)
        aba = 'Geral' if 'Geral' in xls.sheet_names else ('geral' if 'geral' in xls.sheet_names else xls.sheet_names[0])
        df = pd.read_excel(xls, sheet_name=aba)
        
        cols_norm = {c: clean_col(c) for c in df.columns}
        
        # Mapeamento para as colunas exatas exigidas do vocabulário controlado
        col_inic = next((c for c in df.columns if 'nome da iniciativa' in cols_norm[c] or 'iniciativa' in cols_norm[c]), None)
        col_int = next((c for c in df.columns if 'intervencao' in cols_norm[c]), None)
        col_abr = next((c for c in df.columns if 'abrangencia' in cols_norm[c]), None)
        col_mod = next((c for c in df.columns if 'modalidade' in cols_norm[c]), None)
        col_ano = next((c for c in df.columns if 'ano' in cols_norm[c] or 'data' in cols_norm[c]), None)
        
        # Mapeia a coluna de Título que nos MAPEMENTOS está como "02 de outubro", "penha" ou "titulo"
        col_tit = next((c for c in df.columns if '02 de outubro' in cols_norm[c] or 'penha' in cols_norm[c] or 'titulo' in cols_norm[c]), None)
        
        for _, r in df.iterrows():
            t = str(r[col_tit]).strip() if col_tit and pd.notna(r[col_tit]) else ''
            inic = str(r[col_inic]).strip() if col_inic and pd.notna(r[col_inic]) else ''
            
            if (not t or t.lower() in ['nan', 'none']) and (not inic or inic.lower() in ['nan', 'none']):
                continue
                
            linhas.append({
                'Arquivo_origem': nome,
                'Nome da iniciativa': inic,
                'Intervenção': str(r[col_int]).strip() if col_int and pd.notna(r[col_int]) else '',
                'Abrangência': str(r[col_abr]).strip() if col_abr and pd.notna(r[col_abr]) else '',
                'Modalidade': str(r[col_mod]).strip() if col_mod and pd.notna(r[col_mod]) else '',
                'Ano': str(r[col_ano]).strip() if col_ano and pd.notna(r[col_ano]) else '',
                'Título': t
            })
            
    return pd.DataFrame(linhas)


@st.cache_data(ttl=3600)
def buscar_producao_autoras(api_tokens, lista_autoras):
    resultados_unicos = {}

    if isinstance(api_tokens, str):
        api_tokens = [api_tokens]

    for autora in lista_autoras:
        partes = autora.split(", ")
        if len(partes) == 2:
            nome_invertido = f"{partes[1]} {partes[0]}"
        else:
            nome_invertido = autora

        queries_scielo = [
            f'"{autora}"',
            f'"{nome_invertido}"',
            f'author:"{autora}"',
            f'author:"{nome_invertido}"',
            autora,
            nome_invertido,
        ]

        for token in api_tokens:
            headers = {"X-Dataverse-key": token} if token else {}
            url_fgv = "https://dataverse.fgv.br/api/search"
            params_fgv = {
                "q": f'"{autora}"',
                "type": "dataset",
                "per_page": 100,
            }
            try:
                res_fgv = requests.get(url_fgv, headers=headers, params=params_fgv)
                if res_fgv.status_code == 200:
                    itens = res_fgv.json().get("data", {}).get("items", [])
                    for item in itens:
                        ident = item.get("global_id")
                        if ident and ident not in resultados_unicos:
                            resultados_unicos[ident] = {
                                "Título da base": item.get(
                                    "name", "[sem título]"
                                ),
                                "Autores": (
                                    "; ".join(item.get("authors", []))
                                    if isinstance(item.get("authors"), list)
                                    else str(item.get("authors", ""))
                                ),
                                "Identificador": ident,
                                "Link de acesso": item.get("url", ""),
                            }
            except Exception:
                pass

        url_scielo = "https://data.scielo.org/api/search"
        encontrou = False
        for q in queries_scielo:
            if encontrou:
                break
            params_scielo = {"q": q, "type": "dataset", "per_page": 100}
            try:
                res_scielo = requests.get(url_scielo, params=params_scielo)
                if res_scielo.status_code == 200:
                    itens = res_scielo.json().get("data", {}).get("items", [])
                    if itens:
                        for item in itens:
                            ident = item.get("global_id")
                            if ident and ident not in resultados_unicos:
                                autores_raw = item.get("authors", [])
                                if isinstance(autores_raw, list):
                                    autores_str = "; ".join(autores_raw)
                                else:
                                    autores_str = (
                                        str(autores_raw) if autores_raw else ""
                                    )
                                resultados_unicos[ident] = {
                                    "Título da base": item.get(
                                        "name", "[sem título]"
                                    ),
                                    "Autores": autores_str,
                                    "Identificador": ident,
                                    "Link de acesso": item.get("url", ""),
                                }
                        encontrou = True
            except Exception:
                pass

    return pd.DataFrame(list(resultados_unicos.values()))


@st.cache_data(ttl=86400)
def extrair_equipe_fgv():
    url = (
        "https://direitosp.fgv.br/grupos-de-pesquisa/"
        "grupo-pesquisa-direito-violencia-estado"
    )
    equipe_extraida = []
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            textos = soup.stripped_strings
            capturando = False
            for text in textos:
                if text.strip().lower() == "equipe":
                    capturando = True
                    continue
                if capturando and text.strip().lower() in [
                    "mídias",
                    "projetos de pesquisa",
                    "contato",
                    "vídeo",
                ]:
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
            "Maíra Rocha Machado",
            "Carolina Cutrupi Ferreira",
            "Luisa Moraes Abreu Ferreira",
            "Cecília Asperti",
            "Bianca Tavolari",
            "Roberta Canheo",
            "Ana Beatriz Passos",
            "Luisa Plastino",
            "Mariana Zambom",
            "Viviane Balbuglio",
            "Maria Eduarda de Castro",
            "Natalia Santana",
            "Luciano Pinheiro",
            "Iasmin Milfont",
            "Beatriz de Paula",
            "Cecília Moreira",
            "Maria Luiza Silva Oliveira",
            "Maurício Monteiro",
            "Millena Franco",
        ]


# ============================================================
# CABEÇALHO DO PROGRAMA E DEFINIÇÕES GLOBAIS
# ============================================================
st.title(
    traduzir(
        "Inventário e estatística de coleções em Direito e Violência de Estado"
    )
)
st.markdown(traduzir("Gestão e visualização transversal de metadados arquivísticos."))
st.caption(
    traduzir(
        "O programa foi concebido para realizar análises estatísticas sobre "
        "bases de dados estruturadas e padronizadas, especificamente voltadas "
        "à catalogação e descrição arquivística de documentos, permitindo "
        "visualizações transversais de metadados e instrumentos de pesquisa."
    )
)

# Separa os arquivos no diretório antes de alimentar as abas
pasta_acervo = "."
arquivos_totais = [f for f in os.listdir(pasta_acervo) if f.lower().endswith((".xlsx", ".xls"))]

if not arquivos_totais:
    st.warning(traduzir("Nenhum arquivo Excel encontrado na pasta do sistema."))
    st.stop()

# Dividindo listas: Família 3 (Mapeamentos) vs Famílias 1 e 2 (Acervo Geral)
arquivos_map = [f for f in arquivos_totais if 'MAPEAMENTOS' in f.upper()]
arquivos_cat = [f for f in arquivos_totais if 'MAPEAMENTOS' not in f.upper()]

# Descrições padronizadas
descricoes_planilhas = {
    "BR-SPAPESP_CPOS.xlsx": {
        "Português": "Inventário das plantas estruturais da Companhia Paulista de Obras e Serviços (CPOS) referentes à Casa de Detenção. Base pronta, mas com uso condicionado à autorização do APESP para futuras bases de dados.",
    },
    "BR-SPAPESP_DASP.xlsx": {
        "Português": "Inventário de documentos e fotografias do fundo Diários Associados (DASP) sobre penitenciárias e a Casa de Detenção. Base pronta e autorizada para uso em futuras bases de dados.",
    },
    "BR-SPGPDVE_ARCOENGE.xlsx": {
        "Português": "Inventário do acervo Arcoenge sobre a demolição e implosão dos pavilhões 2, 5, 6, 8 e 9. Inclui clippings de repercussão midiática; pronta, autorizada e em publicação no Dataverse da FGV.",
    },
    "BR-SPGPDVE_ARCOENGE-NOTDEMOLI.xlsx": {
        "Português": "Subconjunto de notícias/clippings sobre a demolição e implosão no acervo Arcoenge. Complementa a base Arcoenge com a repercussão midiática do processo.",
    },
    "BR-SPGPDVE_FILMES-CSDTCARANDIRU.xlsx": {
        "Português": "Inventário de produções audiovisuais sobre a Casa de Detenção/Carandiru. Inclui a Penitenciária do Estado em 1928 e extras do filme Carandiru, de Hector Babenco (2002).",
    },
    "BR-SPGPDVE_MAPEAMENTOS-NOTICIAS-MSSCPENHA.xlsx": {
        "Português": "Mapeamento de rememorações e notícias sobre o massacre da Penha (RJ, 2025). Base em progresso no eixo Direito e Violência de Estado.",
    },
    "BR-SPGPDVE_MAPEAMENTOS-REMEMORA-CARANDIRU.xlsx": {
        "Português": "Mapeamento de rememorações do massacre do Carandiru (1992). Base em progresso, vinculada à série Mapeamento de rememorações.",
    },
    "BR-SPGPDVE_NOTICIAS-MASSACRE-CSDTCARANDIRU.xlsx": {
        "Português": "Inventário de notícias e documentos sobre o massacre do Carandiru. Inclui processo criminal e laudos de lesão corporal; base publicada.",
    },
}
descricoes_norm = {norm_nome_arquivo(k): v for k, v in descricoes_planilhas.items()}


# ============================================================
# CRIAÇÃO DAS ABAS (4 ABAS AGORA)
# ============================================================
aba_inventario, aba_iniciativas, aba_producao, aba_equipe = st.tabs(
    [
        traduzir("Inventário do acervo catalogado"),
        traduzir("Iniciativas de Rememoração"),
        traduzir("Visão geral do acervo"),
        traduzir("Equipe e observatório"),
    ]
)


# ============================================================
# ABA 1: INVENTÁRIO DO ACERVO
# ============================================================
with aba_inventario:
    dicionario_tematico = {
        "Família": ["mãe", "filho", "criança", "pai", "avó"],
        "Educação, artes e ofícios": ["escola", "alfabetização", "atividade cultural", "costura"],
        "Arquitetura prisional": ["grade", "cela", "pavilhão", "parede", "portão"],
    }

    # Seletor exclusivo para Aba 1 (Planilhas de acervo)
    selecionados_cat = st.multiselect(
        traduzir("Selecione as planilhas do acervo para integrar:"),
        arquivos_cat,
        default=arquivos_cat,
    )

    if selecionados_cat:
        partes = []
        sem_descricao = []
        for arq in selecionados_cat:
            trads = descricoes_planilhas.get(arq)
            if trads is None:
                trads = descricoes_norm.get(norm_nome_arquivo(arq))
            if trads is None:
                alvo = norm_nome_arquivo(arq)
                for k_norm, v in descricoes_norm.items():
                    if alvo and (alvo in k_norm or k_norm in alvo):
                        trads = v
                        break

            if not trads:
                sem_descricao.append(arq)
                continue

            desc = trads.get(idioma) or trads.get("Português") or ""
            partes.append(f"<span class='desc-nome'>{arq}</span>: {desc}")

        if partes:
            st.markdown(f"<div class='desc-lista'>{' '.join(partes)}</div>", unsafe_allow_html=True)
        if sem_descricao:
            st.caption(f"⚠️ {traduzir('Sem descrição cadastrada para:')} {', '.join(sem_descricao)}")

    if not selecionados_cat:
        st.info("Nenhuma planilha de acervo selecionada.")
    else:
        df_consolidado = carregar_e_cruzar_dados(selecionados_cat, pasta_acervo)

        st.subheader(traduzir("Busca avançada"))
        termo = st.text_input(
            traduzir("Pesquisar termo nas planilhas (ex: criança, portão, costura)")
        )
        df_filtrado = df_consolidado.copy()

        if termo and not df_filtrado.empty:
            stemmer = get_stemmer()
            termo_normal = normalizar_texto(termo, stemmer)
            termo_stem = " ".join([stemmer.stem(p) for p in termo_normal.split()])

            df_filtrado["NORMAL_BUSCA"] = df_filtrado.apply(
                lambda row: normalizar_texto(" ".join(row.dropna().astype(str)), stemmer),
                axis=1,
            )
            padrao = r"\b" + r"\b|\b".join(termo_stem.split()) + r"\b"
            mask = df_filtrado["NORMAL_BUSCA"].str.contains(padrao, regex=True, na=False)
            df_filtrado = df_filtrado[mask].drop(columns=["NORMAL_BUSCA"])

        st.subheader(traduzir("Filtros categoriais"))
        cols_int = ["Gênero documental", "Espécie/Tipo documental", "Técnica de registro", "Arquivo_origem"]
        cols_exist = [c for c in cols_int if c in df_consolidado.columns]

        dicionario_siglas = {
            "FOT": traduzir("Fotografia (FOT)"), "PLN": traduzir("Planta cartográfica (PLN)"),
            "DGZ": traduzir("Digitalizado (DGZ)"), "ICO": traduzir("Iconográfico (ICO)"),
            "MTO": traduzir("Meio magnético/ótico (MTO)"), "TXT": traduzir("Textual (TXT)"),
            "AVS": traduzir("Audiovisual (AVS)"), "FLG": traduzir("Filmográfico (FLG)"),
            "FME": traduzir("Filme (FME)"), "NOT": traduzir("Notícia (NOT)"),
            "REL": traduzir("Relatório (REL)"), "NDG": traduzir("Nato-digital (NDG)"),
            "NDT": traduzir("Não determinado (NDT)"),
        }

        filtros_selecionados = {}
        if cols_exist and not df_filtrado.empty:
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
                        traduzir(col), sorted(valores), key=f"f_{col}", format_func=lambda x: dicionario_siglas.get(str(x), str(x)),
                    )

        for col, sel in filtros_selecionados.items():
            if sel:
                df_filtrado = df_filtrado[df_filtrado[col].isin(sel)]

        st.subheader(traduzir("Indicadores"))
        col1, col2, col3 = st.columns(3)
        col1.metric(traduzir("Itens exibidos"), len(df_filtrado))
        if "Gênero documental" in df_filtrado.columns:
            col2.metric(traduzir("Gêneros documentais"), df_filtrado["Gênero documental"].nunique())

        df_metricas = df_filtrado.drop(columns=["Arquivo_origem", "SUPER_STRING"], errors="ignore")
        df_metricas = df_metricas.replace(r"^\s*$", pd.NA, regex=True).replace("[Título não localizado]", pd.NA)
        
        if not df_metricas.empty:
            col3.metric(traduzir("Metadados indexados (total)"), df_metricas.notna().sum().sum())
        else:
            col3.metric(traduzir("Metadados indexados (total)"), 0)

        st.subheader(traduzir("Análises e visualizações do acervo"))
        opcao_limpar = traduzir("Nenhuma visualização (limpar tela)")
        opcao_timeline = traduzir("Linha do tempo (distribuição cronológica)")
        opcao_nuvem = traduzir("Nuvem de palavras (título e conteúdo)")
        opcoes_menu = ([opcao_limpar, opcao_timeline] + [traduzir(k) for k in dicionario_tematico.keys()] + [opcao_nuvem])

        visualizacao_selecionada = st.selectbox(
            traduzir("Escolha uma visualização ou eixo temático:"), opcoes_menu, index=1,
        )

        if visualizacao_selecionada == opcao_timeline and not df_filtrado.empty:
            df_datas = df_filtrado.copy()
            if "Data (Busca)" in df_datas.columns:
                df_datas["Ano_Extraido"] = df_datas["Data (Busca)"].astype(str).str.extract(r"((?:18|19|20)\d{2})")
                df_anos = df_datas.dropna(subset=["Ano_Extraido"])

                if not df_anos.empty:
                    contagem_anos = df_anos["Ano_Extraido"].value_counts().reset_index()
                    contagem_anos.columns = ["Ano", "Frequência"]
                    fig_linha = px.line(contagem_anos.sort_values(by="Ano"), x="Ano", y="Frequência", markers=True, color_discrete_sequence=["#4ba3a6"])
                    fig_linha.update_layout(
                        template="plotly_dark", font=dict(family="Source Serif 4, serif", size=15),
                        title=dict(text=traduzir("Frequência de datas grafadas nos documentos"), font=dict(family="Cormorant Garamond, serif", size=24)),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(title="", showgrid=False),
                        yaxis=dict(title=traduzir("Volume documental"), gridcolor="rgba(120,120,120,0.15)")
                    )
                    fig_linha.update_traces(line=dict(width=3), marker=dict(size=8))
                    st.plotly_chart(fig_linha, use_container_width=True)

        elif visualizacao_selecionada in [traduzir(k) for k in dicionario_tematico.keys()] and not df_filtrado.empty:
            chave_original = next(k for k in dicionario_tematico.keys() if traduzir(k) == visualizacao_selecionada)
            palavras_chave = dicionario_tematico[chave_original]
            
            texto_comb_lista = []
            if "Conteúdo (Busca)" in df_filtrado.columns:
                texto_comb_lista.append(" ".join(df_filtrado["Conteúdo (Busca)"].dropna().astype(str)))
            if "Título (Busca)" in df_filtrado.columns:
                texto_comb_lista.append(" ".join(df_filtrado["Título (Busca)"].dropna().astype(str)))
                
            texto_combinado = " ".join(texto_comb_lista)
            stemmer = get_stemmer()
            texto_combinado_normal = normalizar_texto(texto_combinado, stemmer)

            contagem_termos = {}
            for palavra in palavras_chave:
                palavra_stem = normalizar_texto(palavra, stemmer)
                ocorrencias = len(re.findall(rf"\b{palavra_stem}\b", texto_combinado_normal))
                contagem_termos[palavra] = ocorrencias

            fig_tema = px.bar(
                pd.DataFrame(list(contagem_termos.items()), columns=["Termo", "Frequência"]),
                x="Termo", y="Frequência", text="Frequência", color="Frequência",
                color_continuous_scale=["#16324F", "#235789", "#2F6F8F", "#4BA3A6", "#7BC6CC"]
            )
            fig_tema.update_traces(textposition="outside")
            fig_tema.update_layout(
                template="plotly_dark", font=dict(family="Source Serif 4, serif", size=15),
                title=dict(text=f"{traduzir('Distribuição estatística')} — {visualizacao_selecionada.lower()}", font=dict(family="Cormorant Garamond, serif", size=24)),
                coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(title="", showgrid=False), yaxis=dict(title="", gridcolor="rgba(120,120,120,0.15)")
            )
            st.plotly_chart(fig_tema, use_container_width=True)

        elif visualizacao_selecionada == opcao_nuvem and not df_filtrado.empty:
            textos_lista = []
            if "Conteúdo (Busca)" in df_filtrado.columns:
                textos_lista += df_filtrado["Conteúdo (Busca)"].dropna().astype(str).tolist()
            if "Título (Busca)" in df_filtrado.columns:
                textos_lista += df_filtrado["Título (Busca)"].dropna().astype(str).tolist()
            if "Palavras-chave" in df_filtrado.columns:
                textos_lista += df_filtrado["Palavras-chave"].dropna().astype(str).tolist()

            texto_completo = " ".join(textos_lista).strip()
            stopwords = set(["de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com", "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "ao", "ele", "das", "à", "seu", "sua", "ou", "quando", "muito", "nos", "já", "eu", "também", "só", "pelo", "pela", "até", "isso", "ela", "entre", "depois", "sem", "mesmo", "aos", "seus", "quem", "nas", "me", "esse", "eles", "você", "essa", "num", "nem", "suas", "meu", "às", "minha", "numa", "pelos", "elas", "qual", "nós", "lhe", "deles", "essas", "esses", "pelas", "este", "dele", "tu", "te", "vocês", "vos", "lhes", "meus", "minhas", "teu", "tua", "teus", "tuas", "nosso", "nossa", "nossos", "nossas", "nan", "título", "localizado"])

            try:
                wordcloud = WordCloud(width=800, height=400, background_color="rgba(0,0,0,0)", mode="RGBA", colormap="viridis", stopwords=stopwords, max_words=100).generate(texto_completo)
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation="bilinear")
                ax.axis("off")
                fig.patch.set_alpha(0)
                st.pyplot(fig)
            except ValueError:
                st.warning(traduzir("Não há vocabulário útil suficiente nos itens filtrados para gerar a nuvem de palavras. Tente remover alguns filtros."))


# ============================================================
# ABA 2: INICIATIVAS DE REMEMORAÇÃO (Mapeamentos)
# ============================================================
with aba_iniciativas:
    
    # Seletor exclusivo para Aba 2 (Planilhas de rememoração)
    selecionados_map = st.multiselect(
        traduzir("Selecione as planilhas de rememoração:"),
        arquivos_map,
        default=arquivos_map,
    )

    if selecionados_map:
        partes_map = []
        sem_descricao_map = []
        for arq in selecionados_map:
            trads = descricoes_planilhas.get(arq)
            if trads is None: trads = descricoes_norm.get(norm_nome_arquivo(arq))
            if trads is None:
                alvo = norm_nome_arquivo(arq)
                for k_norm, v in descricoes_norm.items():
                    if alvo and (alvo in k_norm or k_norm in alvo):
                        trads = v
                        break
            if not trads:
                sem_descricao_map.append(arq)
                continue
            desc = trads.get(idioma) or trads.get("Português") or ""
            partes_map.append(f"<span class='desc-nome'>{arq}</span>: {desc}")

        if partes_map:
            st.markdown(f"<div class='desc-lista'>{' '.join(partes_map)}</div>", unsafe_allow_html=True)
        if sem_descricao_map:
            st.caption(f"⚠️ {traduzir('Sem descrição cadastrada para:')} {', '.join(sem_descricao_map)}")

    if not selecionados_map:
        st.info(traduzir("Nenhuma planilha de rememoração selecionada."))
    else:
        df_iniciativas = carregar_iniciativas(selecionados_map, pasta_acervo)
        
        st.subheader(traduzir("Busca avançada"))
        termo_inic = st.text_input(
            traduzir("Busca avançada por termo (ex: podcast, exposição, filme)"), key="busca_inic"
        )
        
        df_inic_filtrado = df_iniciativas.copy()
        
        if termo_inic and not df_inic_filtrado.empty:
            stemmer = get_stemmer()
            termo_normal = normalizar_texto(termo_inic, stemmer)
            termo_stem = " ".join([stemmer.stem(p) for p in termo_normal.split()])

            df_inic_filtrado["NORMAL_BUSCA"] = df_inic_filtrado.apply(
                lambda row: normalizar_texto(" ".join(row.dropna().astype(str)), stemmer),
                axis=1,
            )
            padrao = r"\b" + r"\b|\b".join(termo_stem.split()) + r"\b"
            mask_inic = df_inic_filtrado["NORMAL_BUSCA"].str.contains(padrao, regex=True, na=False)
            df_inic_filtrado = df_inic_filtrado[mask_inic].drop(columns=["NORMAL_BUSCA"])

        st.subheader(traduzir("Filtros categoriais"))
        cols_inic = ["Nome da iniciativa", "Intervenção", "Abrangência", "Modalidade"]
        cols_exist_inic = [c for c in cols_inic if c in df_inic_filtrado.columns]

        filtros_sel_inic = {}
        if cols_exist_inic and not df_inic_filtrado.empty:
            l_cols_inic = st.columns(len(cols_exist_inic))
            for i, col in enumerate(cols_exist_inic):
                with l_cols_inic[i]:
                    valores = [v for v in df_inic_filtrado[col].dropna().unique() if str(v).strip() != ""]
                    filtros_sel_inic[col] = st.multiselect(traduzir(col), sorted(valores), key=f"f_inic_{col}")

        for col, sel in filtros_sel_inic.items():
            if sel:
                df_inic_filtrado = df_inic_filtrado[df_inic_filtrado[col].isin(sel)]

        st.subheader(traduzir("Indicadores"))
        st.metric(traduzir("Total de iniciativas mapeadas"), len(df_inic_filtrado))

        st.subheader(traduzir("Análises e visualizações do acervo"))
        opcao_limpar_inic = traduzir("Nenhuma visualização (limpar tela)")
        opcao_timeline_inic = traduzir("Linha do tempo")
        opcao_nuvem_inic = traduzir("Nuvem de palavras")

        vis_inic = st.selectbox(
            traduzir("Escolha uma visualização ou eixo temático:"),
            [opcao_limpar_inic, opcao_timeline_inic, opcao_nuvem_inic],
            index=1,
            key="vis_inic"
        )
        
        if vis_inic == opcao_timeline_inic and not df_inic_filtrado.empty:
            if "Ano" in df_inic_filtrado.columns:
                df_inic_datas = df_inic_filtrado.copy()
                df_inic_datas["Ano_Limpo"] = df_inic_datas["Ano"].astype(str).str.extract(r"((?:19|20)\d{2})")
                df_inic_anos = df_inic_datas.dropna(subset=["Ano_Limpo"])
                
                if not df_inic_anos.empty:
                    contagem_anos_inic = df_inic_anos["Ano_Limpo"].value_counts().reset_index()
                    contagem_anos_inic.columns = ["Ano", "Frequência"]
                    fig_linha_inic = px.line(
                        contagem_anos_inic.sort_values(by="Ano"), 
                        x="Ano", y="Frequência", markers=True, color_discrete_sequence=["#7BC6CC"]
                    )
                    fig_linha_inic.update_layout(
                        template="plotly_dark", font=dict(family="Source Serif 4, serif", size=15),
                        title=dict(text=traduzir("Linha do tempo"), font=dict(family="Cormorant Garamond, serif", size=24)), 
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(title="", showgrid=False), 
                        yaxis=dict(title=traduzir("Volume documental"), gridcolor="rgba(120,120,120,0.15)")
                    )
                    fig_linha_inic.update_traces(line=dict(width=3), marker=dict(size=8))
                    st.plotly_chart(fig_linha_inic, use_container_width=True)

        elif vis_inic == opcao_nuvem_inic and not df_inic_filtrado.empty:
            if "Título" in df_inic_filtrado.columns:
                textos_lista_inic = df_inic_filtrado["Título"].dropna().astype(str).tolist()
                texto_completo_inic = " ".join(textos_lista_inic).strip()
                
                stopwords = set(["de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com", "não", "uma", "os", "no", "se", "na", "por", "mais", "as", "dos", "como", "mas", "ao", "ele", "das", "à", "seu", "sua", "ou", "quando", "muito", "nos", "já", "eu", "também", "só", "pelo", "pela", "até", "isso", "ela", "entre", "depois", "sem", "mesmo", "aos", "seus", "quem", "nas", "me", "esse", "eles", "você", "essa", "num", "nem", "suas", "meu", "às", "minha", "numa", "pelos", "elas", "qual", "nós", "lhe", "deles", "essas", "esses", "pelas", "este", "dele", "tu", "te", "vocês", "vos", "lhes", "meus", "minhas", "teu", "tua", "teus", "tuas", "nosso", "nossa", "nossos", "nossas", "nan", "título", "localizado"])
                
                try:
                    wordcloud_inic = WordCloud(width=800, height=400, background_color="rgba(0,0,0,0)", mode="RGBA", colormap="viridis", stopwords=stopwords, max_words=100).generate(texto_completo_inic)
                    fig_inic, ax_inic = plt.subplots(figsize=(10, 5))
                    ax_inic.imshow(wordcloud_inic, interpolation="bilinear")
                    ax_inic.axis("off")
                    fig_inic.patch.set_alpha(0)
                    st.pyplot(fig_inic)
                except ValueError:
                    st.warning(traduzir("Não há vocabulário útil suficiente nos itens filtrados para gerar a nuvem de palavras. Tente remover alguns filtros."))

        st.dataframe(df_inic_filtrado, use_container_width=True, hide_index=True)


# ============================================================
# ABA 3: VISÃO GERAL DO ACERVO
# ============================================================
# Adicionando o 'open' nos Níveis 1 (Coleção) e Níveis 2 (Série). Nível 3 (Subsérie) permanece fechado.
html_arvore = """
<style>
.arvore-acervo { font-family: 'Source Serif 4', serif; font-size: 1rem; line-height: 1.5; color: var(--text-color); }
.arvore-acervo details { margin-left: 24px; margin-bottom: 2px; }
.arvore-acervo summary { cursor: pointer; margin-bottom: 4px; outline: none; }
.arvore-acervo summary:hover { color: #4ba3a6; }
.item-simples { margin-left: 40px; margin-bottom: 4px; }
.tag-azul { background-color: #2f6f8f; color: white; border-radius: 6px; padding: 4px 10px; font-size: 0.85rem; display: inline-block; margin-top: 2px; margin-bottom: 8px; font-family: 'IBM Plex Mono', monospace; }
.sigla-codigo { font-family: 'IBM Plex Mono', monospace; color: #2F6F8F; font-weight: 600; font-size: 0.9em; background: rgba(47, 111, 143, 0.08); padding: 2px 5px; border-radius: 4px; }

/* Estilos das Badges */
.status-badge { font-size: 0.8rem; padding: 3px 8px; border-radius: 4px; display: inline-block; font-weight: 500; margin-top: 4px; margin-bottom: 6px; line-height: 1.2; font-family: 'Source Serif 4', sans-serif; }
.bg-verde { background-color: rgba(25, 135, 84, 0.1); color: #198754; border: 1px solid rgba(25, 135, 84, 0.2); }
.bg-vermelho { background-color: rgba(220, 53, 69, 0.1); color: #dc3545; border: 1px solid rgba(220, 53, 69, 0.2); }
.bg-azul { background-color: rgba(13, 110, 253, 0.1); color: #0d6efd; border: 1px solid rgba(13, 110, 253, 0.2); }
.bg-amarelo { background-color: rgba(255, 193, 7, 0.1); color: #b38600; border: 1px solid rgba(255, 193, 7, 0.3); }
</style>

<div class="arvore-acervo">

<!-- COLEÇÃO 1: CARANDIRU -->
<details open>
<summary><strong>Coleção: Carandiru</strong></summary>

<details open>
<summary><strong>Série: Arquivo Público do Estado de São Paulo <span class="sigla-codigo">(APESP)</span></strong></summary>
<details>
<summary>Subsérie: Criar, construir, inaugurar (1952-1978)</summary>
<div class="item-simples"><span class="status-badge bg-verde">🟢 Publicada.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPAPESP_CPOS-PLNCARANDIRU_TXT-PNL-MT0_0001.xlsx</span></div>
</details>
<details>
<summary>Subsérie: Planta estrutural (Companhia Paulista de Obras e Serviços — CPOS)</summary>
<div class="item-simples"><span class="status-badge bg-vermelho">🔴 Pronta, mas aguardando autorização para uso em futuras bases de dados.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPAPESP_CPOS-PLNCARANDIRU_TXT-PNL-MT0_0001.xlsx</span></div>
</details>
<details>
<summary>Subsérie: Penitenciárias e presídios — Casa de Detenção de São Paulo no Carandiru (jornal Diários Associados do Estado de São Paulo — DASP)</summary>
<div class="item-simples"><span class="status-badge bg-azul">🔵 Pronta e autorizada para uso em futuras bases de dados.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPAPESP_DASP-PENITPRE-CSDTCARANDIRU_TXT-PNL-MT0_0001.xlsx</span></div>
</details>
</details>

<details open>
<summary><strong>Série: Processo criminal - Massacre do Carandiru</strong></summary>
<details>
<summary>Subsérie: Laudos de lesão corporal</summary>
<div class="item-simples"><span class="status-badge bg-verde">🟢 Publicada.</span></div>
</details>
</details>

<details open>
<summary><strong>Série: Arcoenge <span class="sigla-codigo">(ARCOENGE)</span></strong></summary>
<details>
<summary>Subsérie: Demolição e implosão dos pavilhões 2, 5, 6, 8 e 9 da Casa de Detenção e clippings de repercussão midiática</summary>
<div class="item-simples"><span class="status-badge bg-verde">🟢 Publicada.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPGPDVE_ARCOENGE-DEMOLICAO-CSDTCARANDIRU_TXT-PNL-MT0_0001.xlsx</span></div>
</details>
</details>

<details open>
<summary><strong>Série: Mapeamento de rememorações <span class="sigla-codigo">(MAPEAMENTOS)</span></strong></summary>
<details>
<summary>Subsérie: Rememorações do massacre do Carandiru (1992)</summary>
<div class="item-simples"><span class="status-badge bg-verde">🟢 Pronta, autorizada e em processo de publicação no Dataverse da FGV.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPGPDVE_MAPEAMENTOS-REMEMORA-CARANDIRU_TXT-PNL-MT0_0001.xlsx</span></div>
</details>
</details>

<details open>
<summary><strong>Série: Produções audiovisuais <span class="sigla-codigo">(FILMES/NOTICIAS)</span></strong></summary>
<details>
<summary>Subsérie: Penitenciária do Estado em 1928</summary>
<div class="item-simples"><span class="status-badge bg-amarelo">🟡 Em progresso.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPGPDVE_FILMES-CSDTCARANDIRU_TXT-PNL-MT0_0001.xlsx</span></div>
</details>
<details>
<summary>Subsérie: Extras do filme Carandiru, por Hector Babenco (2002)</summary>
<div class="item-simples"><span class="status-badge bg-azul">🔵 Pronta para uso em futuras bases de dados.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPGPDVE_FILMES-CSDTCARANDIRU_TXT-PNL-MT0_0001.xlsx</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPGPDVE_NOTICIAS-CSDTCARANDIRU_TXT-PNL-MT0_0001.xlsx</span></div>
</details>
</details>

</details>

<!-- COLEÇÃO 2: DIREITO E VIOLÊNCIA DE ESTADO -->
<details open>
<summary><strong>Coleção: Direito e Violência de Estado</strong></summary>

<details open>
<summary><strong>Série: Mapeamento de rememorações</strong></summary>
<details>
<summary>Subsérie: Rememorações e notícias do massacre da Penha no Rio de Janeiro (2025)</summary>
<div class="item-simples"><span class="status-badge bg-amarelo">🟡 Em progresso (fase final).</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPGPDVE_MAPEAMENTOS-NOTICIAS-MSSCPENHA_TXT-PNL-MT0_0001.xlsx</span></div>
</details>
</details>

<details open>
<summary><strong>Série: Os anteprojetos da Lei de Execução Penal</strong></summary>
<details>
<summary>Subsérie: Repositórios de ideias para punir: uma navegação textual pelos anteprojetos da Lei de Execução Penal (1935-1975)</summary>
<div class="item-simples"><span class="status-badge bg-verde">🟢 Publicada.</span></div>
</details>
</details>

<details open>
<summary><strong>Série: Massacre prisional do Amazonas</strong></summary>
<details>
<summary>Subsérie: A construção jurídica da identificação indígena de "pelo menos" cinco homens mortos no contexto de massacre prisional do AM, em 2017</summary>
<div class="item-simples"><span class="status-badge bg-verde">🟢 Publicada.</span></div>
</details>
</details>

</details>

<!-- COLEÇÃO 3: PROCJURADM -->
<details open>
<summary><strong>Coleção: Procedimentos judiciais e administrativos <span class="sigla-codigo">(PROCJURADM)</span></strong></summary>

<details open>
<summary><strong>Série: Tribunal de Justiça do Estado de São Paulo <span class="sigla-codigo">(TJSP)</span></strong></summary>
<div class="item-simples">Subsérie: Processo criminal contra 120 policiais militares <span class="sigla-codigo">(PROCRIM-POLMIL)</span></div>
<div class="item-simples">Subsérie: Sindicância da Corregedoria dos Presídios de 1992 <span class="sigla-codigo">(SINDIC-CORREGEDPRES)</span></div>
<div class="item-simples">Subsérie: Processos cíveis de indenização por danos materiais e morais <span class="sigla-codigo">(PROCCIVEL)</span></div>
</details>

<details open>
<summary><strong>Série: Assembleia Legislativa do Estado de São Paulo <span class="sigla-codigo">(ALESP)</span></strong></summary>
<div class="item-simples">Subsérie: Comissão Parlamentar de Inquérito de 1992 <span class="sigla-codigo">(CPI)</span></div>
</details>

<details open>
<summary><strong>Série: Ministério Público do Estado de São Paulo <span class="sigla-codigo">(MPSP)</span></strong></summary>
<div class="item-simples">Subsérie: Inquérito Civil Público de 1992 <span class="sigla-codigo">(INQCIVPUBLICO)</span></div>
</details>

<details open>
<summary><strong>Série: Tribunal de Justiça Militar do Estado de São Paulo <span class="sigla-codigo">(TJMSP)</span></strong></summary>
<div class="item-simples">Subsérie: Sindicância Justiça Militar de 1992 <span class="sigla-codigo">(SINDIC-TJM)</span></div>
</details>

<details open>
<summary><strong>Série: Ministério da Justiça <span class="sigla-codigo">(MINJUSTICA)</span></strong></summary>
<div class="item-simples">Subsérie: Relatório final do Conselho Nacional de Política Criminal e Penitenciária <span class="sigla-codigo">(RELFINAL-CNPCP)</span></div>
</details>

<details open>
<summary><strong>Série: Conselho Municipal de Preservação do Patrimônio <span class="sigla-codigo">(CONPRESPSP)</span></strong></summary>
<div class="item-simples">Subsérie: Processo de tombamento <span class="sigla-codigo">(PROCTOM)</span></div>
</details>

</details>
</div>
"""

with aba_producao:
    st.markdown(html_arvore, unsafe_allow_html=True)


# ============================================================
# ABA 4: EQUIPE E OBSERVATÓRIO DATAVERSE
# ============================================================
with aba_equipe:
    st.subheader(traduzir("Equipe do GPDVE"))
    st.markdown(
        traduzir("Dados extraídos em tempo real da página oficial da FGV Direito SP.")
    )

    with st.spinner(traduzir("Extraindo informações da web...")):
        lista_equipe = extrair_equipe_fgv()

    colunas_equipe = st.columns(3)
    fatias_lista = [lista_equipe[:6], lista_equipe[6:12], lista_equipe[12:]]
    contador = 1

    for idx_coluna, st_col in enumerate(colunas_equipe):
        with st_col:
            for membro in fatias_lista[idx_coluna]:
                st.markdown(
                    f"<div class='equipe-item'><strong>{contador}.</strong> "
                    f"{membro}</div>",
                    unsafe_allow_html=True,
                )
                contador += 1

    st.markdown("<br><hr>", unsafe_allow_html=True)

    st.subheader(
        traduzir("Observatório de bases publicadas pelo GPDVE no Dataverse da FGV")
    )
    st.markdown(
        traduzir(
            "Listagem automatizada das publicações institucionais das autoras "
            "do GPDVE."
        )
    )

    chave_original_fgv = st.secrets.get("api_dataverse", "")
    chave_nova = st.secrets.get("api_dataverse_nova", "")
    chaves_api = [chave_original_fgv, chave_nova]

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
        "Balbuglio, Viviane",
        "Castro, Maria Eduarda de",
        "Santos, Natália Santana dos",
        "Milfont, Iasmin",
        "Moreira, Maria Cecília",
        "Oliveira, Maria Luiza Silva",
        "Monteiro, Maurício",
        "Franco, Millena Miranda",
    ]

    with st.spinner(traduzir("Consultando o repositório...")):
        df_producao = buscar_producao_autoras(chaves_api, pesquisadoras_rastreadas)

    # Inserção manual da publicação de Viviane Balbuglio
    registro_manual = pd.DataFrame(
        [
            {
                "Título da base": (
                    "A construção jurídica da identificação indígena de "
                    "“pelo menos” cinco homens mortos no contexto de massacre "
                    "prisional do AM, em 2017"
                ),
                "Autores": "Balbuglio, Viviane",
                "Identificador": "doi:10.48331/SCIELODATA.HQACHL",
                "Link de acesso": (
                    "https://data.scielo.org/dataset.xhtml?"
                    "persistentId=doi:10.48331/SCIELODATA.HQACHL"
                ),
            }
        ]
    )

    if df_producao.empty:
        df_producao = registro_manual
    else:
        if not df_producao["Identificador"].str.contains(
            "10.48331/SCIELODATA.HQACHL", na=False
        ).any():
            df_producao = pd.concat(
                [df_producao, registro_manual], ignore_index=True
            )

    if not df_producao.empty:
        st.data_editor(
            df_producao,
            column_config={
                "Link de acesso": st.column_config.LinkColumn("Link de acesso")
            },
            hide_index=True,
            use_container_width=True,
        )


# ============================================================
# RODAPÉ INSTITUCIONAL
# ============================================================
meses = [
    "jan.", "fev.", "mar.", "abr.", "maio", "jun.",
    "jul.", "ago.", "set.", "out.", "nov.", "dez.",
]
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
    <p style="margin: 0; font-family: 'Source Serif 4', serif; font-size: 0.95rem; color: var(--text-color);">FRANCO, Millena Miranda. Inventário e estatísticas de coleções em Direito e Violência de Estado: gestão e visualização transversal de metadados arquivísticos. São Paulo: Escola de Direito de São Paulo, Fundação Getulio Vargas (FGV), 2026. Programa de computador. Acesso em: {data_formatada}.</p>
</div>
"""
st.markdown(rodape_html, unsafe_allow_html=True)