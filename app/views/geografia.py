import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import metrics as m
from core.data import ORDEM_REGIAO, com_mes, dados_filtrados
from core.ui import AZUL, CINZA, ESCALA_AZUL, brl, estilo, exigir_dados, grafico, insight, kpi, num, pct

p, it = dados_filtrados()

st.title("Clientes e geografia")
st.caption("Onde estão os clientes, onde a entrega demora e quem paga mais caro pelo frete.")
exigir_dados(p)

# ---------------- Agregados por estado ----------------
itu = com_mes(it, p, colunas=("cliente_uf", "cliente_regiao"))
e = m.entregues(p)
por_uf = (
    p.groupby("cliente_uf").agg(regiao=("cliente_regiao", "first"), pedidos=("pedido_id", "nunique"))
    .join(itu.groupby("cliente_uf").agg(receita=("preco", "sum"), frete=("frete", "sum")))
    .join(e.groupby("cliente_uf").agg(dias=("dias_entrega", "mean"), prazo=("no_prazo", "mean")))
    .join(p.groupby("cliente_uf").agg(nota=("nota", "mean")))
)
por_uf["ticket"] = por_uf.receita / por_uf.pedidos
por_uf["frete_pct"] = por_uf.frete / por_uf.receita

# Centro aproximado de cada estado = média das coordenadas dos clientes (via geolocalização)
todos = st.session_state["dados"]["pedidos"]
centros = todos.groupby("cliente_uf")[["cliente_lat", "cliente_lng"]].mean() if "cliente_lat" in todos else None

c = st.columns(4)
kpi(c[0], "Clientes únicos", num(m.clientes_unicos(p)), m.AJUDA["clientes"])
kpi(c[1], "Taxa de recompra", pct(m.taxa_recompra(p)), m.AJUDA["recompra"])
kpi(c[2], "Estados atendidos", num(len(por_uf)), "Estados com ao menos um pedido no recorte.")
kpi(c[3], "Frete sobre receita", pct(m.frete_sobre_receita(it)), m.AJUDA["frete"])

# ---------------- Mapa + detalhamento por cidade ----------------
st.subheader("Mapa por estado")
opcoes = {
    "Pedidos": ("pedidos", "{:,.0f} pedidos", ",.0f"),
    "Tempo médio de entrega (dias)": ("dias", "{:.1f} dias", ".1f"),
    "% entregue no prazo": ("prazo", "{:.1%}", ".0%"),
    "Nota média": ("nota", "{:.2f}", ".2f"),
    "Frete sobre receita": ("frete_pct", "{:.1%}", ".0%"),
}
escolha = st.segmented_control("Cor do mapa", list(opcoes), default="Tempo médio de entrega (dias)",
                               key="geo_metrica") or "Pedidos"
col_metrica, _, fmt_eixo = opcoes[escolha]

col_a, col_b = st.columns([3, 2])
with col_a:
    if centros is not None:
        mapa = por_uf.join(centros, how="inner")
        tam = 12 + 48 * (mapa.pedidos / mapa.pedidos.max()) ** 0.5
        fig = go.Figure(go.Scattergeo(
            lat=mapa.cliente_lat, lon=mapa.cliente_lng, text=mapa.index, mode="markers+text",
            textposition="middle center", textfont=dict(size=10, color="#0b0b0b"),
            marker=dict(
                size=tam, color=mapa[col_metrica], colorscale=ESCALA_AZUL, line=dict(width=1, color="#fcfcfb"),
                colorbar=dict(title=dict(text=escolha, side="right"), tickformat=fmt_eixo, thickness=12),
                opacity=0.9,
            ),
            customdata=mapa[["pedidos", col_metrica]].values,
            hovertemplate="<b>%{text}</b><br>" + escolha + ": %{customdata[1]:" + fmt_eixo + "}"
                          "<br>%{customdata[0]:,.0f} pedidos<extra></extra>",
        ))
        fig.update_geos(
            scope="south america", fitbounds="locations", showcountries=True, countrycolor="#c3c2b7",
            showland=True, landcolor="#f0efec", showocean=False, showlakes=False, bgcolor="rgba(0,0,0,0)",
            projection_type="mercator",
        )
        fig.update_layout(geo=dict(domain=dict(x=[0, 1], y=[0, 1])))
        grafico(estilo(fig, 520), key="geo_mapa")
        st.caption("Tamanho do círculo = número de pedidos. Cor = métrica escolhida acima.")

