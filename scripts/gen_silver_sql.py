"""Regera os modelos dbt (silver e dq) a partir do esquema. Uso: uv run poe gen-sql"""

from credit_risk import config
from credit_risk.silver_gen import write_all

for p in write_all(config.ROOT):
    print("gerado:", p.relative_to(config.ROOT).as_posix())
