# Inventory and Statistics of GPDVE Collections

![Python](https://img.shields.io/badge/Python-3.14%2B-3776AB?style=flat&logo=python&logoColor=white)
<img src="https://github.com/user-attachments/assets/73c92635-287d-4530-afeb-9015b83f2d13" width="933" height="448" />
<img src="https://github.com/user-attachments/assets/deda2963-0170-4e98-bd36-b51bdb71b0be" width="937" height="225" />
<img src="https://github.com/user-attachments/assets/69e3fed4-204c-449a-9f24-38757b2140d0" width="930" height="574" />

Aplicação de análise de metadados arquivísticos e mapeamentos de rememorações e notícias. [Abrir aplicação](https://inventory-and-statistics.streamlit.app/).

## Contagens e critérios

O total de metadados aparece no topo e soma os campos de origem dos registros carregados nas oito bases. Campos internos e classificações derivadas não são contados novamente. Os filtros alteram somente o recorte de cada aba.

O inventário distingue descrições documentais de representações/arquivos da Geral. Gênero, espécie, técnica e forma vêm da Geral e são vinculados pelo código normalizado dentro de cada planilha. Frente/verso podem pertencer à mesma descrição. Códigos conflitantes e relações ausentes são sinalizados; nenhuma descrição desaparece por repetir um código.

Nos mapeamentos, Data, Ano, Título do documento, Fonte/Origem, Finalidade e Intervenção são campos separados. A contagem é de registros, sem presumir eventos distintos.

Opções no mesmo filtro usam OR; categorias diferentes usam AND. A busca aceita frases completas e números, ignorando acentos e caixa. A nuvem preserva termos separados por vírgulas e oferece frequências por campo. As linhas do tempo informam a cobertura e exibem zeros no intervalo observado. As frequências temáticas contam documentos que contêm cada termo.

As fontes atuais têm **348 descrições**, **574 representações** e **560 registros mapeados**, com **17.186 metadados preenchidos**. As seis descrições de filmes têm códigos conflitantes e são preservadas sem classificação atribuída automaticamente. Das 348 descrições, 305 têm ano extraível e 43 não têm. Linhas incompletas e erros de fórmula nos mapeamentos aparecem nas pendências. Os XLSX originais não são alterados.

## Código

- `data_logic.py`: leitura, validação, relações e cálculos.
- `analysis_ui.py`: filtros, gráficos, conferência e exportação CSV/DOCX.
- `integrations.py`: Dataverse com paginação, timeout e falhas explícitas.
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

Quando `senha_porta` está configurada nos segredos do Streamlit, a senha é exigida antes de carregar os dados. Sem essa chave, o acesso é público. Tokens `api_dataverse` e `api_dataverse_nova` são opcionais e permanecem nos segredos.

A equipe e as publicações são atualizadas sob demanda. A referência do programa pode ser editada e baixada na sessão. A paginação segue a [documentação oficial do Dataverse](https://guides.dataverse.org/en/6.4/api/search.html).
