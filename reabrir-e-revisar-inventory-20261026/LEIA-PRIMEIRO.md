# Reabertura e revisão de 26/10/2026

## Reabrir imediatamente

No GitHub, edite `app.py`, apague o bloco `st.markdown(...)` que contém `.manutencao-tela` e a chamada `st.stop()` seguinte, e confirme o commit em `main`. Preserve `st.set_page_config(...)`.

Ou, no Codespace, depois de extrair este pacote, execute na raiz do repositório:

```bash
python /tmp/revisao-inventory/reabrir_app.py
git add app.py
git commit -m "Retira manutencao e reabre aplicativo"
git push origin main
```

O script retira somente o bloqueio conhecido e salva uma cópia de `app.py` em `.backup-correcoes`. Não envia nada ao GitHub por conta própria.

## Aplicar também as melhorias das calculadoras

Na raiz do repositório, com o pacote extraído em `/tmp/revisao-inventory`:

```bash
python /tmp/revisao-inventory/aplicar.py
python -m unittest discover -s tests -v
git add app.py analysis_ui.py data_logic.py auditar_planilhas.py reabrir_app.py tests/test_app.py tests/test_data_logic.py
git commit -m "Reabre app e amplia frequencias, cruzamentos e nuvens"
git push origin main
```

O instalador confere as versões dos arquivos antes de substituir e preserva mudanças de `app.py` feitas depois da publicação anterior. Salva backup e não altera os oito XLSX, requisitos, senhas ou configurações. Se detectar um arquivo de cálculo alterado desde a versão examinada, para antes de sobrescrevê-lo.

As melhorias permitem frequências de todos os campos preenchidos, cruzamento de dois campos, exportação das frequências e mais opções na nuvem. A nuvem apresenta os nomes das classificações, sem converter a tupla de códigos em texto ilegível. Os testes da interface usam respostas simuladas de rede; não certificam a disponibilidade dos serviços externos.

## Limpeza dos dados

`bases-para-analise-20261026.xlsx` é uma cópia tabular para consulta e análise, com cinco abas: Resumo, Inventario, Mapeamentos, Representacoes e Checagens. Não substitua os oito arquivos do app por esse arquivo: o importador do site continua lendo os XLSX originais.

Os originais foram preservados. Na cópia, foram normalizados espaços e campos vazios, preservados os registros elegíveis e acrescentadas as referências de arquivo, aba e linha. Os textos descritivos e as classificações divergentes não foram reescritos por suposição. As classificações do inventário continuam derivadas da aba Geral; o texto de técnica declarado na descrição permanece em coluna separada para comparação. Esta é uma exportação estática dos resultados salvos das fórmulas dos arquivos enviados, não uma recriação das fórmulas do Google Sheets.

### Totais conferidos independentemente

| Unidade | Quantidade |
| --- | ---: |
| Descrições documentais | 348 |
| Representações/arquivos componentes | 574 |
| Registros de mapeamento | 560 |
| Campos de origem preenchidos nos registros | 17.186 |

Não some descrições e representações como se fossem a mesma unidade. A soma de metadados inclui os campos das descrições e dos mapeamentos, sem contar novamente as classificações derivadas e os campos técnicos internos.

### Correções que precisam de decisão na fonte

1. **CPOS:** a aba `3350 0001`, células `Q3:Q14`, informa digitalização, mas os códigos em `K3:K14` e `Geral!O3:O14` usam `FOT`. São 12 divergências. Definir qual classificação representa a técnica que se pretende contabilizar antes de alterar os códigos.
2. **FILMES:** as seis abas de descrição repetem o mesmo código em `K2`. Elas descrevem itens distintos; não excluir linhas por suposta duplicação. Conferir o código de cada descrição contra o subconjunto e a forma documental da Geral.
3. **Mapeamentos:** 16 linhas em Carandiru e 55 em Penha não têm iniciativa. Ficam fora das estatísticas e da cópia tabular, mas permanecem nos originais. Existem quatro registros de Penha com iniciativa e sem título do documento; foram preservados e sinalizados.
4. **Fórmulas:** há 3.144 ocorrências de `__xludf.DUMMYFUNCTION` nos arquivos. São fórmulas exportadas do Google Sheets, com limitações de recálculo em outros programas. Não foram encontrados erros Excel nos resultados salvos nesta cópia. Existem 22 células de fórmulas sem valor salvo em registros preenchidos; algumas podem ser vazias por regra da categoria. Conferir antes de preencher.
5. **Vocabulário:** distinguir `Geral!Q` (forma documental) de `Q` nas abas descritivas (técnica detalhada). A letra da coluna sozinha não identifica o campo sem indicar a aba.

### Evidência de NDT

NDT existe em `Geral!O2:O3` de MASSACRE, `Geral!O2:O45` de NOTDEMOLI e `Geral!O2:O40` de FILMES. Nas descrições, há o texto: `Possivelmente, filmagem digital ou vídeo digital. Optou-se por "não determinado" por incerteza quanto ao processo da técnica.`

São 85 representações com esse código, vinculadas a 41 descrições. Isso comprova o conteúdo dos arquivos recebidos, não quem o escreveu nem que a classificação deva ser mantida. A escolha da técnica precisa ser revista na fonte, com a evidência do processo de produção.

### Procedimento recomendado

- Mantenha os arquivos de origem como versão arquivística.
- Corrija primeiro as divergências de técnica e os códigos repetidos, usando a aba Checagens para localizar cada caso.
- Faça correções nas planilhas de origem. Se forem Google Sheets, exporte novamente depois de recalcular.
- Não deduplique apenas por título, código copiado, frente/verso ou arquivos componentes.
- Gere uma nova auditoria após cada exportação:

```bash
python auditar_planilhas.py --pasta . --saida auditoria-planilhas
```

Os CSV da pasta `auditoria` contêm as bases e os apontamentos completos. A aba Checagens do XLSX resume as ocorrências que exigem leitura; o CSV inclui também todas as ocorrências de fórmulas e o conteúdo completo necessário à inspeção.

## Publicação

A tentativa de atualização por esta conexão recebeu HTTP 403 do GitHub. A reabertura e as melhorias só estarão publicadas após um commit e push autorizado por você no GitHub ou Codespace. Este pacote foi preparado a partir de `bc498a5` e a conferência das planilhas usa os arquivos enviados em 26/10/2026.
