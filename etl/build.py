"""
Pipeline de tratamento da base Olist.

Lê os CSVs originais de data/raw/, aplica as regras de limpeza documentadas em
docs/qualidade.md, monta o modelo (merges validados) e salva as tabelas
analíticas em data/processed/.

Uso:  python etl/build.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

# Recorte de período: 2016 e set/out de 2018 têm volume residual (dados incompletos)
INICIO = pd.Timestamp("2017-01-01")
FIM = pd.Timestamp("2018-09-01")  # exclusivo

STATUS_INVALIDOS = {"canceled", "unavailable"}

REGIAO = {
    **dict.fromkeys(["AC", "AP", "AM", "PA", "RO", "RR", "TO"], "Norte"),
    **dict.fromkeys(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"], "Nordeste"),
    **dict.fromkeys(["DF", "GO", "MT", "MS"], "Centro-Oeste"),
    **dict.fromkeys(["ES", "MG", "RJ", "SP"], "Sudeste"),
    **dict.fromkeys(["PR", "RS", "SC"], "Sul"),
}

STATUS_PT = {
    "delivered": "Entregue", "shipped": "Enviado", "canceled": "Cancelado",
    "unavailable": "Indisponível", "invoiced": "Faturado", "processing": "Em processamento",
    "created": "Criado", "approved": "Aprovado",
}

PAGAMENTO_PT = {
    "credit_card": "Cartão de crédito", "boleto": "Boleto",
    "voucher": "Voucher", "debit_card": "Cartão de débito",
}

# Grupos de categoria: 73 categorias originais em 13 grupos, para filtros e gráficos legíveis
GRUPOS = {
    "Casa e decoração": [
        "cama_mesa_banho", "moveis_decoracao", "utilidades_domesticas", "casa_conforto",
        "casa_conforto_2", "moveis_sala", "moveis_quarto", "moveis_escritorio",
        "moveis_cozinha_area_de_servico_jantar_e_jardim", "moveis_colchao_e_estofado",
        "la_cuisine", "artigos_de_natal", "artigos_de_festas", "flores",
    ],
    "Eletrodomésticos": [
        "eletrodomesticos", "eletrodomesticos_2", "eletroportateis", "climatizacao",
        "portateis_casa_forno_e_cafe", "portateis_cozinha_e_preparadores_de_alimentos",
    ],
    "Construção e ferramentas": [
        "casa_construcao", "construcao_ferramentas_construcao", "construcao_ferramentas_ferramentas",
        "construcao_ferramentas_iluminacao", "construcao_ferramentas_jardim",
        "construcao_ferramentas_seguranca", "ferramentas_jardim", "sinalizacao_e_seguranca",
    ],
    "Tecnologia": [
        "informatica_acessorios", "pcs", "pc_gamer", "eletronicos", "telefonia", "telefonia_fixa",
        "tablets_impressao_imagem", "consoles_games", "audio", "cine_foto",
    ],
    "Beleza e saúde": ["beleza_saude", "perfumaria", "fraldas_higiene"],
    "Moda e acessórios": [
        "relogios_presentes", "malas_acessorios", "fashion_bolsas_e_acessorios", "fashion_calcados",
        "fashion_esporte", "fashion_roupa_feminina", "fashion_roupa_infanto_juvenil",
        "fashion_roupa_masculina", "fashion_underwear_e_moda_praia",
    ],
    "Esporte e lazer": ["esporte_lazer", "cool_stuff", "instrumentos_musicais"],
    "Bebês e brinquedos": ["bebes", "brinquedos"],
    "Livros, mídia e papelaria": [
        "livros_importados", "livros_interesse_geral", "livros_tecnicos", "papelaria",
        "cds_dvds_musicais", "dvds_blu_ray", "musica", "artes", "artes_e_artesanato",
    ],
    "Alimentos e bebidas": ["alimentos", "alimentos_bebidas", "bebidas"],
    "Automotivo": ["automotivo"],
    "Pet shop": ["pet_shop"],
    "Outros": [
        "agro_industria_e_comercio", "industria_comercio_e_negocios", "market_place",
        "seguros_e_servicos",
    ],
}
GRUPO_DE = {cat: grupo for grupo, cats in GRUPOS.items() for cat in cats}

NOMES_CATEGORIA = {
    "agro_industria_e_comercio": "Agroindústria e comércio", "alimentos": "Alimentos",
    "alimentos_bebidas": "Alimentos e bebidas", "artes": "Artes", "artes_e_artesanato": "Artes e artesanato",
    "artigos_de_festas": "Artigos de festa", "artigos_de_natal": "Artigos de Natal", "audio": "Áudio",
    "automotivo": "Automotivo", "bebes": "Bebês", "bebidas": "Bebidas", "beleza_saude": "Beleza e saúde",
    "brinquedos": "Brinquedos", "cama_mesa_banho": "Cama, mesa e banho", "casa_conforto": "Casa conforto",
    "casa_conforto_2": "Casa conforto", "casa_construcao": "Casa e construção",
    "cds_dvds_musicais": "CDs e DVDs musicais", "cine_foto": "Cine e foto", "climatizacao": "Climatização",
    "consoles_games": "Consoles e games", "construcao_ferramentas_construcao": "Ferramentas de construção",
    "construcao_ferramentas_ferramentas": "Ferramentas", "construcao_ferramentas_iluminacao": "Iluminação",
    "construcao_ferramentas_jardim": "Construção e jardim", "construcao_ferramentas_seguranca": "Segurança",
    "cool_stuff": "Cool stuff", "dvds_blu_ray": "DVDs e Blu-ray", "eletrodomesticos": "Eletrodomésticos",
    "eletrodomesticos_2": "Eletrodomésticos", "eletronicos": "Eletrônicos", "eletroportateis": "Eletroportáteis",
    "esporte_lazer": "Esporte e lazer", "fashion_bolsas_e_acessorios": "Bolsas e acessórios",
    "fashion_calcados": "Calçados", "fashion_esporte": "Moda esportiva", "fashion_roupa_feminina": "Roupa feminina",
    "fashion_roupa_infanto_juvenil": "Roupa infantojuvenil", "fashion_roupa_masculina": "Roupa masculina",
    "fashion_underwear_e_moda_praia": "Moda íntima e praia", "ferramentas_jardim": "Ferramentas de jardim",
    "flores": "Flores", "fraldas_higiene": "Fraldas e higiene",
    "industria_comercio_e_negocios": "Indústria, comércio e negócios",
    "informatica_acessorios": "Informática e acessórios", "instrumentos_musicais": "Instrumentos musicais",
    "la_cuisine": "La cuisine", "livros_importados": "Livros importados",
    "livros_interesse_geral": "Livros de interesse geral", "livros_tecnicos": "Livros técnicos",
    "malas_acessorios": "Malas e acessórios", "market_place": "Marketplace",
    "moveis_colchao_e_estofado": "Colchões e estofados",
    "moveis_cozinha_area_de_servico_jantar_e_jardim": "Móveis de cozinha e jardim",
    "moveis_decoracao": "Móveis e decoração", "moveis_escritorio": "Móveis de escritório",
    "moveis_quarto": "Móveis de quarto", "moveis_sala": "Móveis de sala", "musica": "Música",
    "papelaria": "Papelaria", "pc_gamer": "PC gamer", "pcs": "PCs", "perfumaria": "Perfumaria",
    "pet_shop": "Pet shop", "portateis_casa_forno_e_cafe": "Fornos e cafeteiras",
    "portateis_cozinha_e_preparadores_de_alimentos": "Portáteis de cozinha",
    "relogios_presentes": "Relógios e presentes", "seguros_e_servicos": "Seguros e serviços",
    "sinalizacao_e_seguranca": "Sinalização e segurança", "tablets_impressao_imagem": "Tablets e impressão",
    "telefonia": "Telefonia", "telefonia_fixa": "Telefonia fixa", "utilidades_domesticas": "Utilidades domésticas",
}

SEM_CATEGORIA = "Sem categoria"


def nome_categoria(cat: str | float) -> str:
    if pd.isna(cat):
        return SEM_CATEGORIA
    return NOMES_CATEGORIA.get(cat, cat.replace("_", " ").capitalize())


def faixa_atraso(dias: float) -> str | float:
    if pd.isna(dias):
        return np.nan
    if dias <= 0:
        return "No prazo"
    if dias <= 3:
        return "1 a 3 dias"
    if dias <= 7:
        return "4 a 7 dias"
    if dias <= 14:
        return "8 a 14 dias"
    return "15+ dias"


def haversine_km(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(np.radians, (lat1, lng1, lat2, lng2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def ler(nome: str, **kw) -> pd.DataFrame:
    arq = RAW / (nome if nome.endswith(".csv") else f"olist_{nome}_dataset.csv")
    return pd.read_csv(arq, **kw)


def salvar(df: pd.DataFrame, nome: str) -> Path:
    """Salva em Parquet; sem pyarrow, cai para CSV comprimido (o app lê os dois)."""
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        caminho = OUT / f"{nome}.parquet"
        df.to_parquet(caminho, index=False)
    except ImportError:
        caminho = OUT / f"{nome}.csv.gz"
        df.to_csv(caminho, index=False)
    return caminho


def merge_validado(esq, dir_, log, nome, **kw):
    """Merge muitos-para-um que garante que nenhuma linha foi duplicada."""
    antes = len(esq)
    res = esq.merge(dir_, validate="m:1", **kw)
    if kw.get("how", "inner") == "left":
        assert len(res) == antes, f"{nome}: merge duplicou linhas"
    log.append({"merge": nome, "linhas_antes": antes, "linhas_depois": len(res)})
    return res


def main() -> None:
    log_merges: list[dict] = []
    tratamentos: dict[str, int] = {}

    # ---------------- Leitura ----------------
    datas = [
        "order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ]
    orders = ler("orders", parse_dates=datas)
    customers = ler("customers")
    items = ler("order_items", parse_dates=["shipping_limit_date"])
    payments = ler("order_payments")
    reviews = ler("order_reviews", parse_dates=["review_creation_date", "review_answer_timestamp"])
    products = ler("products")
    sellers = ler("sellers")
    geo = ler("geolocation")

    # ---------------- Geolocalização ----------------
    # 1M de linhas, várias por CEP e 42 pontos fora do Brasil -> 1 ponto médio por prefixo de CEP
    dentro = geo.geolocation_lat.between(-33.8, 5.3) & geo.geolocation_lng.between(-74.0, -34.7)
    tratamentos["geo_pontos_fora_do_brasil"] = int((~dentro).sum())
    geo = (
        geo[dentro]
        .groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(lat=("geolocation_lat", "mean"), lng=("geolocation_lng", "mean"))
        .rename(columns={"geolocation_zip_code_prefix": "zip"})
    )

    # ---------------- Clientes ----------------
    customers["cliente_cidade"] = customers.customer_city.str.title()
    customers["cliente_uf"] = customers.customer_state
    customers["cliente_regiao"] = customers.customer_state.map(REGIAO)
    customers = merge_validado(
        customers, geo.rename(columns={"zip": "customer_zip_code_prefix", "lat": "cliente_lat", "lng": "cliente_lng"}),
        log_merges, "clientes -> geolocalização", on="customer_zip_code_prefix", how="left",
    )
    tratamentos["clientes_sem_geolocalizacao"] = int(customers.cliente_lat.isna().sum())

    # ---------------- Vendedores ----------------
    sellers["vendedor_cidade"] = sellers.seller_city.str.title()
    sellers["vendedor_uf"] = sellers.seller_state
    sellers["vendedor_regiao"] = sellers.seller_state.map(REGIAO)
    sellers = merge_validado(
        sellers, geo.rename(columns={"zip": "seller_zip_code_prefix", "lat": "vendedor_lat", "lng": "vendedor_lng"}),
        log_merges, "vendedores -> geolocalização", on="seller_zip_code_prefix", how="left",
    )

    # ---------------- Produtos ----------------
    tratamentos["produtos_sem_categoria"] = int(products.product_category_name.isna().sum())
    products["categoria"] = products.product_category_name.map(nome_categoria)
    products["grupo_categoria"] = products.product_category_name.map(GRUPO_DE).fillna("Outros")
    products["peso_kg"] = products.product_weight_g / 1000

    # ---------------- Avaliações: 1 por pedido (a respondida mais recentemente) ----------------
    tratamentos["avaliacoes_duplicadas_por_pedido"] = int(reviews.order_id.duplicated().sum())
    reviews = (
        reviews.sort_values("review_answer_timestamp")
        .drop_duplicates("order_id", keep="last")
        .assign(tem_comentario=lambda d: d.review_comment_message.notna())
        [["order_id", "review_score", "tem_comentario", "review_creation_date"]]
        .rename(columns={"review_score": "nota", "review_creation_date": "data_avaliacao"})
    )

    # ---------------- Pagamentos: agregados por pedido ----------------
    tratamentos["pagamentos_tipo_indefinido"] = int((payments.payment_type == "not_defined").sum())
    payments = payments[payments.payment_type != "not_defined"]
    principal = (
        payments.sort_values("payment_value")
        .drop_duplicates("order_id", keep="last")
        .set_index("order_id")
        .payment_type.map(PAGAMENTO_PT)
        .rename("pagamento_principal")
    )
    pag = payments.groupby("order_id").agg(
        valor_pago=("payment_value", "sum"),
        parcelas=("payment_installments", "max"),
        qtd_formas_pagamento=("payment_type", "nunique"),
        usou_voucher=("payment_type", lambda s: (s == "voucher").any()),
    ).join(principal).reset_index()

    # ---------------- Itens (fato de grão item) ----------------
    items = merge_validado(
        items, products[["product_id", "categoria", "grupo_categoria", "peso_kg"]],
        log_merges, "itens -> produtos", on="product_id", how="left",
    )
    items = merge_validado(
        items, sellers[["seller_id", "vendedor_cidade", "vendedor_uf", "vendedor_regiao", "vendedor_lat", "vendedor_lng"]],
        log_merges, "itens -> vendedores", on="seller_id", how="left",
    )

    # ---------------- Pedidos (fato de grão pedido) ----------------
    tratamentos["pedidos_fora_do_periodo"] = int(
        (~orders.order_purchase_timestamp.between(INICIO, FIM, inclusive="left")).sum()
    )
    orders = orders[orders.order_purchase_timestamp.between(INICIO, FIM, inclusive="left")].copy()

    orders = merge_validado(
        orders, customers[["customer_id", "customer_unique_id", "cliente_cidade", "cliente_uf",
                           "cliente_regiao", "cliente_lat", "cliente_lng"]],
        log_merges, "pedidos -> clientes", on="customer_id", how="left",
    )

    agg_itens = items.groupby("order_id").agg(
        receita=("price", "sum"),
        frete=("freight_value", "sum"),
        qtd_itens=("order_item_id", "count"),
        qtd_vendedores=("seller_id", "nunique"),
        peso_kg=("peso_kg", "sum"),
    ).reset_index()
    # Categoria e vendedor principais = do item de maior preço
    item_principal = (
        items.sort_values("price").drop_duplicates("order_id", keep="last")
        [["order_id", "seller_id", "categoria", "grupo_categoria", "vendedor_uf", "vendedor_regiao",
          "vendedor_lat", "vendedor_lng"]]
    )
    orders = merge_validado(orders, agg_itens, log_merges, "pedidos -> itens (agregado)", on="order_id", how="left")
    orders = merge_validado(orders, item_principal, log_merges, "pedidos -> item principal", on="order_id", how="left")
    orders = merge_validado(orders, pag, log_merges, "pedidos -> pagamentos (agregado)", on="order_id", how="left")
    orders = merge_validado(orders, reviews, log_merges, "pedidos -> avaliação", on="order_id", how="left")

    # ---------------- Colunas derivadas ----------------
    o = orders
    o["status"] = o.order_status.map(STATUS_PT)
    o["pedido_valido"] = ~o.order_status.isin(STATUS_INVALIDOS) & o.receita.notna()
    o["data_compra"] = o.order_purchase_timestamp
    o["mes"] = o.data_compra.dt.to_period("M").dt.to_timestamp()
    o["dia_semana"] = o.data_compra.dt.dayofweek
    o["hora"] = o.data_compra.dt.hour

    entregue = (o.order_status == "delivered") & o.order_delivered_customer_date.notna()
    tratamentos["entregues_sem_data_de_entrega"] = int(
        ((o.order_status == "delivered") & o.order_delivered_customer_date.isna()).sum()
    )
    o["entregue"] = entregue
    o["dias_entrega"] = np.where(
        entregue, (o.order_delivered_customer_date - o.data_compra).dt.total_seconds() / 86400, np.nan
    )
    o["dias_prometidos"] = (o.order_estimated_delivery_date - o.data_compra).dt.total_seconds() / 86400
    # Atraso em dias inteiros de calendário: a data estimada não tem horário
    atraso = (o.order_delivered_customer_date.dt.normalize() - o.order_estimated_delivery_date.dt.normalize()).dt.days
    o["dias_atraso"] = np.where(entregue, atraso, np.nan)
    o["no_prazo"] = np.where(entregue, o.dias_atraso <= 0, np.nan)
    o["faixa_atraso"] = o.dias_atraso.map(faixa_atraso)
    o["nota_baixa"] = np.where(o.nota.notna(), o.nota <= 2, np.nan)
    o["mesmo_estado"] = o.cliente_uf == o.vendedor_uf
    o["distancia_km"] = haversine_km(o.vendedor_lat, o.vendedor_lng, o.cliente_lat, o.cliente_lng).round(1)
    o["frete_pct"] = o.frete / o.receita
    o["usou_voucher"] = o.usou_voucher.fillna(False).astype(bool)

    pedidos = o[[
        "order_id", "customer_unique_id", "status", "pedido_valido", "entregue",
        "data_compra", "mes", "dia_semana", "hora",
        "cliente_cidade", "cliente_uf", "cliente_regiao", "cliente_lat", "cliente_lng",
        "seller_id", "vendedor_uf", "vendedor_regiao", "mesmo_estado", "distancia_km",
        "categoria", "grupo_categoria",
        "receita", "frete", "frete_pct", "qtd_itens", "qtd_vendedores", "peso_kg",
        "valor_pago", "pagamento_principal", "parcelas", "qtd_formas_pagamento", "usou_voucher",
        "dias_entrega", "dias_prometidos", "dias_atraso", "no_prazo", "faixa_atraso",
        "nota", "nota_baixa", "tem_comentario",
    ]].rename(columns={"order_id": "pedido_id", "customer_unique_id": "cliente_id", "seller_id": "vendedor_principal_id"})

    # Itens restritos aos pedidos do período, com as chaves para filtrar pela tabela de pedidos
    itens = items[items.order_id.isin(pedidos.pedido_id)][[
        "order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value",
        "categoria", "grupo_categoria", "vendedor_cidade", "vendedor_uf", "vendedor_regiao",
    ]].rename(columns={
        "order_id": "pedido_id", "order_item_id": "item_seq", "product_id": "produto_id",
        "seller_id": "vendedor_id", "price": "preco", "freight_value": "frete",
    })

    # Clientes únicos (base da recompra), considerando só pedidos válidos
    validos = pedidos[pedidos.pedido_valido]
    clientes = validos.groupby("cliente_id").agg(
        qtd_pedidos=("pedido_id", "nunique"),
        primeira_compra=("data_compra", "min"),
        ultima_compra=("data_compra", "max"),
        receita_total=("receita", "sum"),
        uf=("cliente_uf", "last"),
        regiao=("cliente_regiao", "last"),
    ).reset_index()
    clientes["recorrente"] = clientes.qtd_pedidos >= 2

    # Vendedores com métricas agregadas (para ranking)
    vendedores = sellers[["seller_id", "vendedor_cidade", "vendedor_uf", "vendedor_regiao"]].rename(
        columns={"seller_id": "vendedor_id"}
    )

    # ---------------- Saída ----------------
    caminhos = {
        "pedidos": salvar(pedidos, "pedidos"),
        "itens": salvar(itens, "itens"),
        "clientes": salvar(clientes, "clientes"),
        "vendedores": salvar(vendedores, "vendedores"),
    }

    referencia = {
        "periodo": f"{INICIO.date()} a {(FIM - pd.Timedelta(days=1)).date()}",
        "pedidos_no_periodo": int(len(pedidos)),
        "pedidos_validos": int(validos.pedido_id.nunique()),
        "receita_pedidos_validos": round(float(validos.receita.sum()), 2),
        "frete_pedidos_validos": round(float(validos.frete.sum()), 2),
        "clientes_unicos": int(clientes.cliente_id.nunique()),
        "itens_no_periodo": int(len(itens)),
        "tratamentos": tratamentos,
        "merges": log_merges,
    }
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "referencia.json").write_text(json.dumps(referencia, indent=2, ensure_ascii=False), encoding="utf-8")

    for nome, c in caminhos.items():
        print(f"{nome:12s} -> {c.relative_to(ROOT)}")
    print(json.dumps(referencia, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
