"""O relatorio de default recusa rodar sobre uma gold desatualizada (em vez de deixar o arquivo antigo)."""

import os
import subprocess
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def _old_gold(data: Path):
    con = duckdb.connect(str(data / "warehouse.duckdb"))
    con.execute("create schema gold; create schema dq")
    # versao ANTIGA da gold: sem as colunas e definicoes da v3
    con.execute(
        "create table gold.gold_default_summary as select 2010 as vintage_year, 100 as n_with_perf"
    )
    con.execute(
        "create table gold.gold_vintage_curves as select 'dpd90' as definition, 2010 as vintage_year, "
        "12 as age_months, 100 as n_at_risk, 1 as n_default_cum, 0.01 as default_rate_cum"
    )
    con.execute(
        "create table dq.dq_rule_results as select 'R21' as rule_id, 1 as n_checked, 0 as n_failed, 0.0 as pct_failed"
    )
    con.close()


def test_stale_gold_stops_with_clear_message_and_writes_nothing(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    _old_gold(data)
    work = tmp_path / "work"
    work.mkdir()
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "report_default.py")],
        capture_output=True,
        text=True,
        cwd=work,
        env={**os.environ, "CREDIT_RISK_DATA_DIR": str(data)},
    )
    assert r.returncode == 1
    assert "DESATUALIZADA" in r.stdout and "uv run poe gold" in r.stdout
    assert "n_default_na_24m" in r.stdout and "dpd90_noassist" in r.stdout
    assert not (work / "docs").exists()  # nenhum relatorio parcial/antigo foi escrito
    assert not list((work / "reports" / "tables").glob("*.csv"))
