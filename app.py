import streamlit as st
import pandas as pd
import os, re, unicodedata
from wordcloud import WordCloud
import matplotlib.pyplot as plt

st.set_page_config(page_title="Inventário do Acervo — Carandiru", layout="wide")

PASTA = r"C:\Users\mille\OneDrive\Área de Trabalho\inventario_acervo"

# ============================================================
# UTILIDADES
# ============================================================
def normalizar(s):
    if pd.isna(s):
        return ''
    s = str(s).strip().lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    return s

def achar_coluna(colunas, *frags):
    for c in colunas:
        cn = normalizar(c)
        if any(f in cn for f in frags):
            return c
    return None

def achar_coluna_data(colunas):
    for c in colunas:
        cn = normalizar(c)
        if cn.startswith('data') and 'acesso' not in cn:
            return c
    return None

def extrair_ano(valor):
    if valor is None:
        return None
    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass
    m = re.search(r'(\d{4})', str(valor))
    if m:
        n = int(m.group(1))
        if 1900 <= n <= 2100:
            return n
    return None

def detectar_tipo_e_cabecalho(xls, aba, max_linhas=25):
    try:
        raw = pd.read_excel(xls, sheet_name=aba, header=None, nrows=max_linhas)
    except Exception:
        return None, None
    for i, r in raw.iterrows():
        texto = normalizar(' | '.join(str(v) for v in r if pd.notna(v)))
        if 'titulo descritivo' in texto:
            return 'catalogo', i
        if 'iniciativa' in texto and ('finalidade' in texto or 'intervencao' in texto):
            return 'iniciativa', i
    return None, None

def get(row, col, default=''):
    if col is None or col not in row.index:
        return default
    v = row[col]
    if pd.isna(v):
        return default
    return str(v).strip()

