"""Relatorio de EDA (Fase 4): poder discriminatorio, perfis de risco, 2022-2023 e calibracao das exclusoes.

Uso: uv run poe eda-report      (antes: uv run poe gold  e  uv run poe eda)
Saidas: docs/eda_report.md, reports/tables/eda_*.csv, reports/figures/eda_*.png
Somente agregados (contagens por faixa): publicaveis. Alvo = target_24m (D-002, definicao B).
"""

import datetime as dt
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator

from credit_risk import config
from credit_risk.duck import connect
from credit_risk.eda_stats import iv_of, standardize_mix
from credit_risk.reportlib import read_manual

BASE_ERA, TEST_ERA = "2012-2017", "2022-2023"
MIN_POINT = 200  # pontos de vintage x grupo com menos loans nao entram no grafico de linhas (ruido)
MIN_CELL = 100  # celulas do mapa de calor com menos loans ficam mascaradas (taxa instavel)
con = connect(config.WAREHOUSE, read_only=True)
try:
    F = con.execute("select * from eda.eda_features").fetchdf()
    X = con.execute("select * from eda.eda_exclusion_check").fetchdf()
    H = con.execute("select * from eda.eda_fico_ltv").fetchdf()
except Exception as e:  # noqa: BLE001
    print(
        "ERRO: as tabelas de EDA nao existem ou estao desatualizadas (o relatorio NAO foi gerado)."
    )
    print(f"  detalhe: {type(e).__name__}: {str(e).splitlines()[0]}")
    print(
        "  Corrija com:  uv run poe gold   e depois:  uv run poe eda   (e entao:  uv run poe eda-report)"
    )
    sys.exit(1)
con.close()

tables, figs = Path("reports/tables"), Path("reports/figures")
tables.mkdir(parents=True, exist_ok=True)
figs.mkdir(parents=True, exist_ok=True)

n = lambda v: f"{int(v):,}".replace(",", ".")  # noqa: E731
pc = lambda v: "" if v != v else f"{100 * float(v):.2f}%"  # noqa: E731
f2 = lambda v: "" if v != v else f"{float(v):.2f}"  # noqa: E731
f3 = lambda v: "" if v != v else f"{float(v):.3f}"  # noqa: E731


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


# ---------- 1) perfis agregados e poder discriminatorio (IV) --------------------------------------
P = F.groupby(["feature", "bucket"], as_index=False)[["n_loans", "n_defaults"]].sum()
tot_loans = P[P["feature"] == "fico_band"]["n_loans"].sum()
tot_def = P[P["feature"] == "fico_band"]["n_defaults"].sum()
overall = tot_def / tot_loans
P["share"] = P["n_loans"] / P.groupby("feature")["n_loans"].transform("sum")
P["default_rate"] = P["n_defaults"] / P["n_loans"]
P["lift"] = P["default_rate"] / overall

IV = pd.DataFrame(
    [(f, len(g), iv_of(g)) for f, g in P.groupby("feature")], columns=["variavel", "faixas", "IV"]
).sort_values("IV", ascending=False)
IV["leitura"] = pd.cut(
    IV["IV"],
    [-1, 0.02, 0.1, 0.3, 0.5, 99],
    labels=["sem poder", "fraco", "medio", "forte", "suspeito (>0,5)"],
).astype(str)
IV.loc[IV["variavel"] == "property_state", "leitura"] += " (muitas faixas)"

# ---------- 2) FICO x LTV: padronizacao 2012-2017 -> 2022-2023 ------------------------------------
H["cell"] = H["fico_band"] + " | " + H["ltv_band"]
decomp, mix_effect, rate_effect = None, 0.0, 0.0
sm = standardize_mix(H, BASE_ERA, TEST_ERA)
if sm is not None:
    mix_effect, rate_effect = sm["mix_effect"], sm["rate_effect"]
    decomp = pd.DataFrame(
        [
            (f"taxa {BASE_ERA} (base)", sm["base"]),
            (
                f"taxa esperada em {TEST_ERA} se so o PERFIL (mix FICO x LTV) mudasse",
                sm["expected"],
            ),
            (f"taxa observada em {TEST_ERA}", sm["actual"]),
        ],
        columns=["medida", "taxa_24m"],
    )

