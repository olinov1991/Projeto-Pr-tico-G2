# Dicionário de dados

**Fonte:** Kaggle, *Dados de suicídio no Brasil, 2014 a 2018* (psicodata), originado do Sistema de Informações sobre Mortalidade (SIM/DataSUS).
https://www.kaggle.com/datasets/psicodata/dados-de-suicdio-no-brasil-2014-a-2018

**Granularidade:** uma linha por óbito registrado. A base não contém identificadores pessoais nem denominadores populacionais (taxas exigem dados externos, como as projeções de população do IBGE).

**Arquivos**

| Arquivo | Descrição |
| --- | --- |
| `data/raw/datasus_suicidio_2014_2018.csv` | Dados brutos originais (58.634 linhas × 17 colunas; codificação `latin-1`, separador `,`). Nunca alterado. |
| `data/processed/suicidios_2014_2018.parquet` | Dados tratados (58.634 linhas × 23 colunas), formato principal. |
| `data/processed/suicidios_2014_2018.csv.gz` | Mesmos dados tratados em CSV comprimido (UTF-8). |
| `data/processed/etl_report.json` | Contagem de cada correção aplicada pelo ETL (rastreabilidade). |

## Variáveis originais (renomeadas no processamento)

| Nome bruto | Nome tratado | Tipo | Formato / valores | Significado |
| --- | --- | --- | --- | --- |
| `estado` | `uf` | texto | sigla da UF (27 valores) | Unidade da Federação. |
| `ano` | `ano` | inteiro | 2014 a 2018 | Ano do óbito. |
| `CIRCOBITO` | `circunstancia_obito` | texto | Suicídio, Acidente, Homicídio, Outro, Não informado | Circunstância do óbito declarada na certidão. |
| `DTOBITO` | `data_obito` | data | `AAAA-MM-DD` (bruto: `dd-mm-aa`) | Data do óbito. |
| `DTNASC` | `data_nascimento` | data | `AAAA-MM-DD` (bruto: `dd-mm-aa`) | Data de nascimento. Ausente em 227 linhas. |
| `SEXO` | `sexo` | texto | Masculino, Feminino, Não informado | Sexo registrado. |
| `RACACOR` | `raca_cor` | texto | Branca, Parda, Preta, Indígena, Amarela, Não informado | Raça/cor declarada. |
| `ESTCIV` | `estado_civil` | texto | Solteiro, Casado, União consensual, Separado judicialmente, Viúvo, Não informado | Estado civil. |
| `ESC` | `escolaridade` | texto | Nenhuma, 1 a 3 anos, 4 a 7 anos, 8 a 11 anos, 12 e mais, Não informado | Anos de estudo. |
| `OCUP` | `ocupacao` | texto | descrição em maiúsculas | Ocupação (cerca de 1.100 valores distintos). `0` no bruto significa sem informação. |
| `CODMUNRES` | `municipio_residencia` | texto | nome do município | Município de residência. Apesar do nome bruto, **não é código**, é o nome do município. |
| `LOCOCOR` | `local_ocorrencia` | texto | Domicílio, Hospital, Via pública, Outro estabelecimento de saúde, Outros, Não informado | Local de ocorrência do óbito. |
| `ASSISTMED` | `assistencia_medica` | texto | Sim, Não, Não informado | Houve assistência médica antes do óbito. |
| `CAUSABAS` | `causa_basica` | texto | código CID-10, ex.: `X700` | Causa básica do óbito (CID-10). |
| `CAUSABAS_O` | `causa_basica_original` | texto | código CID-10 | Causa básica original, antes de reclassificação. Ausente em 90 linhas. |
| `idade` | `idade` | inteiro | 0 a 110 | Idade em anos completos. Valores fora de 0–110 viram NA. |
| `mes` | `mes` | inteiro | 1 a 12 | Mês do óbito. |

## Variáveis derivadas (criadas em `src/etl.py`)

| Nome | Tipo | Valores | Regra |
| --- | --- | --- | --- |
| `faixa_etaria` | texto | 0-9, 10-14, 15-19, 20-29, 30-39, 40-49, 50-59, 60-69, 70-79, 80+, Não informado | Faixas a partir de `idade`. |
| `regiao` | texto | Norte, Nordeste, Centro-Oeste, Sudeste, Sul | Região geográfica a partir de `uf`. |
| `lesao_autoprovocada` | booleano | `True`/`False` | `True` se `causa_basica` está entre X60 e X84 (CID-10: lesões autoprovocadas intencionalmente). |
| `meio_utilizado` | texto | Enforcamento/sufocação, Intoxicação/envenenamento, Arma de fogo, Precipitação de lugar elevado, Objeto cortante/contundente, Afogamento, Outros meios, Fora de X60-X84 | Agrupamento do código CID-10 em grandes grupos. |
| `flag_data_inconsistente` | booleano | `True`/`False` | `True` se ano/mês de `data_obito` diverge de `ano`/`mes`. |
| `flag_idade_invalida` | booleano | `True`/`False` | `True` se a idade informada estava fora de 0–110 (valor original substituído por NA). |

## Tratamentos aplicados (resumo)

1. Leitura em `latin-1`; remoção de espaços nas bordas das strings.
2. Datas: ano de 2 dígitos é ambíguo; quando a data de nascimento resultava posterior ao óbito, subtraíram-se 100 anos (21.473 casos). Após a correção, a idade calculada pelas datas coincide (±1 ano) com `idade` em 99,98% dos casos.
3. `local_ocorrencia = "6"` (24 linhas) não existe no dicionário original e virou "Não informado".
4. Nulos categóricos foram preenchidos com "Não informado" (a contagem original está em `etl_report.json`).
5. **Nenhuma linha é removida.** Para análises restritas a suicídios, filtre `lesao_autoprovocada == True` (58.492 linhas; 142 ficam de fora).

## Limitações conhecidas

- Sem população de referência: comparações entre UFs devem usar taxas por 100 mil habitantes (dados externos).
- Subnotificação e erros de classificação de causa são conhecidos em registros de mortalidade.
- Há 31 registros com idade de 0 a 9 anos, que merecem verificação antes de interpretação.
- Campos com muitos "Não informado" (`escolaridade`, `assistencia_medica`, `ocupacao`) limitam análises por esses atributos.
