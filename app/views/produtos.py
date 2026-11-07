import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import metrics as m
from core.data import dados_filtrados
from core.ui import AZUL, CATEGORICAS, CINZA, VERMELHO, brl, estilo, exigir_dados, grafico, insight, kpi, num, pct

p, it = dados_filtrados()

st.title("Produtos e vendedores")
st.caption("Quais categorias e vendedores concentram atraso e insatisfação?")
exigir_dados(p)

# Atributos do pedido levados para cada item (relacionamento itens -> pedidos)
itp = it.merge(
    p[["pedido_id", "entregue", "no_prazo", "nota", "nota_baixa"]], on="pedido_id", how="inner", validate="m:1"
)

# ---------------- Categorias: atraso x nota ----------------
st.subheader("Categorias: atraso × nota")
min_ped = st.slider("Mínimo de pedidos por categoria", 50, 1000, 200, step=50, key="pr_min_cat")
pedidos_cat = itp.drop_duplicates(["pedido_id", "categoria"])
cat = pedidos_cat.groupby("categoria").agg(
    pedidos=("pedido_id", "nunique"), nota=("nota", "mean"), baixa=("nota_baixa", "mean"),
).join(
    pedidos_cat[pedidos_cat.entregue].groupby("categoria").no_prazo.mean().rename("prazo")
).join(itp.groupby("categoria").preco.sum().rename("receita"))
cat["atraso"] = 1 - cat.prazo
cat = cat[cat.pedidos >= min_ped].dropna(subset=["atraso", "nota"])

if cat.empty:
    st.info("Nenhuma categoria atinge o mínimo de pedidos no recorte atual. Reduza o mínimo.")
else:
    media_atraso = 1 - m.pct_no_prazo(p)
    media_nota = m.nota_media(p)
    piores = cat[(cat.atraso > media_atraso) & (cat.nota < media_nota)]
    cor = [VERMELHO if c in piores.index else AZUL for c in cat.index]
    fig = go.Figure(go.Scatter(
        x=cat.atraso, y=cat.nota, mode="markers", text=cat.index,
        marker=dict(size=8 + 32 * (cat.pedidos / cat.pedidos.max()) ** 0.5, color=cor, opacity=0.75,
                    line=dict(width=1, color="#fcfcfb")),
        customdata=np.stack([cat.pedidos, cat.receita], axis=-1),
        hovertemplate="<b>%{text}</b><br>%{x:.1%} entregues com atraso<br>Nota média %{y:.2f}"
                      "<br>%{customdata[0]:,.0f} pedidos · R$ %{customdata[1]:,.0f}<extra></extra>",
    ))
    fig.add_vline(x=media_atraso, line_dash="dot", line_color=CINZA)
    fig.add_hline(y=media_nota, line_dash="dot", line_color=CINZA)
    fig.add_annotation(x=1, y=0, xref="paper", yref="paper", xanchor="right", yanchor="bottom",
                       text="Mais atraso e pior nota", showarrow=False, font=dict(color=VERMELHO, size=12))
    # Rótulos só nas categorias de destaque, para não poluir
    destaque = pd.concat([piores, cat.nlargest(3, "pedidos")]).drop_duplicates()
    for nome, linha in destaque.iterrows():
        fig.add_annotation(x=linha.atraso, y=linha.nota, text=nome, showarrow=False, yshift=14, font=dict(size=11))
    fig.update_xaxes(title="% de pedidos entregues com atraso", tickformat=".0%")
    fig.update_yaxes(title="Nota média")
    grafico(estilo(fig, 460), key="pr_dispersao")
    st.caption("Tamanho = número de pedidos. Linhas pontilhadas = médias do recorte. "
               "Vermelho: acima da média de atraso e abaixo da média de nota.")

# ---------------- Vendedores ----------------
st.subheader("Vendedores")
vend = itp.drop_duplicates(["pedido_id", "vendedor_id"]).groupby("vendedor_id").agg(
    pedidos=("pedido_id", "nunique"), nota=("nota", "mean"), uf=("vendedor_uf", "first"),
).join(
    itp.drop_duplicates(["pedido_id", "vendedor_id"]).query("entregue").groupby("vendedor_id").no_prazo.mean()
    .rename("prazo")
).join(itp.groupby("vendedor_id").preco.sum().rename("receita"))

col_a, col_b = st.columns(2)
with col_a:
    min_v = st.slider("Mínimo de pedidos por vendedor", 10, 200, 30, step=10, key="pr_min_vend")
    ruins = vend[vend.pedidos >= min_v].nsmallest(10, "nota").sort_values("nota", ascending=False)
    if ruins.empty:
        st.info("Nenhum vendedor atinge o mínimo de pedidos no recorte atual.")
    else:
        rotulo = [f"{i[:8]}… ({u})" for i, u in zip(ruins.index, ruins.uf)]
        fig = go.Figure(go.Bar(
            x=ruins.nota, y=rotulo, orientation="h", marker_color=VERMELHO,
            text=[num(v, 2) for v in ruins.nota], textposition="outside",
            customdata=np.stack([ruins.pedidos, ruins.prazo.fillna(np.nan), ruins.receita], axis=-1),
            hovertemplate="<b>%{y}</b><br>Nota %{x:.2f}<br>%{customdata[0]:,.0f} pedidos"
                          "<br>%{customdata[1]:.1%} no prazo<br>R$ %{customdata[2]:,.0f}<extra></extra>",
        ))
        fig.update_xaxes(title="Nota média", range=[0, 5.4])
        grafico(estilo(fig, 400, titulo="10 vendedores com pior nota média"), key="pr_vend_ruins")
        st.caption("IDs encurtados (a base é anonimizada); entre parênteses, o estado do vendedor.")