# ---------- 3) vintage: mix e risco por faixa de FICO ---------------------------------------------
fv = F[F["feature"] == "fico_band"].copy()
first = fv["bucket"].str[0]
fv["grupo"] = np.where(
    first.isin(list("abc")),
    "FICO < 700",
    np.where(
        first.isin(list("de")), "FICO 700-779", np.where(first == "f", "FICO >= 780", "sem FICO")
    ),
)
fvg = fv.groupby(["vintage_year", "grupo"], as_index=False)[["n_loans", "n_defaults"]].sum()
fvg["rate"] = fvg["n_defaults"] / fvg["n_loans"]


def share_by_vintage(feature, buckets):
    d = F[F["feature"] == feature]
    s = d[d["bucket"].isin(buckets)].groupby("vintage_year")["n_loans"].sum()
    t = d.groupby("vintage_year")["n_loans"].sum()
    return (s / t).reindex(t.index).fillna(0)


mix = pd.DataFrame(
    {
        "FICO < 700": share_by_vintage("fico_band", ["a <620", "b 620-659", "c 660-699"]),
        "LTV > 90": share_by_vintage("ltv_band", ["e 91-95", "f >95"]),
        "DTI > 45": share_by_vintage("dti_band", ["e 46-50", "f >50"]),
        "taxa >= 6%": share_by_vintage("rate_band", ["e 6-6.99", "f >=7"]),
    }
)

# ---------- 4) valuation method: proxy de tempo? --------------------------------------------------
vm = F[F["feature"] == "property_valuation_method"]
vmt = vm.groupby("vintage_year")["n_loans"].sum()
vmm = (
    vm[vm["bucket"] == "missing"]
    .groupby("vintage_year")["n_loans"]
    .sum()
    .reindex(vmt.index)
    .fillna(0)
)
VM = pd.DataFrame(
    {"vintage": vmt.index, "loans": vmt.values, "pct_sem_informacao": (vmm / vmt).values}
)
VM["taxa_24m_B"] = (vm.groupby("vintage_year")["n_defaults"].sum() / vmt).values

# ---------- 5) exclusoes ---------------------------------------------------------------------------
X["taxa_24m"] = X["n_defaults_24m"] / X["n_loans"]
X["taxa_alguma_vez"] = X["n_ever_default"] / X["n_loans"]
X["pct_dos_loans"] = X["n_loans"] / X.groupby("check_name")["n_loans"].transform("sum")

# ---------- saidas: csv --------------------------------------------------------------------------
F.to_csv(tables / "eda_features.csv", index=False, lineterminator="\n")
P.round({"share": 6, "default_rate": 6, "lift": 4}).to_csv(
    tables / "eda_feature_pooled.csv", index=False, lineterminator="\n"
)
IV.round({"IV": 5}).to_csv(tables / "eda_iv.csv", index=False, lineterminator="\n")
X.round(6).to_csv(tables / "eda_exclusion_check.csv", index=False, lineterminator="\n")
H.drop(columns="cell").to_csv(tables / "eda_fico_ltv.csv", index=False, lineterminator="\n")

