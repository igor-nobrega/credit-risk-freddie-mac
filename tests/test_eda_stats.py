import math

import pandas as pd
import pytest

from credit_risk.eda_stats import iv_of, standardize_mix


def test_iv_hand_computed_two_buckets():
    # bons=[90,10], maus=[10,90], suavizacao 0,5 -> dg=[90.5,10.5]/101, db=[10.5,90.5]/101
    g = pd.DataFrame({"n_loans": [100, 100], "n_defaults": [10, 90]})
    dg1, dg2, db1, db2 = 90.5 / 101, 10.5 / 101, 10.5 / 101, 90.5 / 101
    expected = (dg1 - db1) * math.log(dg1 / db1) + (dg2 - db2) * math.log(dg2 / db2)
    assert iv_of(g) == pytest.approx(expected, rel=1e-12)
    assert expected == pytest.approx(
        3.40, abs=0.05
    )  # ordem de grandeza conhecida (separacao forte)


def test_iv_is_zero_without_separation_and_grows_with_it():
    flat = pd.DataFrame({"n_loans": [1000, 1000, 1000], "n_defaults": [100, 100, 100]})
    mild = pd.DataFrame({"n_loans": [1000, 1000, 1000], "n_defaults": [60, 100, 140]})
    strong = pd.DataFrame({"n_loans": [1000, 1000, 1000], "n_defaults": [20, 100, 300]})
    assert iv_of(flat) == pytest.approx(0.0, abs=1e-3)
    assert 0 < iv_of(mild) < iv_of(strong)


def test_standardize_mix_hand_computed():
    # base: A 100 loans/10 defaults (10%), B 100/30 (30%) -> taxa 20%
    # teste: A 300/45 (15%), B 100/40 (40%) -> taxa 85/400 = 21,25%
    cells = pd.DataFrame(
        {
            "era": ["b", "b", "t", "t"],
            "cell": ["A", "B", "A", "B"],
            "n_loans": [100, 100, 300, 100],
            "n_defaults": [10, 30, 45, 40],
        }
    )
    r = standardize_mix(cells, "b", "t")
    # mix de teste = 75% A + 25% B com taxas da base: 0,75*0,10 + 0,25*0,30 = 0,15
    assert r["base"] == pytest.approx(0.20)
    assert r["expected"] == pytest.approx(0.15)
    assert r["actual"] == pytest.approx(0.2125)
    assert r["mix_effect"] == pytest.approx(-0.05)  # o perfil de teste e MELHOR
    assert r["rate_effect"] == pytest.approx(0.0625)  # mas o risco dentro das celulas piorou
    assert r["mix_effect"] + r["rate_effect"] == pytest.approx(r["actual"] - r["base"])


def test_standardize_mix_unseen_cell_uses_base_average_and_missing_era_returns_none():
    cells = pd.DataFrame(
        {
            "era": ["b", "t", "t"],
            "cell": ["A", "A", "C"],
            "n_loans": [100, 100, 100],
            "n_defaults": [10, 10, 30],
        }
    )
    r = standardize_mix(cells, "b", "t")
    # celula C nao existe na base: usa a taxa media da base (10%) -> esperado = 0,5*0,10 + 0,5*0,10
    assert r["expected"] == pytest.approx(0.10)
    assert standardize_mix(cells, "b", "x") is None
