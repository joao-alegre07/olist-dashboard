"""
Dashboard Olist — o que determina a satisfação do cliente?

Rodar a partir da raiz do projeto:
    streamlit run app/app.py
"""
import pandas as pd
import streamlit as st

from core.data import ORDEM_REGIAO, Filtros, carregar, filtrar
from core.ui import mes_label

st.set_page_config(page_title="Dashboard Olist", page_icon=":material/insights:", layout="wide")

dados = carregar()
pedidos_todos = dados["pedidos"]

# ---------------- Filtros globais (valem para todas as páginas) ----------------
meses = sorted(pedidos_todos.mes.dropna().unique())
meses = [pd.Timestamp(m) for m in meses]

PADROES = {
    "f_periodo": (meses[0], meses[-1]),
    "f_regioes": [],
    "f_ufs": [],
    "f_grupos": [],
    "f_pagamentos": [],
    "f_invalidos": False,
}
for chave, valor in PADROES.items():
    st.session_state.setdefault(chave, valor)


def limpar_filtros():
    for chave, valor in PADROES.items():
        st.session_state[chave] = valor


with st.sidebar:
    st.header("Filtros")
    st.caption("Os filtros valem para todas as páginas.")

    inicio, fim = st.select_slider(
        "Período da compra", options=meses, format_func=mes_label, key="f_periodo",
        value=PADROES["f_periodo"],  # sem isso, a partir do 2º rerun o widget volta como valor único
    )

    regioes = st.multiselect("Região do cliente", ORDEM_REGIAO, key="f_regioes", placeholder="Todas")

    ufs_disponiveis = sorted(
        pedidos_todos[pedidos_todos.cliente_regiao.isin(regioes)].cliente_uf.unique()
        if regioes else pedidos_todos.cliente_uf.unique()
    )
    st.session_state["f_ufs"] = [u for u in st.session_state["f_ufs"] if u in ufs_disponiveis]
    ufs = st.multiselect("Estado do cliente", ufs_disponiveis, key="f_ufs", placeholder="Todos")

    grupos = st.multiselect(
        "Grupo de categoria", sorted(dados["itens"].grupo_categoria.dropna().unique()),
        key="f_grupos", placeholder="Todos",
        help="Um pedido entra no recorte se tiver ao menos um item do grupo escolhido.",
    )
    pagamentos = st.multiselect(
        "Forma de pagamento", sorted(pedidos_todos.pagamento_principal.dropna().unique()),
        key="f_pagamentos", placeholder="Todas",
        help="Forma principal: a de maior valor no pedido.",
    )
    incluir_invalidos = st.toggle(
        "Incluir cancelados e indisponíveis", key="f_invalidos",
        help="Por padrão, os KPIs consideram só pedidos válidos (sem cancelados e indisponíveis).",
    )
    st.button("Limpar filtros", on_click=limpar_filtros, width="stretch")

filtros = Filtros(
    inicio=inicio, fim=fim, regioes=tuple(regioes), ufs=tuple(ufs), grupos=tuple(grupos),
    pagamentos=tuple(pagamentos), incluir_invalidos=incluir_invalidos,
)
pedidos_f, itens_f = filtrar(dados, filtros)
st.session_state["pedidos_f"] = pedidos_f
st.session_state["itens_f"] = itens_f
st.session_state["dados"] = dados

with st.sidebar:
    st.divider()
    st.caption(
        f"Recorte atual: **{len(pedidos_f):,}** pedidos de **{len(pedidos_todos):,}**".replace(",", ".")
    )

# ---------------- Navegação ----------------
paginas = [
    st.Page("views/visao_geral.py", title="Visão geral", icon=":material/dashboard:", default=True),
    st.Page("views/logistica.py", title="Logística e satisfação", icon=":material/local_shipping:"),
    st.Page("views/geografia.py", title="Clientes e geografia", icon=":material/map:"),
    st.Page("views/produtos.py", title="Produtos e vendedores", icon=":material/storefront:"),
    st.Page("views/exploracao.py", title="Exploração", icon=":material/table_view:"),
    st.Page("views/modelo.py", title="Dados e modelo", icon=":material/schema:"),
]
st.navigation(paginas).run()
