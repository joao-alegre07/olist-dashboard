# O que tem no dashboard

Referência de tudo o que aparece na tela: filtros, páginas, KPIs, gráficos e interações. Código em `app/`.

## Barra lateral (todas as páginas)

Os filtros ficam em `app/app.py` e valem para todas as páginas. O recorte resultante é guardado em
`st.session_state` e lido pelas páginas com `dados_filtrados()` (`app/core/data.py`).

| Filtro | Key | Comportamento |
| --- | --- | --- |
| Período da compra | `f_periodo` | Slider de intervalo por mês, jan/2017 a ago/2018 |
| Região do cliente | `f_regioes` | Norte, Nordeste, Centro-Oeste, Sudeste, Sul. Vazio = todas |
| Estado do cliente | `f_ufs` | Lista só os estados das regiões escolhidas; estados fora delas são descartados |
| Grupo de categoria | `f_grupos` | 13 grupos. Filtra a tabela de itens e volta para os pedidos: o pedido entra se tiver ao menos um item do grupo |
| Forma de pagamento | `f_pagamentos` | Forma principal do pedido (a de maior valor) |
| Incluir cancelados e indisponíveis | `f_invalidos` | Desligado por padrão: KPIs só com pedidos válidos |
| Limpar filtros | — | Volta tudo ao padrão |

No rodapé da barra lateral aparece "Recorte atual: X pedidos de Y".

Quando o recorte fica vazio, cada página mostra o aviso "Nenhum pedido no recorte atual. Amplie os filtros na barra
lateral." em vez de um erro.

## Padrão de toda página

- Cartões de KPI no topo, com um ícone de ajuda que mostra a fórmula e o motivo do indicador.
- Gráficos com hover em português (números no formato 1.234,56).
- Uma caixa **"O que os dados mostram"** no fim. Os textos são calculados a partir do recorte atual, então mudam
  com os filtros.

Paleta: azul `#2a78d6` para a série principal, vermelho `#d03b3b` só para "ruim" (atraso, abaixo da média), cinza
para contexto. Nenhum gráfico usa eixo duplo.

## 1. Visão geral (`views/visao_geral.py`)

Pergunta: qual o tamanho do negócio, como evoluiu e o que mais vende?

- **KPIs (8):** receita, pedidos, ticket médio, clientes únicos, nota média, entregas no prazo, taxa de recompra,
  frete sobre receita.
- **Linha mensal:** seletor entre Receita, Pedidos e Ticket médio. Anota o pico e a Black Friday (nov/2017).
- **Barras por grupo de categoria (receita):** clicar numa barra seleciona o grupo (`on_select`).
- **Barras das 10 principais categorias do grupo selecionado:** sem clique, mostra o grupo de maior receita.
- **Interpretação:** crescimento entre os 6 primeiros e os 6 últimos meses, dia de maior volume, grupo líder e
  taxa de recompra.

## 2. Logística e satisfação (`views/logistica.py`)

Pergunta: o atraso na entrega explica a nota?

- **KPIs (5):** % no prazo, tempo médio de entrega, prazo prometido médio, nota dos entregues no prazo, nota dos
  entregues com atraso.
- **Nota média por faixa de atraso:** no prazo, 1 a 3, 4 a 7, 8 a 14, 15+ dias. Azul = no prazo, vermelho =
  atrasado. É o gráfico central da apresentação.
- **% de notas 1 ou 2 por faixa de atraso.**
- **Histograma do tempo de entrega:** dias até 60 (acima disso, agrupados em 60), com linhas da média real e da
  média prometida.
- **% no prazo por estado:** estados com 30+ entregas; vermelho = abaixo da média do recorte.
- **Dispersão distância × dias de entrega:** amostra de 4.000 pedidos (mesmo estado vs. outro estado) e a mediana
  a cada 250 km, calculada com todos os pedidos.
- **Interpretação:** nota no prazo vs. atrasado, faixa a partir da qual a maioria vira nota 1 ou 2, participação
  dos atrasos nas notas ruins, prometido vs. real, mesmo estado vs. outro estado.

## 3. Clientes e geografia (`views/geografia.py`)

Pergunta: onde estão os clientes, onde a entrega demora e o cliente volta?

- **KPIs (4):** clientes únicos, taxa de recompra, estados atendidos, frete sobre receita.
- **Mapa por estado:** um círculo por estado (tamanho = pedidos). A cor segue o seletor: pedidos, tempo médio de
  entrega, % no prazo, nota média ou frete sobre receita.
- **Detalhar um estado:** caixa de seleção e tabela das 15 maiores cidades (pedidos, dias, % no prazo, nota).
- **Frete ÷ receita por região** e **tabela comparativa das regiões** (% dos pedidos, ticket, frete, prazo
  prometido, entrega real, % no prazo, nota).
- **Recompra:** rosca "comprou uma vez" vs. "2 ou mais" e barras de quantos pedidos fizeram os que voltam.
- **Interpretação:** concentração no Sudeste, peso do frete no Norte e Nordeste, região com pior prazo e pior nota,
  caso do Norte (promessa longa), recompra.

## 4. Produtos e vendedores (`views/produtos.py`)

Pergunta: quais categorias e vendedores concentram atraso e insatisfação?

- **Dispersão de categorias (% de atraso × nota média):** slider de mínimo de pedidos (padrão 200). Tamanho =
  pedidos; vermelho = acima da média de atraso e abaixo da média de nota; linhas pontilhadas nas médias.
- **10 vendedores com pior nota:** slider de mínimo de pedidos (padrão 30). IDs encurtados, com o estado.
- **Curva de concentração da receita entre vendedores:** marca quanto os 10% maiores respondem.
- **Forma principal de pagamento (rosca)** e **parcelamento no cartão de crédito.**
- **Interpretação:** pior categoria, quantas caem no quadrante ruim, concentração dos vendedores, peso do cartão
  parcelado.

## 5. Exploração (`views/exploracao.py`)

Pergunta: quais pedidos estão por trás de cada número?

- Busca por cidade, categoria ou início do ID do pedido; filtros de faixa de atraso e de nota.
- Tabela de pedidos (mais recentes primeiro): compra, status, cidade, UF, categoria principal, valor, frete,
  pagamento, parcelas, dias para entregar, dias de atraso, nota.
- Botão para baixar o recorte em CSV.

## 6. Dados e modelo (`views/modelo.py`)

Não depende dos filtros: documenta a base inteira.

- Diagrama do modelo (Graphviz) e tabela de onde cada relacionamento é usado.
- Tabela de problemas da base e tratamentos, com os registros afetados (lidos de `docs/referencia.json`).
- Totais de referência e a conferência dos merges.
- Definição de cada KPI e limitações da análise.

## KPIs

Fórmulas em [kpis.md](kpis.md) e no dicionário `AJUDA` de `app/core/metrics.py`. As duas fontes precisam dizer a
mesma coisa.
