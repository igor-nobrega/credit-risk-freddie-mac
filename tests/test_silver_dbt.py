"""Integracao: bronze sintetica com sujeira injetada -> dbt (silver + dq) -> regras detectam."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from credit_risk.duck import connect
from credit_risk.freddie_schema import ORIG_COLS, PERF_COLS
from credit_risk.ingest import ingest_all
from credit_risk.silver_gen import render_all
from credit_risk.synth import make_synthetic

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "dbt"
OI = {c[0]: i for i, c in enumerate(ORIG_COLS)}
PI = {c[0]: i for i, c in enumerate(PERF_COLS)}


def _set(line: str, idx: dict, **vals) -> str:
    f = line.split("|")
    for k, v in vals.items():
        f[idx[k]] = v
    return "|".join(f)


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    data = tmp_path_factory.mktemp("data")
    make_synthetic(data / "raw", year=2010, n_loans=60)
    o = data / "raw" / "orig" / "sample_orig_2010.txt"
    p = data / "raw" / "perf" / "sample_perf_2010.txt"
    ol = o.read_text().split("\n")
    ol[0] = _set(ol[0], OI, credit_score="ABC")  # falha de conversao
    ol[2] = _set(ol[2], OI, dti="80")  # R03
    ol[3] = _set(ol[3], OI, cltv="20", ltv="90")  # R05
    ol[4] = _set(ol[4], OI, property_state="Texas")  # R10
    ol[5] = _set(ol[5], OI, maturity_date="200001")  # R06 e R07
    o.write_text("\n".join(ol))
    pl = p.read_text().split("\n")
    zb = next(x for x in pl if x and x.split("|")[PI["zero_balance_code"]])
    extra = [
        pl[0],  # R15: duplicata exata
        _set(pl[0], PI, loan_id="F10Q10999999"),  # R13: orfao
        _set(zb, PI, monthly_reporting_period="203001"),  # R18: linha apos o evento
    ]
    p.write_text("\n".join([x for x in pl if x] + extra) + "\n")

    ingest_all(raw_dir=data / "raw", bronze_dir=data / "bronze", db_path=data / "warehouse.duckdb")
    exe = Path(sys.executable).parent / ("dbt.exe" if os.name == "nt" else "dbt")
    env = {**os.environ, "CREDIT_RISK_DATA_DIR": str(data)}

    def dbt(cmd):
        return subprocess.run(
            [
                str(exe),
                cmd,
                "--select",
                "silver",
                "dq",
                "--project-dir",
                str(DBT_DIR),
                "--profiles-dir",
                str(DBT_DIR),
                "--target-path",
                str(data / "target"),
                "--log-path",
                str(data / "logs"),
            ],
            capture_output=True,
            text=True,
            env=env,
            cwd=ROOT,
        )

    # run e test separados: um teste de unicidade reprovado NAO pode impedir a medicao de qualidade (dq_*)
    run = dbt("run")
    assert run.returncode == 0, run.stdout[-1500:]
    proc = dbt("test")
    results = json.loads((data / "target" / "run_results.json").read_text(encoding="utf-8"))[
        "results"
    ]
    return data, proc, results


def _rules(data):
    con = connect(data / "warehouse.duckdb", read_only=True)
    rows = con.execute("select rule_id, n_failed from dq.dq_rule_results").fetchall()
    con.close()
    return dict(rows)


def test_dbt_build_runs_and_only_expected_tests_fail(warehouse):
    _, proc, results = warehouse
    failed = [r["unique_id"].split(".")[-2] for r in results if r["status"] in ("fail", "error")]
    # a duplicata injetada em silver_perf DEVE reprovar o teste de unicidade (e so ele)
    assert failed == ["unique_combination_silver_perf_loan_id__monthly_reporting_period"], (
        failed,
        proc.stdout[-800:],
    )


def test_rules_detect_injected_dirt(warehouse):
    r = _rules(warehouse[0])
    assert r["R03"] == 1 and r["R05"] == 1 and r["R10"] == 1
    assert r["R06"] == 1 and r["R07"] >= 1
    assert r["R13"] == 1 and r["R15"] == 1 and r["R18"] >= 1
    assert r["R17"] == 0  # o gerador zera o saldo no encerramento


def test_cast_failure_and_sentinel_flags(warehouse):
    data = warehouse[0]
    con = connect(data / "warehouse.duckdb", read_only=True)
    n_cast = con.execute(
        "select n_cast_fail from dq.dq_column_profile where table_name='orig' and column_name='credit_score'"
    ).fetchone()[0]
    assert n_cast == 1
    # sentinela e ausente sao coisas diferentes de falha de conversao
    miss, nulls = con.execute(
        "select sum(case when credit_score_was_missing then 1 else 0 end), "
        "sum(case when credit_score is null then 1 else 0 end) from silver.silver_orig"
    ).fetchone()
    assert nulls == miss + 1  # +1: o 'ABC' vira NULL mas nao e sentinela
    con.close()


def test_silver_orig_is_deduplicated_and_typed(warehouse):
    data = warehouse[0]
    con = connect(data / "warehouse.duckdb", read_only=True)
    n, nd = con.execute(
        "select count(*), count(distinct loan_id) from silver.silver_orig"
    ).fetchone()
    assert n == nd == 60
    assert (
        con.execute("select typeof(first_payment_date) from silver.silver_orig limit 1").fetchone()[
            0
        ]
        == "DATE"
    )
    con.close()


def test_generated_sql_matches_committed_models():
    for rel, text in render_all().items():
        assert (ROOT / rel).read_text(encoding="utf-8") == text, (
            f"{rel} desatualizado: rode `uv run poe gen-sql`"
        )
