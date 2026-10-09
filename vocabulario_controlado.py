# -*- coding: utf-8 -*-
"""
Vocabulário controlado do GPDVE.
Dicionários de Gênero, Espécie, Técnica e Forma documental.
Chaves = siglas; valores = descrição completa.
"""
import re

DICT_GENERO = {
    "ATT": "Desenho técnico arquitetônico, de engenharia ou de construção (plantas, cortes, elevações).",
    "AVS": "Documento audiovisual: integra imagem em movimento e som (ex.: filme com trilha sonora).",
    "BIB": "Material bibliográfico: publicação impressa e editada, com tiragem e distribuição.",
    "CAR": "Documento cartográfico: representação geográfica de superfície terrestre ou celeste (mapas, cartas).",
    "CIN": "Cinematográfico: imagem em movimento registrada em película fotográfica (suporte fílmico).",
    "ELE": "Documento eletrônico: linguagem de programação, marcação ou código legível por computador.",
    "FLG": "Videográfico: imagem em movimento registrada em suporte magnético (fita de vídeo).",
    "FON": "Fonográfico: registro exclusivamente sonoro fixado em suporte físico (disco, fita, cilindro).",
    "NDT": "Gênero não determinado: informações insuficientes para classificação (suporte ou forma irreconhecíveis).",
    "VAR": "Gênero variado: usado para agrupamentos que contêm múltiplos gêneros documentais mistos.",
    "HEM": "Hemerográfico: publicações periódicas (jornais, revistas) ou recortes destas.",
    "ICO": "Iconográfico: imagem estática bidimensional (fotografia, desenho, gravura, pintura).",
    "SOM": "Sonoro: abrangente para qualquer registro de áudio, independentemente do suporte.",
    "TCT": "Tátil: documento percebido pelo toque (Braille, mapas em relevo, maquetes táteis).",
    "TXT": "Textual: informação principal baseada em linguagem escrita (manuscrito, impresso, digital).",
    "3DM": "Tridimensional: objeto físico com altura, largura e profundidade (escultura, maquete, artefato).",
}

