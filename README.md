# Dashboard Olist — o que determina a satisfação do cliente?

Trabalho de Business Intelligence (P2) sobre a base pública
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
feito em Python com Streamlit e Plotly.

Grupo: João Pedro Moreno Alegre, Mateus dos Santos Pereira, Iago Amorim Lebron de Lima, Guilherme Dias dos Santos.

**Resposta curta:** a entrega no prazo é o fator mais claramente ligado à nota. Pedidos entregues no prazo têm nota
média 4,29; atrasados, 2,27. Só 6,8% das entregas atrasam, mas elas geram 32,6% das notas 1 e 2.
Detalhes em [docs/descobertas.md](docs/descobertas.md).

## Como rodar

Precisa de Python 3.10 ou mais novo.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    |    Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

O navegador abre em `http://localhost:8501`. No Windows, dá para usar só `rodar.bat`.

As tabelas tratadas já vêm em `data/processed/`. Para refazer o tratamento do zero, coloque os 9 CSVs do Kaggle
em `data/raw/` e rode `python etl/build.py` (cerca de 15 segundos).

## Testes

```bash
pip install pytest
python -m pytest tests -v -s
```

Abrem cada uma das 6 páginas em 5 recortes de filtro, conferem os KPIs da Visão geral e a busca da Exploração, e
medem o tempo de cada página.

## Estrutura

```
app/
  app.py              entrada: filtros globais e navegação
  core/data.py        carga das tabelas e aplicação dos filtros
  core/metrics.py     KPIs (funções sobre o recorte filtrado) e textos de ajuda
  core/ui.py          formatação pt-BR, paleta e componentes de gráfico
  views/              uma página por arquivo (6 páginas)
etl/build.py          limpeza, modelo (merges validados) e tabelas analíticas
data/processed/       tabelas tratadas lidas pelo app
data/raw/             CSVs originais do Kaggle (fora do Git)
tests/test_app.py     testes com streamlit.testing (AppTest)
docs/                 documentação (abaixo)
.claude/launch.json   configuração para subir o app pelo Claude Code
CLAUDE.md             regras do projeto para o Claude Code
rodar.bat / rodar.sh  criam o ambiente e abrem o app
```

## Documentação

| Arquivo | Conteúdo |
| --- | --- |
| [docs/dashboard.md](docs/dashboard.md) | Tudo o que aparece no app: filtros, páginas, gráficos e interações |
| [docs/decisoes.md](docs/decisoes.md) | Registro das decisões de projeto e pendências conhecidas |
| [docs/qualidade.md](docs/qualidade.md) | Perfil da base original e tratamentos aplicados |
| [docs/modelo.md](docs/modelo.md) | Modelo de dados e onde cada relacionamento é usado |
| [docs/kpis.md](docs/kpis.md) | Fórmula e motivo de cada indicador |
| [docs/descobertas.md](docs/descobertas.md) | Descobertas, decisões que os dados apoiam e limitações |
| [docs/apresentacao.md](docs/apresentacao.md) | Estrutura da apresentação e divisão das falas |
| [docs/roteiro-de-falas.pdf](docs/roteiro-de-falas.pdf) | Roteiro de falas de cada integrante |
| `docs/referencia.json` | Números de referência e log dos merges, gerado pelo `etl/build.py` |

## Páginas

| Página | Pergunta |
| --- | --- |
| Visão geral | Qual o tamanho do negócio, como evoluiu e o que mais vende? |
| Logística e satisfação | O atraso na entrega explica a nota? |
| Clientes e geografia | Onde estão os clientes, onde a entrega demora, o cliente volta? |
| Produtos e vendedores | Quais categorias e vendedores concentram atraso e insatisfação? |
| Exploração | Quais pedidos estão por trás de cada número? |
| Dados e modelo | Como a base foi tratada e como as tabelas se relacionam? |