# ---------- figuras --------------------------------------------------------------------------------
top = [v for v in IV["variavel"] if v != "property_state"][:6]
fig, axes = plt.subplots(2, 3, figsize=(13, 7))
for ax, v in zip(axes.ravel(), top, strict=False):
    d = P[P["feature"] == v].sort_values("bucket")
    ax.bar(
        d["bucket"].str.replace(r"^[a-z] ", "", regex=True),
        100 * d["default_rate"],
        color="#4c72b0",
    )
    ax.axhline(100 * overall, color="crimson", lw=1, ls="--")
    ax.set_title(f"{v} (IV {IV.loc[IV['variavel'] == v, 'IV'].iloc[0]:.3f})", fontsize=9)
    ax.tick_params(axis="x", labelrotation=45, labelsize=7)
    ax.set_ylabel("default 24m (%)", fontsize=8)
fig.suptitle("Taxa de default em 24 meses por faixa (linha = media geral)")
fig.tight_layout()
fig.savefig(figs / "eda_default_by_feature.png", dpi=150)
plt.close(fig)

eras_plot = [e for e in ("2004-2008", BASE_ERA, TEST_ERA) if e in set(H["era"])]
if eras_plot:
    fig, axes = plt.subplots(1, len(eras_plot), figsize=(5.2 * len(eras_plot), 4.6), squeeze=False)
    fb, lb = sorted(H["fico_band"].unique()), sorted(H["ltv_band"].unique())
    vmax, mats = 0.0, {}
    for e in eras_plot:
        d = H[H["era"] == e].pivot_table(
            index="fico_band", columns="ltv_band", values=["n_loans", "n_defaults"], aggfunc="sum"
        )
        rate = (d["n_defaults"] / d["n_loans"]).reindex(index=fb, columns=lb) * 100
        mats[e] = rate.where(d["n_loans"].reindex(index=fb, columns=lb) >= MIN_CELL)
        if mats[e].notna().any().any():
            vmax = max(vmax, float(np.nanmax(mats[e].to_numpy(float))))
    for ax, e in zip(axes.ravel(), eras_plot, strict=False):
        m = mats[e]
        cmap = plt.get_cmap("YlOrRd").copy()
        cmap.set_bad("lightgrey")
        ax.imshow(
            np.ma.masked_invalid(m.to_numpy(float)),
            cmap=cmap,
            vmin=0,
            vmax=max(vmax, 1e-9),
            aspect="auto",
        )
        ax.set_xticks(range(len(lb)), [x[2:] for x in lb], fontsize=7, rotation=45)
        ax.set_yticks(range(len(fb)), [x[2:] for x in fb], fontsize=7)
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                if not np.isnan(m.iat[i, j]):
                    ax.text(j, i, f"{m.iat[i, j]:.1f}", ha="center", va="center", fontsize=6)
        ax.set_title(f"Vintages {e}", fontsize=9)
        ax.set_xlabel("LTV")
        ax.set_ylabel("FICO")
    fig.suptitle(f"Default em 24 meses (%) por FICO x LTV (cinza = menos de {MIN_CELL} loans)")
    fig.tight_layout()
    fig.savefig(figs / "eda_fico_ltv_heatmap.png", dpi=150)
    plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
for c in mix.columns:
    axes[0].plot(mix.index, 100 * mix[c], marker="o", ms=3, label=c)
axes[0].set_title("Perfil de originacao por vintage (% dos loans)")
axes[0].legend(fontsize=8)
for g, d in fvg[fvg["n_loans"] >= MIN_POINT].groupby("grupo"):
    d = d.sort_values("vintage_year")
    axes[1].plot(d["vintage_year"], 100 * d["rate"], marker="o", ms=3, label=g)
axes[1].set_title(
    "Default em 24m (definicao B) por vintage e faixa de FICO\n(pontos com menos de 200 loans omitidos)",
    fontsize=10,
)
axes[1].legend(fontsize=8)
for ax in axes:
    ax.grid(alpha=0.3)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("Vintage")
    ax.set_ylim(bottom=0)
fig.tight_layout()
fig.savefig(figs / "eda_vintage_mix_vs_risk.png", dpi=150)
plt.close(fig)