DICT_ESPECIE = {
    "ALB": "Álbum: volume ou pasta que reúne itens como fotografias, selos ou recortes.",
    "AMP": "Ampliação fotográfica: cópia positiva opaca ou translúcida, em tamanho superior ao original.",
    "APP": "Aplicativo: software com função específica para dispositivo móvel ou desktop.",
    "AFT": "Arquivo-fonte: arquivo original não compilado de desenvolvimento (código-fonte, design).",
    "BLN": "Balanço: demonstrativo contábil da situação financeira em determinada data.",
    "BDD": "Banco de dados: coleção estruturada de dados eletrônicos gerenciada por sistema.",
    "BND": "Bando: edital ou ordem pública proclamada por autoridade (pregoeiro, oficial).",
    "BBL": "Bibliografia: lista sistemática de obras, artigos ou fontes referenciadas.",
    "BLH": "Bilhete: comunicação escrita breve, geralmente informal.",
    "BIO": "Biografia: relato da vida e trajetória de uma pessoa.",
    "BOL": "Boletim: publicação periódica informativa de caráter oficial ou institucional.",
    "BRV": "Breve: documento eclesiástico (resumo, nota, alvará) expedido por autoridade religiosa.",
    "CDN": "Caderno: pequeno livro ou conjunto de folhas para anotações sequenciais.",
    "CDR": "Caderno de registro: conjunto de folhas pautadas ou não para uso de registro manuscrito contínuo.",
    "CAL": "Cálculo: demonstrativo numérico de operações matemáticas, financeiras ou métricas.",
    "CRC": "Charge: desenho ou representação satírica e humorística.",
    "CRT": "Carta: correspondência escrita entre partes, com formalidade variável.",
    "CTG": "Carta geográfica: representação plana (mapa) de área geográfica específica.",
    "CTO": "Cartão: pequeno pedaço de papel retangular para registros breves ou identificação.",
    "CPS": "Cartão-postal: impresso retangular com imagem de um lado e espaço para mensagem e endereço no outro.",
    "CTZ": "Cartaz: impresso afixado em local público para divulgação de avisos ou ideias.",
    "CLH": "Cartilha: publicação com fins didáticos, instrutivos ou de alfabetização.",
    "CAT": "Catálogo: lista ordenada e descritiva de objetos, exposições, livros ou documentos.",
    "IPC": "Catálogo de peças: instrumento de pesquisa que descreve itens ou peças de um acervo.",
    "CDI": "Cédula: papel-moeda representativo de valor financeiro oficial.",
    "CID": "Cédula de identidade: documento oficial comprobatório de identidade civil ou institucional.",
    "CEN": "Censo: levantamento demográfico, estatístico ou patrimonial em determinada região.",
    "CTD": "Certidão: cópia ou atestado legal extraído de registro oficial público.",
    "CTF": "Certificado: documento solene que atesta um fato ou conclusão de curso.",
    "CRL": "Circular: comunicação oficial administrativa reproduzida para vários destinatários.",
    "CDC": "Códice: manuscrito antigo encadernado em forma de livro.",
    "CFT": "Código-fonte: conjunto de instruções lógicas estruturadas em linguagem de programação.",
    "COL": "Coletânea: reunião de obras, textos ou leis agrupadas em um só volume.",
    "CMP": "Comprovante: documento ou recibo que evidencia execução ou quitação de ato.",
    "COM": "Comunicado: nota oficial transmitida ao público para conhecimento geral.",
    "CNH": "Conhecimento: documento formal (ex.: de transporte) que prova recebimento de carga.",
    "CNS": "Constituição: lei fundamental que organiza estrutural e politicamente uma nação.",
    "CSL": "Consulta: pedido formal de parecer ou orientação técnica/jurídica.",
    "CNT": "Conta: registro de débitos, créditos ou faturas.",
    "CON": "Contato: cópia fotográfica obtida por contato direto do negativo com o papel, em tamanho real.",
    "CTT": "Contrato: acordo legal vinculante que gera obrigações entre as partes.",
    "EML": "E-mail: mensagem textual transmitida via rede computacional, com cabeçalho padrão.",
    "CRS": "Correspondência: qualquer tipo de troca de comunicação escrita (cartas, ofícios, memorandos).",
    "CRH": "Crachá: cartão de identificação funcional, geralmente atado à vestimenta.",
    "CNC": "Crônica: texto narrativo focado na observação de eventos cotidianos ou temporais.",
    "CNG": "Cronograma: representação gráfica do tempo de execução planejado para atividades.",
    "DCL": "Declaração: manifestação formal atestando condição, direito ou fato jurídico.",
    "DCR": "Decreto: ordem normativa com força de lei emanada do Poder Executivo.",
    "DCU": "Decupagem: relatório de marcação minuciosa de cenas e falas em produção audiovisual.",
    "DEF": "Defesa: documento judicial que refuta acusações ou resguarda direitos.",
    "DMN": "Demonstrativo: peça técnica com explanação minuciosa de dados financeiros ou estatísticos.",
    "DNN": "Denúncia: peça inicial de acusação em processos penais e investigativos.",
    "DPM": "Depoimento: declaração de fatos feita oralmente e reduzida a termo em inquérito.",
    "DES": "Desenho: representação visual de formas mediante linhas e traços manuais ou digitais.",
    "DCH": "Despacho: resolução administrativa ou judicial proferida no andamento de autos.",
    "DGR": "Diagrama: esquema gráfico demonstrativo de relações lógicas ou estatísticas.",
    "DPS": "Diapositivo: imagem positiva translúcida projetável (slide fotográfico).",
    "DIA": "Diário: registro sequencial de eventos organizado dia a dia.",
    "DIC": "Dicionário: obra lexicográfica que lista e define vocábulos de um idioma ou área.",
    "DPL": "Diploma: documento formal certificador de grau acadêmico ou láurea.",
    "DSC": "Discurso: texto redigido para leitura e locução pública.",
    "DSR": "Dissertação: trabalho acadêmico de investigação rigorosa em nível de mestrado.",
    "DSS": "Dossiê: conjunto de peças processuais ou documentos reunidos em torno de uma pessoa ou caso.",
    "EDT": "Edital: publicação oficial afixada publicamente contendo convocações ou regras.",
    "ECL": "Enciclopédia: obra de referência de caráter universal e explicativa.",
    "ENT": "Entrevista: registro estruturado em perguntas e respostas.",
    "ENV": "Envelope: invólucro para guarda e expedição de correspondências.",
    "ESQ": "Esquema: desenho simplificado focado nos traços principais de um projeto ou conceito.",
    "ETT": "Estatuto: corpo de normas jurídicas que rege a estrutura de uma associação ou entidade.",
    "EXD": "Expediente: peças documentais produzidas para tramitação interna de serviço.",
    "EXP": "Exposição: registro visual descritivo da organização espacial de uma mostra cultural.",
    "FAS": "Fascículo: publicação dividida em entregas parciais seriadas.",
    "FEE": "Fé de ofício: documento expedido atestando formalmente a veracidade de situação.",
    "FCH": "Ficha: formulário impresso ou cartão para controle ou registro cadastral.",
    "FIG": "Figura: ilustração ou esquema que acompanha e elucida um texto principal.",
    "FME": "Filme: materialidade fílmica em rolo ou peça audiovisual acabada.",
    "FGF": "Filmografia: catálogo sistemático ou listagem de obras cinematográficas.",
    "FLH": "Folheto: impresso de poucas páginas sem encadernação para difusão de ideias.",
    "FNG": "Fonograma: suporte contendo registro mecânico ou digital de vibração sonora.",
    "FRM": "Formulário: papel ou tela pré-estruturada com espaços para inserção de dados específicos.",
    "FOT": "Fotografia: imagem fixada pela ação da luz sobre superfície fotossensível (química ou digital).",
    "GZT": "Gazeta: publicação periódica (jornal) ou boletim oficial governamental.",
    "GLB": "Globo: representação cartográfica esférica do planeta ou de abóbada celeste.",
    "GRR": "Gravura: imagem transferida por pressão de uma matriz entalhada para um suporte.",
    "GIA": "Guia: obra de orientação, roteiro prático ou instrumento que indica caminhos.",
    "IPG": "Guia de fundos: instrumento arquivístico que descreve os fundos ou coleções de um repositório.",
    "HCR": "Habeas corpus: ordem judicial em prol do direito de locomoção e liberdade.",
    "IND": "Índice: lista remissiva e ordenada dos tópicos ou nomes contidos num documento.",
    "INF": "Informação: aviso sintético, circular ou documento com dados em resposta técnica.",
    "INQ": "Inquérito: conjunto procedimental focado na investigação ou apuração policial e civil.",
    "INS": "Instrução: ato administrativo com normas diretivas para execução padronizada de tarefas.",
    "ITM": "Intimação: ordem imperativa e legal para comparecimento a ato judiciário.",
    "INV": "Inventário: arrolamento pormenorizado de bens patrimoniais ou documentais.",
    "IPI": "Inventário de séries: instrumento que descreve detalhadamente as séries que compõem um fundo.",
    "JOR": "Jornal: folha impressa ou digital, de publicação contínua, com noticiário de amplo interesse.",
    "JUS": "Justificativa: peça documental que expõe as motivações lícitas de uma escolha ou ato.",
    "LAU": "Laudo: peça escrita, fundamentada em conhecimento técnico, emitindo juízo de valor especializado.",
    "LEI": "Lei: preceito jurídico com força normativa elaborado pelo Poder Legislativo.",
    "LBR": "Lembrança: pequena anotação ou aviso que serve à memória imediata.",
    "LCN": "Licença: ato formal que defere o direito de uso ou de execução de algo.",
    "LST": "Lista: rol ou enumeração sistematizada de arquivos, indivíduos ou itens.",
    "LVT": "Livreto: publicação em formato de bolso, geralmente encadernada ou grampeada.",
    "LVR": "Livro: conjunto de folhas consolidadas em volume, para registro contábil, oficial ou literário.",
    "MCO": "Maço: feixe de papéis ou conjunto documental agrupado fisicamente (ex.: processos atados).",
    "MND": "Mandado: ordem processual emanada de juízo com determinação executória cogente.",
    "MNF": "Manifesto: declaração pública expressando posições teóricas, políticas ou intenções coletivas.",
    "MCG": "Manifesto de conteúdo: lista gerada por sistemas detalhando pacotes, metadados ou lotes para submissão digital.",
    "MNL": "Manual: livro ou livreto focado em prover passos, regras e instruções operativas.",
    "MAP": "Mapa: representação visual em plano das convenções da superfície terrestre.",
    "MEM": "Memorando: documento oficial para comunicações internas horizontais entre setores de uma organização.",
    "MMR": "Memorial: anotação, muitas vezes processual ou acadêmica, em defesa e registro histórico da parte.",
    "MSG": "Mensagem: exposição textual de comunicação direta, comum em ambiente telegráfico ou executivo.",
    "MNG": "Monografia: trabalho exaustivo pormenorizando investigação pontual (ex.: TCC, dissertação).",
    "MUS": "Música: material contendo registro de linguagem e simbologia rítmica/melódica (partitura).",
    "NEG": "Negativo: original fotográfico em suporte translúcido com tons invertidos (complementares).",
    "NOM": "Nomeação: expediente administrativo que provê sujeito para assunção de cargo estatal.",
    "NRM": "Norma: regra vinculativa de procedimento, técnica ou medida disciplinadora aprovada (ex.: ABNT).",
    "NTA": "Nota: peça de apontamentos, conta comercial simples ou comentário marginal ao texto.",
    "NOT": "Notícia: formato de cunho puramente difusor, relatando um fato específico de impacto mediato.",
    "NTF": "Notificação: peça comunicativa alertando parte sobre fato administrativo gerador de obrigação.",
    "OBS": "Observação: pareceres curtos baseados em inspeção ou laudos parciais sem força de laudo técnico.",
    "OFC": "Ofício: correspondência entre chefias públicas, direcionada a repartições externas.",
    "OPS": "Opúsculo: pequeno volume ou impresso menor que o livro, mas não periódico (brochura).",
    "ORC": "Orçamento: peça de planificação estimativa contendo cotação de despesas, receitas e avaliações mercantis.",
    "ORD": "Ordem: comunicação com preceito afirmativo que determina imediata execução de diretriz.",
    "ORG": "Organograma: diagrama descritivo da estrutura de setores, áreas e hierarquia institucional.",
    "WWW": "Página web: conjunto de hipertextos e dados abrigado sob uma mesma URL.",
    "PFL": "Panfleto: folheto ou volante de poucas vias, frequentemente para uso político ou propagandístico.",
    "PRM": "Parâmetro: conjunto de valores lógicos definidos para scripts, configurações ou análises computacionais.",
    "PAR": "Parecer: declaração de jurista, técnico ou conselho orientador analisando material à luz do direito ou técnica.",
    "PSG": "Passagem: cupom, bilhete ou título comprovador de tarifa para transporte geográfico.",
    "PSP": "Passaporte: livrete ou cédula emitida pela soberania nacional, habilitando trânsito em território estrangeiro.",
    "PTT": "Patente: concessão do poder público certificando privilégios a autor de invenção ou projeto útil.",
    "PTA": "Pauta: sumário dos pontos propostos ou valores que instruirão votações e reuniões.",
    "PED": "Pedido: petição não formal, pleito mercadológico ou requerimento para suprimento perante órgão.",
    "PRD": "Periódico: revista, folhetim, caderno ou qualquer publicação serial com calendário pré-definido.",
    "PET": "Petição: expediente em que se postula resguardo jurisdicional da causa junto a foro adequado.",
    "PIN": "Pintura: obra fixada pela oposição de tintas colorantes sobre suporte como tela ou papel.",
    "PNL": "Planilha: grade matricial, quadro analítico ou software para tabular valores escalares.",
    "PNO": "Plano: projeto, delineamento ou intenção preestabelecendo cronogramas ou traçados urbanísticos.",
    "PLN": "Planta: configuração ortográfica que expõe modelagem do espaço e cortes de pavimento arquitetônico.",
    "POM": "Poema: gênero textual estruturado por métrica, estrofes e intencionalidade poética.",
    "POR": "Portaria: estatuto ou ato expedido por dirigentes contendo provimentos disciplinares de funcionamento.",
    "POS": "Postagem: inserção de blocos curtos em mídia social ou fórum, integrando fluxos comunicativos virtuais.",
    "PRC": "Processo: reunião de autos devidamente sequenciais com rito para instrução civil, penal ou administrativa.",
    "PCL": "Proclamação: declaração verbal promulgada com alta reverência em esferas governamentais e castrenses.",
    "PCR": "Procuração: instrumento de direito com delegação oficial permitindo a mandatário agir em nome de outorgante.",
    "PGR": "Programa: série de rotinas, códigos ou matrizes computacionais para operação de hardware ou software.",
    "PGM": "Programa (radiofônico/TV): emissão continuada de som e/ou vídeo integrando grade de radiodifusão.",
    "PNC": "Pronunciamento: enunciação formal e solene manifestando posicionamento em debates no parlamento.",
    "PRT": "Prontuário: histórico de paciente, sentenciado ou funcionário, englobando interações de saúde e sistema.",
    "PPG": "Propaganda: impresso, pôster ou anúncio para difundir ou persuadir comercialmente.",
    "PPS": "Proposta: plano comercial, oferta de concorrência ou prospecção sugerida a outrem para aceitação.",
    "PRO": "Prospecto: pequena e concisa exibição impressa visando atrair aderentes por meio de informe resumido.",
    "PRV": "Provisão: rescrito mandamental de poder contendo determinações para prover necessidades interinas.",
    "QDR": "Quadro: tábua expográfica em síntese de tabelas analíticas visuais com ou sem hierarquia.",
    "RCB": "Quitação: declaração e termo onde se confessa e atesta liberação e adimplemento monetário.",
    "REC": "Recorte: parte desmembrada de impresso ou hemeroteca contendo fragmento colecionado do original.",
    "RCR": "Recurso: instrumento interpelativo protocolar que pugna pela anulação ou modificação de decisão anterior.",
    "RGM": "Regimento: norma pormenorizadora que disciplina o modus operandi de repartição ou instância.",
    "REG": "Registro: assentamento legal anotando e arquivando em tomos fatos como nascimentos, patentes e imóveis.",
    "RGL": "Regulamento: preceito que normatiza e estabelece a prática regimental das garantias previstas em lei.",
    "RLC": "Relação: lista detalhada apontando itens enumerados (despesas, processos, nomes).",
    "RLT": "Relato: anotação rápida e não dogmática, de memória de evento em forma discorrida.",
    "REL": "Relatório: relato metódico prestando conta, diagnosticando andamentos a instâncias comissárias.",
    "DG2": "Relatório pós-processamento: documento com logísticas ou parecer avaliando saídas de processos digitais.",
    "DGN": "Relatório pré-processamento: diagnóstico situacional que autoriza critérios a serem aplicados.",
    "LOG": "Relatório de sistema: resumo cronológico de eventos reportando sucesso/falha de software.",
    "EXT": "Relatório de extração: tábua com amostragens metadadas extraídas de banco via consulta (query).",
    "ERR": "Relatório de erros: sumário de conflitos e incompatibilidades detectadas por ferramentas de verificação.",
    "TEC": "Relatório técnico: subsídio complementar de informática englobando laudo especializado.",
    "REP": "Representação: modelo esquemático reduzindo objetos ou manifestação/denúncia dirigida a autoridade.",
    "REQ": "Requerimento: formulação suplicante com rogos embasados administrativamente por direito de pleito lícito.",
    "RES": "Resolução: disposição ratificada e exarada a rigor da norma deliberativa de órgão diretivo.",
    "RTT": "Retrato: imagem figurativa fixada com ênfase na expressividade facial.",
    "VER": "Revista: fascículo impresso e seriado de perfil ilustrativo/especializado.",
    "ROT": "Roteiro: textualização guia pormenorizando trajetos, trilhas documentais ou passos operacionais.",
    "SVC": "Salvo-conduto: resguardo diplomático que isenta de penalidade fiscal ou prisional.",
    "SCR": "Script: instrução rotineira e comando imperativo programado para repetições autônomas.",
    "SEN": "Sentença: proclamação conclusiva decisória prolatada pelo crivo dos julgados, definindo fim condenatório ou extintivo.",
    "SIS": "Sistema: conjunto de múltiplas operações e engrenagens computacionais articuladas.",
    "SDA": "Sistema de arquivos: estrutura dedicada a abrigar, indexar e recuperar documentos (ex.: DSpace, AtoM).",
    "SGB": "Sistema gerenciador de banco de dados: arquitetura baseada no manejo de massas de dados transacionais.",
    "SIG": "Sistema informatizado de gestão arquivística: voltado à produção, trâmite, custódia e ciclo orgânico (SIGAD).",
    "SPD": "Sistema preservador digital: arquitetura alinhada à ISO 14721 (OAIS) e ISO 16363, incluindo repositórios confiáveis.",
    "SOL": "Solicitação: mensagem que roga deferimento intersetorial para aquisição de objeto ou bem.",
    "SUP": "Suplemento: obra anexa a publicação central, contendo conteúdos analíticos avulsos.",
    "TBL": "Tabela: organograma tabular relacional focado na cruzagem de quantitativos ordenados nos eixos X e Y.",
    "ATM": "Tabela AtoM: folha tabular metadada específica para injeção em lote no repositório AtoM (CSV).",
    "TLG": "Telegrama: despacho telegráfico transmitido por sinais breves a distância.",
    "TRM": "Termo: finalização autêntica de concordância, assinada, documentando prática transacional ou judicial.",
    "TSE": "Tese: opúsculo inédito e minucioso de aprofundamento investigativo (nível de doutorado).",
    "TES": "Testamento: delegação volitiva para partilha pós-morte, determinando sucessão patrimonial.",
    "TRA": "Transcrição: transferência da oralidade para sinais gráficos, mantendo autenticidade de depoimentos.",
    "TSL": "Transladado: traslado oficial fidedigno extraindo fé e certidões notariais de matrizes cartorárias.",
    "TRT": "Tratado: acordo diplomático com alianças pactuadas entre nações, aprovado por governo.",
    "VFG": "Vídeo fonográfico: filme com elementos visuais amalgamados ao espectro auditivo simultâneo.",
    "VGR": "Vídeo gráfico: filme ou gravação de visualidade contínua sem trilha sonora (mudo).",
    "VNH": "Vinheta: curto intervalo introdutório ou transicional com apelo ilustrativo (jingle / marca sonora).",
}

