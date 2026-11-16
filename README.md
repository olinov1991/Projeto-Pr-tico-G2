# Análise de óbitos por lesão autoprovocada no Brasil (2014–2018)

![Python](https://img.shields.io/badge/python-3.12-blue)
![Licença do código](https://img.shields.io/badge/c%C3%B3digo-MIT-green)
![Licença dos dados e texto](https://img.shields.io/badge/dados%20e%20texto-CC--BY%204.0-lightgrey)
![FAIR](https://img.shields.io/badge/FAIR-compliant-informational)

**Autores:** Leandro Parreira Novarino
**Instituição:** UNILASALLE-niteroi · Bacharelado em Sistemas de Informação, 6º período
**Disciplina:** Linguagem de Programação (Análise e Visualização de Dados com Python) · 6º semestre do ano de 2026
**Docente:** Alexandre Neves Louzada

**Artigo publicado:** https://github.com/olinov1991/Projeto-Pr-tico-G2

## Resumo executivo

[TODO: 3 a 5 linhas com tema, método e principais achados. Copie o resumo do artigo em `docs/index.html`.]

Este projeto analisa 58.634 registros de óbitos do Sistema de Informações sobre Mortalidade (SIM/DataSUS) entre 2014 e 2018, com um pipeline reproduzível em Python (pandas) e visualizações estáticas e interativas.

## Palavras-chave

análise de dados; saúde pública; mortalidade; DataSUS; Python; ciência aberta

## Perguntas de pesquisa

- **RQ1:** Como evoluíram os óbitos por ano e por região/UF no período?
- **RQ2:** Qual o perfil por sexo, faixa etária e escolaridade?
- **RQ3:** Há padrão sazonal (mês) ou por local de ocorrência?
## Fonte dos dados

- Kaggle, *Dados de suicídio no Brasil, 2014 a 2018* (psicodata): https://www.kaggle.com/datasets/psicodata/dados-de-suicdio-no-brasil-2014-a-2018
- Origem primária: SIM/DataSUS, Ministério da Saúde.
- Confira a licença indicada na página do Kaggle e cite a fonte em qualquer reuso.

## Estrutura do repositório

```
.
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/                  # CSV original, nunca alterado
│   ├── processed/            # Parquet, CSV.gz e etl_report.json
│   ├── external/             # (opcional) populacao_uf.csv do IBGE para taxas
│   └── data_dictionary.md    # Dicionário de variáveis
├── notebooks/
│   └── analise_exploratoria.ipynb
├── src/
│   ├── __init__.py
│   └── etl.py                # Limpeza, variáveis derivadas e validações
└── docs/
    ├── index.html            # Artigo (GitHub Pages)
    └── assets/               # Figuras e gráficos exportados
```

## Como reproduzir

Requer Python 3.12.

```bash
git clone https://github.com/olinov1991/Projeto-Pr-tico-G2.git
cd Projeto-Pr-tico-G2

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.etl                # gera os arquivos em data/processed/
pip install jupyterlab           # se ainda não tiver
jupyter lab notebooks/analise_exploratoria.ipynb   # Run All; exporta figuras para docs/assets/
```

O notebook cobre as RQ1 a RQ3 e grava as figuras (PNG e HTML interativo) em `docs/assets/`. Para calcular taxas por 100 mil habitantes, salve a população do IBGE em `data/external/populacao_uf.csv` (colunas `uf,ano,populacao`; veja `populacao_uf_MODELO.csv`); sem esse arquivo, a seção de taxas é ignorada.

O ETL não descarta linhas; cada correção é contada em `data/processed/etl_report.json`. Detalhes dos campos e tratamentos em [`data/data_dictionary.md`](data/data_dictionary.md).

## Publicação no GitHub Pages

Em **Settings → Pages**, escolha *Deploy from a branch*, branch `main` e pasta `/docs`.

## Licenças

- **Código** (`src/`, notebooks): MIT.
- **Texto, figuras e dados tratados:** CC-BY 4.0 (https://creativecommons.org/licenses/by/4.0/), respeitada a licença da fonte original.


## Nota sobre o tema

Os dados tratam de mortes e devem ser lidos com respeito. Se você ou alguém próximo precisa de apoio, o Centro de Valorização da Vida (CVV) atende gratuitamente, 24 horas, pelo telefone **188** e em cvv.org.br.
