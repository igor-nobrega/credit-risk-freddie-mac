"""Verificacao de saude do projeto: prova, em segundos, ate que etapa tudo esta integro e o que fazer a seguir.

Uso: uv run poe doctor     (codigo de saida 1 se houver [FAIL])
Somente leitura. Nao baixa nada, nao altera o warehouse.
"""

from __future__ import annotations

import importlib.metadata as md
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .duck import connect
from .pyproject_tasks import ensure_tasks

REQUIRED_DISTS = [
    "duckdb", "pyarrow", "polars", "pandas", "dbt-core", "dbt-duckdb", "matplotlib",
    "scikit-learn", "statsmodels", "lightgbm", "lifelines", "optbinning", "shap",
    "pytest", "ruff", "pre-commit", "poethepoet",
]  # fmt: skip

TABLES = {
    "silver": ["silver.silver_orig", "silver.silver_perf"],
    "dq": ["dq.dq_rule_results", "dq.dq_column_profile", "dq.dq_missing_by_vintage"],
    "gold": [
        "gold.gold_loan_events", "gold.gold_pd_dataset", "gold.gold_vintage_curves", "gold.gold_default_summary",
    ],
    "eda": [
        "eda.eda_features", "eda.eda_exclusion_check", "eda.eda_fico_ltv", "eda.eda_mix_decomposition",
    ],
}  # fmt: skip

REQUIRED_COLUMNS = {
    "gold.gold_loan_events": [
        "first_row_age", "credit_event_code", "default_na_age", "upb_at_default", "months_to_first_payment",
        "first_payment_inconsistent", "assisted_while_dpd90",
    ],
    "gold.gold_pd_dataset": ["target_24m", "target_12m", "usable_24m", "usable_12m", "excluded_reason", "first_row_age"],
    "gold.gold_default_summary": [
        "n_default_na_24m", "n_default_in_first_payment_inconsistent", "n_without_perf", "n_late_entry",
    ],
}  # fmt: skip

N_DQ_RULES = 28
REPORTS = {
    "docs/data_quality_report.md": ("R28", "uv run poe dq-report"),
    "docs/default_definition_report.md": ("Layout v3", "uv run poe default-report"),
    "docs/eda_report.md": ("Relatorio de EDA", "uv run poe eda-report"),
}


@dataclass
class Check:
    status: str  # OK | WARN | FAIL
    name: str
    detail: str = ""
    hint: str = ""


def _n(v: int) -> str:
    return f"{v:,}".replace(",", ".")


