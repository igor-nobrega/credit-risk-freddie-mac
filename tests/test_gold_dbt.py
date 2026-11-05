"""Gold: compara o SQL (dbt) com um ORACULO independente em Python sobre dados sinteticos.

O sintetico cobre os ramos que importam: loans ativos no corte, vintage recente (janela incompleta),
modificados, default so por evento de credito, outras remocoes, curas, status desconhecido e loans
sem performance. Os asserts de cobertura garantem que o teste nao passa "no vazio".
"""

import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

from credit_risk.duck import connect
from credit_risk.freddie_schema import ORIG_COLS, PERF_COLS
from credit_risk.ingest import ingest_all
from credit_risk.synth import make_synthetic

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "dbt"
OI = {c[0]: i for i, c in enumerate(ORIG_COLS)}
PI = {c[0]: i for i, c in enumerate(PERF_COLS)}
CREDIT_EVENT = {"02", "03", "09", "15"}
CUTOFF = "202206"
N_PER_VINTAGE, ORIG_ONLY = 250, 10


def _ym(s: str) -> int:
    return int(s[:4]) * 12 + int(s[4:6])


def _f(s: str):
    return float(s) if s else None


def oracle(raw: Path):
    first_pay, m2fp = {}, {}
    for f in (raw / "orig").glob("*.txt"):
        for line in f.read_text().split("\n"):
            if line:
                c = line.split("|")
                lid = c[OI["loan_id"]]
                first_pay[lid] = _ym(c[OI["first_payment_date"]])
                yy, q = int(lid[1:3]), int(lid[4])
                m2fp[lid] = first_pay[lid] - (
                    (1999 if yy == 99 else 2000 + yy) * 12 + (q - 1) * 3 + 1
                )
    rows = defaultdict(list)
    cutoff = 0
    for f in (raw / "perf").glob("*.txt"):
        for line in f.read_text().split("\n"):
            if line:
                c = line.split("|")
                per = _ym(c[PI["monthly_reporting_period"]])
                cutoff = max(cutoff, per)
                rows[c[PI["loan_id"]]].append(
                    dict(
                        per=per,
                        st=c[PI["current_loan_delinquency_status"]],
                        zb=c[PI["zero_balance_code"]],
                        upb=_f(c[PI["current_actual_upb"]]),
                        zb_upb=_f(c[PI["zero_balance_removal_upb"]]),
                        mod=c[PI["modification_flag"]],
                        assisted=bool(
                            c[PI["borrower_assistance_plan"]] in ("F", "R", "T")
                            or c[PI["delinquency_due_to_disaster"]] == "Y"
                            or c[PI["payment_deferral_flag"]] in ("C", "P")
                        ),
                    )
                )
    out = {}
    for lid, rs in rows.items():
        rs.sort(key=lambda r: r["per"])
        fp = first_pay[lid]
        is90 = lambda r: r["st"] == "RA" or (r["st"].isdigit() and int(r["st"]) >= 3)  # noqa: E731
        d90r = next((r for r in rs if is90(r)), None)
        d90n = next((r for r in rs if is90(r) and not r["assisted"]), None)
        cer = next((r for r in rs if r["zb"] in CREDIT_EVENT), None)
        d90, ce = (d90r["per"] if d90r else None), (cer["per"] if cer else None)
        d90na = d90n["per"] if d90n else None
        cands = [x for x in (d90, ce) if x is not None]
        cands_na = [x for x in (d90na, ce) if x is not None]
        dper = min(cands) if cands else None
        dper_na = min(cands_na) if cands_na else None
        zb = [r for r in rs if r["zb"]]
        if d90r and (cer is None or d90 <= ce):
            upb_def = d90r["upb"]
        else:
            upb_def = cer["zb_upb"] if cer else None
        out[lid] = dict(
            default_age=(dper - fp + 1) if dper else None,
            default_na_age=(dper_na - fp + 1) if dper_na else None,
            dpd90_na_age=(d90na - fp + 1) if d90na else None,
            assisted_dpd90=any(is90(r) and r["assisted"] for r in rs),
            trigger=None
            if not cands
            else ("both" if d90 and ce else "dpd90" if d90 else "credit_event"),
            cured=bool(d90 and any(r["st"] == "00" and r["per"] > d90 for r in rs)),
            zb_age=(zb[-1]["per"] - fp + 1) if zb else None,
            months_obs=cutoff - fp + 1,
            terminal=(
                "active"
                if not zb
                else "credit_event"
                if zb[-1]["zb"] in CREDIT_EVENT
                else "prepaid_or_matured"
                if zb[-1]["zb"] == "01"
                else "other_removal"
            ),
            modified=any(r["mod"] for r in rs),
            upb_default=upb_def,
            ce_code=cer["zb"] if cer else None,
            m2fp=m2fp[lid],
        )
    return out


