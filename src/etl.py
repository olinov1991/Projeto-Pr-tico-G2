"""
ETL da base "Dados de suicídio no Brasil, 2014 a 2018" (DataSUS/SIM, via Kaggle).

Uso (na raiz do repositório):
    python -m src.etl

Princípios:
- Nenhuma linha é descartada: inconsistências viram NA ou recebem uma flag,
  e todas as correções são contadas em data/processed/etl_report.json.
- O arquivo bruto em data/raw/ nunca é alterado.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVO_BRUTO = RAIZ / "data" / "raw" / "datasus_suicidio_2014_2018.csv"
PASTA_SAIDA = RAIZ / "data" / "processed"

NAO_INFORMADO = "Não informado"
IDADE_MAXIMA = 110

COLUNAS = {
    "estado": "uf",
    "ano": "ano",
    "CIRCOBITO": "circunstancia_obito",
    "DTOBITO": "data_obito",
    "DTNASC": "data_nascimento",
    "SEXO": "sexo",
    "RACACOR": "raca_cor",
    "ESTCIV": "estado_civil",
    "ESC": "escolaridade",
    "OCUP": "ocupacao",
    "CODMUNRES": "municipio_residencia",
    "LOCOCOR": "local_ocorrencia",
    "ASSISTMED": "assistencia_medica",
    "CAUSABAS": "causa_basica",
    "CAUSABAS_O": "causa_basica_original",
    "idade": "idade",
    "mes": "mes",
}

CATEGORICAS = [
    "circunstancia_obito", "sexo", "raca_cor", "estado_civil", "escolaridade",
    "local_ocorrencia", "assistencia_medica",
]

REGIAO = {
    **dict.fromkeys(["AC", "AM", "AP", "PA", "RO", "RR", "TO"], "Norte"),
    **dict.fromkeys(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"], "Nordeste"),
    **dict.fromkeys(["DF", "GO", "MS", "MT"], "Centro-Oeste"),
    **dict.fromkeys(["ES", "MG", "RJ", "SP"], "Sudeste"),
    **dict.fromkeys(["PR", "RS", "SC"], "Sul"),
}

FAIXAS_BORDAS = [0, 10, 15, 20, 30, 40, 50, 60, 70, 80, IDADE_MAXIMA + 1]
FAIXAS_ROTULOS = ["0-9", "10-14", "15-19", "20-29", "30-39", "40-49",
                  "50-59", "60-69", "70-79", "80+"]

logger = logging.getLogger("etl")


# --------------------------------------------------------------------------- #
# Extração
# --------------------------------------------------------------------------- #
def carregar_bruto(caminho: Path = ARQUIVO_BRUTO) -> pd.DataFrame:
    """Lê o CSV bruto (codificação latin-1, separador vírgula)."""
    df = pd.read_csv(caminho, encoding="latin-1", dtype=str)
    logger.info("Linhas lidas: %d | colunas: %d", *df.shape)
    return df


# --------------------------------------------------------------------------- #
# Transformação
# --------------------------------------------------------------------------- #
def padronizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=COLUNAS)
    df = df[list(COLUNAS.values())].copy()
    for col in df.columns:
        df[col] = df[col].str.strip()
    df["ano"] = pd.to_numeric(df["ano"], errors="raise").astype("int16")
    df["mes"] = pd.to_numeric(df["mes"], errors="raise").astype("int8")
    df["idade"] = pd.to_numeric(df["idade"], errors="coerce")
    return df


def tratar_datas(df: pd.DataFrame, rel: dict) -> pd.DataFrame:
    """Converte datas dd-mm-aa. O ano de 2 dígitos é ambíguo para nascimentos,
    então, se a data de nascimento ficar posterior ao óbito, subtrai 100 anos."""
    obito = pd.to_datetime(df["data_obito"], format="%d-%m-%y", errors="coerce")
    nasc = pd.to_datetime(df["data_nascimento"], format="%d-%m-%y", errors="coerce")

    posterior = nasc > obito
    rel["nascimentos_corrigidos_seculo"] = int(posterior.sum())
    nasc = nasc.mask(posterior, nasc - pd.DateOffset(years=100))

    df["data_obito"] = obito
    df["data_nascimento"] = nasc
    df["flag_data_inconsistente"] = (
        (obito.dt.year != df["ano"]) | (obito.dt.month != df["mes"])
    )
    rel["datas_obito_invalidas"] = int(obito.isna().sum())
    rel["linhas_data_inconsistente_com_ano_mes"] = int(df["flag_data_inconsistente"].sum())
    return df


def tratar_idade(df: pd.DataFrame, rel: dict) -> pd.DataFrame:
    invalida = df["idade"].notna() & ~df["idade"].between(0, IDADE_MAXIMA)
    rel["idades_fora_de_0_110_viraram_na"] = int(invalida.sum())
    df["flag_idade_invalida"] = invalida
    df.loc[invalida, "idade"] = np.nan
    df["idade"] = df["idade"].astype("Int16")
    df["faixa_etaria"] = pd.cut(
        df["idade"].astype("float"), bins=FAIXAS_BORDAS, labels=FAIXAS_ROTULOS, right=False
    ).astype("str").replace("nan", NAO_INFORMADO)
    return df


def tratar_categoricas(df: pd.DataFrame, rel: dict) -> pd.DataFrame:
    # Código numérico solto em local_ocorrencia ("6") não consta no dicionário original
    codigo_invalido = df["local_ocorrencia"] == "6"
    rel["local_ocorrencia_codigo_6_invalido"] = int(codigo_invalido.sum())
    df.loc[codigo_invalido, "local_ocorrencia"] = np.nan

    # Ocupação "0" significa ausência de informação
    ocup_zero = df["ocupacao"] == "0"
    rel["ocupacao_zero_sem_informacao"] = int(ocup_zero.sum())
    df.loc[ocup_zero, "ocupacao"] = np.nan

    rel["nulos_antes_do_preenchimento"] = {c: int(df[c].isna().sum()) for c in CATEGORICAS + ["ocupacao"]}
    df["ocupacao"] = df["ocupacao"].str.upper()   # padroniza antes de preencher, para não alterar "Não informado"
    for col in CATEGORICAS + ["ocupacao"]:
        df[col] = df[col].fillna(NAO_INFORMADO)
    return df


def classificar_meio(codigo: str) -> str:
    """Agrupa o código CID-10 X60–X84 (lesão autoprovocada intencional) em grandes grupos."""
    if not isinstance(codigo, str) or not codigo.startswith("X") or len(codigo) < 3:
        return "Fora de X60-X84"
    try:
        n = int(codigo[1:3])
    except ValueError:
        return "Fora de X60-X84"
    if 60 <= n <= 69:
        return "Intoxicação/envenenamento"
    if n == 70:
        return "Enforcamento/sufocação"
    if n == 71:
        return "Afogamento"
    if 72 <= n <= 74:
        return "Arma de fogo"
    if n in (78, 79):
        return "Objeto cortante/contundente"
    if n == 80:
        return "Precipitação de lugar elevado"
    if 75 <= n <= 84:
        return "Outros meios"
    return "Fora de X60-X84"


def criar_variaveis(df: pd.DataFrame, rel: dict) -> pd.DataFrame:
    df["regiao"] = df["uf"].map(REGIAO).fillna(NAO_INFORMADO)
    df["meio_utilizado"] = df["causa_basica"].map(classificar_meio)
    df["lesao_autoprovocada"] = df["meio_utilizado"] != "Fora de X60-X84"
    rel["uf_sem_regiao"] = int((df["regiao"] == NAO_INFORMADO).sum())
    rel["linhas_lesao_autoprovocada_x60_x84"] = int(df["lesao_autoprovocada"].sum())
    rel["linhas_fora_de_x60_x84"] = int((~df["lesao_autoprovocada"]).sum())
    return df


# --------------------------------------------------------------------------- #
# Validação e carga
# --------------------------------------------------------------------------- #
def validar(df: pd.DataFrame, n_bruto: int) -> None:
    assert len(df) == n_bruto, "O ETL não pode descartar linhas"
    assert df["ano"].between(2014, 2018).all(), "Ano fora do intervalo 2014-2018"
    assert df["mes"].between(1, 12).all(), "Mês inválido"
    assert df["uf"].nunique() == 27, "Esperadas 27 UFs"
    assert not df.duplicated().any(), "Linhas duplicadas"


def salvar(df: pd.DataFrame, rel: dict, pasta: Path = PASTA_SAIDA) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    df.to_parquet(pasta / "suicidios_2014_2018.parquet", index=False)
    df.to_csv(pasta / "suicidios_2014_2018.csv.gz", index=False, compression="gzip")
    with open(pasta / "etl_report.json", "w", encoding="utf-8") as f:
        json.dump(rel, f, ensure_ascii=False, indent=2)
    logger.info("Arquivos salvos em %s", pasta)


def executar() -> pd.DataFrame:
    rel: dict = {}
    bruto = carregar_bruto()
    rel["linhas_brutas"] = len(bruto)
    rel["nulos_brutos"] = {c: int(v) for c, v in bruto.isna().sum().items() if v}

    df = padronizar_colunas(bruto)
    df = tratar_datas(df, rel)
    df = tratar_idade(df, rel)
    df = tratar_categoricas(df, rel)
    df = criar_variaveis(df, rel)

    validar(df, len(bruto))
    rel["linhas_processadas"] = len(df)
    salvar(df, rel)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    executar()
