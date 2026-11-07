import streamlit as st

from core.data import ORDEM_FAIXA_ATRASO, dados_filtrados
from core.ui import exigir_dados, num

p, it = dados_filtrados()

st.title("Exploração")
st.caption("Os pedidos por trás de cada número. A tabela respeita os filtros da barra lateral.")
exigir_dados(p)

c1, c2, c3 = st.columns([2, 1, 1])
busca = c1.text_input("Buscar por cidade, categoria ou ID do pedido", key="ex_busca",
                      placeholder="ex.: salvador, cama, 8a2e7…")
faixas = c2.multiselect("Faixa de atraso", ORDEM_FAIXA_ATRASO, key="ex_faixas", placeholder="Todas")
notas = c3.multiselect("Nota", [1, 2, 3, 4, 5], key="ex_notas", placeholder="Todas")

t = p
if busca:
    b = busca.strip().lower()
    t = t[
        t.cliente_cidade.str.lower().str.contains(b, na=False, regex=False)
        | t.categoria.str.lower().str.contains(b, na=False, regex=False)
        | t.pedido_id.str.startswith(b)
    ]
if faixas:
    t = t[t.faixa_atraso.isin(faixas)]
if notas:
    t = t[t.nota.isin(notas)]

colunas = ["pedido_id", "data_compra", "status", "cliente_cidade", "cliente_uf", "categoria", "receita", "frete",
           "pagamento_principal", "parcelas", "dias_entrega", "dias_atraso", "nota"]
t = t.sort_values("data_compra", ascending=False)[colunas]

st.caption(f"{num(len(t))} pedidos")
st.dataframe(
    t, hide_index=True, width="stretch", height=560,
    column_config={
        "pedido_id": st.column_config.TextColumn("Pedido"),
        "data_compra": st.column_config.DatetimeColumn("Compra", format="DD/MM/YYYY HH:mm"),
        "status": st.column_config.TextColumn("Status"),
        "cliente_cidade": st.column_config.TextColumn("Cidade"),
        "cliente_uf": st.column_config.TextColumn("UF"),
        "categoria": st.column_config.TextColumn("Categoria principal"),
        "receita": st.column_config.NumberColumn("Produtos (R$)", format="%.2f"),
        "frete": st.column_config.NumberColumn("Frete (R$)", format="%.2f"),
        "pagamento_principal": st.column_config.TextColumn("Pagamento"),
        "parcelas": st.column_config.NumberColumn("Parcelas", format="%d"),
        "dias_entrega": st.column_config.NumberColumn("Dias p/ entregar", format="%.1f"),
        "dias_atraso": st.column_config.NumberColumn("Dias de atraso", format="%d",
                                                     help="Negativo = entregue antes da data estimada."),
        "nota": st.column_config.NumberColumn("Nota", format="%d"),
    },
)
st.download_button(
    "Baixar CSV deste recorte", t.to_csv(index=False).encode("utf-8-sig"), file_name="pedidos_olist_recorte.csv",
    mime="text/csv", icon=":material/download:",
)
