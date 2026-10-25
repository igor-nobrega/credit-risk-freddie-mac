"""Fase 1: ingestao bronze. Uso: uv run poe ingest   (ou: uv run python scripts/ingest_bronze.py --kind perf --force)"""

import argparse
import sys
from pathlib import Path

from credit_risk import config
from credit_risk.ingest import ingest_all

ap = argparse.ArgumentParser()
ap.add_argument("--kind", choices=["orig", "perf", "all"], default="all")
ap.add_argument("--force", action="store_true", help="reingere mesmo arquivos ja ingeridos")
args = ap.parse_args()

config.ensure_dirs()
kinds = ("orig", "perf") if args.kind == "all" else (args.kind,)
results = ingest_all(
    kinds, force=args.force, report_csv=Path("reports/tables/bronze_reconciliation.csv")
)

bad = [r for r in results if r.status not in ("OK", "SKIPPED")]
n_rows = sum(r.rows_loaded for r in results)
n_rej = sum(r.rows_rejected for r in results)
print(
    f"\n{len(results)} arquivo(s) | {n_rows:,} linhas carregadas | {n_rej:,} rejeitadas | {len(bad)} com problema"
)
if bad:
    print("PROBLEMAS:")
    for r in bad:
        print(f"  - {r.file}: {r.status} {r.detail}")
    sys.exit(1)
print("Bronze OK: reconciliacao fechada em todos os arquivos.")
