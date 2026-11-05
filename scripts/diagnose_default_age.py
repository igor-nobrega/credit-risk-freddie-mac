"""Explica os loans com default_age < 1 (causa do WARN em assert_default_age_positive).

Uso: uv run poe diagnose-age   |   Saida: terminal e data/tmp/diagnose_default_age.txt (copie para o chat).
A secao G e em nivel de emprestimo: nao publique.
"""

from credit_risk import config
from credit_risk.diagnostics import default_age_report
from credit_risk.duck import connect

con = connect(read_only=True)
text = default_age_report(con)
con.close()
print(text)
out = config.TMP_DIR / "diagnose_default_age.txt"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text + "\n", encoding="utf-8")
print(f"\n(salvo em {out})")
