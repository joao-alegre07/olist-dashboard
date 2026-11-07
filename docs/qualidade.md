# Qualidade dos dados e tratamento

Perfil da base original (9 CSVs do Kaggle) e o que foi feito com cada problema. Os números de registros afetados
são gerados pelo `etl/build.py` e ficam em `docs/referencia.json`.

## Tamanho das tabelas

| Tabela | Linhas | Observação |
| --- | ---: | --- |
| orders | 99.441 | 8 status; datas de aprovação e entrega com nulos (pedidos não entregues) |
| order_items | 112.650 | até 21 itens por pedido |
| order_payments | 103.886 | várias linhas por pedido (cartão + voucher, por exemplo) |
| order_reviews | 99.224 | 551 avaliações extras para pedidos já avaliados |
| customers | 99.441 | 96.096 clientes reais (`customer_unique_id`) |
| products | 32.951 | 610 sem categoria |
| sellers | 3.095 | 23 estados |
| geolocation | 1.000.163 | 261.831 linhas idênticas, 42 pontos fora do Brasil |
| category_name_translation | 71 | 2 categorias sem tradução |

## Problemas e tratamentos

| Problema | Tratamento | Afetados |
| --- | --- | ---: |
| 2016 e set–out/2018 com volume residual (dados incompletos nas pontas) | Recorte de jan/2017 a ago/2018 | 349 pedidos |
| Geolocalização com várias linhas por CEP e pontos fora do Brasil | Remove pontos fora do Brasil; 1 ponto médio por prefixo de CEP | 42 pontos |
| `customer_id` é gerado por pedido | Clientes e recompra contados por `customer_unique_id` | — |
| Pedidos com mais de uma avaliação | Mantém a respondida mais recentemente | 551 |
| Produtos sem categoria | "Sem categoria", grupo "Outros" | 610 |
| 73 categorias em snake_case, algumas duplicadas (`_2`) | Nomes legíveis em português e 13 grupos | — |
| Pagamento em várias linhas por pedido | Agregado por pedido; forma principal = a de maior valor | — |
| `payment_type = not_defined` | Removido | 3 |
| Status "delivered" sem data de entrega | Fora das métricas de prazo | 8 |
| CEP do cliente sem geolocalização | Fora do mapa e do cálculo de distância | 279 |
| Pedidos cancelados, indisponíveis ou sem itens | Fora dos KPIs por padrão (o filtro permite incluir) | 1.187 no período |

## Outras observações (não tratadas, registradas)

- 249 pedidos têm diferença maior que R$ 1 entre itens + frete e o valor pago (provavelmente juros de parcelamento
  ou vouchers). A receita do dashboard usa o preço dos itens, então não é afetada.
- 166 pedidos têm data de envio à transportadora anterior à compra. Essa data não é usada nas métricas.
- Cidades aparecem com e sem acento na geolocalização ("sao paulo" e "são paulo"). O dashboard usa a cidade do
  cadastro do cliente, que é padronizada.

## Conferência

Os totais do pipeline foram recalculados direto dos CSVs brutos, por um caminho independente, e bateram:
97.905 pedidos válidos, R$ 13.449.529,68 de receita, R$ 2.234.177,06 de frete e 94.703 clientes únicos.
Nenhum merge duplicou linhas (todos com `validate="m:1"`; log em `docs/referencia.json`).
