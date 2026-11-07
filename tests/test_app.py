"""Testes de fumaça do dashboard com streamlit.testing.v1.AppTest.

Rodar a partir da raiz do projeto:
    python -m pytest tests -v -s

Cada página é aberta (switch_page) em vários recortes dos filtros globais da
barra lateral. O teste falha se qualquer página levantar exceção. No recorte
vazio, as páginas que dependem do recorte precisam mostrar um aviso.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "app.py"
sys.path.insert(0, str(APP.parent))  # mesmo efeito do `streamlit run`: `core` importável

PAGINAS = {
    "Visão geral": "views/visao_geral.py",
    "Logística e satisfação": "views/logistica.py",
    "Clientes e geografia": "views/geografia.py",
    "Produtos e vendedores": "views/produtos.py",
    "Exploração": "views/exploracao.py",
    "Dados e modelo": "views/modelo.py",
}
# Dados e modelo não usa o recorte (documenta a base inteira), então não tem aviso de recorte vazio
PAGINAS_COM_RECORTE = [n for n in PAGINAS if n != "Dados e modelo"]

TIMEOUT = 120
LIMITE_SEGUNDOS = 3.0


def mes(ano: int, m: int) -> pd.Timestamp:
    return pd.Timestamp(year=ano, month=m, day=1)


# Recortes pedidos: nome -> {key do widget: valor}
RECORTES = {
    "padrao": {},
    "nordeste_tecnologia": {"f_regioes": ["Nordeste"], "f_grupos": ["Tecnologia"]},
    "ap_mar2018": {"f_ufs": ["AP"], "f_periodo": (mes(2018, 3), mes(2018, 3))},
    "invalidos_voucher": {"f_invalidos": True, "f_pagamentos": ["Voucher"]},
    "vazio": {"f_ufs": ["RR"], "f_grupos": ["Alimentos e bebidas"], "f_periodo": (mes(2017, 1), mes(2017, 1))},
}


def aplicar(at: AppTest, valores: dict) -> None:
    """Muda os widgets da barra lateral pelas keys (sem rodar)."""
    for chave, valor in valores.items():
        if chave == "f_periodo":
            at.select_slider(key=chave).set_range(*valor)
        elif chave == "f_invalidos":
            at.toggle(key=chave).set_value(valor)
        else:
            at.multiselect(key=chave).set_value(valor)


def sem_excecao(at: AppTest, contexto: str) -> None:
    erros = [e.value for e in at.exception]
    assert not erros, f"{contexto}: exceção\n" + "\n---\n".join(str(e) for e in erros)
    assert not at.error, f"{contexto}: st.error -> {[e.value for e in at.error]}"


def novo_app() -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=TIMEOUT)
    at.run()
    sem_excecao(at, "abertura")
    return at


def abrir(at: AppTest, pagina: str) -> float:
    inicio = time.perf_counter()
    at.switch_page(PAGINAS[pagina]).run()
    return time.perf_counter() - inicio


def conferir_filtros(at: AppTest, valores: dict) -> None:
    """Garante que o recorte pedido foi mesmo aplicado (e não descartado no rerun)."""
    for chave, valor in valores.items():
        atual = at.session_state[chave]
        if chave == "f_periodo":
            atual = tuple(pd.Timestamp(v) for v in atual)
            valor = tuple(valor)
        assert atual == valor, f"filtro {chave}: esperado {valor!r}, ficou {atual!r}"


@pytest.mark.parametrize("recorte", list(RECORTES))
def test_paginas_por_recorte(recorte):
    at = novo_app()
    aplicar(at, RECORTES[recorte])
    at.run()
    sem_excecao(at, f"[{recorte}] após aplicar filtros")
    conferir_filtros(at, RECORTES[recorte])

    for pagina in PAGINAS:
        abrir(at, pagina)
        sem_excecao(at, f"[{recorte}] {pagina}")
        conferir_filtros(at, RECORTES[recorte])
        if recorte == "vazio" and pagina in PAGINAS_COM_RECORTE:
            avisos = [w.value for w in at.warning]
            assert avisos, f"[vazio] {pagina}: esperava um aviso de recorte vazio"


def test_exploracao_filtros_da_pagina():
    at = novo_app()
    abrir(at, "Exploração")
    sem_excecao(at, "Exploração")
    at.text_input(key="ex_busca").input("salvador")
    at.multiselect(key="ex_faixas").set_value(["15+ dias"])
    at.multiselect(key="ex_notas").set_value([1])
    at.run()
    sem_excecao(at, "Exploração com busca/faixa/nota")
    df = at.dataframe[0].value
    assert len(df) > 0, "esperava pedidos de Salvador com 15+ dias de atraso e nota 1"
    assert df.cliente_cidade.str.lower().str.contains("salvador").all()
    assert (df.nota == 1).all()
    assert (df.dias_atraso >= 15).all()


def test_kpis_visao_geral_padrao():
    at = novo_app()
    abrir(at, "Visão geral")
    sem_excecao(at, "Visão geral")
    valores = {mt.label: mt.value for mt in at.metric}
    esperado = {
        "Receita": "R$ 13,45 mi",
        "Pedidos": "97.905",
        "Ticket médio": "R$ 137,37",
        "Nota média": "4,12",
        "Entregas no prazo": "93,2%",
        "Taxa de recompra": "3,0%",
    }
    for rotulo, valor in esperado.items():
        assert valores.get(rotulo) == valor, f"{rotulo}: esperado {valor}, veio {valores.get(rotulo)}"


def test_tempo_por_pagina(capsys):
    at = novo_app()  # carga dos dados (cache_resource) fica fora da medição
    tempos = {}
    for pagina in PAGINAS:
        tempos[pagina] = abrir(at, pagina)
        sem_excecao(at, pagina)
    with capsys.disabled():
        print("\nTempo por página (recorte padrão, dados já em cache):")
        for pagina, seg in tempos.items():
            alerta = "  <-- acima de 3 s" if seg > LIMITE_SEGUNDOS else ""
            print(f"  {pagina:<26} {seg:5.2f} s{alerta}")
    lentas = {p: round(s, 2) for p, s in tempos.items() if s > LIMITE_SEGUNDOS}
    if lentas:
        pytest.fail(f"páginas acima de {LIMITE_SEGUNDOS} s: {lentas}")
