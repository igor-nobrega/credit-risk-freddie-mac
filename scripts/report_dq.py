"""Gera o relatorio de qualidade de dados a partir das tabelas dq.* do warehouse.

Uso:  uv run poe dq-report
Saidas: docs/data_quality_report.md, reports/tables/dq_*.csv, reports/figures/missing_by_vintage.png
Somente agregados (contagens e percentuais): publicaveis.
"""

import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from credit_risk import config
from credit_risk.duck import connect

con = connect(config.WAREHOUSE, read_only=True)
df = lambda sql: con.execute(sql).fetchdf()  # noqa: E731

tables = Path("reports/tables")
figs = Path("reports/figures")
tables.mkdir(parents=True, exist_ok=True)
figs.mkdir(parents=True, exist_ok=True)


def md(frame, fmt=None) -> str:
    fmt = fmt or {}
    cols = list(frame.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in frame.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            cells.append(fmt[c](v) if c in fmt else ("" if v is None else str(v)))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


n = lambda v: f"{int(v):,}".replace(",", ".")  # noqa: E731
p = lambda v: "" if v != v else f"{float(v):.2f}%"  # noqa: E731

rules = df("select * from dq.dq_rule_results order by rule_id")
prof = df("select * from dq.dq_column_profile")
miss = df("select * from dq.dq_missing_by_vintage order by table_name, column_name, vintage_year")
vol = df("""
  select kind as tabela, count(*) as arquivos, sum(lines_nonblank) as linhas_arquivo,
         sum(rows_loaded) as carregadas, sum(rows_rejected) as rejeitadas
  from bronze_ingestion_log group by kind order by kind""")
sil = df("""
  select 'orig' as tabela, (select count(*) from bronze_orig) as bronze, (select count(*) from silver.silver_orig) as silver
  union all
  select 'perf', (select count(*) from bronze_perf), (select count(*) from silver.silver_perf)""")
sil["diferenca"] = sil["bronze"] - sil["silver"]

prof["pct_blank"] = 100 * prof["n_blank"] / prof["n_rows"]
prof["pct_sentinel"] = 100 * prof["n_sentinel"] / prof["n_rows"]
prof["pct_cast_fail"] = 100 * prof["n_cast_fail"] / prof["n_rows"]

rules.to_csv(tables / "dq_rule_results.csv", index=False, lineterminator="\n")
prof.to_csv(tables / "dq_column_profile.csv", index=False, lineterminator="\n")
miss.to_csv(tables / "dq_missing_by_vintage.csv", index=False, lineterminator="\n")

# figura: evolucao do % de ausentes (sentinela/branco) por vintage nas variaveis mais afetadas
mo = miss[miss["table_name"] == "orig"]
top = mo.groupby("column_name")["pct_missing"].max().sort_values(ascending=False).head(6).index
fig, ax = plt.subplots(figsize=(9, 4.8))
for c in top:
    d = mo[mo["column_name"] == c]
    ax.plot(d["vintage_year"], 100 * d["pct_missing"], marker="o", ms=3, label=c)
ax.set_xlabel("Vintage (ano de originacao)")
ax.set_ylabel("% ausente (sentinela ou branco)")
ax.set_title("Ausencia por vintage nas variaveis de originacao mais afetadas")
ax.grid(alpha=0.3)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(figs / "missing_by_vintage.png", dpi=150)

worst = prof[(prof["n_blank"] > 0) | (prof["n_sentinel"] > 0)].copy()
worst["pct_ausente"] = worst["pct_blank"] + worst["pct_sentinel"]
worst = worst.sort_values("pct_ausente", ascending=False).head(15)
cast = prof[prof["n_cast_fail"] > 0][
    ["table_name", "column_name", "declared_type", "n_cast_fail", "pct_cast_fail"]
]

doc = [
    "# Relatorio de Qualidade de Dados",
    f"\nGerado em {dt.date.today().isoformat()} por `uv run poe dq-report` (somente agregados).\n",
    "## 1. Volumetria e reconciliacao (arquivo -> bronze)",
    md(vol, {c: n for c in ["arquivos", "linhas_arquivo", "carregadas", "rejeitadas"]}),
    "\n## 2. Bronze -> Silver",
    md(sil, {c: n for c in ["bronze", "silver", "diferenca"]}),
    "\nA diferenca em `orig` corresponde a loans duplicados na bronze (regra R01); `perf` nao remove linhas.\n",
    "## 3. Regras de consistencia de negocio",
    md(
        rules[
            [
                "rule_id",
                "table_name",
                "severity",
                "description",
                "n_checked",
                "n_failed",
                "pct_failed",
                "suggested_action",
            ]
        ],
        {"n_checked": n, "n_failed": n, "pct_failed": p},
    ),
    "\n## 4. Variaveis com mais ausentes (brancos + sentinelas)",
    md(
        worst[["table_name", "column_name", "n_blank", "n_sentinel", "pct_ausente"]],
        {"n_blank": n, "n_sentinel": n, "pct_ausente": p},
    ),
    "\n![Ausencia por vintage](../reports/figures/missing_by_vintage.png)\n",
    "## 5. Falhas de conversao de tipo (valor existia mas nao converteu)",
    md(cast, {"n_cast_fail": n, "pct_cast_fail": p}) if len(cast) else "Nenhuma.",
    "\n## 6. Conclusoes e riscos para a modelagem",
    "_(a preencher a mao apos ler as tabelas acima: o que muda no target, nas features e na amostra)_\n",
]
Path("docs/data_quality_report.md").write_text(
    "\n".join(doc) + "\n", encoding="utf-8", newline="\n"
)
con.close()
print(
    "OK: docs/data_quality_report.md + reports/tables/dq_*.csv + reports/figures/missing_by_vintage.png"
)
