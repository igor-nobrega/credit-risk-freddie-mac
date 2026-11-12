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


def _feats(rows):
    return pd.DataFrame(
        rows, columns=["feature", "bucket", "vintage_year", "n_loans", "n_defaults"]
    )


def test_iv_table_separates_a_pure_time_proxy_from_a_truly_predictive_variable():
    from credit_risk.eda_stats import iv_table

    rows = []
    for year, rate in ((2000, 0.10), (2001, 0.01)):  # duas vintages com risco MUITO diferente
        n = 10_000
        # "proxy": faixa x so existe em 2000 e faixa y so em 2001 -> identifica a epoca, nao o risco do loan
        rows.append(("proxy", "x" if year == 2000 else "y", year, n, int(n * rate)))
        # "real": em AMBAS as vintages a faixa alta tem 4x o risco da baixa
        rows.append(("real", "baixa", year, n // 2, int(n // 2 * rate * 0.4)))
        rows.append(("real", "alta", year, n // 2, int(n // 2 * rate * 1.6)))
    t = iv_table(_feats(rows)).set_index("variavel")
    assert t.loc["proxy", "IV_agregado"] > 0.5  # o agregado parece muito forte...
    assert t.loc["proxy", "IV_intra_vintage"] == pytest.approx(
        0.0, abs=1e-9
    )  # ...mas dentro da vintage e zero
    assert t.loc["proxy", "leitura"] == "confundida com a epoca"
    assert t.loc["real", "IV_intra_vintage"] > 0.1 and t.loc["real", "leitura"] == "estavel"
    assert (
        t.loc["real", "2012-2017"] != t.loc["real", "2012-2017"]
    )  # era sem dados -> NaN (nao zero)
    assert t.loc["real", "1999-2003"] == pytest.approx(t.loc["real", "IV_intra_vintage"], rel=0.2)


def test_era_of_matches_the_dbt_macro_boundaries():
    from credit_risk.eda_stats import era_of

    assert [era_of(y) for y in (1999, 2003, 2004, 2008, 2009, 2011, 2012, 2017, 2018, 2021, 2022, 2023)] == [
        "1999-2003", "1999-2003", "2004-2008", "2004-2008", "2009-2011", "2009-2011",
        "2012-2017", "2012-2017", "2018-2021", "2018-2021", "2022-2023", "2022-2023",
    ]  # fmt: skip


def test_null_iv_bias_formula_and_correction_on_pure_noise():
    """Variavel INDEPENDENTE do alvo com muitas faixas e poucos defaults: o IV bruto e positivo por puro ruido."""
    import numpy as np

    from credit_risk.eda_stats import iv_corrected, iv_null_expectation

    rng = np.random.default_rng(42)
    k, n, p_bad = 30, 20_000, 0.01  # 30 faixas, 20k loans, ~200 defaults (como uma vintage benigna)
    raw, corr, expected = [], [], []
    for _ in range(300):
        bucket = rng.integers(0, k, n)
        bad = rng.random(n) < p_bad  # independente da faixa
        g = pd.DataFrame(
            {
                "n_loans": np.bincount(bucket, minlength=k),
                "n_defaults": np.bincount(bucket[bad], minlength=k),
            }
        )
        raw.append(iv_of(g))
        corr.append(iv_corrected(g))
        expected.append(iv_null_expectation(g))
    assert np.mean(raw) > 0.1  # sem correcao, uma variavel sem poder aparece com IV "medio"
    assert np.mean(raw) == pytest.approx(
        np.mean(expected), rel=0.25
    )  # a formula analitica descreve o ruido
    assert np.mean(corr) < 0.3 * np.mean(raw)  # depois da correcao o ruido some quase todo


def test_iv_corrected_keeps_real_signal():
    from credit_risk.eda_stats import iv_corrected

    g = pd.DataFrame({"n_loans": [50_000, 50_000, 50_000], "n_defaults": [100, 500, 1_500]})
    assert iv_corrected(g) == pytest.approx(
        iv_of(g), rel=0.01
    )  # com sinal forte e muitos defaults, quase nao muda
    assert (
        iv_corrected(pd.DataFrame({"n_loans": [10], "n_defaults": [0]})) == 0.0
    )  # sem defaults: sem informacao
