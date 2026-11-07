import json
from pathlib import Path

import pandas as pd
import streamlit as st

from core.metrics import AJUDA
from core.ui import num

REF = Path(__file__).resolve().parents[2] / "docs" / "referencia.json"

st.title("Dados e modelo")
st.caption("Como a base foi tratada, como as tabelas se relacionam e como cada indicador é calculado.")

# ---------------- Modelo ----------------
st.subheader("Modelo de dados")
st.graphviz_chart(
    """
digraph modelo {
  graph [rankdir=LR, bgcolor="transparent", fontname="Helvetica", nodesep=0.35, ranksep=0.9];
  node  [shape=box, style="rounded,filled", fillcolor="#e7f1fb", color="#2a78d6", fontname="Helvetica", fontsize=11];
  edge  [color="#52514e", fontname="Helvetica", fontsize=9, arrowsize=0.6];

  geo [label="geolocation\\n(1 ponto por prefixo de CEP)", fillcolor="#f0efec", color="#898781"];
  customers [label="customers\\ncustomer_id · customer_unique_id"];
  sellers [label="sellers\\nseller_id"];
  products [label="products\\nproduct_id · categoria"];
  orders [label="orders  (fato: pedido)\\norder_id", fillcolor="#2a78d6", fontcolor="white"];
  items [label="order_items  (fato: item)\\norder_id + order_item_id", fillcolor="#2a78d6", fontcolor="white"];
  payments [label="order_payments\\n(agregado por pedido)"];
  reviews [label="order_reviews\\n(1 por pedido)"];

  orders -> customers [label="customer_id  N:1"];
  items -> orders [label="order_id  N:1"];
  items -> products [label="product_id  N:1"];
  items -> sellers [label="seller_id  N:1"];
  payments -> orders [label="order_id  N:1"];
  reviews -> orders [label="order_id  N:1"];
  customers -> geo [label="zip_code_prefix  N:1", style=dashed];
  sellers -> geo [label="zip_code_prefix  N:1", style=dashed];
}
""",
)

st.markdown("**Onde cada relacionamento é usado no dashboard**")
st.dataframe(
    pd.DataFrame([
        ["itens → pedidos", "Receita mensal, filtro de categoria (um pedido entra se tiver item do grupo)", "Visão geral, todas"],
        ["pedidos → clientes", "Clientes únicos, recompra, estado e região do cliente", "Visão geral, Geografia"],
        ["pedidos → avaliações", "Nota média por faixa de atraso, por estado, por categoria", "Logística, Produtos"],
        ["itens → produtos", "Receita e atraso por categoria e grupo", "Visão geral, Produtos"],
        ["itens → vendedores", "Ranking de vendedores, concentração da receita, mesmo estado ou não", "Produtos, Logística"],
        ["clientes e vendedores → geolocalização", "Distância vendedor–cliente e posição dos estados no mapa", "Logística, Geografia"],
        ["pedidos → pagamentos", "Forma principal de pagamento (filtro) e parcelamento", "Produtos, filtros"],
    ], columns=["Relacionamento", "Uso", "Páginas"]),
    hide_index=True, width="stretch",
)

# ---------------- Tratamento ----------------
st.subheader("Tratamento dos dados")
ref = json.loads(REF.read_text(encoding="utf-8")) if REF.exists() else {}
t = ref.get("tratamentos", {})
tratamentos = pd.DataFrame([
    ["Período incompleto", "2016 e set–out/2018 têm volume residual", "Recorte jan/2017 a ago/2018",
     t.get("pedidos_fora_do_periodo")],
    ["Geolocalização repetida", "~1 milhão de linhas, várias por CEP; pontos fora do Brasil",
     "Remove pontos fora do Brasil e usa a média por prefixo de CEP", t.get("geo_pontos_fora_do_brasil")],
    ["Cliente muda de ID a cada pedido", "customer_id é gerado por pedido",
     "Clientes e recompra contados por customer_unique_id", None],
    ["Avaliações duplicadas", "Pedidos com mais de uma avaliação", "Mantém a respondida mais recentemente",
     t.get("avaliacoes_duplicadas_por_pedido")],
    ["Produtos sem categoria", "Categoria nula", "Categoria \"Sem categoria\", grupo \"Outros\"",
     t.get("produtos_sem_categoria")],
    ["Nomes de categoria", "73 categorias em snake_case, algumas repetidas (_2)",
     "Nomes legíveis e 13 grupos de categoria", None],
    ["Pagamentos em várias linhas", "Um pedido pode ter cartão + voucher",
     "Agregado por pedido; forma principal = a de maior valor", None],
    ["Tipo de pagamento indefinido", "payment_type = not_defined", "Removido", t.get("pagamentos_tipo_indefinido")],
    ["Entregue sem data de entrega", "Status delivered sem data", "Fora das métricas de prazo",
     t.get("entregues_sem_data_de_entrega")],
    ["Clientes sem geolocalização", "CEP não encontrado na tabela de geolocalização", "Ficam fora do mapa e da distância",
     t.get("clientes_sem_geolocalizacao")],
], columns=["Problema", "Detalhe", "Tratamento", "Registros afetados"])
st.dataframe(tratamentos, hide_index=True, width="stretch",
             column_config={"Registros afetados": st.column_config.NumberColumn(format="localized")})

if ref:
    c = st.columns(4)
    c[0].metric("Pedidos no período", num(ref["pedidos_no_periodo"]))
    c[1].metric("Pedidos válidos", num(ref["pedidos_validos"]))
    c[2].metric("Itens", num(ref["itens_no_periodo"]))
    c[3].metric("Clientes únicos", num(ref["clientes_unicos"]))
    with st.expander("Conferência dos merges (nenhum duplicou linhas)"):
        st.dataframe(pd.DataFrame(ref["merges"]).rename(columns={
            "merge": "Merge", "linhas_antes": "Linhas antes", "linhas_depois": "Linhas depois"}),
            hide_index=True, width="stretch")

# ---------------- KPIs ----------------
st.subheader("Definição dos indicadores")
nomes = {
    "receita": "Receita", "pedidos": "Pedidos", "ticket": "Ticket médio", "clientes": "Clientes únicos",
    "recompra": "Taxa de recompra", "prazo": "% entregas no prazo", "dias": "Tempo médio de entrega",
    "prometido": "Prazo prometido médio", "nota": "Nota média", "notas_baixas": "% notas baixas",
    "frete": "Frete sobre receita",
}
st.dataframe(pd.DataFrame([[nomes[k], v] for k, v in AJUDA.items()], columns=["Indicador", "Cálculo e motivo"]),
             hide_index=True, width="stretch")

st.subheader("Limitações")
st.markdown(
    "- A base não tem custo dos produtos: não é possível falar de margem ou lucro.\n"
    "- O período é curto (20 meses), o que limita a análise de recompra e sazonalidade.\n"
    "- Os dados são anonimizados: vendedores e clientes aparecem só por ID.\n"
    "- Atraso e nota andam juntos, mas correlação não prova causa: o mesmo problema (produto errado, avaria) "
    "pode gerar os dois.\n"
    "- A base cobre só pedidos que passaram pela Olist, não o e-commerce brasileiro como um todo."
)
