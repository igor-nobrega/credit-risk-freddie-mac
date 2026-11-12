"""Estatisticas da EDA, isoladas do script para serem testadas com numeros conhecidos."""

from __future__ import annotations

import numpy as np
import pandas as pd


def iv_of(g: pd.DataFrame) -> float:
    """Information Value de uma variavel. g: uma linha por faixa, colunas n_loans e n_defaults.

    Usa suavizacao de 0,5 por faixa para evitar log(0). IV = soma (%bons - %maus) * ln(%bons / %maus).
    """
    bad = g["n_defaults"].to_numpy(float)
    good = (g["n_loans"] - g["n_defaults"]).to_numpy(float)
    k = len(g)
    dg, db = (good + 0.5) / (good.sum() + 0.5 * k), (bad + 0.5) / (bad.sum() + 0.5 * k)
    return float(((dg - db) * np.log(dg / db)).sum())


def iv_null_expectation(g: pd.DataFrame) -> float:
    """IV esperado quando a variavel e INDEPENDENTE do alvo (puro ruido amostral): (k-1) * (1/N_bons + 1/N_maus).

    O IV e uma divergencia de Jeffreys, que sob independencia se comporta como qui-quadrado / N. O viés cresce com o
    numero de faixas e com poucos defaults, o que distorce o IV calculado por vintage ou por era.
    """
    bad = float(g["n_defaults"].sum())
    good = float((g["n_loans"] - g["n_defaults"]).sum())
    if bad <= 0 or good <= 0:
        return 0.0
    return (len(g) - 1) * (1.0 / good + 1.0 / bad)


def iv_corrected(g: pd.DataFrame) -> float:
    """IV menos o ruido amostral esperado (nunca negativo). Use para comparar vintages/eras e variaveis com muitas faixas."""
    return max(0.0, iv_of(g) - iv_null_expectation(g))


def standardize_mix(cells: pd.DataFrame, base_era: str, test_era: str) -> dict | None:
    """Separa o efeito do PERFIL (mix de celulas) do efeito do RISCO dentro das celulas.

    cells: colunas era, cell, n_loans, n_defaults. Retorna taxa base, taxa esperada (mix da era de teste com as
    taxas por celula da era base), taxa observada e os dois efeitos. Celulas sem loans na base usam a taxa media da base.
    """
    p = cells.pivot_table(
        index="cell", columns="era", values=["n_loans", "n_defaults"], aggfunc="sum", fill_value=0
    )
    if base_era not in p["n_loans"] or test_era not in p["n_loans"]:
        return None
    nb, db, nt, dt_ = (
        p["n_loans"][base_era],
        p["n_defaults"][base_era],
        p["n_loans"][test_era],
        p["n_defaults"][test_era],
    )
    if nb.sum() == 0 or nt.sum() == 0:
        return None
    base, actual = db.sum() / nb.sum(), dt_.sum() / nt.sum()
    cell_rate = (db / nb.where(nb > 0)).fillna(base)
    expected = float((nt / nt.sum() * cell_rate).sum())
    return {
        "base": float(base),
        "expected": expected,
        "actual": float(actual),
        "mix_effect": expected - float(base),
        "rate_effect": float(actual) - expected,
    }


ERAS = ["1999-2003", "2004-2008", "2009-2011", "2012-2017", "2018-2021", "2022-2023"]


def era_of(year: int) -> str:
    """Mesma regra da macro `era()` do dbt."""
    return (
        "1999-2003" if year <= 2003 else "2004-2008" if year <= 2008 else "2009-2011" if year <= 2011
        else "2012-2017" if year <= 2017 else "2018-2021" if year <= 2021 else "2022-2023"
    )  # fmt: skip


def iv_table(feats: pd.DataFrame) -> pd.DataFrame:
    """IV por variavel (corrigido do ruido amostral): agregado (todas as vintages juntas), por era e INTRA-vintage.

    feats: colunas feature, bucket, vintage_year, n_loans, n_defaults.
    O IV intra-vintage e a media dos IV de cada vintage ponderada pelos defaults da vintage: remove o efeito de
    variaveis que apenas identificam a EPOCA (ex.: taxa de juros, campos que so existem em safras recentes).
    """
    f = feats.copy()
    f["era"] = f["vintage_year"].map(era_of)
    rows = []
    for feature, g in f.groupby("feature"):
        pooled = iv_corrected(g.groupby("bucket", as_index=False)[["n_loans", "n_defaults"]].sum())
        by_v = {v: iv_corrected(gv) for v, gv in g.groupby("vintage_year")}
        w = g.groupby("vintage_year")["n_defaults"].sum()
        intra = float(sum(by_v[v] * w[v] for v in by_v) / w.sum()) if w.sum() > 0 else float("nan")
        row = {"variavel": feature, "IV_agregado": pooled, "IV_intra_vintage": intra}
        for era, ge in g.groupby("era"):
            row[era] = iv_corrected(
                ge.groupby("bucket", as_index=False)[["n_loans", "n_defaults"]].sum()
            )
        rows.append(row)
    out = pd.DataFrame(rows)
    for e in ERAS:
        if e not in out:
            out[e] = np.nan
    out["razao_intra_agregado"] = out["IV_intra_vintage"] / out["IV_agregado"].where(
        out["IV_agregado"] > 0
    )
    out["leitura"] = np.where(
        out["IV_agregado"] < 0.02, "sem poder",
        np.where(out["razao_intra_agregado"] < 0.6, "confundida com a epoca", "estavel"),
    )  # fmt: skip
    return out[
        ["variavel", "IV_agregado", "IV_intra_vintage", "razao_intra_agregado", *ERAS, "leitura"]
    ].sort_values("IV_agregado", ascending=False)