DICT_TECNICA = {
    "AMP": "Ampliação fotográfica: processo de aumento da imagem latente do negativo para cópia positiva opaca.",
    "MDA": "Marca d'água digital: técnica de sobreposição de assinatura translúcida para proteção de direitos.",
    "APR": "Apresentação digital: criação de slides eletrônicos e projeções sequenciais (ex.: PowerPoint).",
    "AUD": "Digitalização de áudio: conversão de sinais sonoros analógicos em códigos binários audíveis.",
    "CON": "Contato fotográfico: obtenção de cópia no mesmo tamanho do negativo, por contato direto.",
    "COO": "Conversão em lote: extração e recodificação automatizada de formatos digitais (ex.: TIF para JPEG).",
    "CCR": "Cópia com renomeação: duplicação de arquivos com alteração de nomes lógicos para controle logístico.",
    "CSR": "Cópia simples espelhada: clonagem integral de disco ou diretório preservando todas as instâncias.",
    "DDS": "Desenho sistêmico: concepção não documental focada em relacionamentos SQL e dados matriciais.",
    "DAT": "Datilografia: registro de sinais linguísticos por choque de tipos em máquina de escrever.",
    "DSM": "Desenho manual: representação linear esboçada a pulso com instrumentos de escrita.",
    "DGT": "Digital (sem especificação): código generalista para material codificado em pulsos sem detalhamento técnico.",
    "DGZ": "Digitalização por scanner: conversão de imagens analógicas em matrizes digitais por refletância ótica.",
    "DEL": "Eliminação programada: ato sistêmico de remoção de resíduos temporários em repositórios (higienização).",
    "ME0": "Extração de metadados: cópia em lote de valores EXIF e descritivos de arquivos originais.",
    "EXF": "Exposição fotográfica analógica: abertura mecânica do obturador, expondo química de prata.",
    "FLA": "Filmagem analógica: captação de quadros sucessivos em equipamentos cinematográficos ou magnéticos (VHS).",
    "FLC": "Filmagem cinematográfica clássica: processo restrito a película de cinema (8/16 mm).",
    "FLM": "Filmagem (indiscriminada): captura de movimento sem identificação da técnica ou suporte original.",
    "FOT": "Fotografia (abrangente): captura bidimensional por lente, seja química ou digital.",
    "PDF": "Geração de PDF: encapsulamento de texto/impressos em formato portátil sem garantia arquivística.",
    "PDA": "PDF/A: geração conforme ISO 19005, incorporando fontes e sem dependências externas para preservação.",
    "GRA": "Gravação analógica de áudio: registro por ondas elétricas, agulhas ou cabeças magnéticas (vinil, fita K7).",
    "GRC": "Gravação de estúdio (masterização): aquisição fonográfica original sem processamento digital.",
    "GRV": "Gravação de áudio (genérica): registro sonoro contínuo sem especificação do meio (analógico ou digital).",
    "IMG": "Imagem computação gráfica: criação artística digital sem captura por lente (design, ilustração vetorial).",
    "IMT": "Imagem matricial (raster): pixels fotossensíveis com perda de nitidez na ampliação (JPG, PNG).",
    "IVT": "Imagem vetorial: composições matemáticas de nós elásticos sem degradação em escalas (AI, SVG).",
    "MI0": "Inserção de metadados: enxerto de campos IPTC ou XML no corpo do arquivo digital.",
    "IMP": "Impressão: gravação de tinta por choque, prensa ou plotter (offset, toner, jato de tinta).",
    "LCM": "Levantamento computacional de metadados: geração de listas com propriedades e tamanhos para inventário.",
    "LSM": "Levantamento simples de nomes: script que lista apenas os nomes de arquivos sem metadados adicionais.",
    "MAN": "Manuscrito: escrita manual direta sobre suporte analógico com tinta/carvão.",
    "MFM": "Microfilmagem: redução ótica de imagens para filme de alta segurança e resolução miniaturizada.",
    "MCR": "Movimentação com renomeação: alteração de nome e diretório simultaneamente.",
    "MSR": "Movimentação simples: transferência de arquivos sem alteração de nomenclatura.",
    "NDG": "Nato-digital: documento nascido em ambiente informático, sem original físico.",
    "NEG": "Negativo fotográfico: imagem com tons invertidos, em suporte translúcido, para revelação posterior.",
    "PP1": "Checksum de integridade: criptografia alfanumérica (hash) para monitoramento de corrupção.",
    "PP2": "Empacotamento OAIS: criação de DIP/SIP para envio de longo prazo (ex.: RDC-Arq).",
    "OCR": "Reconhecimento ótico de caracteres: extração de strings textuais de imagens, gerando camada editável.",
    "RNM": "Renomeação pura: reescritura do nome do arquivo sem mover, copiar ou modificar conteúdo.",
    "NDT": "Técnica não determinada: impossibilidade de identificação do processo técnico original.",
    "VAR": "Técnica variada: mistura de processos em um mesmo agrupamento documental.",
    "TXT": "Texto digital: codificação de letras e linguagens em formatos computacionais legíveis.",
    "V00": "Validação de formatos: varredura para conferir se perfis PRONOM correspondem à estrutura lógica.",
    "VDP": "Teste de desempenho: medição de velocidade e resistência de sistemas com carga de trabalho.",
    "CKC": "Verificação de integridade: comparação de hash/checksum contra base gerada para auditoria.",
    "CKO": "Cálculo de checksum: geração da assinatura criptográfica de um arquivo para atestar integridade.",
    "VID": "Captura de vídeo digital: codificação de quadros por sensor ou exportação de editores nativos.",
}

