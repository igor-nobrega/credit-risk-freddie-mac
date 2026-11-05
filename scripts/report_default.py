"""Relatorio de definicao de default: compara candidatos com os SEUS dados para decidir a D-002.

Uso: uv run poe default-report
Saidas: docs/default_definition_report.md, reports/tables/default_*.csv e vintage_curves.csv,
        reports/figures/vintage_default_curves.png, reports/figures/default_definitions_compare.png
Somente agregados (contagens e taxas por vintage): publicaveis.
"""

import datetime as dt
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from credit_risk import config
from credit_risk.duck import connect
from credit_risk.reportlib import read_manual

MIN_EVENTS = 100  # abaixo disso a vintage tem poucos eventos para validar modelo

con = connect(config.WAREHOUSE, read_only=True)
df = lambda sql: con.execute(sql).fetchdf()  # noqa: E731
tables, figs = Path("reports/tables"), Path("reports/figures")
tables.mkdir(parents=True, exist_ok=True)
figs.mkdir(parents=True, exist_ok=True)

S = df("select * from gold.gold_default_summary order by vintage_year")
# nao desenha pontos de curva com poucos loans em risco: 20% da maior vintage (10.000 no Sample real)
MIN_AT_RISK = max(1, int(0.2 * S["n_with_perf"].max()))
C = df("select * from gold.gold_vintage_curves")
dq = df("select * from dq.dq_rule_results where rule_id = 'R21'")

n = lambda v: f"{int(v):,}".replace(",", ".")  # noqa: E731
pc = lambda v: "" if v != v else f"{100 * float(v):.2f}%"  # noqa: E731


