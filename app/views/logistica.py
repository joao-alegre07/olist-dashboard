import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import metrics as m
from core.data import ORDEM_FAIXA_ATRASO, dados_filtrados
from core.ui import (AZUL, CINZA, VERMELHO, CATEGORICAS, estilo, exigir_dados, grafico, insight, kpi, num,
                     pct)

p, it = dados_filtrados()

st.title("Logística e satisfação")
st.caption("O atraso na entrega explica a nota que o cliente dá?")

e = m.entregues(p)
exigir_dados(e)

no_prazo = e[e.no_prazo == 1]
atrasados = e[e.no_prazo == 0]

c = st.columns(5)
kpi(c[0], "Entregas no prazo", pct(m.pct_no_prazo(p)), m.AJUDA["prazo"])
kpi(c[1], "Tempo médio de entrega", f"{num(m.tempo_medio_entrega(p), 1)} dias", m.AJUDA["dias"])
kpi(c[2], "Prazo prometido médio", f"{num(m.prazo_prometido_medio(p), 1)} dias", m.AJUDA["prometido"])
kpi(c[3], "Nota: entregue no prazo", num(no_prazo.nota.mean(), 2), "Nota média dos pedidos entregues até a data estimada.")
kpi(c[4], "Nota: entregue com atraso", num(atrasados.nota.mean(), 2), "Nota média dos pedidos entregues depois da data estimada.")

# ---------------- Nota x atraso (gráfico central da história) ----------------
st.subheader("Quanto maior o atraso, pior a nota")
faixas = (
    e.groupby("faixa_atraso")
    .agg(pedidos=("pedido_id", "count"), nota=("nota", "mean"), baixa=("nota_baixa", "mean"))
    .reindex(ORDEM_FAIXA_ATRASO).dropna(how="all")
)
col_a, col_b = st.columns(2)
with col_a:
    fig = go.Figure(go.Bar(
        x=faixas.index, y=faixas.nota, marker_color=[AZUL] + [VERMELHO] * (len(faixas) - 1),
        text=[num(v, 2) for v in faixas.nota], textposition="outside",
        customdata=faixas.pedidos,
        hovertemplate="<b>%{x}</b><br>Nota média %{y:.2f}<br>%{customdata:,} pedidos<extra></extra>",
    ))
    fig.update_yaxes(title="Nota média (1 a 5)", range=[0, 5.4])
    fig.update_xaxes(title="Atraso em relação à data estimada")
    grafico(estilo(fig, 360, titulo="Nota média por faixa de atraso"), key="lg_nota")
with col_b:
    fig = go.Figure(go.Bar(
        x=faixas.index, y=faixas.baixa, marker_color=[AZUL] + [VERMELHO] * (len(faixas) - 1),
        text=[pct(v, 0) for v in faixas.baixa], textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:.1%} de notas 1 ou 2<extra></extra>",
    ))
    fig.update_yaxes(title="% de avaliações com nota 1 ou 2", tickformat=".0%", range=[0, 1])
    fig.update_xaxes(title="Atraso em relação à data estimada")
    grafico(estilo(fig, 360, titulo="Insatisfação explícita por faixa de atraso"), key="lg_baixa")
st.caption("Azul: entregue no prazo. Vermelho: entregue com atraso.")

# ---------------- Distribuição do tempo de entrega ----------------
st.subheader("Prometido vs. realizado")
col_a, col_b = st.columns(2)
with col_a:
    real, prometido = e.dias_entrega.mean(), e.dias_prometidos.mean()
    limite = 60
    fig = go.Figure(go.Histogram(
        x=e.dias_entrega.clip(upper=limite), xbins=dict(start=0, end=limite + 1, size=1),
        marker_color=AZUL, hovertemplate="%{x} dias: %{y:,} pedidos<extra></extra>",
    ))
    for valor, rotulo, cor in [(real, "Média real", "#0b0b0b"), (prometido, "Média prometida", VERMELHO)]:
        fig.add_vline(x=valor, line_dash="dash", line_color=cor, line_width=2)
        fig.add_annotation(x=valor, y=1, yref="paper", text=f"{rotulo}: {num(valor, 1)} dias",
                           showarrow=False, xanchor="left", xshift=4, font=dict(size=12))
    fig.update_xaxes(title=f"Dias entre compra e entrega (acima de {limite} agrupados em {limite})")
    fig.update_yaxes(title="Pedidos")
    grafico(estilo(fig, 360, titulo="Distribuição do tempo de entrega"), key="lg_hist")

