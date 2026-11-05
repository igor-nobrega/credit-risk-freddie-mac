"""Garante, de forma IDEMPOTENTE, que o pyproject.toml tenha todas as tarefas `poe` do projeto.

Evita edicao manual (fonte de erro: no `sequence` do poe, strings sao referencias a tarefas e nao
comandos; aqui os passos sao tabelas `{ cmd = ... }`). Preserva o estilo de quebra de linha do arquivo.
"""

from __future__ import annotations

import json
import re
import tomllib

DBT = "--project-dir dbt --profiles-dir dbt"

SIMPLE: dict[str, str] = {
    "check": "python scripts/check_env.py",
    "smoke": "python scripts/smoke_test.py",
    "manifest": "python scripts/make_manifest.py",
    "ingest": "python scripts/ingest_bronze.py",
    "gen-sql": "python scripts/gen_silver_sql.py",
    "dq-report": "python scripts/report_dq.py",
    "default-report": "python scripts/report_default.py",
    "inspect-dq": "python scripts/inspect_dq.py",
    "diagnose-age": "python scripts/diagnose_default_age.py",
    "lint": "ruff check .",
    "fmt": "ruff format .",
    "test": "pytest -q",
    "dbt-debug": f"dbt debug {DBT}",
    "dbt-smoke": f"dbt build --select smoke {DBT}",
    "lab": "jupyter lab",
}

SEQUENCES: dict[str, tuple[str, list[str]]] = {
    "silver": (
        "Silver + DQ: roda os modelos e depois os testes",
        [f"dbt run --select silver dq {DBT}", f"dbt test --select silver dq {DBT}"],
    ),
    "gold": (
        "Gold (eventos de default, curvas, dataset de PD): modelos e depois testes",
        [f"dbt run --select gold {DBT}", f"dbt test --select gold {DBT}"],
    ),
}


def _seq_block(name: str, help_: str, cmds: list[str]) -> str:
    steps = "".join(f"  {{ cmd = {json.dumps(c)} }},\n" for c in cmds)
    return f"[tool.poe.tasks.{name}]\nhelp = {json.dumps(help_)}\nsequence = [\n{steps}]\n"


def _simple_line(name: str, cmd: str) -> str:
    return f"{name} = {json.dumps(cmd)}"


def ensure_tasks(text: str) -> tuple[str, list[str]]:
    """Retorna (novo_texto, lista_de_mudancas). Sem mudancas => texto identico."""
    nl = "\r\n" if "\r\n" in text else "\n"
    work = text.replace("\r\n", "\n")
    data = tomllib.loads(work)  # invalido => levanta erro antes de tocar em qualquer coisa
    tasks = data.get("tool", {}).get("poe", {}).get("tasks", {})
    changes: list[str] = []

    # 1) tarefas simples ausentes (e dbt-smoke desatualizado)
    missing = [(n, c) for n, c in SIMPLE.items() if n not in tasks]
    header = re.search(r"^\[tool\.poe\.tasks\][ \t]*$", work, flags=re.M)
    if missing:
        lines = "\n".join(_simple_line(n, c) for n, c in missing)
        if header:
            work = work[: header.end()] + "\n" + lines + work[header.end() :]
        else:
            work = work.rstrip("\n") + "\n\n[tool.poe.tasks]\n" + lines + "\n"
        changes += [f"adicionada tarefa '{n}'" for n, _ in missing]
    if "dbt-smoke" in tasks and "--select smoke" not in str(tasks["dbt-smoke"]):
        work, n_sub = re.subn(
            r"^dbt-smoke\s*=.*$", _simple_line("dbt-smoke", SIMPLE["dbt-smoke"]), work, flags=re.M
        )
        if n_sub:
            changes.append("atualizada tarefa 'dbt-smoke' (agora so o modelo smoke)")

    # 2) tarefas em sequencia (tabelas). Forma antiga em string e substituida; forma quebrada e apenas avisada
    for name, (help_, cmds) in SEQUENCES.items():
        cur = tasks.get(name)
        if isinstance(cur, dict) and isinstance(cur.get("sequence"), list):
            if all(isinstance(s, str) for s in cur["sequence"]):
                changes.append(
                    f"ATENCAO: '{name}' usa strings no sequence (referencias, nao comandos): corrija manualmente"
                )
            continue
        if isinstance(cur, str):
            work = re.sub(rf"^{re.escape(name)}\s*=.*\n?", "", work, flags=re.M)
            changes.append(f"substituida '{name}' (string) por tabela em sequencia")
        else:
            changes.append(f"adicionada tarefa '{name}' (sequencia)")
        work = work.rstrip("\n") + "\n\n" + _seq_block(name, help_, cmds)

    if changes:  # valida o resultado antes de devolver
        new = tomllib.loads(work)["tool"]["poe"]["tasks"]
        absent = [n for n in (*SIMPLE, *SEQUENCES) if n not in new]
        if absent:
            raise RuntimeError(f"tarefas ainda ausentes apos a edicao: {absent}")
    return work.replace("\n", nl), changes


def apply_to_file(path, backup_dir) -> list[str]:
    """Le (sem converter quebras de linha), atualiza e grava o pyproject; guarda backup. Retorna as mudancas."""
    import shutil
    from pathlib import Path

    path = Path(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        text = f.read()
    new, changes = ensure_tasks(text)
    if changes:
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, backup_dir / f"{path.name}.bak")
        with path.open("w", encoding="utf-8", newline="") as f:
            f.write(new)
    return changes
