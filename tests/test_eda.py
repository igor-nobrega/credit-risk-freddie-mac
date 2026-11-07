"""EDA: modelos agregados vs recalculo independente em pandas; relatorio de ponta a ponta; guarda de atualidade."""

import os
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from credit_risk.duck import connect
from credit_risk.ingest import ingest_all
from credit_risk.synth import make_synthetic

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "dbt"


def _exe(name: str) -> str:
    return str(Path(sys.executable).parent / (name + (".exe" if os.name == "nt" else "")))


def fico(v):
    if pd.isna(v):
        return "z missing"
    return (
        "a <620"
        if v < 620
        else "b 620-659"
        if v < 660
        else "c 660-699"
        if v < 700
        else "d 700-739"
        if v < 740
        else "e 740-779"
        if v < 780
        else "f >=780"
    )


def ltv(v):
    if pd.isna(v):
        return "z missing"
    return (
        "a <=60"
        if v <= 60
        else "b 61-70"
        if v <= 70
        else "c 71-80"
        if v <= 80
        else "d 81-90"
        if v <= 90
        else "e 91-95"
        if v <= 95
        else "f >95"
    )


@pytest.fixture(scope="module")
def eda(tmp_path_factory):
    data = tmp_path_factory.mktemp("edadata")
    for y in (
        2013,
        2015,
        2022,
        2023,
    ):  # eras 2012-2017 (base) e 2022-2023 (teste) para a decomposicao
        make_synthetic(data / "raw", year=y, n_loans=300, dirty=False)
    ingest_all(raw_dir=data / "raw", bronze_dir=data / "bronze", db_path=data / "warehouse.duckdb")
    env = {**os.environ, "CREDIT_RISK_DATA_DIR": str(data)}
    common = [
        "--project-dir",
        str(DBT_DIR),
        "--profiles-dir",
        str(DBT_DIR),
        "--target-path",
        str(data / "target"),
        "--log-path",
        str(data / "logs"),
    ]
    r = subprocess.run(
        [_exe("dbt"), "run", "--select", "silver", "dq", "gold", "eda", *common],
        capture_output=True,
        text=True,
        env=env,
        cwd=ROOT,
    )
    assert r.returncode == 0, r.stdout[-2000:]
    t = subprocess.run(
        [_exe("dbt"), "test", "--select", "eda", *common],
        capture_output=True,
        text=True,
        env=env,
        cwd=ROOT,
    )
    assert t.returncode == 0, t.stdout[
        -2000:
    ]  # inclui o invariante: toda variavel particiona a mesma populacao
    work = tmp_path_factory.mktemp("work")
    rep = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "report_eda.py")],
        capture_output=True,
        text=True,
        env=env,
        cwd=work,
    )
    return data, work, rep


def _pd(data):
    con = connect(data / "warehouse.duckdb", read_only=True)
    df = con.execute(
        "select vintage_year, credit_score, ltv, occupancy_status, property_valuation_method, target_24m, usable_24m, "
        "observable_24m, first_row_age, default_na_age from gold.gold_pd_dataset"
    ).fetchdf()
    feats = con.execute("select * from eda.eda_features").fetchdf()
    excl = con.execute("select * from eda.eda_exclusion_check").fetchdf()
    con.close()
    return df, feats, excl


def test_feature_tables_match_independent_pandas_recount(eda):
    df, feats, _ = _pd(eda[0])
    u = df[df["usable_24m"]].copy()
    assert len(u) > 1000
    u["fico_band"] = u["credit_score"].map(fico)
    u["ltv_band"] = u["ltv"].map(ltv)
    u["occupancy_status"] = u["occupancy_status"].fillna("missing")
    u["property_valuation_method"] = u["property_valuation_method"].map(
        lambda v: "missing" if pd.isna(v) else str(int(v))
    )
    for feature in ("fico_band", "ltv_band", "occupancy_status", "property_valuation_method"):
        want = (
            u.groupby([feature, "vintage_year"])
            .agg(n_loans=("target_24m", "size"), n_defaults=("target_24m", "sum"))
            .reset_index()
            .rename(columns={feature: "bucket"})
        )
        got = feats[feats["feature"] == feature][
            ["bucket", "vintage_year", "n_loans", "n_defaults"]
        ]
        m = want.merge(got, on=["bucket", "vintage_year"], suffixes=("_py", "_sql"), how="outer")
        assert m.notna().all().all(), (feature, m[m.isna().any(axis=1)])
        assert (m["n_loans_py"] == m["n_loans_sql"]).all(), feature
        assert (m["n_defaults_py"] == m["n_defaults_sql"]).all(), feature
    assert feats["n_defaults"].sum() > 0 and (feats["n_defaults"] <= feats["n_loans"]).all()


def test_exclusion_check_matches_pandas(eda):
    df, _, excl = _pd(eda[0])
    obs = df[df["observable_24m"]].copy()
    obs["b"] = pd.cut(
        obs["first_row_age"],
        [-(10**6), 0, 1, 3, 12, 10**6],
        labels=["a <=0", "b 1", "c 2-3", "d 4-12", "e >12"],
    )
    want = obs.groupby("b", observed=True).agg(
        n=("target_24m", "size"), d=("target_24m", "sum"), ever=("default_na_age", "count")
    )
    got = excl[excl["check_name"] == "first_row_age"].set_index("bucket")
    assert (want["n"] == got.loc[want.index, "n_loans"]).all()
    assert (want["d"] == got.loc[want.index, "n_defaults_24m"]).all()
    assert (want["ever"] == got.loc[want.index, "n_ever_default"]).all()


def test_report_runs_end_to_end_with_decomposition(eda):
    _, work, rep = eda
    assert rep.returncode == 0, rep.stdout + rep.stderr
    doc = (work / "docs" / "eda_report.md").read_text(encoding="utf-8")
    assert "Efeito do PERFIL" in doc
    assert doc.endswith("\n") and not doc.endswith("\n\n")
    for f in (
        "eda_default_by_feature.png",
        "eda_fico_ltv_heatmap.png",
        "eda_vintage_mix_vs_risk.png",
    ):
        assert (work / "reports" / "figures" / f).stat().st_size > 10_000
    iv = pd.read_csv(work / "reports" / "tables" / "eda_iv.csv")
    assert len(iv) == 19 and (iv["IV"] >= 0).all()


def test_report_refuses_without_eda_tables(tmp_path):
    data = tmp_path / "d"
    data.mkdir()
    con = duckdb.connect(str(data / "warehouse.duckdb"))
    con.execute("create schema gold")
    con.close()
    work = tmp_path / "w"
    work.mkdir()
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "report_eda.py")],
        capture_output=True,
        text=True,
        cwd=work,
        env={**os.environ, "CREDIT_RISK_DATA_DIR": str(data)},
    )
    assert r.returncode == 1 and "uv run poe eda" in r.stdout
    assert not (work / "docs").exists()


@pytest.mark.parametrize(
    ("script", "doc"),
    [
        ("report_dq.py", "data_quality_report.md"),
        ("report_default.py", "default_definition_report.md"),
    ],
)
def test_all_reports_work_in_a_clean_checkout_without_docs_dir(eda, tmp_path, script, doc):
    """Regressao: os relatorios criam docs/ se ela nao existir (ex.: clone novo)."""
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={**os.environ, "CREDIT_RISK_DATA_DIR": str(eda[0])},
    )
    assert r.returncode == 0, r.stdout + r.stderr
    text = (tmp_path / "docs" / doc).read_text(encoding="utf-8")
    assert text.endswith("\n") and not text.endswith("\n\n")
