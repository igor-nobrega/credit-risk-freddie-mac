"""Conexao DuckDB padronizada do projeto (limites de memoria, spill em disco, threads)."""

from __future__ import annotations

from pathlib import Path

import duckdb

from . import config


def connect(
    db_path: str | Path | None = None, read_only: bool = False
) -> duckdb.DuckDBPyConnection:
    """Abre o warehouse local. Use read_only=True em notebooks para nao travar o arquivo.

    DuckDB aceita UM escritor por arquivo: feche conexoes (ou reinicie o kernel) antes de rodar dbt.
    """
    config.ensure_dirs()
    target = ":memory:" if db_path == ":memory:" else str(db_path or config.WAREHOUSE)
    con = duckdb.connect(target, read_only=read_only and target != ":memory:")
    con.execute(f"SET memory_limit='{config.DUCKDB_MEMORY_LIMIT}'")
    con.execute(f"SET temp_directory='{config.TMP_DIR.as_posix()}'")
    con.execute(f"SET threads={config.DUCKDB_THREADS}")
    con.execute("SET preserve_insertion_order=false")
    return con