def md(frame, fmt=None) -> str:
    fmt = fmt or {}
    cols = list(frame.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for i in range(len(frame)):
        out.append(
            "| "
            + " | ".join(
                fmt[c](frame[c].iloc[i]) if c in fmt else str(frame[c].iloc[i]) for c in cols
            )
            + " |"
        )
    return "\n".join(out)


S.to_csv(tables / "default_summary.csv", index=False, lineterminator="\n")
C.round({"default_rate_cum": 6}).to_csv(
    tables / "vintage_curves.csv", index=False, lineterminator="\n"
)
tot = S.sum(numeric_only=True)
cutoff = str(S["cutoff_period"].max())[:7]

# 1) estados terminais
t1 = [
    ("ativo no corte (censurado)", tot["n_active"]),
    ("liquidado: prepago ou vencido (ZB 01)", tot["n_prepaid"]),
    ("liquidado: evento de credito (ZB 02/03/09/15)", tot["n_credit_event_terminal"]),
    ("liquidado: outra remocao (ZB 16/96)", tot["n_other_removal"]),
]
T1 = pd.DataFrame(t1, columns=["estado_terminal", "loans"])
T1["pct"] = T1["loans"] / tot["n_with_perf"]

# 2) candidatos por vintage (vida inteira; vintages recentes ainda estao censuradas)
T2 = pd.DataFrame({"vintage": S["vintage_year"], "loans": S["n_with_perf"]})
for lab, col in [
    ("dpd60", "n_ever_dpd60"),
    ("dpd90", "n_ever_dpd90"),
    ("dpd180", "n_ever_dpd180"),
    ("evento_credito", "n_ever_credit_event"),
    ("dpd90_ou_evento_A", "n_ever_default"),
    ("B_sem_assistencia", "n_ever_default_noassist"),
]:
    T2[lab] = S[col] / S["n_with_perf"]

# 3) taxa a 24 meses: definicao A (simples) vs B (ignora atraso sob assistencia/desastre/adiamento)
T3 = pd.DataFrame(
    {
        "vintage": S["vintage_year"],
        "loans_obs_24m": S["n_obs_24m"],
        "eventos_A": S["n_default_24m"],
        "taxa_A": S["n_default_24m"] / S["n_obs_24m"].where(S["n_obs_24m"] > 0),
        "eventos_B": S["n_default_na_24m"],
        "taxa_B": S["n_default_na_24m"] / S["n_obs_24m"].where(S["n_obs_24m"] > 0),
    }
)
T3["alerta"] = np.where(
    T3["loans_obs_24m"] == 0,
    "sem janela de 24m",
    np.where(T3["eventos_B"] < MIN_EVENTS, f"B: < {MIN_EVENTS} eventos", ""),
)

# 3b) atrasos 90+ sob plano de assistencia / desastre / adiamento, por vintage
T3b = pd.DataFrame(
    {
        "vintage": S["vintage_year"],
        "loans_90mais": S["n_ever_dpd90"],
        "com_assistencia": S["n_dpd90_with_assistance"],
    }
)
T3b["pct_com_assistencia"] = T3b["com_assistencia"] / T3b["loans_90mais"].where(
    T3b["loans_90mais"] > 0
)

# 4) gatilhos, curas, modificacoes
n_def = tot["n_ever_default"]
T4 = pd.DataFrame(
    [
        ("so 90+ dias (sem evento de credito)", tot["n_trigger_dpd90_only"]),
        ("so evento de credito (sem 90+ previo)", tot["n_trigger_credit_event_only"]),
        ("ambos", tot["n_trigger_both"]),
    ],
    columns=["gatilho", "loans"],
)
T4["pct_dos_defaults"] = T4["loans"] / n_def
d90 = tot["n_ever_dpd90"]
T5 = pd.DataFrame(
    [
        ("chegaram a 90+ dias", d90, 1.0),
        (
            "voltaram a ficar em dia depois (cura)",
            tot["n_cured_after_dpd90"],
            tot["n_cured_after_dpd90"] / d90,
        ),
        (
            "90+ e depois prepagaram (sem evento de credito)",
            tot["n_dpd90_then_prepaid"],
            tot["n_dpd90_then_prepaid"] / d90,
        ),
    ],
    columns=["grupo", "loans", "pct_dos_90plus"],
)
mod = pd.DataFrame(
    [
        (
            "loans modificados em algum momento",
            tot["n_ever_modified"],
            tot["n_ever_modified"] / tot["n_with_perf"],
        ),
        (
            "defaults que foram modificados",
            tot["n_default_and_modified"],
            tot["n_default_and_modified"] / n_def,
        ),
    ],
    columns=["grupo", "loans", "pct"],
)

# figuras
primary = C[(C["definition"] == "dpd90_or_credit_event") & (C["n_at_risk"] >= MIN_AT_RISK)]
fig, ax = plt.subplots(figsize=(10, 5.5))
cmap = plt.get_cmap("viridis")
ys = sorted(primary["vintage_year"].unique())
for y in ys:
    d = primary[primary["vintage_year"] == y]
    ax.plot(
        d["age_months"],
        100 * d["default_rate_cum"],
        color=cmap((y - ys[0]) / max(1, ys[-1] - ys[0])),
        lw=1.4,
    )
sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(ys[0], ys[-1]))
fig.colorbar(sm, ax=ax, label="Vintage")
ax.set_xlabel("Idade do emprestimo (meses desde o 1o pagamento)")
ax.set_ylabel("Default cumulativo (%)")
ax.set_title("Default cumulativo por vintage (90+ dias ou evento de credito)")
ax.set_ylim(bottom=0)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(figs / "vintage_default_curves.png", dpi=150)

c24 = C[(C["age_months"] == 24) & (C["n_at_risk"] >= MIN_AT_RISK)]
fig, ax = plt.subplots(figsize=(10, 5))
for d, g in c24.groupby("definition"):
    g = g.sort_values("vintage_year")
    ax.plot(g["vintage_year"], 100 * g["default_rate_cum"], marker="o", ms=3, label=d)
