from pathlib import Path
from data_logic import load_collection, metadata_count
from analysis_ui import render_analysis
import re
import unicodedata
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup



# ============================================================
# RECURSOS CACHEADOS E FUNÇÕES UTILITÁRIAS
# ============================================================
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


def chave_ordenacao_alfabetica(texto):
    """Chave de ordenação que ignora acentos e caixa (Álbum < Banda)."""
    if texto is None:
        return ""
    return (
        unicodedata.normalize("NFKD", str(texto))
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .lower()
    )


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    layout="wide",
    page_title="Inventário e estatísticas de coleções",
)


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
        "Inventário e estatísticas de coleções em Direito e Violência de Estado": {
            "English": (
                "Inventory and statistics of collections about Law and state violence"
            ),
            "Español": (
                "Inventario y estadísticas de las colecciones en derecho "
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
        "Rememorações e Notícias": {
            "English": "Remembrances and News",
            "Español": "Rememoraciones y Noticias",
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
        "Equipe do Grupo de Pesquisa em Direito e Violência de Estado.": {
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
        "Filtros categoriais": {
            "English": "Categorical filters",
            "Español": "Filtros categóricos",
        },
        "Selecione as planilhas para integrar:": {
            "English": "Select the spreadsheets to integrate:",
            "Español": "Seleccione las hojas de cálculo a integrar:",
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
        "Linha do Tempo das Iniciativas": {
            "English": "Initiatives Timeline",
            "Español": "Línea de tiempo de Iniciativas",
        },
        "Pesquisar nas iniciativas...": {
            "English": "Search initiatives...",
            "Español": "Buscar en iniciativas...",
        },
        "Total de iniciativas mapeadas": {
            "English": "Total mapped initiatives",
            "Español": "Total de iniciativas mapeadas",
        },
        "Nenhuma iniciativa carregada. Selecione planilhas de MAPEAMENTOS.": {
            "English": "No initiatives loaded. Select MAPEAMENTOS spreadsheets.",
            "Español": "No se cargaron iniciativas. Seleccione hojas de MAPEAMENTOS.",
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
                "Rememorações e Notícias": {
            "English": "Remembrances and News",
            "Español": "Rememoraciones y Noticias",
        },
        "Nome da iniciativa": {
            "English": "Initiative name",
            "Español": "Nombre de la iniciativa",
        },
        "Abrangência": {"English": "Reach", "Español": "Alcance"},
        "Modalidade": {"English": "Modality", "Español": "Modalidad"},
        "Intervenção": {"English": "Intervention", "Español": "Intervención"},
        "Ano": {"English": "Year", "Español": "Año"},
        "Proponente": {"English": "Proponent", "Español": "Proponente"},
        "Fonte / Origem": {"English": "Source / Origin", "Español": "Fuente / Origen"},
        "Pesquisar termo nas iniciativas (ex: podcast, exposição, filme)": {
            "English": "Search term in initiatives (e.g., podcast, exhibition, film)",
            "Español": "Buscar término en iniciativas (ej: podcast, exposición, película)",
        },
        "Selecione as planilhas de rememorações para integrar:": {
            "English": "Select the remembrances spreadsheets to integrate:",
            "Español": "Seleccione las hojas de rememoraciones a integrar:",
        },
        "Nuvem de palavras (Nome da iniciativa)": {
            "English": "Word cloud (initiative name)",
            "Español": "Nube de palabras (nombre de la iniciativa)",
        },
        "Nenhuma planilha de MAPEAMENTOS encontrada.": {
            "English": "No MAPEAMENTOS spreadsheet found.",
            "Español": "No se encontró ninguna hoja de MAPEAMENTOS.",
        },
        "Frequência de datas grafadas nas iniciativas": {
            "English": "Frequency of dates written in initiatives",
            "Español": "Frecuencia de fechas escritas en las iniciativas",
        },
        "Nuvem de palavras": {
            "English": "Word cloud",
            "Español": "Nube de palabras",
        },
        "O que deve conter? Selecione as colunas para gerar a nuvem:": {
            "English": (
                "What should it include? Select the columns to generate "
                "the cloud:"
            ),
            "Español": (
                "¿Qué debe contener? Seleccione las columnas para generar "
                "la nube:"
            ),
        },
        "Selecione ao menos uma coluna para gerar a nuvem.": {
            "English": "Select at least one column to generate the cloud.",
            "Español": "Seleccione al menos una columna para generar la nube.",
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
.st-key-cat_sources [data-testid="stCheckbox"] p,
.st-key-inic_sources [data-testid="stCheckbox"] p {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    color: #7BC6CC;
    font-weight: 600;
    white-space: normal;
    overflow-wrap: anywhere;
}
.st-key-cat_sources .desc-lista,
.st-key-inic_sources .desc-lista {
    margin-bottom: 8px;
    overflow-wrap: anywhere;
}
</style>
"""
st.markdown(css_base, unsafe_allow_html=True)


# ============================================================
# FUNÇÕES DE EXTRAÇÃO, CACHE E WEBSCRAPING
# ============================================================
@st.cache_data
def _carregar_cache(lista_arquivos, pasta, assinatura):
    return load_collection(lista_arquivos, pasta)


def carregar_e_cruzar_dados(lista_arquivos, pasta):
    assinatura = tuple((nome, (Path(pasta)/nome).stat().st_mtime_ns, (Path(pasta)/nome).stat().st_size) for nome in sorted(lista_arquivos))
    return _carregar_cache(lista_arquivos, pasta, assinatura)


def segredo(nome):
    try:
        return st.secrets.get(nome, "")
    except FileNotFoundError:
        return ""


@st.cache_data(ttl=300)
def buscar_producao_autoras(api_tokens, lista_autoras):
    from integrations import author_publications
    return author_publications(api_tokens, lista_autoras)


@st.cache_data(ttl=86400)
def extrair_equipe_fgv(consultar_online=False):
    if not consultar_online:
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
    url = (
        "https://direitosp.fgv.br/grupos-de-pesquisa/"
        "grupo-pesquisa-direito-violencia-estado"
    )
    equipe_extraida = []
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
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
# CABEÇALHO DO PROGRAMA
# ============================================================
# Acesso aberto, conforme solicitado pela responsável pelo aplicativo.
st.session_state["app_language"] = idioma

st.title(
    traduzir(
        "Inventário e estatísticas de coleções em Direito e Violência de Estado"
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


# ============================================================
# CRIAÇÃO DAS ABAS (4 ABAS AGORA)
# ============================================================

# Dados globais: o total no topo não muda ao filtrar um recorte em uma aba.
pasta_acervo = str(Path(__file__).resolve().parent)
arquivos_todos = sorted(p.name for p in Path(pasta_acervo).glob("*.xlsx") if not p.name.startswith("~$"))
arquivos_catalogacao = [f for f in arquivos_todos if "MAPEAMENTOS" not in f.upper()]
arquivos_mapeamentos = [f for f in arquivos_todos if "MAPEAMENTOS" in f.upper()]
base_catalogacao, base_iniciativas = carregar_e_cruzar_dados(arquivos_todos, pasta_acervo)
total_metadados = metadata_count(base_catalogacao, "catalogue") + metadata_count(base_iniciativas, "initiatives")
st.metric("Total de metadados preenchidos", f"{total_metadados:,}".replace(",", "."))
st.caption(f"Soma dos campos de origem em {len(arquivos_todos)} bases: {len(base_catalogacao)} descrições documentais e {len(base_iniciativas)} registros mapeados. Campos internos e cópias derivadas não entram na soma. Os filtros abaixo alteram somente o recorte de cada aba.")

aba_inventario, aba_iniciativas, aba_producao, aba_equipe = st.tabs(
    [
        traduzir("Inventário do acervo catalogado"),
        traduzir("Rememorações e Notícias"),
        traduzir("Visão geral do acervo"),
        traduzir("Equipe e observatório"),
    ]
)


# ============================================================
# ABA 1: INVENTÁRIO DO ACERVO
# ============================================================
descricoes_planilhas = {
        "BR-SPAPESP_CPOS-PLNCARANDIRU.xlsx": {
            "Português": (
                "Inventário das plantas estruturais da Companhia Paulista de "
                "Obras e Serviços (CPOS) referentes à Casa de Detenção. Base "
                "pronta, mas com uso condicionado à autorização do APESP para "
                "futuras bases de dados."
            ),
            "English": (
                "Inventory of the structural plans by Companhia Paulista de "
                "Obras e Serviços (CPOS) concerning the Casa de Detenção. "
                "Dataset ready, but use subject to APESP authorisation for "
                "future databases."
            ),
            "Español": (
                "Inventario de los planos estructurales de la Companhia "
                "Paulista de Obras e Serviços (CPOS) relativos a la Casa de "
                "Detención. Base lista, pero con uso condicionado a la "
                "autorización del APESP para futuras bases de datos."
            ),
        },
        "BR-SPAPESP_DASP-PENITPRE-CSDTCARANDIRU.xlsx": {
            "Português": (
                "Inventário de documentos e fotografias do fundo Diários "
                "Associados (DASP) sobre penitenciárias e a Casa de Detenção. "
                "Base pronta e autorizada para uso em futuras bases de dados."
            ),
            "English": (
                "Inventory of documents and photographs from the Diários "
                "Associados fund (DASP) on penitentiaries and the Casa de "
                "Detenção. Dataset ready and authorised for use in future "
                "databases."
            ),
            "Español": (
                "Inventario de documentos y fotografías del fondo Diários "
                "Associados (DASP) sobre penitenciarías y la Casa de "
                "Detención. Base lista y autorizada para uso en futuras bases "
                "de datos."
            ),
        },
        "BR-SPCARANDIRU_ARCOENGE-DEMOLICAO-CSDTCARANDIRU.xlsx": {
            "Português": (
                "Inventário do acervo Arcoenge sobre a demolição e implosão "
                "dos pavilhões 2, 5, 6, 8 e 9. Inclui clippings de repercussão "
                "midiática; pronta, autorizada e em publicação no Dataverse "
                "da FGV."
            ),
            "English": (
                "Inventory of the Arcoenge collection on the demolition and "
                "implosion of pavilions 2, 5, 6, 8 and 9. Includes media "
                "coverage clippings; ready, authorised and being published on "
                "the FGV Dataverse."
            ),
            "Español": (
                "Inventario del acervo Arcoenge sobre la demolición e "
                "implosión de los pabellones 2, 5, 6, 8 y 9. Incluye "
                "clippings de repercusión mediática; lista, autorizada y en "
                "publicación en el Dataverse de la FGV."
            ),
        },
        "BR-SPCARANDIRU_ARCOENGE-NOTDEMOLI-CSDTCARANDIRU.xlsx": {
            "Português": (
                "Subconjunto de notícias/clippings sobre a demolição e "
                "implosão no acervo Arcoenge. Complementa a base Arcoenge com "
                "a repercussão midiática do processo."
            ),
            "English": (
                "Subset of news/clippings on the demolition and implosion in "
                "the Arcoenge collection. Complements the Arcoenge dataset "
                "with media coverage of the process."
            ),
            "Español": (
                "Subconjunto de noticias/clippings sobre la demolición e "
                "implosión en el acervo Arcoenge. Complementa la base "
                "Arcoenge con la repercusión mediática del proceso."
            ),
        },
        "BR-SPCARANDIRU_FILMES-CSDTCARANDIRU.xlsx": {
            "Português": (
                "Inventário de produções audiovisuais sobre a Casa de "
                "Detenção/Carandiru. Inclui a Penitenciária do Estado em 1928 "
                "e extras do filme Carandiru, de Hector Babenco (2002)."
            ),
            "English": (
                "Inventory of audiovisual productions about the Casa de "
                "Detenção/Carandiru. Includes the Penitenciária do Estado in "
                "1928 and extras from the film Carandiru, by Hector Babenco "
                "(2002)."
            ),
            "Español": (
                "Inventario de producciones audiovisuales sobre la Casa de "
                "Detención/Carandiru. Incluye la Penitenciaría del Estado en "
                "1928 y extras de la película Carandiru, de Hector Babenco "
                "(2002)."
            ),
        },
        "BR-SPDIREITOVIOLESTADO_MAPEAMENTOS-NOTICIAS-MSSCPENHA.xlsx": {
            "Português": (
                "Mapeamento de rememorações e notícias sobre o massacre da "
                "Penha (RJ, 2025). Base em progresso no eixo Direito e "
                "Violência de Estado."
            ),
            "English": (
                "Mapping of remembrances and news about the Penha massacre "
                "(Rio de Janeiro, 2025). Dataset in progress under the Law "
                "and State Violence axis."
            ),
            "Español": (
                "Mapeo de rememoraciones y noticias sobre la masacre de la "
                "Penha (RJ, 2025). Base en progreso en el eje Derecho y "
                "Violencia de Estado."
            ),
        },
        "BR-SPCARANDIRU_MAPEAMENTOS-REMEMORA-CARANDIRU.xlsx": {
            "Português": (
                "Mapeamento de rememorações do massacre do Carandiru (1992). "
                "Base em progresso, vinculada à série Mapeamento de "
                "rememorações."
            ),
            "English": (
                "Mapping of remembrances of the Carandiru massacre (1992). "
                "Dataset in progress, linked to the Mapping of Remembrances "
                "series."
            ),
            "Español": (
                "Mapeo de rememoraciones de la masacre del Carandiru (1992). "
                "Base en progreso, vinculada a la serie Mapeo de "
                "rememoraciones."
            ),
        },
        "BR-SPCARANDIRU_ARCOENGE-MASSACRE-CSDTCARANDIRU.xlsx": {
            "Português": (
                "Inventário de notícias e documentos sobre o massacre do "
                "Carandiru. Inclui processo criminal e laudos de lesão "
                "corporal; base publicada."
            ),
            "English": (
                "Inventory of news and documents about the Carandiru "
                "massacre. Includes criminal proceedings and bodily injury "
                "reports; dataset published."
            ),
            "Español": (
                "Inventario de noticias y documentos sobre la masacre del "
                "Carandiru. Incluye proceso penal e informes de lesiones "
                "corporales; base publicada."
            ),
        },
    }
descricoes_inic = {
            "BR-SPDIREITOVIOLESTADO_MAPEAMENTOS-NOTICIAS-MSSCPENHA.xlsx": {
                "Português": (
                    "Mapeamento de rememorações e notícias sobre o massacre "
                    "da Penha (RJ, 2025). Base em progresso no eixo Direito "
                    "e Violência de Estado."
                ),
                "English": (
                    "Mapping of remembrances and news about the Penha "
                    "massacre (Rio de Janeiro, 2025). Dataset in progress "
                    "under the Law and State Violence axis."
                ),
                "Español": (
                    "Mapeo de rememoraciones y noticias sobre la masacre de "
                    "la Penha (RJ, 2025). Base en progreso en el eje Derecho "
                    "y Violencia de Estado."
                ),
            },
            "BR-SPCARANDIRU_MAPEAMENTOS-REMEMORA-CARANDIRU.xlsx": {
                "Português": (
                    "Mapeamento de rememorações do massacre do Carandiru "
                    "(1992). Base em progresso, vinculada à série Mapeamento "
                    "de rememorações."
                ),
                "English": (
                    "Mapping of remembrances of the Carandiru massacre "
                    "(1992). Dataset in progress, linked to the Mapping of "
                    "Remembrances series."
                ),
                "Español": (
                    "Mapeo de rememoraciones de la masacre del Carandiru "
                    "(1992). Base en progreso, vinculada a la serie Mapeo "
                    "de rememoraciones."
                ),
            },
        }

with aba_inventario:
    render_analysis("catalogue", arquivos_catalogacao, descricoes_planilhas, carregar_e_cruzar_dados, pasta_acervo, traduzir)

with aba_iniciativas:
    render_analysis("initiatives", arquivos_mapeamentos, descricoes_inic, carregar_e_cruzar_dados, pasta_acervo, traduzir)

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
.tag-azul {
    background-color: rgba(25, 135, 84, 0.08);
    color: #1e7e34;
    border: 1px solid rgba(25, 135, 84, 0.22);
    border-left: 3px solid #198754;
    border-radius: 4px;
    padding: 4px 10px 4px 26px;
    font-size: 0.85rem;
    display: inline-block;
    margin-top: 2px;
    margin-bottom: 8px;
    font-family: 'IBM Plex Mono', monospace;
    position: relative;
}
.tag-azul::before {
    content: "▦";
    position: absolute;
    left: 8px;
    top: 50%;
    transform: translateY(-50%);
    color: #198754;
    font-size: 0.85rem;
    line-height: 1;
    opacity: 0.85;
}.sigla-codigo { font-family: 'IBM Plex Mono', monospace; color: #2F6F8F; font-weight: 600; font-size: 0.9em; background: rgba(47, 111, 143, 0.08); padding: 2px 5px; border-radius: 4px; }

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
<div class="item-simples"><span class="status-badge bg-verde">🟢 Publicada (seleção).</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPAPESP_DASP-PENITPRE-CSDTCARANDIRU.xlsx</span></div>
</details>
<details>
<summary>Subsérie: Planta estrutural (Companhia Paulista de Obras e Serviços — CPOS)</summary>
<div class="item-simples"><span class="status-badge bg-vermelho">🔴 Pronta, mas aguardando autorização para uso em futuras bases de dados.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPAPESP_CPOS-PLNCARANDIRU.xlsx</span></div>
</details>
<details>
<summary>Subsérie: Penitenciárias e presídios — Casa de Detenção de São Paulo no Carandiru (jornal Diários Associados do Estado de São Paulo — DASP)</summary>
<div class="item-simples"><span class="status-badge bg-azul">🔵 Pronta e autorizada para uso em futuras bases de dados.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPAPESP_DASP-PENITPRE-CSDTCARANDIRU.xlsx</span></div>
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
<div class="item-simples"><span class="tag-azul">BR-SPCARANDIRU_ARCOENGE-DEMOLICAO-CSDTCARANDIRU.xlsx</span></div>
</details>
</details>

<details open>
<summary><strong>Série: Mapeamento de rememorações <span class="sigla-codigo">(MAPEAMENTOS)</span></strong></summary>
<details>
<summary>Subsérie: Rememorações do massacre do Carandiru (1992)</summary>
<div class="item-simples"><span class="status-badge bg-verde">🟢 Pronta, autorizada e em processo de publicação no Dataverse da FGV.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPCARANDIRU_MAPEAMENTOS-REMEMORA-CARANDIRU.xlsx</span></div>
</details>
</details>

<details open>
<summary><strong>Série: Produções audiovisuais <span class="sigla-codigo">(FILMES/NOTICIAS)</span></strong></summary>
<details>
<summary>Subsérie: Penitenciária do Estado em 1928</summary>
<div class="item-simples"><span class="status-badge bg-amarelo">🔵 Pronta e autorizada para uso em futuras bases de dados.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPCARANDIRU_FILMES-CSDTCARANDIRU.xlsx</span></div>
</details>
<details>
<summary>Subsérie: Extras do filme Carandiru, por Hector Babenco (2002)</summary>
<div class="item-simples"><span class="status-badge bg-azul">🔵 Pronta para uso em futuras bases de dados.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPCARANDIRU_FILMES-CSDTCARANDIRU.xlsx</span></div>
</details>
<details>
<summary>Subsérie: Notícias do Massacre do Carandiru (2002)</summary>
<div class="item-simples"><span class="status-badge bg-azul">🔵 Pronta para uso em futuras bases de dados.</span></div>
<div class="item-simples"><span class="tag-azul">BR-SPCARANDIRU_ARCOENGE-NOTDEMOLI-CSDTCARANDIRU.xlsx</span></div>
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
<div class="item-simples"><span class="tag-azul">BR-SPDIREITOVIOLESTADO_MAPEAMENTOS-NOTICIAS-MSSCPENHA.xlsx</span></div>
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
        traduzir("Equipe do Grupo de Pesquisa em Direito e Violência de Estado.")
    )

    with st.spinner(traduzir("Extraindo informações da web...")):
        lista_equipe = extrair_equipe_fgv(True)

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

    chave_original_fgv = segredo("api_dataverse")
    chave_nova = segredo("api_dataverse_nova")
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

    aviso_repositorio = df_producao.attrs.get("notice", "")
    if aviso_repositorio:
        st.caption(aviso_repositorio)

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
            width="stretch",
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
