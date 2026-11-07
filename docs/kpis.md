# Indicadores

Todos calculados sobre o recorte filtrado (`app/core/metrics.py`). Por padrão, só pedidos válidos: sem cancelados
e indisponíveis. Valores abaixo = base inteira, jan/2017 a ago/2018.

| KPI | Fórmula | Por que importa | Valor |
| --- | --- | --- | ---: |
| Receita | soma de `price` dos itens (sem frete) | tamanho do negócio | R$ 13,45 mi |
| Pedidos | contagem distinta de `order_id` | volume | 97.905 |
| Ticket médio | receita ÷ pedidos | quanto o cliente gasta por compra | R$ 137,37 |
| Clientes únicos | contagem distinta de `customer_unique_id` | base de clientes | 94.703 |
| Taxa de recompra | clientes com 2+ pedidos ÷ clientes únicos | fidelização | 3,0% |
| % entregas no prazo | entregues até a data estimada ÷ entregues | promessa cumprida | 93,2% |
| Tempo médio de entrega | média de dias entre compra e entrega | experiência | 12,5 dias |
| Prazo prometido médio | média de dias entre compra e data estimada | o que o cliente espera | 23,6 dias |
| Nota média | média de `review_score` (1 avaliação por pedido) | satisfação | 4,12 |
| % notas baixas | notas 1 ou 2 ÷ avaliações | insatisfação explícita | 13,8% |
| Frete sobre receita | soma do frete ÷ receita | peso da logística no bolso do cliente | 16,6% |

## Decisões de cálculo

- **Atraso** é contado em dias de calendário: a data estimada não tem horário, então um pedido entregue no próprio
  dia estimado conta como no prazo.
- **Receita por categoria** usa o preço de cada item; um pedido com itens de duas categorias divide sua receita
  entre elas.
- **Recompra** depende do período filtrado: com um mês só, quase ninguém volta. O valor de referência usa os 20 meses.