# ============================================================
# LEITURA
# ============================================================
@st.cache_data(ttl=300, show_spinner="Lendo planilhas…")
def ler_tudo(pasta):
    catalogo, iniciativas = [], []

    if not os.path.isdir(pasta):
        return pd.DataFrame(), pd.DataFrame()

    for arq in sorted(os.listdir(pasta)):
        if not arq.lower().endswith(('.xlsx', '.xls')) or arq.startswith('~$'):
            continue
        caminho = os.path.join(pasta, arq)
        try:
            xls = pd.ExcelFile(caminho)
        except Exception:
            continue

        for aba in xls.sheet_names:
            tipo, hr = detectar_tipo_e_cabecalho(xls, aba)
            if tipo is None:
                continue
            try:
                df = pd.read_excel(xls, sheet_name=aba, header=hr).dropna(how='all')
            except Exception:
                continue
            if df.empty:
                continue

            # ---------------- CATÁLOGO ----------------
            if tipo == 'catalogo':
                c_tit  = achar_coluna(df.columns, 'titulo descritivo', 'titulo')
                if not c_tit:
                    continue
                c_con  = achar_coluna(df.columns, 'conteudo', 'assunto')
                c_dat  = achar_coluna_data(df.columns)
                c_cod  = achar_coluna(df.columns, 'codigo de referencia', 'codigo')
                c_kw   = achar_coluna(df.columns, 'palavras')
                c_not  = achar_coluna(df.columns, 'notas')
                c_loc  = achar_coluna(df.columns, 'local')
                c_aut  = achar_coluna(df.columns, 'autor', 'responsavel')
                c_sup  = achar_coluna(df.columns, 'suporte')
                c_gen  = achar_coluna(df.columns, 'genero')
                c_esp  = achar_coluna(df.columns, 'especie', 'tipo doc')
                c_den  = achar_coluna(df.columns, 'denominacao')
                c_his  = achar_coluna(df.columns, 'historia')
                c_con  = c_con  # já existe
                c_cac  = achar_coluna(df.columns, 'condicoes de acesso')
                c_niv  = achar_coluna(df.columns, 'nivel')
                c_pub  = achar_coluna(df.columns, 'legenda')
                c_cit  = achar_coluna(df.columns, 'citacao')

                for _, r in df.iterrows():
                    titulo = get(r, c_tit)
                    if not titulo or titulo.lower() in ('nan', 'none'):
                        continue
                    data_val = get(r, c_dat)
                    catalogo.append({
                        'Arquivo': arq,
                        'Aba': aba,
                        'Título': titulo,
                        'Conteúdo': get(r, c_con),
                        'Data': data_val,
                        'Ano': extrair_ano(data_val),
                        'Código de referência': get(r, c_cod),
                        'Palavras-chave': get(r, c_kw),
                        'Notas': get(r, c_not),
                        'Local': get(r, c_loc),
                        'Autor/Responsável': get(r, c_aut),
                        'Suporte': get(r, c_sup),
                        'Gênero': get(r, c_gen),
                        'Espécie/Tipo': get(r, c_esp),
                        'Denominação do catálogo': get(r, c_den),
                        'História arquivística': get(r, c_his),
                        'Condições de acesso': get(r, c_cac),
                        'Nível de descrição': get(r, c_niv),
                        'Legenda': get(r, c_pub),
                        'Citação': get(r, c_cit),
                    })

            # ---------------- INICIATIVAS ----------------
            elif tipo == 'iniciativa':
                c_tit = achar_coluna(df.columns, 'titulo')
                if not c_tit:
                    continue
                c_ini = achar_coluna(df.columns, 'iniciativa')
                c_fin = achar_coluna(df.columns, 'finalidade')
                c_int = achar_coluna(df.columns, 'intervencao')
                c_abr = achar_coluna(df.columns, 'abrangencia')
                c_mod = achar_coluna(df.columns, 'modalidade')
                c_dat = achar_coluna_data(df.columns)
                c_ano = achar_coluna(df.columns, 'ano')
                c_loc = achar_coluna(df.columns, 'local')
                c_pro = achar_coluna(df.columns, 'proponente')
                c_gen = achar_coluna(df.columns, 'genero documental')
                c_tec = achar_coluna(df.columns, 'tecnica de registro', 'reproducao')
                c_fon = achar_coluna(df.columns, 'fonte', 'origem')
                c_idi = achar_coluna(df.columns, 'idioma')
                c_cha = achar_coluna(df.columns, 'chave de busca', 'entrada')
                c_dac = achar_coluna(df.columns, 'data de acesso')
                c_dis = achar_coluna(df.columns, 'disponibilidade')
                c_lin = achar_coluna(df.columns, 'link')
                c_abn = achar_coluna(df.columns, 'abnt')

                for _, r in df.iterrows():
                    titulo = get(r, c_tit)
                    if not titulo or titulo.lower() in ('nan', 'none'):
                        continue
                    ano_val = extrair_ano(get(r, c_ano)) or extrair_ano(get(r, c_dat))
                    iniciativas.append({
                        'Arquivo': arq,
                        'Aba': aba,
                        'Título': titulo,
                        'Iniciativa': get(r, c_ini),
                        'Finalidade': get(r, c_fin),
                        'Intervenção': get(r, c_int),
                        'Abrangência': get(r, c_abr),
                        'Modalidade': get(r, c_mod),
                        'Data': get(r, c_dat),
                        'Ano': ano_val,
                        'Local': get(r, c_loc),
                        'Proponente': get(r, c_pro),
                        'Gênero documental': get(r, c_gen),
                        'Técnica de registro': get(r, c_tec),
                        'Fonte/Origem': get(r, c_fon),
                        'Idioma': get(r, c_idi),
                        'Chave de busca': get(r, c_cha),
                        'Data de acesso': get(r, c_dac),
                        'Disponibilidade': get(r, c_dis),
                        'Link': get(r, c_lin),
                        'Citação ABNT': get(r, c_abn),
                    })

    df_cat = pd.DataFrame(catalogo)
    df_ini = pd.DataFrame(iniciativas)

    # ---------------- DEDUPLICAÇÃO (só remove duplicata literal) ----------------
    if not df_cat.empty:
        def chave_cat(row):
            cod = str(row.get('Código de referência', '')).strip()
            if cod:
                return f"cod::{cod}"
            return f"aba::{row.get('Aba','')}::tit::{row.get('Título','')}::dat::{row.get('Data','')}"
        df_cat['_k'] = df_cat.apply(chave_cat, axis=1)
        df_cat = df_cat.loc[~df_cat['_k'].duplicated(keep='first')].drop(columns='_k').reset_index(drop=True)

    if not df_ini.empty:
        def chave_ini(row):
            return "::".join([str(row.get(c, '')) for c in
                              ['Arquivo', 'Aba', 'Título', 'Data', 'Link']])
        df_ini['_k'] = df_ini.apply(chave_ini, axis=1)
        df_ini = df_ini.loc[~df_ini['_k'].duplicated(keep='first')].drop(columns='_k').reset_index(drop=True)

    return df_cat, df_ini

