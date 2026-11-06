"""Ponta a ponta: default ANTES do 1o pagamento -> WARN do dbt test e explicacao do diagnostico."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from credit_risk.diagnostics import default_age_report
from credit_risk.duck import connect
from credit_risk.freddie_schema import ORIG_COLS, PERF_COLS
from credit_risk.ingest import ingest_all
from credit_risk.synth import make_synthetic

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "dbt"
PI = {c[0]: i for i, c in enumerate(PERF_COLS)}
OI = {c[0]: i for i, c in enumerate(ORIG_COLS)}


def _row(base: str, **vals) -> str:
    f = base.split("|")
    for k, v in vals.items():
        f[PI[k]] = v
    return "|".join(f)


@pytest.fixture(scope="module")
def early(tmp_path_factory):
    data = tmp_path_factory.mktemp("edata")
    make_synthetic(data / "raw", year=2012, n_loans=80, dirty=False)
    p = data / "raw" / "perf" / "sample_perf_2012.txt"
    lines = [x for x in p.read_text().split("\n") if x]
    first, dirty = (
        {},
        set(),
    )  # 1a linha de cada loan (idade 1 = 201203) e loans que ja tem default proprio
    for x in lines:
        c = x.split("|")
        first.setdefault(c[0], x)
        st, zb = c[PI["current_loan_delinquency_status"]], c[PI["zero_balance_code"]]
        if st == "RA" or (st.isdigit() and int(st) >= 3) or zb in ("02", "03", "09", "15"):
            dirty.add(c[0])
    clean = [
        i for i in sorted(first) if i not in dirty
    ]  # so loans "limpos": o unico default e o injetado
    assert len(clean) >= 4
    ids, bad_fp = clean[:3], clean[3]
    o = data / "raw" / "orig" / "sample_orig_2012.txt"
    ol = []
    for x in o.read_text().split("\n"):
        c = x.split("|")
        if (
            x and c[OI["loan_id"]] == bad_fp
        ):  # 1o pagamento 41 meses depois do trimestre do loan_id (modificado/convertido)
            c[OI["first_payment_date"]] = "201506"
            x = "|".join(c)
        ol.append(x)
    o.write_text("\n".join(ol))
    extra = [
        # idade 0 (201202): venda de nota (ZB 15 = evento de credito) no mes anterior ao 1o pagamento
        _row(
            first[ids[0]],
            monthly_reporting_period="201202",
            loan_age="0",
            zero_balance_code="15",
            zero_balance_effective_date="201202",
            zero_balance_removal_upb="100000.00",
        ),
        # idade 0: ja nasce 90+ dias
        _row(
            first[ids[1]],
            monthly_reporting_period="201202",
            loan_age="0",
            current_loan_delinquency_status="03",
        ),
        # idade -1 (201201): short sale (ZB 03)
        _row(
            first[ids[2]],
            monthly_reporting_period="201201",
            loan_age="-1",
            zero_balance_code="03",
            zero_balance_effective_date="201201",
            zero_balance_removal_upb="80000.00",
        ),
    ]
    p.write_text("\n".join(lines + extra) + "\n")
    ingest_all(raw_dir=data / "raw", bronze_dir=data / "bronze", db_path=data / "warehouse.duckdb")
    exe = Path(sys.executable).parent / ("dbt.exe" if os.name == "nt" else "dbt")
    env = {**os.environ, "CREDIT_RISK_DATA_DIR": str(data)}

    def dbt(cmd, sel):
        return subprocess.run(
            [
                str(exe),
                cmd,
                "--select",
                *sel,
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

    assert dbt("run", ["silver", "dq", "gold"]).returncode == 0
    t = dbt("test", ["gold"])
    results = json.loads((data / "target" / "run_results.json").read_text(encoding="utf-8"))[
        "results"
    ]
    return data, t, results, ids, bad_fp


def test_dbt_emits_warn_not_error(early):
    _, proc, results, _, _ = early
    assert proc.returncode == 0  # WARN nao derruba o build
    by = {r["unique_id"].split(".")[2]: r for r in results}
    assert by["assert_default_age_positive"]["status"] == "warn"
    assert by["assert_default_age_positive"]["failures"] == 3
    assert not [r for r in results if r["status"] in ("fail", "error")]


def test_double_termination_rule_flags_the_two_loans(early):
    data, _, _, _, _ = early
    con = connect(data / "warehouse.duckdb", read_only=True)
    r = dict(con.execute("select rule_id, n_failed from dq.dq_rule_results").fetchall())
    con.close()
    assert r["R27"] == 2  # as 2 injecoes com ZB antecipado terminam depois com outro ZB


def test_gold_ages_for_early_events(early):
    data, _, _, ids, _ = early
    con = connect(data / "warehouse.duckdb", read_only=True)
    got = {
        r[0]: r[1:]
        for r in con.execute(
            "select loan_id, default_age, default_trigger, credit_event_code from gold.gold_loan_events "
            f"where loan_id in ({','.join(repr(i) for i in ids)})"
        ).fetchall()
    }
    con.close()
    assert got[ids[0]] == (0, "credit_event", "15")
    assert got[ids[1]][:2] == (0, "dpd90")
    assert got[ids[2]] == (-1, "credit_event", "03")


def test_diagnostic_explains_the_warn(early):
    data, _, _, ids, _ = early
    con = connect(data / "warehouse.duckdb", read_only=True)
    text = default_age_report(con)
    con.close()
    assert "idade < 1" in text
    for i in ids:
        assert i in text.split("=== G.")[1]
    sec_c = text.split("=== C.")[1].split("=== D.")[0]
    assert "15" in sec_c and "03" in sec_c
    # a idade da 1a linha tambem revela a causa: 3 loans comecam em 0 ou -1 (o normal e 0)
    sec_f = text.split("=== F.")[1].split("=== G.")[0]
    assert "-1" in sec_f


def test_first_payment_inconsistency_is_flagged_and_excluded(early):
    data, _, _, ids, bad_fp = early
    con = connect(data / "warehouse.duckdb", read_only=True)
    ev = con.execute(
        "select first_payment_inconsistent, months_to_first_payment from gold.gold_loan_events where loan_id = ?",
        [bad_fp],
    ).fetchone()
    reasons = dict(
        con.execute("select loan_id, excluded_reason from gold.gold_pd_dataset").fetchall()
    )
    n_flag = con.execute(
        "select count(*) from gold.gold_loan_events where first_payment_inconsistent"
    ).fetchone()[0]
    r28 = con.execute("select n_failed from dq.dq_rule_results where rule_id = 'R28'").fetchone()[0]
    usable = dict(con.execute("select loan_id, usable_24m from gold.gold_pd_dataset").fetchall())
    con.close()
    assert ev == (True, 41)
    assert [usable[i] for i in [*ids, bad_fp]] == [False] * 4  # excluidos nao entram no treino
    assert sum(usable.values()) == len(usable) - 4
    assert reasons[bad_fp] == "first_payment_inconsistent"
    assert [reasons[i] for i in ids] == ["default_before_first_payment"] * 3
    assert (
        sum(v is None for v in reasons.values()) == len(reasons) - 4
    )  # so esses 4 loans sao excluidos
    assert n_flag == 1 and r28 == 1
