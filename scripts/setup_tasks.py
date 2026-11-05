"""Adiciona ao pyproject.toml as tarefas `poe` que faltam (idempotente). Uso: uv run python scripts/setup_tasks.py"""

from credit_risk import config
from credit_risk.pyproject_tasks import apply_to_file

changes = apply_to_file(config.ROOT / "pyproject.toml", config.TMP_DIR)
if not changes:
    print("pyproject.toml ja esta completo: nada a fazer.")
else:
    print(f"pyproject.toml atualizado (backup em {config.TMP_DIR / 'pyproject.toml.bak'}):")
    for c in changes:
        print("  -", c)