# ============================================================
# CARREGA
# ============================================================
df_cat, df_ini = ler_tudo(PASTA)

st.title("📚 Inventário do Acervo — Carandiru")
if st.button("🔄 Recarregar planilhas"):
    st.cache_data.clear()
    st.rerun()

tab1, tab2 = st.tabs(["📁 Acervo catalogado", "📰 Iniciativas & Rememoração"])

# ============================================================
# ABA 1 — ACERVO CATALOGADO
# ============================================================
with tab1:
    if df_cat.empty:
        st.warning("Nenhum item catalogado encontrado.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Itens", len(df_cat))
        c2.metric("Arquivos", df_cat['Arquivo'].nunique())
        c3.metric("Abas", df_cat['Aba'].nunique())
        anos_validos = df_cat['Ano'].dropna()
        c4.metric("Período", f"{int(anos_validos.min())}–{int(anos_validos.max())}" if len(anos_validos) else "—")

        f1, f2, f3 = st.columns(3)
        with f1:
            f_arq = st.multiselect("Arquivo", sorted(df_cat['Arquivo'].unique()))
        with f2:
            f_aba = st.multiselect("Aba", sorted(df_cat['Aba'].unique()))
        with f3:
            anos_ord = sorted(df_cat['Ano'].dropna().unique())
            f_ano = st.multiselect("Ano", anos_ord)

        busca = st.text_input("🔎 Busca livre (título, conteúdo, palavras-chave, notas, local, autor)")

        dff = df_cat.copy()
        if f_arq: dff = dff[dff['Arquivo'].isin(f_arq)]
        if f_aba: dff = dff[dff['Aba'].isin(f_aba)]
        if f_ano: dff = dff[dff['Ano'].isin(f_ano)]
        if busca:
            nb = normalizar(busca)
            campos = ['Título', 'Conteúdo', 'Palavras-chave', 'Notas', 'Local', 'Autor/Responsável']
            dff = dff[dff.apply(lambda r: any(nb in normalizar(r[c]) for c in campos), axis=1)]

        st.caption(f"{len(dff)} itens após filtros")

        with st.expander("☁️ Nuvem de palavras", expanded=False):
            textos = []
            for _, r in dff.iterrows():
                partes = [str(r.get('Título', '')), str(r.get('Conteúdo', '')),
                          str(r.get('Palavras-chave', '')).replace(';', ' ')]
                textos.append(' '.join(p for p in partes if p))
            texto = ' '.join(textos).strip()
            if len(texto) < 60:
                st.warning("Não há vocabulário útil suficiente nos itens filtrados. Remova alguns filtros.")
            else:
                try:
                    wc = WordCloud(width=900, height=400, background_color='white',
                                   collocations=False).generate(texto)
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                except ValueError as e:
                    st.warning(f"Não foi possível gerar a nuvem: {e}")

        st.subheader("Itens")
        colunas_padrao = ['Arquivo', 'Aba', 'Título', 'Data', 'Ano',
                          'Palavras-chave', 'Local', 'Autor/Responsável', 'Código de referência']
        colunas_padrao = [c for c in colunas_padrao if c in dff.columns]
        escolha = st.multiselect("Colunas visíveis", list(dff.columns), default=colunas_padrao)
        if escolha:
            st.dataframe(dff[escolha], use_container_width=True, height=500)

        st.download_button("⬇️ Baixar CSV (acervo)",
                           dff.to_csv(index=False).encode('utf-8'),
                           "acervo_catalogado.csv", "text/csv")