def _git(root: Path, *args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(["git", *args], capture_output=True, text=True, cwd=root, timeout=30)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def run_checks(root: Path, data_dir: Path) -> tuple[list[Check], str]:
    """Retorna (checks, ultima_etapa_valida)."""
    out: list[Check] = []
    add = lambda *a, **k: out.append(Check(*a, **k))  # noqa: E731
    stage = "nenhuma"

    # --- ambiente ---------------------------------------------------------------------------
    v = sys.version_info
    add(
        "OK" if (v.major, v.minor) == (3, 12) else "WARN",
        "python",
        f"{v.major}.{v.minor}.{v.micro}",
        ""
        if (v.major, v.minor) == (3, 12)
        else "o projeto foi validado no Python 3.12 (uv python install 3.12)",
    )
    missing = []
    for d in REQUIRED_DISTS:
        try:
            md.version(d)
        except md.PackageNotFoundError:
            missing.append(d)
    add(
        "OK" if not missing else "FAIL",
        "dependencias",
        f"{len(REQUIRED_DISTS) - len(missing)}/{len(REQUIRED_DISTS)}",
        "" if not missing else f"faltam {missing}: rode `uv sync --locked`",
    )

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            with pyproject.open("r", encoding="utf-8", newline="") as f:
                _, changes = ensure_tasks(f.read())
            warn = next((c for c in changes if c.startswith("ATENCAO")), None)
            add(
                "OK" if not changes else "FAIL",
                "tarefas poe",
                "completas" if not changes else (warn or f"{len(changes)} pendente(s)"),
                ""
                if not changes
                else (
                    "siga a mensagem acima"
                    if warn
                    else "rode `uv run python scripts/setup_tasks.py`"
                ),
            )
        except tomllib.TOMLDecodeError as e:
            add("FAIL", "tarefas poe", f"pyproject.toml invalido: {e}")
    else:
        add("FAIL", "tarefas poe", "pyproject.toml ausente")

    # --- dados brutos e bronze --------------------------------------------------------------
    raw_o = sorted((data_dir / "raw" / "orig").glob("*.txt"))
    raw_p = sorted((data_dir / "raw" / "perf").glob("*.txt"))
    if raw_o and len(raw_o) == len(raw_p):
        add(
            "OK",
            "dados brutos",
            f"{len(raw_o)} arquivos de originacao e {len(raw_p)} de performance",
        )
    else:
        add(
            "FAIL",
            "dados brutos",
            f"orig={len(raw_o)} perf={len(raw_p)} (devem existir e ser iguais)",
            f"coloque os .txt do Sample em {data_dir / 'raw'} (orig/ e perf/)",
        )
    logs = (
        sorted((data_dir / "bronze" / "_log").glob("*.json"))
        if (data_dir / "bronze" / "_log").exists()
        else []
    )
    if logs:
        bad = [
            p.name
            for p in logs
            if not re.search(r'"status":\s*"(OK|SKIPPED)"', p.read_text(encoding="utf-8"))
        ]
        add(
            "OK" if not bad and len(logs) == len(raw_o) + len(raw_p) else "FAIL",
            "bronze (ingestao)",
            f"{len(logs)} logs; {len(bad)} com problema",
            "rode `uv run poe ingest` e `uv run python scripts/report_bronze.py`",
        )
        stage = "bronze" if not bad else stage
    else:
        add("FAIL", "bronze (ingestao)", "nenhum log de ingestao", "rode `uv run poe ingest`")

    # --- warehouse --------------------------------------------------------------------------
    wh = data_dir / "warehouse.duckdb"
    if not wh.exists():
        add(
            "FAIL",
            "warehouse",
            f"{wh} nao existe",
            "rode `uv run poe ingest` e depois `uv run poe silver`",
        )
    else:
        try:
            con = connect(wh, read_only=True)
        except Exception as e:  # noqa: BLE001
            add(
                "FAIL",
                "warehouse",
                f"nao abriu: {type(e).__name__}",
                "feche notebooks/terminais que usam o .duckdb",
            )
            con = None
        if con is not None:
            try:
                stage = _warehouse_checks(con, out, stage)
            finally:
                con.close()

    # --- relatorios -------------------------------------------------------------------------
    for rel, (marker, cmd) in REPORTS.items():
        p = root / rel
        if not p.exists():
            add("WARN", rel, "nao gerado", f"rode `{cmd}`")
            continue
        text = p.read_text(encoding="utf-8")
        stale = wh.exists() and p.stat().st_mtime < wh.stat().st_mtime - 2
        if marker not in text:
            add("FAIL", rel, "versao antiga do relatorio", f"rode `{cmd}`")
        elif stale:
            add("WARN", rel, "mais antigo que o warehouse", f"rode `{cmd}`")
        else:
            add("OK", rel, "atualizado")
    dd = root / "docs" / "default_decision.md"
    add(
        "OK" if dd.exists() else "WARN",
        "decisao D-002",
        "docs/default_decision.md presente" if dd.exists() else "ausente",
        ""
        if dd.exists()
        else "copie docs/_templates/default_decision.template.md para docs/default_decision.md e ajuste",
    )

    ei = root / "docs" / "eda_insights.md"
    add(
        "OK" if ei.exists() else "WARN",
        "insights da EDA",
        "docs/eda_insights.md presente" if ei.exists() else "ausente",
        ""
        if ei.exists()
        else "copie docs/_templates/eda_insights.template.md para docs/eda_insights.md e revise",
    )

    # --- git --------------------------------------------------------------------------------
    if (root / ".git").exists():
        rc, remote = _git(root, "remote", "get-url", "origin")
        if rc != 0:
            add(
                "WARN",
                "git/github",
                "sem remote origin",
                "rode `gh repo create ...` ou `git remote add origin ...`",
            )
        else:
            _, st = _git(root, "status", "-sb")
            first = st.splitlines()[0] if st else ""
            dirty = len([ln for ln in st.splitlines()[1:] if ln.strip()])
            sync = "ahead" in first or "behind" in first
            _, tag = _git(root, "describe", "--tags", "--abbrev=0")
            add(
                "OK" if not sync and not dirty else "WARN",
                "git/github",
                f"{first} | {dirty} arquivo(s) alterado(s) | ultima tag: {tag if tag and 'fatal' not in tag else '(nenhuma)'}",
                ""
                if not sync and not dirty
                else "faca commit e `git push` para sincronizar com o GitHub",
            )
    else:
        add("WARN", "git/github", "pasta sem repositorio git")
    return out, stage


def _warehouse_checks(con, out: list[Check], stage: str) -> str:
    add = lambda *a, **k: out.append(Check(*a, **k))  # noqa: E731
    have = {
        r[0] + "." + r[1]
        for r in con.execute(
            "select table_schema, table_name from information_schema.tables"
        ).fetchall()
    }
    views_ok = True
    for t in ("bronze_orig", "bronze_perf"):
        try:
            con.execute(f"select 1 from {t} limit 1").fetchone()
        except Exception:  # noqa: BLE001
            views_ok = False
    add(
        "OK" if views_ok else "FAIL",
        "views bronze",
        "legiveis" if views_ok else "quebradas",
        ""
        if views_ok
        else "rode `uv run poe ingest` (recria as views com o caminho atual dos dados)",
    )
    cmds = {
        "silver": "uv run poe silver",
        "dq": "uv run poe silver",
        "gold": "uv run poe gold",
        "eda": "uv run poe eda",
    }
    valid = {}  # camada -> existe E esta na versao atual
    for layer in ("silver", "dq", "gold", "eda"):
        absent = [t for t in TABLES[layer] if t not in have]
        valid[layer] = not absent
        add(
            "OK" if not absent else "FAIL",
            f"tabelas {layer}",
            "completas" if not absent else f"ausentes: {absent}",
            "" if not absent else f"rode `{cmds[layer]}`",
        )
    for table, cols in REQUIRED_COLUMNS.items():
        if table not in have:
            continue
        existing = {r[0] for r in con.execute(f"describe {table}").fetchall()}
        gap = [c for c in cols if c not in existing]
        if gap:
            valid["gold"] = False
        add(
            "OK" if not gap else "FAIL",
            f"colunas {table.split('.')[1]}",
            "versao atual" if not gap else f"faltam {gap}",
            "" if not gap else "a camada esta DESATUALIZADA: rode `uv run poe gold`",
        )
    if valid["silver"] and valid["gold"] and views_ok:
        bo, so, bp, sp, ge, gep, pd_ = con.execute(
            "select (select count(*) from bronze_orig), (select count(*) from silver.silver_orig), "
            "(select count(*) from bronze_perf), (select count(*) from silver.silver_perf), "
            "(select count(*) from gold.gold_loan_events), "
            "(select count(*) from gold.gold_loan_events where has_perf), (select count(*) from gold.gold_pd_dataset)"
        ).fetchone()
        probs = []
        if so > bo:
            probs.append(f"silver_orig ({_n(so)}) > bronze_orig ({_n(bo)})")
        if sp != bp:
            probs.append(f"silver_perf ({_n(sp)}) != bronze_perf ({_n(bp)})")
        if ge != so:
            probs.append(f"gold_loan_events ({_n(ge)}) != silver_orig ({_n(so)})")
        if pd_ != gep:
            probs.append(f"gold_pd_dataset ({_n(pd_)}) != loans com performance ({_n(gep)})")
        if probs:
            valid["gold"] = False
        add(
            "OK" if not probs else "FAIL",
            "reconciliacao de linhas",
            f"orig {_n(bo)}->{_n(so)} | perf {_n(bp)}->{_n(sp)} | loans com performance {_n(gep)}"
            if not probs
            else "; ".join(probs),
            "" if not probs else "reconstrua: `uv run poe silver` e `uv run poe gold`",
        )
    if "dq.dq_rule_results" in have:
        n = con.execute("select count(*) from dq.dq_rule_results").fetchone()[0]
        if n < N_DQ_RULES:
            valid["dq"] = False
        add(
            "OK" if n >= N_DQ_RULES else "FAIL",
            "regras de DQ",
            f"{n} de {N_DQ_RULES}",
            "" if n >= N_DQ_RULES else "rode `uv run poe silver` (reconstroi as regras)",
        )
    if valid["eda"] and valid["gold"]:
        eq = con.execute(
            "select count(distinct n) = 1 and max(n) = (select count(*) from gold.gold_pd_dataset "
            "where usable_24m and vintage_year <= 2023) from (select feature, sum(n_loans) n from eda.eda_features group by 1)"
        ).fetchone()[0]
        if not eq:
            valid["eda"] = False
        add(
            "OK" if eq else "FAIL",
            "EDA vs gold",
            "mesma populacao" if eq else "totais divergem",
            "" if eq else "a EDA esta desatualizada: rode `uv run poe eda`",
        )
    if views_ok:
        for layer in ("silver", "dq", "gold", "eda"):
            if not valid[layer]:
                break
            stage = layer
    return stage


_ORDER = [
    "uv sync",
    "setup_tasks",
    "ingest",
    "silver",
    "gold",
    "eda",
    "dq-report",
    "default-report",
    "eda-report",
]


def _rank(hint: str) -> int:
    """Ordem do pipeline: o primeiro comando a rodar vem antes (ex.: gold antes de eda)."""
    for i, key in enumerate(_ORDER):
        if re.search(rf"(poe {re.escape(key)}\b|{re.escape(key)})", hint):
            return i
    return len(_ORDER)


def render(checks: list[Check], stage: str) -> tuple[str, int]:
    lines = []
    for c in checks:
        lines.append(f"[{c.status:^4}] {c.name}" + (f" - {c.detail}" if c.detail else ""))
        if c.hint and c.status != "OK":
            lines.append(f"         -> {c.hint}")
    n = {s: sum(c.status == s for c in checks) for s in ("OK", "WARN", "FAIL")}
    fails = sorted((c.hint for c in checks if c.status == "FAIL" and c.hint), key=_rank)
    warns = sorted((c.hint for c in checks if c.status == "WARN" and c.hint), key=_rank)
    nxt = (fails or warns or [None])[0]
    lines += [
        "",
        f"RESULTADO: {n['OK']} OK, {n['WARN']} WARN, {n['FAIL']} FAIL | ultima camada valida do warehouse: {stage}",
        f"PROXIMO PASSO: {nxt}"
        if nxt
        else "PROXIMO PASSO: nada pendente. Projeto integro ate a ultima etapa (EDA).",
    ]
    return "\n".join(lines), (1 if n["FAIL"] else 0)
