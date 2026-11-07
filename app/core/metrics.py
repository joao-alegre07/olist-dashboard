"""KPIs do dashboard.

Toda função recebe as tabelas JÁ FILTRADAS (pedidos `p` e itens `it`), por isso
os indicadores acompanham qualquer filtro. As definições estão em docs/kpis.md
e também aparecem no tooltip de cada cartão (campo `ajuda`).
"""
from __future__ import annotations

import math

import pandas as pd


def _div(a: float, b: float) -> float:
    return a / b if b else math.nan


def entregues(p: pd.DataFrame) -> pd.DataFrame:
    return p[p.entregue]


def receita(it: pd.DataFrame) -> float:
    return float(it.preco.sum())


def frete(it: pd.DataFrame) -> float:
    return float(it.frete.sum())


def pedidos(p: pd.DataFrame) -> int:
    return int(p.pedido_id.nunique())


def ticket_medio(p: pd.DataFrame, it: pd.DataFrame) -> float:
    return _div(receita(it), pedidos(p))


def clientes_unicos(p: pd.DataFrame) -> int:
    return int(p.cliente_id.nunique())


def pedidos_por_cliente(p: pd.DataFrame) -> pd.Series:
    return p.groupby("cliente_id").pedido_id.nunique()


def taxa_recompra(p: pd.DataFrame) -> float:
    ppc = pedidos_por_cliente(p)
    return _div((ppc >= 2).sum(), len(ppc))


def pct_no_prazo(p: pd.DataFrame) -> float:
    e = entregues(p)
    return _div(e.no_prazo.sum(), len(e))


def tempo_medio_entrega(p: pd.DataFrame) -> float:
    return float(entregues(p).dias_entrega.mean())


def prazo_prometido_medio(p: pd.DataFrame) -> float:
    return float(entregues(p).dias_prometidos.mean())


def nota_media(p: pd.DataFrame) -> float:
    return float(p.nota.mean())


def pct_notas_baixas(p: pd.DataFrame) -> float:
    return float(p.nota_baixa.mean())


def frete_sobre_receita(it: pd.DataFrame) -> float:
    return _div(frete(it), receita(it))


# Texto exibido no tooltip (ícone de ajuda) de cada KPI
AJUDA = {
    "receita": "Soma do preço dos itens vendidos (sem frete). Mede o tamanho do negócio.",
    "pedidos": "Contagem distinta de pedidos (order_id) no recorte.",
    "ticket": "Receita ÷ pedidos. Valor médio gasto por compra.",
    "clientes": "Contagem distinta de customer_unique_id (o customer_id muda a cada pedido).",
    "recompra": "Clientes com 2 ou mais pedidos no recorte ÷ clientes únicos. Mede fidelização.",
    "prazo": "Pedidos entregues até a data estimada ÷ pedidos entregues. Mede se a promessa foi cumprida.",
    "dias": "Média de dias entre a compra e a entrega ao cliente (só pedidos entregues).",
    "prometido": "Média de dias entre a compra e a data de entrega estimada informada ao cliente.",
    "nota": "Média da nota da avaliação (1 a 5), uma avaliação por pedido.",
    "notas_baixas": "Avaliações com nota 1 ou 2 ÷ avaliações. Mede insatisfação explícita.",
    "frete": "Soma do frete ÷ receita. Quanto o cliente paga de frete para cada R$ 1 em produtos.",
}
