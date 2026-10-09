# Inventory and Statistics of GPDVE Collections

![Python](https://img.shields.io/badge/Python-3.14%2B-3776AB?style=flat&logo=python&logoColor=white)
<img src="https://github.com/user-attachments/assets/73c92635-287d-4530-afeb-9015b83f2d13" width="933" height="448" />
<img src="https://github.com/user-attachments/assets/deda2963-0170-4e98-bd36-b51bdb71b0be" width="937" height="225" />
<img src="https://github.com/user-attachments/assets/69e3fed4-204c-449a-9f24-38757b2140d0" width="930" height="574" />

Aplicação de análise de metadados arquivísticos e mapeamentos de rememorações e notícias. [Abrir aplicação](https://inventory-and-statistics.streamlit.app/).

## Contagens e critérios

O total de metadados aparece no topo e soma os campos de origem dos registros carregados nas oito bases. Campos internos e classificações derivadas não são contados novamente. Os filtros alteram somente o recorte de cada aba.

O inventário conta descrições documentais. Gênero, espécie, técnica e forma vêm da Geral e são vinculados pelo código normalizado dentro de cada planilha. Frente/verso podem pertencer à mesma descrição. A leitura preserva as descrições com códigos repetidos. DVDs são ligados aos arquivos componentes; as seis abas de filmes são associadas aos subconjuntos identificados na Geral. Os códigos escritos nas planilhas são preservados. Todas as 348 descrições têm classificação vinculada, cobrindo 574 arquivos sem duplicar relações.

Nos mapeamentos, Data, Ano, Título do documento, Fonte/Origem, Finalidade e Intervenção são campos separados. A contagem é de registros, sem presumir eventos distintos.

Opções no mesmo filtro usam OR; categorias diferentes usam AND. Cada menu mostra somente valores compatíveis com a busca e os demais filtros; mudanças na busca ou nas planilhas limpam seleções incompatíveis. A busca aceita frases completas e números, ignorando acentos e caixa. A nuvem preserva termos separados por vírgulas e oferece frequências por campo. As linhas do tempo informam a cobertura e exibem zeros no intervalo observado. As frequências temáticas contam documentos que contêm cada termo.

As fontes atuais têm **348 descrições**, **574 representações** e **560 registros mapeados**, com **17.186 metadados preenchidos**. As seis descrições de filmes têm códigos repetidos e são associadas por aba/subconjunto, preservando as seis descrições e seus códigos de origem. Das 348 descrições, 305 têm ano extraível e 43 não têm. Linhas incompletas e erros de fórmula nos mapeamentos são tratados na leitura. Os XLSX originais não são alterados.

## Código

- `data_logic.py`: leitura, validação, relações e cálculos.
- `analysis_ui.py`: filtros, gráficos, conferência e exportação CSV.
- `integrations.py`: Dataverse público com paginação, consulta por autoria, cache e última listagem disponível.
- `app.py`: composição das quatro abas, idiomas e aparência.
- `vocabulario_controlado.py`: rótulos das siglas; siglas desconhecidas continuam visíveis.
- `tests/`: conferências das planilhas reais e da interface Streamlit.

## Executar e testar

Python 3.12+. As dependências diretas estão fixadas em `requirements.txt`.

```bash
git clone https://github.com/mmillenaa/inventory-and-statistics.git
cd inventory-and-statistics
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
python -m unittest discover -s tests -v
```

No Windows, ative o ambiente com `.venv\\Scripts\\activate`.

## Acesso e integrações

Cada planilha tem uma caixa de seleção junto ao título e à descrição, marcada por padrão. O seletor de tags foi removido. A nuvem dos mapeamentos oferece Nome da iniciativa, Ano, Fonte/Origem e Proponente. As letras das colunas são lidas em cada arquivo: Carandiru B/G/M/I; Penha B/H/N/J. As notas dos gráficos informam a origem.

Os menus mostram o nome seguido da sigla e os gráficos somente o nome. O vocabulário corresponde ao texto enviado pela autora, com os rótulos Audiovisual (AVS) e Matriz bruta (MT0). NDT está explicitamente escrito em 85 arquivos da Geral, associados a 41 descrições; não é um valor inserido para campos vazios.

O acesso ao aplicativo é aberto e não exige senha. A antiga chave `senha_porta`, caso exista nos segredos, é ignorada. Tokens `api_dataverse` e `api_dataverse_nova` são opcionais e permanecem nos segredos.

A equipe e as publicações carregam automaticamente. A referência do programa aparece no rodapé, sem editor. A consulta de publicações usa o campo authorName e somente versões publicadas, sem exigir tokens. A resposta é cacheada por cinco minutos e a última atualização bem-sucedida fica em .cache/observatorio.json. A cópia pública publicacoes_dataverse.json mantém sete publicações da FGV obtidas em 9 de outubro de 2026. O SciELO respondeu HTTP 403 na validação real; nesse caso, a entrada manual é mantida e aparece um único aviso discreto de atualização indisponível. A paginação segue a [documentação oficial do Dataverse](https://guides.dataverse.org/en/6.4/api/search.html).