@pytest.fixture(scope="module")
def gold(tmp_path_factory):
    data = tmp_path_factory.mktemp("gdata")
    # 2008: historico completo | 2019: series truncadas no corte (ativos) | 2021: janela de 24m incompleta
    for y in (2008, 2019, 2021):
        make_synthetic(
            data / "raw",
            year=y,
            n_loans=N_PER_VINTAGE,
            dirty=False,
            cutoff=CUTOFF,
            orig_only=ORIG_ONLY if y == 2019 else 0,
        )
    ingest_all(raw_dir=data / "raw", bronze_dir=data / "bronze", db_path=data / "warehouse.duckdb")
    exe = Path(sys.executable).parent / ("dbt.exe" if os.name == "nt" else "dbt")
    env = {**os.environ, "CREDIT_RISK_DATA_DIR": str(data)}
    for cmd in ("run", "test"):
        r = subprocess.run(
            [
                str(exe),
                cmd,
                "--select",
                "silver",
                "dq",
                "gold",
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
        assert r.returncode == 0, r.stdout[-2000:]
    return data, oracle(data / "raw")


def test_events_match_oracle_for_every_loan(gold):
    data, orc = gold
    con = connect(data / "warehouse.duckdb", read_only=True)
    rows = con.execute(
        "select loan_id, default_age, default_trigger, cured_after_dpd90, zb_age, months_observable, "
        "terminal_state, ever_modified, upb_at_default, credit_event_code, default_na_age, dpd90_na_age, "
        "assisted_while_dpd90, months_to_first_payment, first_payment_inconsistent "
        "from gold.gold_loan_events where has_perf"
    ).fetchall()
    n_no_perf = con.execute(
        "select count(*) from gold.gold_loan_events where not has_perf"
    ).fetchone()[0]
    con.close()
    assert len(rows) == len(orc) == 3 * N_PER_VINTAGE
    assert n_no_perf == ORIG_ONLY
    for (
        lid,
        dage,
        trig,
        cured,
        zage,
        mobs,
        term,
        mod,
        upb,
        cecode,
        dna,
        d90na,
        asst,
        m2fp,
        fpi,
    ) in rows:
        o = orc[lid]
        assert (dage, trig, cured, zage, mobs, term, mod) == (
            o["default_age"],
            o["trigger"],
            o["cured"],
            o["zb_age"],
            o["months_obs"],
            o["terminal"],
            o["modified"],
        ), lid
        assert cecode == o["ce_code"], lid
        assert (dna, d90na, asst, m2fp, fpi) == (
            o["default_na_age"],
            o["dpd90_na_age"],
            o["assisted_dpd90"],
            o["m2fp"],
            not 0 <= o["m2fp"] <= 8,
        ), lid
        if o["upb_default"] is None:
            assert upb is None, lid
        else:
            assert upb == pytest.approx(o["upb_default"], abs=0.011), lid


def test_synthetic_covers_every_branch(gold):
    """Sem isto o teste acima poderia passar 'no vazio'."""
    orc = gold[1].values()
    assert {o["terminal"] for o in orc} == {
        "active",
        "prepaid_or_matured",
        "credit_event",
        "other_removal",
    }
    assert {o["trigger"] for o in orc} == {None, "dpd90", "credit_event", "both"}
    assert any(o["cured"] for o in orc) and any(o["modified"] for o in orc)
    assert any(o["months_obs"] < 24 for o in orc) and any(o["months_obs"] >= 24 for o in orc)
    assert any(o["assisted_dpd90"] for o in orc), "falta 90+ sob assistencia"
    # ha loans cujo default A some na definicao B (todo o 90+ sob assistencia) e loans em que o default B vem depois
    assert any(o["default_age"] is not None and o["default_na_age"] is None for o in orc)
    assert any(
        o["default_na_age"] is not None and o["default_na_age"] > o["default_age"] for o in orc
    )


def test_pd_dataset_targets_and_observability(gold):
    data, orc = gold
    con = connect(data / "warehouse.duckdb", read_only=True)
    rows = con.execute(
        "select loan_id, default_24m, observable_24m, default_12m, observable_12m from gold.gold_pd_dataset"
    ).fetchall()
    cols = [c[0] for c in con.execute("describe gold.gold_pd_dataset").fetchall()]
    con.close()
    assert len(rows) == 3 * N_PER_VINTAGE  # loans sem performance ficam de fora
    assert "vantage_score_4" not in cols and "credit_score" in cols
    assert not {"default_period", "upb_at_default"} & set(cols[: cols.index("default_period")])
    for lid, d24, o24, d12, o12 in rows:
        o = orc[lid]
        da, mo = o["default_age"], o["months_obs"]
        assert d24 == (da is not None and da <= 24) and d12 == (da is not None and da <= 12)
        assert o24 == (mo >= 24) and o12 == (mo >= 12)
    # janela incompleta nao pode entrar no treino: a vintage 2021 nao tem NENHUM loan observavel a 24m
    con = connect(data / "warehouse.duckdb", read_only=True)
    n21 = con.execute(
        "select count(*) from gold.gold_pd_dataset where vintage_year = 2021 and observable_24m"
    ).fetchone()[0]
    con.close()
    assert n21 == 0


def test_vintage_curves_and_summary_match_oracle(gold):
    data, orc = gold
    con = connect(data / "warehouse.duckdb", read_only=True)
    vint = dict(con.execute("select loan_id, vintage_year from silver.silver_orig").fetchall())
    for y in (2008, 2019, 2021):
        for k in (6, 12, 24, 36):
            risk = [o for lid, o in orc.items() if vint[lid] == y and o["months_obs"] >= k]
            n_def = [o for o in risk if o["default_age"] is not None and o["default_age"] <= k]
            got = con.execute(
                "select n_at_risk, n_default_cum from gold.gold_vintage_curves "
                "where definition='dpd90_or_credit_event' and vintage_year=? and age_months=?",
                [y, k],
            ).fetchone()
            assert got == ((len(risk), len(n_def)) if risk else None), (y, k, got)
        s = con.execute(
            "select n_with_perf, n_active, n_ever_default, n_cured_after_dpd90, n_ever_modified, n_obs_24m "
            "from gold.gold_default_summary where vintage_year=?",
            [y],
        ).fetchone()
        mine = [o for lid, o in orc.items() if vint[lid] == y]
        assert s == (
            len(mine),
            sum(o["terminal"] == "active" for o in mine),
            sum(o["trigger"] is not None for o in mine),
            sum(o["cured"] for o in mine),
            sum(o["modified"] for o in mine),
            sum(o["months_obs"] >= 24 for o in mine),
        ), y
    con.close()


def test_new_dq_rules_run(gold):
    data, _ = gold
    con = connect(data / "warehouse.duckdb", read_only=True)
    r = dict(con.execute("select rule_id, n_failed from dq.dq_rule_results").fetchall())
    con.close()
    assert r["R26"] == 0
    assert r["R14"] == ORIG_ONLY  # loans na originacao sem performance
    assert r["R25"] == 0  # as series truncadas terminam exatamente no corte
    assert r["R27"] == 0  # um unico evento de saldo zero por loan