with col_b:
    st.write("")  # alinha com o slider ao lado
    st.write("")
    rec = vend.receita.sort_values(ascending=False)
    acum = rec.cumsum() / rec.sum()
    x = np.arange(1, len(rec) + 1) / len(rec)
    passo = max(1, len(rec) // 300)  # reduz pontos sem perder a forma da curva
    fig = go.Figure(go.Scatter(
        x=x[::passo], y=acum.values[::passo], mode="lines", line=dict(color=AZUL, width=2),
        hovertemplate="%{x:.0%} dos vendedores → %{y:.0%} da receita<extra></extra>",
    ))
    if len(rec) >= 10:
        top10 = acum.iloc[int(len(rec) * 0.1) - 1]
        fig.add_trace(go.Scatter(x=[0.1], y=[top10], mode="markers", marker=dict(size=10, color=VERMELHO),
                                 hoverinfo="skip"))
        fig.add_annotation(x=0.1, y=top10, text=f"10% dos vendedores = {pct(top10, 0)} da receita",
                           showarrow=True, arrowhead=0, ax=60, ay=30, xanchor="left", font=dict(size=12))
    fig.update_xaxes(title="% dos vendedores (do maior para o menor)", tickformat=".0%", range=[0, 1])
    fig.update_yaxes(title="% acumulado da receita", tickformat=".0%", range=[0, 1.02])
    grafico(estilo(fig, 400, titulo="Concentração da receita entre vendedores"), key="pr_pareto")

# ---------------- Pagamentos ----------------
st.subheader("Como o cliente paga")
col_a, col_b = st.columns(2)
pag = p.pagamento_principal.value_counts()
with col_a:
    ordem = ["Cartão de crédito", "Boleto", "Voucher", "Cartão de débito"]
    pag = pag.reindex([o for o in ordem if o in pag.index])
    fig = go.Figure(go.Pie(
        labels=pag.index, values=pag.values, hole=0.55, sort=False,
        marker=dict(colors=CATEGORICAS[: len(pag)], line=dict(color="#fcfcfb", width=2)),
        textinfo="percent", hovertemplate="%{label}: %{value:,} pedidos (%{percent})<extra></extra>",
    ))
    grafico(estilo(fig, 340, legenda=True, titulo="Forma principal de pagamento"), key="pr_pag")
with col_b:
    cc = p[p.pagamento_principal == "Cartão de crédito"]
    if cc.empty:
        st.info("Sem pedidos no cartão de crédito no recorte atual.")
    else:
        parc = cc.parcelas.clip(upper=10).value_counts().sort_index()
        rot = [f"{int(i)}x" if i < 10 else "10x+" for i in parc.index]
        fig = go.Figure(go.Bar(
            x=rot, y=parc.values / parc.sum(), marker_color=AZUL,
            hovertemplate="%{x}: %{y:.1%} dos pedidos no cartão<extra></extra>",
        ))
        fig.update_yaxes(title="% dos pedidos no cartão", tickformat=".0%")
        fig.update_xaxes(title="Número de parcelas", type="category")
        grafico(estilo(fig, 340, titulo="Parcelamento no cartão de crédito"), key="pr_parcelas")

# ---------------- Interpretação ----------------
txt = []
if not cat.empty:
    pior = cat.nsmallest(1, "nota").iloc[0]
    txt.append(
        f"- Entre as categorias com {num(min_ped)}+ pedidos, a pior nota é de **{cat.nota.idxmin()}** "
        f"({num(pior.nota, 2)}, com {pct(pior.atraso)} de atraso). "
        + (f"{len(piores)} categorias ficam no quadrante de mais atraso e pior nota." if len(piores) else "")
    )
if len(vend) >= 10:
    txt.append(
        f"- A receita é concentrada: os 10% maiores vendedores respondem por **{pct(acum.iloc[int(len(rec) * 0.1) - 1], 0)}** "
        "dela. Acompanhar de perto os grandes vendedores com nota baixa tem alto impacto."
    )
if not cc.empty:
    txt.append(
        f"- O cartão de crédito é a forma principal em **{pct(len(cc) / len(p), 0)}** dos pedidos, e "
        f"**{pct((cc.parcelas > 1).mean(), 0)}** deles são parcelados (média de {num(cc.parcelas.mean(), 1)} parcelas)."
    )
insight(*txt)