with col_b:
    uf = (
        e.groupby("cliente_uf")
        .agg(pedidos=("pedido_id", "count"), prazo=("no_prazo", "mean"), dias=("dias_entrega", "mean"))
        .query("pedidos >= 30").sort_values("prazo")
    )
    media = m.pct_no_prazo(p)
    fig = go.Figure(go.Bar(
        x=uf.prazo, y=uf.index, orientation="h",
        marker_color=[VERMELHO if v < media else CINZA for v in uf.prazo],
        customdata=np.stack([uf.pedidos, uf.dias], axis=-1),
        hovertemplate="<b>%{y}</b><br>%{x:.1%} no prazo<br>%{customdata[1]:.1f} dias em média"
                      "<br>%{customdata[0]:,} pedidos<extra></extra>",
    ))
    fig.add_vline(x=media, line_dash="dash", line_color="#0b0b0b", line_width=1.5)
    fig.add_annotation(x=media, y=1, yref="paper", text=f"Média {pct(media)}", showarrow=False,
                       xanchor="left", xshift=4, yshift=8, font=dict(size=12))
    lo = max(0, uf.prazo.min() - 0.05)
    fig.update_xaxes(title="% entregue no prazo", tickformat=".0%", range=[lo, 1])
    fig.update_yaxes(dtick=1, tickfont=dict(size=11))
    grafico(estilo(fig, 520, titulo="% no prazo por estado do cliente"), key="lg_uf")
    st.caption("Vermelho: abaixo da média do recorte. Estados com menos de 30 entregas ficam de fora.")

# ---------------- Distância x tempo ----------------
st.subheader("A distância explica parte do prazo")
amostra = e.dropna(subset=["distancia_km", "dias_entrega"])
amostra = amostra.sample(min(len(amostra), 4000), random_state=42)
fig = go.Figure()
for i, (mesmo, nome) in enumerate([(True, "Vendedor no mesmo estado"), (False, "Vendedor em outro estado")]):
    d = amostra[amostra.mesmo_estado == mesmo]
    fig.add_trace(go.Scattergl(
        x=d.distancia_km, y=d.dias_entrega, mode="markers", name=nome,
        marker=dict(color=CATEGORICAS[i], size=6, opacity=0.45),
        hovertemplate="%{x:,.0f} km · %{y:.1f} dias<extra>" + nome + "</extra>",
    ))
# Mediana por faixa de 250 km, calculada sobre todos os entregues (não só a amostra)
base = e.dropna(subset=["distancia_km"])
bins = (base.distancia_km // 250) * 250 + 125
mediana = base.groupby(bins).dias_entrega.median()
contagem = base.groupby(bins).size()
mediana = mediana[contagem >= 50]
fig.add_trace(go.Scatter(
    x=mediana.index, y=mediana.values, mode="lines+markers", name="Mediana a cada 250 km",
    line=dict(color="#0b0b0b", width=2), marker=dict(size=7),
    hovertemplate="~%{x:,.0f} km: mediana de %{y:.1f} dias<extra></extra>",
))
fig.update_xaxes(title="Distância em linha reta entre vendedor e cliente (km)")
fig.update_yaxes(title="Dias até a entrega", range=[0, 60])
grafico(estilo(fig, 420, legenda=True), key="lg_dispersao")
st.caption(f"Amostra de {num(len(amostra))} pedidos entregues para manter o gráfico leve; a linha usa todos.")

mesmo = e.groupby("mesmo_estado").agg(dias=("dias_entrega", "mean"), prazo=("no_prazo", "mean"), nota=("nota", "mean"))
corr = base[["distancia_km", "dias_entrega"]].corr().iloc[0, 1]

# ---------------- Interpretação ----------------
virada = next((f for f in ORDEM_FAIXA_ATRASO[1:] if f in faixas.index and faixas.loc[f, "baixa"] > 0.5), None)
txt = [
    f"- Pedidos entregues no prazo têm nota média **{num(no_prazo.nota.mean(), 2)}**; os atrasados, "
    f"**{num(atrasados.nota.mean(), 2)}**."
    + (f" A partir de {virada} de atraso, a maioria das avaliações já é nota 1 ou 2." if virada else ""),
    f"- Só **{pct(1 - m.pct_no_prazo(p))}** das entregas atrasam, mas elas respondem por "
    f"**{pct((e[e.nota_baixa == 1].no_prazo == 0).mean())}** das notas 1 e 2 dos pedidos entregues.",
    f"- O prazo prometido ({num(m.prazo_prometido_medio(p), 1)} dias) é quase o dobro do tempo real "
    f"({num(m.tempo_medio_entrega(p), 1)} dias). A promessa é folgada no geral, e mesmo assim falha em alguns estados.",
]
if True in mesmo.index and False in mesmo.index:
    txt.append(
        f"- Quando vendedor e cliente estão no mesmo estado, a entrega leva **{num(mesmo.loc[True, 'dias'], 1)}** dias "
        f"contra **{num(mesmo.loc[False, 'dias'], 1)}** entre estados (correlação distância × dias de {num(corr, 2)}). "
        "A distância pesa, mas não explica tudo: rotas e transportadoras também contam."
    )
insight(*txt)