ax.set_xlabel("Vintage")
ax.set_ylabel("Taxa de default em 24 meses (%)")
ax.set_title("Sensibilidade da taxa de default a definicao (janela de 24 meses)")
ax.set_ylim(bottom=0)
ax.grid(alpha=0.3)
ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(figs / "default_definitions_compare.png", dpi=150)

T7 = pd.DataFrame(
    [
        ("sem nenhuma linha de performance", tot["n_without_perf"]),
        ("1o pagamento incompativel com o loan_id", tot["n_first_payment_inconsistent"]),
        ("default antes do 1o pagamento (idade < 1)", tot["n_default_before_first_payment"]),
    ],
    columns=["motivo", "loans"],
)

r21 = dq.iloc[0] if len(dq) else None
doc = [
    "# Relatorio de Definicao de Default",
    f"\nGerado em {dt.date.today().isoformat()} por `uv run poe default-report` (somente agregados).",
    f"Corte de dados (ultimo periodo de performance): **{cutoff}**. Idade = meses desde o primeiro pagamento.\n",
    "## 1. Estados terminais (todas as vintages)",
    md(T1, {"loans": n, "pct": pc}),
    "\n## 2. Candidatos a default por vintage (vida inteira, % dos loans)",
    "Vintages recentes ainda estao censuradas: as taxas delas vao subir com o tempo.\n",
    md(T2, {c: pc for c in T2.columns if c not in ("vintage", "loans")} | {"loans": n}),
    "\n![Sensibilidade a definicao](../reports/figures/default_definitions_compare.png)\n",
    "## 3. Taxa de default em 24 meses: A (90+ dias ou evento de credito) vs B (A sem atraso sob assistencia)",
    "A = qualquer mes 90+ conta. B ignora meses 90+ sob plano de assistencia (forbearance/repayment/trial), "
    "atraso por desastre ou adiamento de pagamento (campos populados desde 2014).\n",
    md(T3, {"loans_obs_24m": n, "eventos_A": n, "eventos_B": n, "taxa_A": pc, "taxa_B": pc}),
    "\n![Curvas por vintage](../reports/figures/vintage_default_curves.png)\n",
    "### 3b. Loans que chegaram a 90+ dias e tiveram assistencia/desastre/adiamento no periodo",
    md(T3b, {"loans_90mais": n, "com_assistencia": n, "pct_com_assistencia": pc}),
    "\nCampos de assistencia e desastre so existem a partir de 2014: antes disso o percentual e ~0 por construcao.\n",
    "## 4. Gatilhos dos defaults",
    md(T4, {"loans": n, "pct_dos_defaults": pc}),
    "\n## 5. Curas (loans que chegaram a 90+ dias)",
    md(T5, {"loans": n, "pct_dos_90plus": pc}),
    "\n## 6. Modificacoes",
    md(mod, {"loans": n, "pct": pc}),
    "\n## 7. Exclusoes da amostra de PD (coluna `excluded_reason` do `gold_pd_dataset`)",
    md(T7, {"loans": n}),
    "\n## 8. Prontidao para LGD",
    f"Eventos de credito com `actual_loss` ausente (regra R21): {n(r21['n_failed'])} de {n(r21['n_checked'])} "
    f"({r21['pct_failed']:.2f}%). Esperado nos 3 ultimos meses antes do corte e em defeitos; tratar como censura."
    if r21 is not None
    else "(rode `uv run poe silver` antes)",
    "\n## 9. Decisao (D-002)",
    read_manual(
        "docs/default_decision.md",
        "_(a preencher: crie `docs/default_decision.md` com gatilho, janela, tratamento de cura e de "
        "prepagamento; ele sera incluido aqui a cada execucao)_",
    ),
]
Path("docs/default_definition_report.md").write_text(
    "\n".join(doc).rstrip("\n") + "\n", encoding="utf-8", newline="\n"
)
con.close()
print(
    "OK: docs/default_definition_report.md + reports/tables/default_summary.csv, vintage_curves.csv + 2 figuras"
)
