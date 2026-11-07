# Contexto para o Claude Code

Dashboard de BI (trabalho de faculdade) sobre a base Olist, em Python + Streamlit + Plotly. Textos da interface e
documentação em português do Brasil.

## Comandos

- `python etl/build.py` — regera `data/processed/` a partir de `data/raw/` (CSVs do Kaggle).
- `streamlit run app/app.py` — abre o dashboard.
- `python -m pytest tests -v -s` — testes com AppTest (6 páginas × 5 recortes, KPIs, tempo por página).

## Regras que não podem mudar sem atualizar docs/

- Período: jan/2017 a ago/2018 (`INICIO`/`FIM` em `etl/build.py`).
- KPIs padrão só com pedidos válidos (sem `canceled` e `unavailable`).
- Clientes sempre por `customer_unique_id` (coluna `cliente_id` em `pedidos`).
- Uma avaliação por pedido (a respondida por último). Pagamentos agregados por pedido.
- Receita = soma de `preco` na tabela `itens` (sem frete). Atraso em dias de calendário.
- Todo merge com `validate="m:1"`; nenhum pode duplicar linhas.
- Definições dos KPIs: `app/core/metrics.py` (dicionário `AJUDA`) e `docs/kpis.md` devem dizer a mesma coisa.

## Documentação

- `docs/dashboard.md` descreve cada página; atualize quando mudar um gráfico, filtro ou KPI.
- `docs/decisoes.md` registra decisões e pendências; acrescente uma linha a cada decisão nova.

## Convenções do app

- Filtros globais ficam em `app/app.py`; as páginas leem o recorte com `dados_filtrados()`.
- Toda função de KPI recebe dados já filtrados.
- Gráficos passam por `estilo()` e `grafico()` de `app/core/ui.py`. Paleta: azul para a série principal,
  vermelho só para "ruim" (atraso, abaixo da média), cinza para contexto. Nunca eixo duplo.
- Toda página termina com uma caixa `insight()` cujos números são calculados do recorte, não fixos.
