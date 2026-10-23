"""Configuracao central. Tudo que e pesado (dados, warehouse) pode ser movido via variaveis de ambiente."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Onde ficam dados e warehouse. Para tirar do OneDrive/Desktop: setx CREDIT_RISK_DATA_DIR "D:/dados/freddie"
DATA_DIR = Path(os.environ.get("CREDIT_RISK_DATA_DIR", ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
BRONZE_DIR = DATA_DIR / "bronze"
SILVER_DIR = DATA_DIR / "silver"
GOLD_DIR = DATA_DIR / "gold"
TMP_DIR = DATA_DIR / "tmp"
WAREHOUSE = DATA_DIR / "warehouse.duckdb"

# Sua maquina: 20 GB de RAM disponiveis. DuckDB fica com 12 GB, sobrando ~8 GB para
# Windows, VS Code e Python/Jupyter. Ajuste via variavel de ambiente se precisar.
DUCKDB_MEMORY_LIMIT = os.environ.get("DUCKDB_MEMORY_LIMIT", "12GB")
DUCKDB_THREADS = int(os.environ.get("DUCKDB_THREADS", min(8, os.cpu_count() or 4)))


def ensure_dirs() -> None:
    for d in (
        RAW_DIR / "orig",
        RAW_DIR / "perf",
        RAW_DIR / "macro",
        BRONZE_DIR,
        SILVER_DIR,
        GOLD_DIR,
        TMP_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)
