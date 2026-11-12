"""Verificacao de saude do projeto. Uso: uv run poe doctor  (codigo de saida 1 se houver [FAIL])."""

import sys

from credit_risk import config
from credit_risk.doctor import render, run_checks

checks, stage = run_checks(config.ROOT, config.DATA_DIR)
text, code = render(checks, stage)
print(text)
sys.exit(code)