with col_b:
    st.markdown("**Detalhar um estado**")
    ufs = por_uf.sort_values("pedidos", ascending=False).index.tolist()
    uf_sel = st.selectbox("Estado", ufs, index=0, key="geo_uf", label_visibility="collapsed")
    pu = p[p.cliente_uf == uf_sel]
    eu = pu[pu.entregue]
    cidades = (
        pu.groupby("cliente_cidade").agg(pedidos=("pedido_id", "nunique"), nota=("nota", "mean"))
        .join(eu.groupby("cliente_cidade").agg(dias=("dias_entrega", "mean"), prazo=("no_prazo", "mean")))
        .sort_values("pedidos", ascending=False).head(15).reset_index()
    )
    linha = por_uf.loc[uf_sel]
    st.caption(
        f"{uf_sel}: {num(linha.pedidos)} pedidos · {num(linha.dias, 1)} dias em média · "
        f"{pct(linha.prazo)} no prazo · nota {num(linha.nota, 2)}"
    )
    st.dataframe(
        cidades, hide_index=True, width="stretch", height=430,
        column_config={
            "cliente_cidade": st.column_config.TextColumn("Cidade"),
            "pedidos": st.column_config.NumberColumn("Pedidos", format="localized"),
            "dias": st.column_config.NumberColumn("Dias", format="%.1f"),
            "prazo": st.column_config.ProgressColumn("No prazo", format="percent", min_value=0, max_value=1),
            "nota": st.column_config.NumberColumn("Nota", format="%.2f"),
        },
    )

# ---------------- Regiões ----------------
st.subheader("Comparação entre regiões")
reg = (
    p.groupby("cliente_regiao").agg(pedidos=("pedido_id", "nunique"), nota=("nota", "mean"))
    .join(itu.groupby("cliente_regiao").agg(receita=("preco", "sum"), frete=("frete", "sum")))
    .join(e.groupby("cliente_regiao").agg(dias=("dias_entrega", "mean"), prometido=("dias_prometidos", "mean"),
                                          prazo=("no_prazo", "mean")))
    .reindex([r for r in ORDEM_REGIAO if r in set(p.cliente_regiao)])
)
reg["participacao"] = reg.pedidos / reg.pedidos.sum()
reg["ticket"] = reg.receita / reg.pedidos
reg["frete_pct"] = reg.frete / reg.receita

col_a, col_b = st.columns([2, 3])
with col_a:
    ordenado = reg.sort_values("frete_pct")
    fig = go.Figure(go.Bar(
        x=ordenado.frete_pct, y=ordenado.index, orientation="h", marker_color=AZUL,
        text=[pct(v) for v in ordenado.frete_pct], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Frete = %{x:.1%} da receita<extra></extra>",
    ))
    fig.update_xaxes(title="Frete ÷ receita", tickformat=".0%", range=[0, ordenado.frete_pct.max() * 1.25])
    grafico(estilo(fig, 300, titulo="Quanto o frete pesa em cada região"), key="geo_frete")
with col_b:
    tabela = reg.reset_index()[["cliente_regiao", "participacao", "ticket", "frete_pct", "prometido", "dias",
                                "prazo", "nota"]]
    st.dataframe(
        tabela, hide_index=True, width="stretch",
        column_config={
            "cliente_regiao": st.column_config.TextColumn("Região"),
            "participacao": st.column_config.ProgressColumn("% dos pedidos", format="percent", min_value=0, max_value=1),
            "ticket": st.column_config.NumberColumn("Ticket (R$)", format="%.2f"),
            "frete_pct": st.column_config.NumberColumn("Frete/receita", format="percent"),
            "prometido": st.column_config.NumberColumn("Prazo prometido (dias)", format="%.1f"),
            "dias": st.column_config.NumberColumn("Entrega real (dias)", format="%.1f"),
            "prazo": st.column_config.NumberColumn("No prazo", format="percent"),
            "nota": st.column_config.NumberColumn("Nota", format="%.2f"),
        },
    )