DICT_FORMA = {
    "AMP": "Cópia ampliada: impressão fotográfica com tamanho superior ao negativo original.",
    "CON": "Cópia por contato: impressão do mesmo tamanho do negativo, obtida por contato direto.",
    "DB0": "Cópia digital de baixa resolução: thumbnail ou proxy gerado automaticamente para acesso rápido.",
    "DT0": "Cópia digital de acesso direto: extraída manualmente da matriz, sem edição.",
    "DT1": "Cópia digital de difusão: processada intencionalmente (compressão, recorte) com método documentado.",
    "DTX": "Cópia digital de acesso com perda: contém tratamento ou compressão cujo histórico de edição é desconhecido.",
    "MB0": "Original nato-digital gerado de forma autônoma por sistema, sem operação humana arquivo por arquivo (ex.: tabela de microdados extraída via script em R).",
    "MT0": "Arquivo de alta resolução gerado por operação direta no equipamento, sem retoques (ex.: fotografia recém-capturada de um pátio ou planta escaneada).",
    "MT1": "Matriz de preservação com intervenção documentada: recebeu correções arquivísticas (balanço, gama) com registro completo.",
    "MTX": "Matriz com manipulação opaca: alta resolução, mas com alterações cujo histórico se perdeu.",
    "NEG": "Negativo original: imagem primária em suporte translúcido, com inversão de luminosidade.",
}


