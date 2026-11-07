import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import metrics as m
from core.data import com_mes, dados_filtrados
from core.ui import (AZUL, CINZA, brl, estilo, exigir_dados, grafico, insight, kpi, mes_label, num,
                     pct, pontos_selecionados)

p, it = dados_filtrados()

st.title("O que determina a satisfação do cliente na Olist?")
st.caption(
    "Base pública da Olist (Kaggle), pedidos de jan/2017 a ago/2018. "
    "Comece pela visão geral e siga as páginas da barra lateral para investigar."
)
exigir_dados(p)

# ---------------- KPIs ----------------
c = st.columns(4)
kpi(c[0], "Receita", brl(m.receita(it), compacto=True), m.AJUDA["receita"])
kpi(c[1], "Pedidos", num(m.pedidos(p)), m.AJUDA["pedidos"])
kpi(c[2], "Ticket médio", brl(m.ticket_medio(p, it)), m.AJUDA["ticket"])
kpi(c[3], "Clientes únicos", num(m.clientes_unicos(p)), m.AJUDA["clientes"])
c = st.columns(4)
kpi(c[0], "Nota média", num(m.nota_media(p), 2), m.AJUDA["nota"])
kpi(c[1], "Entregas no prazo", pct(m.pct_no_prazo(p)), m.AJUDA["prazo"])
kpi(c[2], "Taxa de recompra", pct(m.taxa_recompra(p)), m.AJUDA["recompra"])
kpi(c[3], "Frete sobre receita", pct(m.frete_sobre_receita(it)), m.AJUDA["frete"])

# ---------------- Evolução mensal ----------------
st.subheader("Como o negócio evoluiu")
metrica = st.segmented_control(
    "Métrica", ["Receita", "Pedidos", "Ticket médio"], default="Pedidos", key="vg_metrica",
    label_visibility="collapsed",
) or "Pedidos"

itm = com_mes(it, p)
mensal = (
    p.groupby("mes").pedido_id.nunique().rename("Pedidos").to_frame()
    .join(itm.groupby("mes").preco.sum().rename("Receita"))
    .reset_index()
)
mensal["Ticket médio"] = mensal.Receita / mensal.Pedidos
mensal["rotulo"] = mensal.mes.map(mes_label)

fmt_hover = {"Receita": "R$ %{y:,.0f}", "Pedidos": "%{y:,.0f} pedidos", "Ticket médio": "R$ %{y:,.2f}"}
fig = go.Figure(go.Scatter(
    x=mensal.mes, y=mensal[metrica], mode="lines+markers", line=dict(color=AZUL, width=2),
    marker=dict(size=7), customdata=mensal.rotulo,
    hovertemplate="%{customdata}<br>" + fmt_hover[metrica] + "<extra></extra>",
))
pico = mensal.loc[mensal[metrica].idxmax()]
fig.add_annotation(
    x=pico.mes, y=pico[metrica], text=f"Pico: {pico.rotulo}", showarrow=True, arrowhead=0, ay=-30,
    font=dict(size=12),
)
bf = pd.Timestamp("2017-11-01")
if bf in set(mensal.mes) and pico.mes != bf:
    fig.add_annotation(x=bf, y=mensal.set_index("mes").loc[bf, metrica], text="Black Friday",
                       showarrow=True, arrowhead=0, ay=-30, font=dict(size=12))
fig.update_xaxes(tickformat="%b/%y", dtick="M2")
fig.update_yaxes(title=metrica, rangemode="tozero")
grafico(estilo(fig, 340), key="vg_linha")

# ---------------- Categorias com drill ----------------
st.subheader("O que mais se vende")
col_a, col_b = st.columns([1, 1])
grupos = itm.groupby("grupo_categoria").agg(receita=("preco", "sum"), pedidos=("pedido_id", "nunique"))
grupos = grupos.sort_values("receita")
grupos["share"] = grupos.receita / grupos.receita.sum()

with col_a:
    st.caption("Receita por grupo de categoria. **Clique numa barra** para ver as categorias do grupo.")
    fig = go.Figure(go.Bar(
        x=grupos.receita, y=grupos.index, orientation="h", marker_color=AZUL,
        customdata=list(zip(grupos.index, grupos.share, grupos.pedidos)),
        hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f} (%{customdata[1]:.1%} da receita)"
                      "<br>%{customdata[2]:,} pedidos<extra></extra>",
    ))
    fig.update_xaxes(title="Receita (R$)")
    evento = grafico(estilo(fig, 420), key="vg_grupos", selecionavel=True)

sel = pontos_selecionados(evento)
grupo_sel = sel[0]["y"] if sel else grupos.index[-1]

with col_b:
    cats = (
        itm[itm.grupo_categoria == grupo_sel].groupby("categoria")
        .agg(receita=("preco", "sum"), pedidos=("pedido_id", "nunique"))
        .sort_values("receita").tail(10)
    )
    st.caption(f"Categorias de **{grupo_sel}**" + ("" if sel else " (grupo de maior receita)") + ".")
    fig = go.Figure(go.Bar(
        x=cats.receita, y=cats.index, orientation="h", marker_color=CINZA,
        customdata=cats.pedidos,
        hovertemplate="<b>%{y}</b><br>R$ %{x:,.0f}<br>%{customdata:,} pedidos<extra></extra>",
    ))
    fig.update_xaxes(title="Receita (R$)")
    grafico(estilo(fig, 420), key="vg_categorias")

# ---------------- Interpretação ----------------
diario = p.groupby(p.data_compra.dt.date).pedido_id.nunique()
melhor_dia = diario.idxmax()
media_dia = diario.mean()
topo = grupos.iloc[-1]
texto = [
    f"- O dia com mais pedidos no recorte foi **{melhor_dia:%d/%m/%Y}**, com **{num(diario.max())}** pedidos, "
    f"{num(diario.max() / media_dia, 1)}× a média diária."
    + (" É a Black Friday de 2017." if str(melhor_dia) == "2017-11-24" else ""),
    f"- **{topo.name}** lidera a receita, com {pct(topo.share)} do total.",
    f"- A taxa de recompra é de apenas **{pct(m.taxa_recompra(p))}**: quase todo pedido vem de um cliente novo. "
    "Por isso a experiência da primeira compra pesa tanto, e é o que as próximas páginas investigam.",
]
if len(mensal) >= 12:
    a = mensal.Pedidos.iloc[:6].mean()
    b = mensal.Pedidos.iloc[-6:].mean()
    texto.insert(0, f"- A média de pedidos por mês saiu de **{num(a)}** nos 6 primeiros meses do recorte para "
                    f"**{num(b)}** nos 6 últimos ({pct(b / a - 1, 0)} de crescimento).")
insight(*texto)
