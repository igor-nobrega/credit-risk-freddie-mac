"""O doctor prova a integridade do projeto e aponta a correcao quando algo esta velho ou ausente."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest

from credit_risk.doctor import render, run_checks
from credit_risk.ingest import ingest_all
from credit_risk.synth import make_synthetic

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "dbt"


def _exe(name: str) -> str:
    return str(Path(sys.executable).parent / (name + (".exe" if os.name == "nt" else "")))


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    """Projeto sintetico completo: dados -> bronze -> silver -> dq -> gold -> eda -> 3 relatorios."""
    data = tmp_path_factory.mktemp("docdata")
    work = tmp_path_factory.mktemp("docroot")
    shutil.copy(ROOT / "pyproject.toml", work / "pyproject.toml")
    for y in (2013, 2015, 2022, 2023):
        make_synthetic(data / "raw", year=y, n_loans=250, dirty=False)
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
    assert r.returncode == 0, r.stdout[-1500:]
    for s in ("report_dq.py", "report_default.py", "report_eda.py"):
        p = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / s)],
            capture_output=True,
            text=True,
            env=env,
            cwd=work,
        )
        assert p.returncode == 0, p.stdout + p.stderr
    (work / "docs" / "default_decision.md").write_text("D-002\n", encoding="utf-8")
    (work / "docs" / "eda_insights.md").write_text("insights\n", encoding="utf-8")
    return data, work


def _by_name(checks):
    return {c.name: c for c in checks}


def test_all_green_on_a_complete_project(project):
    data, work = project
    checks, stage = run_checks(work, data)
    fails = [c for c in checks if c.status == "FAIL"]
    assert not fails, [(c.name, c.detail) for c in fails]
    assert stage == "eda"
    by = _by_name(checks)
    assert by["reconciliacao de linhas"].status == "OK" and by["regras de DQ"].detail == "28 de 28"
    text, code = render(checks, stage)
    assert (
        code == 0 and "ultima camada valida do warehouse: eda" in text and "nada pendente" in text
    )


def test_stale_gold_is_detected_with_the_fix(project, tmp_path):
    data, work = project
    d = tmp_path / "data"
    shutil.copytree(data, d)
    con = duckdb.connect(str(d / "warehouse.duckdb"))
    con.execute("alter table gold.gold_loan_events drop column first_row_age")
    con.close()
    checks, stage = run_checks(work, d)
    by = _by_name(checks)
    assert (
        by["colunas gold_loan_events"].status == "FAIL"
        and "uv run poe gold" in by["colunas gold_loan_events"].hint
    )
    assert stage == "dq"  # silver e dq continuam validos; a gold nao
    text, code = render(checks, stage)
    assert code == 1 and "PROXIMO PASSO: a camada esta DESATUALIZADA" in text


def test_outdated_report_and_missing_tasks_are_flagged(project, tmp_path):
    data, work = project
    root = tmp_path / "root"
    shutil.copytree(work, root)
    (root / "docs" / "default_definition_report.md").write_text("# velho\n", encoding="utf-8")
    text = (
        (root / "pyproject.toml")
        .read_text(encoding="utf-8")
        .replace('doctor = "python scripts/doctor.py"\n', "")
    )
    (root / "pyproject.toml").write_text(text, encoding="utf-8")
    by = _by_name(run_checks(root, data)[0])
    assert by["docs/default_definition_report.md"].status == "FAIL"
    assert by["tarefas poe"].status == "FAIL" and "setup_tasks" in by["tarefas poe"].hint


def test_empty_project_explains_what_to_do(tmp_path):
    root, data = tmp_path / "r", tmp_path / "d"
    root.mkdir()
    data.mkdir()
    checks, stage = run_checks(root, data)
    by = _by_name(checks)
    assert stage == "nenhuma"
    assert by["dados brutos"].status == "FAIL" and "Sample" in by["dados brutos"].hint
    assert by["warehouse"].status == "FAIL" and "ingest" in by["warehouse"].hint
    assert render(checks, stage)[1] == 1


def test_custom_format_task_block_is_explained_not_looped(project, tmp_path):
    data, work = project
    root = tmp_path / "root"
    shutil.copytree(work, root)
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    i = text.index("[tool.poe.tasks.gold]")
    custom = '[tool.poe.tasks.gold]\nsequence = [ { cmd = "dbt run --select gold" }, { cmd = "dbt test --select gold" } ]\n'
    (root / "pyproject.toml").write_text(text[:i] + custom, encoding="utf-8")
    c = _by_name(run_checks(root, data)[0])["tarefas poe"]
    assert c.status == "FAIL" and "ATENCAO" in c.detail and "setup_tasks" not in c.hint


def test_next_step_follows_pipeline_order_gold_before_eda(project, tmp_path):
    data, work = project
    d = tmp_path / "data"
    shutil.copytree(data, d)
    con = duckdb.connect(str(d / "warehouse.duckdb"))
    con.execute(
        "alter table gold.gold_default_summary drop column n_late_entry"
    )  # gold desatualizada
    con.execute("drop table eda.eda_mix_decomposition")  # e uma tabela da EDA ausente
    con.close()
    checks, stage = run_checks(work, d)
    by = _by_name(checks)
    assert (
        by["tabelas eda"].status == "FAIL" and by["colunas gold_default_summary"].status == "FAIL"
    )
    text, _ = render(checks, stage)
    assert (
        "PROXIMO PASSO: a camada esta DESATUALIZADA: rode `uv run poe gold`" in text
    )  # gold ANTES de eda
