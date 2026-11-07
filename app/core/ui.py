"""Formatação pt-BR, paleta e componentes visuais reutilizados pelas páginas."""
from __future__ import annotations

import math

import pandas as pd
import streamlit as st

# Paleta: série principal em azul, status reservados para bom/ruim, cinza para contexto
AZUL = "#2a78d6"
AZUL_CLARO = "#86b6ef"
CINZA = "#b8b6ad"
VERMELHO = "#d03b3b"
VERDE = "#0ca30c"
CATEGORICAS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
ESCALA_AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


# ---------------- Formatação ----------------
def _br(valor: float, casas: int) -> str:
    s = f"{valor:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def num(valor: float, casas: int = 0) -> str:
    return "–" if valor is None or (isinstance(valor, float) and math.isnan(valor)) else _br(valor, casas)


def brl(valor: float, compacto: bool = False) -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "–"
    if compacto and abs(valor) >= 1e6:
        return f"R$ {_br(valor / 1e6, 2)} mi"
    if compacto and abs(valor) >= 1e3:
        return f"R$ {_br(valor / 1e3, 1)} mil"
    return f"R$ {_br(valor, 2)}"


def pct(valor: float, casas: int = 1) -> str:
    return "–" if valor is None or (isinstance(valor, float) and math.isnan(valor)) else f"{_br(valor * 100, casas)}%"


def mes_label(ts: pd.Timestamp) -> str:
    return f"{MESES[ts.month - 1]}/{ts.year}"


# ---------------- Componentes ----------------
def kpi(col, rotulo: str, valor: str, ajuda: str, delta: str | None = None, delta_color: str = "normal"):
    with col:
        st.metric(rotulo, valor, delta=delta, delta_color=delta_color, help=ajuda, border=True)


def insight(*paragrafos: str):
    """Caixa de interpretação: o que os dados do recorte atual mostram."""
    with st.container(border=True):
        st.markdown("**O que os dados mostram**")
        for p in paragrafos:
            st.markdown(p)


def exigir_dados(p: pd.DataFrame, minimo: int = 1):
    if len(p) < minimo:
        st.warning("Nenhum pedido no recorte atual. Amplie os filtros na barra lateral.")
        st.stop()


def estilo(fig, altura: int = 380, legenda: bool = False, titulo: str | None = None):
    """Layout comum: números em pt-BR, grade discreta, hover unificado."""
    fig.update_layout(
        height=altura,
        margin=dict(l=8, r=8, t=48 if titulo else 16, b=8),
        separators=",.",
        showlegend=legenda,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
        hoverlabel=dict(font_size=13),
        font=dict(size=13),
        bargap=0.25,
    )
    if titulo:
        fig.update_layout(title=dict(text=titulo, x=0, xanchor="left", font=dict(size=15)))
    fig.update_xaxes(showgrid=False, title_font=dict(size=12))
    fig.update_yaxes(gridcolor="rgba(137,135,129,0.25)", zeroline=False, title_font=dict(size=12))
    return fig


def grafico(fig, key: str | None = None, selecionavel: bool = False):
    """Renderiza o gráfico. Com selecionavel=True, devolve a seleção do usuário."""
    if selecionavel:
        return st.plotly_chart(
            fig, width="stretch", key=key, on_select="rerun", selection_mode="points",
            config={"displaylogo": False},
        )
    st.plotly_chart(fig, width="stretch", key=key, config={"displaylogo": False})
    return None


def pontos_selecionados(evento) -> list[dict]:
    try:
        return list(evento.selection.points) if evento else []
    except AttributeError:
        return list(evento.get("selection", {}).get("points", [])) if evento else []