# ---------------- Recompra ----------------
st.subheader("O cliente volta?")
ppc = m.pedidos_por_cliente(p)
faixas = pd.cut(ppc, bins=[0, 1, 2, 3, float("inf")], labels=["1 pedido", "2 pedidos", "3 pedidos", "4 ou mais"])
dist = faixas.value_counts().reindex(["1 pedido", "2 pedidos", "3 pedidos", "4 ou mais"])
col_a, col_b = st.columns([2, 3])
with col_a:
    fig = go.Figure(go.Pie(
        labels=["Comprou uma vez", "Comprou 2 vezes ou mais"],
        values=[dist.iloc[0], dist.iloc[1:].sum()], hole=0.62, sort=False,
        marker=dict(colors=[CINZA, AZUL], line=dict(color="#fcfcfb", width=2)),
        textinfo="percent", hovertemplate="%{label}: %{value:,} clientes (%{percent})<extra></extra>",
    ))
    fig.add_annotation(text=f"<b>{pct(m.taxa_recompra(p))}</b><br>voltam", showarrow=False, font=dict(size=16))
    grafico(estilo(fig, 300, legenda=True), key="geo_recompra")
with col_b:
    fig = go.Figure(go.Bar(
        x=dist.index[1:], y=dist.values[1:], marker_color=AZUL, text=[num(v) for v in dist.values[1:]],
        textposition="outside", hovertemplate="%{x}: %{y:,} clientes<extra></extra>",
    ))
    fig.update_yaxes(title="Clientes", range=[0, dist.values[1:].max() * 1.2 if dist.values[1:].max() else 1])
    grafico(estilo(fig, 300, titulo="Entre os que voltam: quantos pedidos fizeram"), key="geo_recompra_barras")

# ---------------- Interpretação ----------------
txt = []
if {"Sudeste", "Norte", "Nordeste"} <= set(reg.index):
    txt.append(
        f"- O Sudeste concentra **{pct(reg.loc['Sudeste', 'participacao'])}** dos pedidos. No Norte e no Nordeste, "
        f"o frete equivale a **{pct(reg.loc['Norte', 'frete_pct'])}** e **{pct(reg.loc['Nordeste', 'frete_pct'])}** "
        f"da receita, contra {pct(reg.loc['Sudeste', 'frete_pct'])} no Sudeste."
    )
    pior_prazo, pior_nota = reg.prazo.idxmin(), reg.nota.idxmin()
    frase = (f"- **{pior_prazo}** tem a menor taxa de entrega no prazo ({pct(reg.loc[pior_prazo, 'prazo'])})"
             + (f" e também a menor nota média ({num(reg.loc[pior_nota, 'nota'], 2)})." if pior_prazo == pior_nota
                else f"; a menor nota média é a de **{pior_nota}** ({num(reg.loc[pior_nota, 'nota'], 2)})."))
    if reg.dias.idxmax() == "Norte" and pior_prazo != "Norte":
        frase += (f" O Norte é o que mais demora ({num(reg.loc['Norte', 'dias'], 1)} dias), mas recebe uma promessa "
                  f"bem mais longa ({num(reg.loc['Norte', 'prometido'], 0)} dias), então atrasa menos.")
    txt.append(frase)
txt.append(
    f"- Só **{pct(m.taxa_recompra(p))}** dos clientes compraram mais de uma vez no período. "
    "A base não diz por quê, mas uma primeira experiência ruim (atraso, frete caro) é candidata natural."
)
insight(*txt)
