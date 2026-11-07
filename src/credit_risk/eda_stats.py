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