# ============================================================
# ABA 2 — INICIATIVAS
# ============================================================
with tab2:
    if df_ini.empty:
        st.warning("Nenhuma iniciativa encontrada.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Iniciativas", len(df_ini))
        c2.metric("Arquivos", df_ini['Arquivo'].nunique())
        c3.metric("Finalidades", df_ini['Finalidade'].nunique())
        anos_i = df_ini['Ano'].dropna()
        c4.metric("Período", f"{int(anos_i.min())}–{int(anos_i.max())}" if len(anos_i) else "—")

        f1, f2, f3, f4 = st.columns(4)
        with f1:
            fi_arq = st.multiselect("Arquivo", sorted(df_ini['Arquivo'].unique()), key='iarq')
        with f2:
            fi_fin = st.multiselect("Finalidade", sorted(df_ini['Finalidade'].dropna().unique()), key='ifin')
        with f3:
            fi_int = st.multiselect("Intervenção", sorted(df_ini['Intervenção'].dropna().unique()), key='iint')
        with f4:
            fi_ano = st.multiselect("Ano", sorted(df_ini['Ano'].dropna().unique()), key='iano')

        busca2 = st.text_input("🔎 Busca livre (título, proponente, local, fonte, iniciativa)")

        dfi = df_ini.copy()
        if fi_arq: dfi = dfi[dfi['Arquivo'].isin(fi_arq)]
        if fi_fin: dfi = dfi[dfi['Finalidade'].isin(fi_fin)]
        if fi_int: dfi = dfi[dfi['Intervenção'].isin(fi_int)]
        if fi_ano: dfi = dfi[dfi['Ano'].isin(fi_ano)]
        if busca2:
            nb = normalizar(busca2)
            campos2 = ['Título', 'Proponente', 'Local', 'Fonte/Origem', 'Iniciativa', 'Chave de busca']
            dfi = dfi[dfi.apply(lambda r: any(nb in normalizar(r[c]) for c in campos2), axis=1)]

        st.caption(f"{len(dfi)} iniciativas após filtros")

        st.subheader("📅 Linha do tempo")
        por_ano = dfi.dropna(subset=['Ano']).groupby('Ano').size().reset_index(name='Qtd')
        if not por_ano.empty:
            por_ano['Ano'] = por_ano['Ano'].astype(int)
            st.bar_chart(por_ano.set_index('Ano'), height=280)
        else:
            st.info("Sem anos preenchidos para montar a linha do tempo.")

        st.subheader("📊 Distribuição por categoria")
        d1, d2 = st.columns(2)
        with d1:
            if dfi['Finalidade'].notna().any():
                st.caption("Finalidade primária")
                st.bar_chart(dfi['Finalidade'].value_counts())
        with d2:
            if dfi['Intervenção'].notna().any():
                st.caption("Intervenção")
                st.bar_chart(dfi['Intervenção'].value_counts())

        with st.expander("☁️ Nuvem de palavras (iniciativas)", expanded=False):
            texto = ' '.join(
                (dfi['Título'].fillna('').astype(str) + ' ' +
                 dfi['Intervenção'].fillna('').astype(str) + ' ' +
                 dfi['Finalidade'].fillna('').astype(str))
            ).strip()
            if len(texto) < 60:
                st.warning("Vocabulário insuficiente.")
            else:
                try:
                    wc = WordCloud(width=900, height=400, background_color='white',
                                   collocations=False).generate(texto)
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                except ValueError as e:
                    st.warning(f"Não foi possível gerar a nuvem: {e}")

        st.subheader("Iniciativas")
        colunas_i = ['Arquivo', 'Título', 'Iniciativa', 'Finalidade', 'Intervenção',
                     'Modalidade', 'Abrangência', 'Ano', 'Proponente', 'Local',
                     'Fonte/Origem', 'Link']
        colunas_i = [c for c in colunas_i if c in dfi.columns]
        escolha_i = st.multiselect("Colunas visíveis (iniciativas)", list(dfi.columns),
                                    default=colunas_i, key='col_i')
        if escolha_i:
            st.dataframe(dfi[escolha_i], use_container_width=True, height=500)

        st.download_button("⬇️ Baixar CSV (iniciativas)",
                           dfi.to_csv(index=False).encode('utf-8'),
                           "iniciativas.csv", "text/csv")

# ============================================================
# DEBUG (opcional)
# ============================================================
with st.expander("🔧 Diagnóstico", expanded=False):
    st.write("Acervo catalogado:", df_cat.shape)
    st.write("Iniciativas:", df_ini.shape)
    if not df_cat.empty:
        st.write("Itens por arquivo:", df_cat['Arquivo'].value_counts().to_dict())
    if not df_ini.empty:
        st.write("Iniciativas por arquivo:", df_ini['Arquivo'].value_counts().to_dict())
