"""Carga das tabelas tratadas e aplicação dos filtros globais."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import streamlit as st

PROCESSED = Path(__file__).resolve().parents[2] / "data" / "processed"

COLUNAS_DATA = {"pedidos": ["data_compra", "mes"], "clientes": ["primeira_compra", "ultima_compra"]}
COLUNAS_BOOL = {
    "pedidos": ["pedido_valido", "entregue", "mesmo_estado", "usou_voucher", "tem_comentario"],
    "clientes": ["recorrente"],
}

ORDEM_FAIXA_ATRASO = ["No prazo", "1 a 3 dias", "4 a 7 dias", "8 a 14 dias", "15+ dias"]
ORDEM_REGIAO = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]


def _ler(nome: str) -> pd.DataFrame:
    parquet = PROCESSED / f"{nome}.parquet"
    csv = PROCESSED / f"{nome}.csv.gz"
    if parquet.exists():
        df = pd.read_parquet(parquet)
    elif csv.exists():
        df = pd.read_csv(csv, low_memory=False)
    else:
        st.error(
            f"Tabela `{nome}` não encontrada em `data/processed/`. "
            "Rode `python etl/build.py` antes de abrir o dashboard."
        )
        st.stop()
    for c in COLUNAS_DATA.get(nome, []):
        df[c] = pd.to_datetime(df[c])
    for c in COLUNAS_BOOL.get(nome, []):
        if c in df:
            df[c] = df[c].map({True: True, False: False, "True": True, "False": False}).fillna(False).astype(bool)
    return df


@st.cache_resource(show_spinner="Carregando dados…")
def carregar() -> dict[str, pd.DataFrame]:
    return {nome: _ler(nome) for nome in ("pedidos", "itens", "clientes", "vendedores")}


@dataclass(frozen=True)
class Filtros:
    inicio: pd.Timestamp
    fim: pd.Timestamp
    regioes: tuple[str, ...] = field(default_factory=tuple)
    ufs: tuple[str, ...] = field(default_factory=tuple)
    grupos: tuple[str, ...] = field(default_factory=tuple)
    pagamentos: tuple[str, ...] = field(default_factory=tuple)
    incluir_invalidos: bool = False


@st.cache_data(show_spinner=False)
def filtrar(_dados: dict[str, pd.DataFrame], f: Filtros) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica os filtros e devolve (pedidos, itens) consistentes entre si.

    Os filtros de período, local e pagamento atuam na tabela de pedidos; o de
    categoria atua na tabela de itens e volta para os pedidos pelo relacionamento
    pedido_id (um pedido entra se tiver ao menos um item do grupo escolhido).
    """
    p = _dados["pedidos"]
    it = _dados["itens"]

    m = p.mes.between(f.inicio, f.fim)
    if not f.incluir_invalidos:
        m &= p.pedido_valido
    if f.regioes:
        m &= p.cliente_regiao.isin(f.regioes)
    if f.ufs:
        m &= p.cliente_uf.isin(f.ufs)
    if f.pagamentos:
        m &= p.pagamento_principal.isin(f.pagamentos)
    p = p[m]

    it = it[it.pedido_id.isin(p.pedido_id)]
    if f.grupos:
        it = it[it.grupo_categoria.isin(f.grupos)]
        p = p[p.pedido_id.isin(it.pedido_id)]

    return p, it


def com_mes(itens: pd.DataFrame, pedidos: pd.DataFrame, colunas=("mes",)) -> pd.DataFrame:
    """Leva atributos do pedido para os itens (relacionamento itens -> pedidos)."""
    return itens.merge(pedidos[["pedido_id", *colunas]], on="pedido_id", how="inner", validate="m:1")


def dados_filtrados() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Usado pelas páginas: o app.py guarda o recorte atual em session_state."""
    return st.session_state["pedidos_f"], st.session_state["itens_f"]