# ============================================================
# Funções utilitárias
# ============================================================
ROTULOS = {
    "genero": {"AVS": "Audiovisual"},
    "forma": {"MT0": "Matriz bruta", "MB0": "Original nato-digital automático"},
}


def descrever_sigla(sigla, tipo=None):
    """Retorna a descrição completa de uma sigla.

    tipo: 'genero', 'especie', 'tecnica', 'forma' ou None (busca em todos).
    Retorna '' se não encontrar.
    """
    if not sigla:
        return ""
    s = str(sigla).strip().upper()
    mapa = {
        "genero": DICT_GENERO,
        "especie": DICT_ESPECIE,
        "tecnica": DICT_TECNICA,
        "forma": DICT_FORMA,
    }
    if tipo and tipo in mapa:
        return mapa[tipo].get(s, "")
    for d in (DICT_GENERO, DICT_ESPECIE, DICT_TECNICA, DICT_FORMA):
        if s in d:
            return d[s]
    return ""


def rotular_sigla(sigla, tipo=None, mostrar_descricao=True):
    """Formato pronto para exibição em filtros.

    Ex.: 'FOT — Fotografia: imagem fixada...'
    Se não achar a sigla, devolve a própria sigla.
    """
    if not sigla:
        return ""
    s = str(sigla).strip()
    desc = descrever_sigla(s, tipo=tipo)
    if not desc or not mostrar_descricao:
        return s
    return f"{rotulo_curto_sigla(s, tipo)} — {s.upper()}"

def rotulo_curto_sigla(sigla, tipo=None):
    """Retorna apenas o rótulo curto da sigla, sem sigla e sem parênteses.

    Exemplos:
        FOT (especie)  -> "Fotografia"
        TXT (genero)   -> "Textual"
        VAR (tecnica)  -> "Técnica variada"
        MT0 (forma)    -> "Arquivo de alta resolução gerado por operação
                           direta no equipamento"
    Se a sigla não existir no vocabulário, devolve a própria sigla.
    """
    if not sigla:
        return ""
    s = str(sigla).strip()
    if tipo in ROTULOS and s.upper() in ROTULOS[tipo]:
        return ROTULOS[tipo][s.upper()]
    desc = descrever_sigla(s, tipo=tipo)
    if not desc:
        return s
    # Corta no primeiro ":" (rótulo antes da explicação)
    rotulo = re.split(r"\s*\(ex\.?", desc, maxsplit=1)[0].split(":", 1)[0].strip()
    # Remove parênteses do tipo "(abrangente)", "(sem especificação)"
    rotulo = re.sub(r"\s*\([^)]*\)\s*", " ", rotulo).strip()
    # Colapsa espaços duplos
    rotulo = re.sub(r"\s+", " ", rotulo).strip()
    return rotulo or s
