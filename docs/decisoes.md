# Registro de decisões

Decisões tomadas durante o desenvolvimento (conversa de planejamento com o Claude em 05 e 06/11/2026 e sessão de
testes no Claude Code). Cada linha diz o que foi decidido e por quê, para o grupo conseguir defender na
apresentação.

## Escopo e entrega

| # | Decisão | Motivo |
| --- | --- | --- |
| 1 | Base: Brazilian E-Commerce Public Dataset by Olist (Kaggle) | Escolha do grupo. Tem relacionamentos reais entre tabelas e dados temporais, geográficos e de satisfação |
| 2 | Pergunta central: "O que determina a satisfação do cliente na Olist?" | O professor avalia interpretação, não só gráficos. Um painel de vendas genérico descreve; uma pergunta obriga a investigar |
| 3 | Ferramenta: Python + Streamlit + Plotly, em vez de Power BI | Código versionável e editável pelo grupo; o script de tratamento documenta a limpeza; o professor aceita Python |
| 4 | João conduziu todos os papéis com o Claude, em uma sessão, para apresentar na segunda (09/11) | Prazo curto. A divisão de responsabilidades fica registrada por épico e nas falas da apresentação |
| 5 | Backlog em épicos (setup, dados, modelo, KPIs, páginas, filtros, validação, descobertas, apresentação), sem cronograma | Trabalho feito de uma vez; o backlog serve de checklist da entrega |

## Tratamento dos dados

| # | Decisão | Motivo |
| --- | --- | --- |
| 6 | Período de jan/2017 a ago/2018 | 2016 e set–out/2018 têm volume residual; manter distorceria as tendências |
| 7 | KPIs só com pedidos válidos (sem `canceled` e `unavailable`), com filtro para incluir | Esses pedidos não geram receita nem entrega |
| 8 | Clientes por `customer_unique_id` | O `customer_id` muda a cada pedido; com ele a recompra seria quase zero |
| 9 | Uma avaliação por pedido: a respondida por último | 551 pedidos tinham avaliações repetidas |
| 10 | Pagamentos agregados por pedido; forma principal = a de maior valor | Um pedido pode ter várias linhas (cartão + voucher); somar com itens duplicaria valores |
| 11 | Receita = preço dos itens, sem frete | Frete vira um KPI à parte (frete sobre receita) |
| 12 | Atraso em dias de calendário | A data estimada não tem horário; entrega no próprio dia conta como no prazo |
| 13 | Geolocalização: remove pontos fora do Brasil e usa a média por prefixo de CEP | 1 milhão de linhas com repetição; evita relação muitos-para-muitos e deixa o app leve |
| 14 | 73 categorias com nome em português e agrupadas em 13 grupos | Filtros e gráficos legíveis; categorias `_2` unificadas |
| 15 | Categoria e vendedor "principais" do pedido = os do item de maior preço | A tabela de pedidos precisa de um valor por pedido para filtros e tabela de exploração |
| 16 | Todo merge com `validate="m:1"` e contagem antes e depois | Garantir que nenhum relacionamento duplica linhas |
| 17 | Tabelas tratadas em CSV comprimido (`.csv.gz`), com suporte a Parquet | O ambiente onde o build rodou não tinha pyarrow; o app lê os dois formatos |

## Dashboard

| # | Decisão | Motivo |
| --- | --- | --- |
| 18 | Filtros globais na barra lateral, guardados em `session_state` | O professor pede filtros que ajudem a investigar; mudar um filtro precisa mudar todas as páginas |
| 19 | Filtro de categoria atua nos itens e volta para os pedidos | Usa o relacionamento itens → pedidos em tempo de execução, como o professor pede |
| 20 | KPIs como funções sobre o recorte filtrado (`app/core/metrics.py`) | Números sempre coerentes com os filtros |
| 21 | Caixa "O que os dados mostram" com textos calculados, não fixos | Interpretação acompanha o recorte e não fica desatualizada |
| 22 | Mapa com círculos por estado (Scattergeo), não choropleth com GeoJSON | Não depende de baixar arquivos na hora da apresentação |
| 23 | Clique no gráfico: grupo de categoria abre as categorias (em vez de clique no estado) | Seleção em barras é mais confiável no `st.plotly_chart`; o detalhamento estado → cidade ficou numa caixa de seleção |
| 24 | Página extra "Dados e modelo" | Tratamento, modelo e fórmulas ficam visíveis dentro do app durante a apresentação |
| 25 | Paleta: azul principal, vermelho só para "ruim", cinza para contexto; nunca eixo duplo | Cor com significado e leitura rápida |
| 26 | Limites mínimos: 30 entregas por estado, 200 pedidos por categoria, 30 por vendedor (ajustáveis); amostra de 4.000 pontos na dispersão | Evita conclusões sobre grupos pequenos e mantém o gráfico leve |

## Validação

| # | Decisão | Motivo |
| --- | --- | --- |
| 27 | Totais conferidos contra os CSVs brutos por um cálculo independente | 97.905 pedidos válidos, R$ 13.449.529,68 e 94.703 clientes bateram |
| 28 | Testes automatizados com `streamlit.testing.v1.AppTest` (feitos no Claude Code) | 5 recortes de filtro × 6 páginas, KPIs da Visão geral, busca da Exploração e tempo por página |
| 29 | Correção do Claude Code: `value=` no slider de período | Sem isso, a partir da segunda interação o slider voltava como valor único e quebrava o intervalo |

## Apresentação

| # | Decisão | Motivo |
| --- | --- | --- |
| 30 | 16 slides, cerca de 13 minutos, narrativa pergunta → base → como foi feito → demo → descobertas → decisões → limitações | Segue o que o professor pede na seção de interpretação dos resultados |
| 31 | Falas: João (1–3, 14–16), Mateus (4–7), Iago (demo, 8), Guilherme (9–13) | Cada integrante apresenta uma parte; roteiro em [roteiro-de-falas.pdf](roteiro-de-falas.pdf) |
| 32 | Descobertas apresentadas como associação, não causa | A base não permite provar que o atraso causa a nota ruim |

## Pendências conhecidas

- **Aviso amarelo do slider de período (não confirmado):** com `value=` no widget e a mesma key pré-carregada no
  `session_state`, o Streamlit pode mostrar "The widget with key f_periodo was created with a default value but
  also had its value set via the Session State API" na primeira abertura. Correção sugerida: tirar `f_periodo` do
  `setdefault` e, em "Limpar filtros", usar `st.session_state.pop("f_periodo", None)`. Conferir abrindo o app.
- O teste do recorte vazio verifica se existe *algum* aviso; o ideal é procurar o texto "Nenhum pedido no recorte
  atual".
- O clique no gráfico de grupos e o mapa não são cobertos pelos testes automatizados: conferir no navegador.
- Plano B da apresentação (vídeo da demo ou publicação no Streamlit Community Cloud) não foi feito.