# ---------- documento ------------------------------------------------------------------------------
sel = P[P["feature"].isin(top[:4])].sort_values(["feature", "bucket"])
fmt_p = {"n_loans": n, "n_defaults": n, "share": pc, "default_rate": pc, "lift": f2}
fmt_x = {
    "n_loans": n,
    "n_defaults_24m": n,
    "n_ever_default": n,
    "taxa_24m": pc,
    "taxa_alguma_vez": pc,
    "pct_dos_loans": pc,
}
doc = [
    "# Relatorio de EDA",
    f"\nGerado em {dt.datetime.now():%Y-%m-%d %H:%M} por `uv run poe eda-report` (somente agregados). "
    f"Alvo: `target_24m` (D-002, definicao B). Populacao: `usable_24m`, vintages 1999-2023 "
    f"({n(tot_loans)} loans, {n(tot_def)} defaults, taxa media {pc(overall)}).\n",
    "## 1. Poder discriminatorio (IV univariado)",
    "IV = soma de (%bons - %maus) x WoE por faixa. Leitura usual: < 0,02 sem poder; 0,02-0,1 fraco; 0,1-0,3 medio; "
    "0,3-0,5 forte; > 0,5 suspeito. Calculado sobre todas as vintages juntas (mistura ciclos): serve para ordenar "
    "variaveis, nao para estimar efeitos.\n",
    md(IV, {"IV": f3}),
    "\n![Default por faixa](../reports/figures/eda_default_by_feature.png)\n",
    "## 2. Perfis de risco das 4 variaveis mais fortes",
    md(sel, fmt_p),
    "\n## 3. FICO x LTV por era",
    "\n![FICO x LTV](../reports/figures/eda_fico_ltv_heatmap.png)\n",
    "## 4. Por que 2022-2023 destoam? Perfil (mix) versus risco dentro do perfil",
]
if decomp is not None:
    doc += [
        md(decomp, {"taxa_24m": pc}),
        f"\nEfeito do PERFIL (FICO x LTV): {100 * mix_effect:+.2f} p.p.; efeito RESIDUAL (risco dentro das mesmas "
        f"celulas, assistencia nao marcada, macro): {100 * rate_effect:+.2f} p.p.\n",
    ]
else:
    doc += ["_(eras de base e de teste nao disponiveis nesta base)_\n"]
doc += [
    "![Mix e risco por vintage](../reports/figures/eda_vintage_mix_vs_risk.png)\n",
    "## 5. `property_valuation_method`: proxy de tempo?",
    "Se a ausencia for ~100% ate certa vintage e cair depois, a variavel identifica a EPOCA e vaza tempo no split "
    "por vintage.\n",
    md(VM, {"loans": n, "pct_sem_informacao": pc, "taxa_24m_B": pc}),
    "\n## 6. Calibracao das exclusoes (toda a populacao com janela de 24 meses, incluindo excluidos)",
    "`taxa_alguma_vez` (qualquer idade) e a medida robusta: nos loans com 1o pagamento inconsistente a idade esta "
    "errada e a taxa de 24 meses nao e confiavel.\n",
    md(
        X[
            [
                "check_name",
                "bucket",
                "n_loans",
                "pct_dos_loans",
                "n_defaults_24m",
                "taxa_24m",
                "n_ever_default",
                "taxa_alguma_vez",
            ]
        ],
        fmt_x,
    ),
    "\n## 7. Insights",
    read_manual(
        "docs/eda_insights.md",
        "_(a preencher: crie `docs/eda_insights.md` no formato Observacao, Evidencia, Por que, Implicacao; "
        "ele sera incluido aqui a cada execucao)_",
    ),
]
Path("docs").mkdir(parents=True, exist_ok=True)
Path("docs/eda_report.md").write_text(
    "\n".join(doc).rstrip("\n") + "\n", encoding="utf-8", newline="\n"
)
print("OK: docs/eda_report.md + reports/tables/eda_*.csv + 3 figuras (eda_*.png)")
