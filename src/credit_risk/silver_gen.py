"""Gera os modelos dbt da camada silver e os perfis de qualidade a partir do esquema Python.

Fonte unica da verdade = src/credit_risk/freddie_schema.py. Os .sql gerados sao versionados
(legiveis no portfolio) e um teste garante que nao divergem do esquema.
Uso: uv run python scripts/gen_silver_sql.py
"""

from __future__ import annotations

from pathlib import Path

from .freddie_schema import ORIG_COLS, PERF_COLS

HEADER = "-- GERADO por scripts/gen_silver_sql.py a partir de src/credit_risk/freddie_schema.py. NAO EDITE.\n"
META = ["_source_file", "_vintage", "_ingested_at"]


def base_expr(name: str, sentinels: list[str]) -> str:
    """trim + branco e sentinelas viram NULL (ainda texto)."""
    e = f"trim({name})"
    for s in ["", *sentinels]:
        e = f"nullif({e}, '{s}')"
    return e


def cast_expr(base: str, typ: str) -> str:
    if typ == "int":
        return f"try_cast({base} as integer)"
    if typ == "double":
        return f"try_cast({base} as double)"
    if typ == "yyyymm":
        return f"try_cast(try_strptime({base} || '01', '%Y%m%d') as date)"
    return base


def _typed_select(cols) -> str:
    lines = [f"    {cast_expr(base_expr(n, s), t)} as {n}" for n, t, s in cols]
    lines += [f"    ({base_expr(n, s)} is null) as {n}_was_missing" for n, _, s in cols if s]
    return ",\n".join(lines)


def silver_orig_sql() -> str:
    return f"""{HEADER}{{{{ config(materialized='table') }}}}

with src as (
  select * from {{{{ source('bronze', 'bronze_orig') }}}}
),
typed as (
  select
{_typed_select(ORIG_COLS)},
    try_cast(_vintage as integer) as vintage_year,
    _source_file,
    _ingested_at
  from src
),
ranked as (
  select
    *,
    count(*) over (partition by loan_id) as _n_source_rows,
    row_number() over (partition by loan_id order by _source_file desc) as _rn
  from typed
)
select * exclude (_rn)
from ranked
where _rn = 1
"""


def silver_perf_sql() -> str:
    return f"""{HEADER}{{{{ config(materialized='table') }}}}

with src as (
  select * from {{{{ source('bronze', 'bronze_perf') }}}}
),
typed as (
  select
{_typed_select(PERF_COLS)},
    try_cast(_vintage as integer) as vintage_year,
    _source_file
  from src
)
select
  *,
  try_cast(current_loan_delinquency_status as integer) as dlq_months,  -- 'RA' (REO) vira NULL aqui
  (current_loan_delinquency_status = 'RA') as is_reo
from typed
"""


def _profile_cte(alias: str, source_sql: str, cols) -> str:
    aggs = []
    for n, t, s in cols:
        sent = ", ".join(f"'{x}'" for x in s)
        b = base_expr(n, s)
        aggs.append(
            f"cast(sum(case when nullif(trim({n}), '') is null then 1 else 0 end) as bigint) as {n}__blank"
        )
        aggs.append(
            f"cast(sum(case when trim({n}) in ({sent}) then 1 else 0 end) as bigint) as {n}__sentinel"
            if s
            else f"cast(0 as bigint) as {n}__sentinel"
        )
        aggs.append(
            f"cast(sum(case when {b} is not null and {cast_expr(b, t)} is null then 1 else 0 end) as bigint) "
            f"as {n}__cast_fail"
        )
    body = ",\n    ".join(aggs)
    return f"{alias} as (\n  select count(*) as n,\n    {body}\n  from {source_sql}\n)"


def dq_column_profile_sql() -> str:
    ctes = [
        _profile_cte("o", "{{ source('bronze', 'bronze_orig') }}", ORIG_COLS),
        _profile_cte("p", "{{ source('bronze', 'bronze_perf') }}", PERF_COLS),
    ]
    sels = []
    for alias, table, cols in (("o", "orig", ORIG_COLS), ("p", "perf", PERF_COLS)):
        for n, t, _ in cols:
            sels.append(
                f"select '{table}' as table_name, '{n}' as column_name, '{t}' as declared_type, "
                f"{alias}.n as n_rows, {alias}.{n}__blank as n_blank, {alias}.{n}__sentinel as n_sentinel, "
                f"{alias}.{n}__cast_fail as n_cast_fail from {alias}"
            )
    return (
        f"{HEADER}{{{{ config(materialized='table') }}}}\n\nwith\n"
        + ",\n".join(ctes)
        + "\n"
        + "\nunion all\n".join(sels)
        + "\n"
    )


def dq_missing_by_vintage_sql() -> str:
    parts, ctes = [], []
    for alias, table, cols, ref in (
        ("o", "orig", ORIG_COLS, "silver_orig"),
        ("p", "perf", PERF_COLS, "silver_perf"),
    ):
        flagged = [n for n, _, s in cols if s]
        sums = ",\n    ".join(
            f"cast(sum(case when {n}_was_missing then 1 else 0 end) as bigint) as {n}"
            for n in flagged
        )
        ctes.append(
            f"{alias} as (\n  select vintage_year, count(*) as n_rows,\n    {sums}\n"
            f"  from {{{{ ref('{ref}') }}}}\n  group by vintage_year\n)"
        )
        for n in flagged:
            parts.append(
                f"select '{table}' as table_name, '{n}' as column_name, vintage_year, n_rows, "
                f"{n} as n_missing, {n} * 1.0 / n_rows as pct_missing from {alias}"
            )
    return (
        f"{HEADER}{{{{ config(materialized='table') }}}}\n\nwith\n"
        + ",\n".join(ctes)
        + "\n"
        + "\nunion all\n".join(parts)
        + "\n"
    )


def render_all() -> dict[str, str]:
    return {
        "dbt/models/silver/silver_orig.sql": silver_orig_sql(),
        "dbt/models/silver/silver_perf.sql": silver_perf_sql(),
        "dbt/models/dq/dq_column_profile.sql": dq_column_profile_sql(),
        "dbt/models/dq/dq_missing_by_vintage.sql": dq_missing_by_vintage_sql(),
    }


def write_all(root: Path) -> list[Path]:
    written = []
    for rel, text in render_all().items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")
        written.append(p)
    return written
