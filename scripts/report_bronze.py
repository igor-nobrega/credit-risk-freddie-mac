"""Resumo da ingestao bronze a partir dos logs em disco (sobrevive a limpar o terminal).

Uso:  uv run python scripts/report_bronze.py
Saida: imprime e salva em data/tmp/bronze_report.txt (pronto para copiar e colar).
"""

import collections
import json

from credit_risk import config
from credit_risk.ingest import SCHEMAS

out: list[str] = []


def say(line: str = "") -> None:
    out.append(line)
    print(line)


def first_line_fields(path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return f.readline().rstrip("\r\n").count("|") + 1


say("=== 1. ARQUIVOS BRUTOS: campos na primeira linha ===")
for kind, cols in SCHEMAS.items():
    files = sorted((config.RAW_DIR / kind).glob("*.txt"))
    counts = collections.Counter(first_line_fields(p) for p in files)
    say(
        f"{kind}: {len(files)} arquivo(s) | esperado {len(cols)} campos | encontrado {dict(counts)}"
    )
    for p in files:
        n = first_line_fields(p)
        if n != len(cols):
            say(f"   DIVERGE: {p.name} tem {n} campos")

logs = [
    json.loads(p.read_text(encoding="utf-8"))
    for p in sorted((config.BRONZE_DIR / "_log").glob("*.json"))
]
say()
say("=== 2. INGESTAO BRONZE ===")
if not logs:
    say("Nenhum log encontrado. Rode: uv run poe ingest")
else:
    for kind in SCHEMAS:
        ls = [x for x in logs if x["kind"] == kind]
        st = collections.Counter(x["status"] for x in ls)
        say(
            f"{kind}: {len(ls)} arquivo(s) | linhas={sum(x['lines_nonblank'] for x in ls):,} | "
            f"carregadas={sum(x['rows_loaded'] for x in ls):,} | "
            f"rejeitadas={sum(x['rows_rejected'] for x in ls):,} | status={dict(st)}"
        )
    say()
    say("=== 3. POR ARQUIVO ===")
    say(
        f"{'tipo':<5}{'vintage':<9}{'linhas':>12}{'carregadas':>12}{'rejeit.':>9}{'%campos_ok':>12}  status"
    )
    for x in sorted(logs, key=lambda r: (r["kind"], r["vintage"])):
        say(
            f"{x['kind']:<5}{x['vintage']:<9}{x['lines_nonblank']:>12,}{x['rows_loaded']:>12,}"
            f"{x['rows_rejected']:>9,}{x['pct_expected_fields']:>12.4f}  {x['status']}"
        )
    say()
    say("=== 4. PROBLEMAS ===")
    bad = [x for x in logs if x["status"] not in ("OK", "SKIPPED")]
    warn = [x for x in logs if x["status"] in ("OK", "SKIPPED") and x["pct_expected_fields"] < 99.9]
    for x in bad:
        say(f"[{x['status']}] {x['kind']}:{x['file']}")
        say(f"    histograma de campos: {x['field_histogram']}")
        say(f"    detalhe: {x['detail']}")
    for x in warn:
        say(
            f"[AVISO] {x['kind']}:{x['file']} com {100 - x['pct_expected_fields']:.4f}% de linhas malformadas"
        )
    if not bad and not warn:
        say("Nenhum.")
    v = {k: {x["vintage"] for x in logs if x["kind"] == k} for k in SCHEMAS}
    if v["orig"] != v["perf"]:
        say(
            f"[AVISO] vintages sem par: so em orig={sorted(v['orig'] - v['perf'])} so em perf={sorted(v['perf'] - v['orig'])}"
        )
    say()
    vs = sorted(v["orig"] | v["perf"])
    say(
        f"RESUMO: vintages {vs[0]}..{vs[-1]} ({len(vs)}) | {len(bad)} arquivo(s) com problema | {len(warn)} aviso(s)"
    )

report = config.TMP_DIR / "bronze_report.txt"
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"\n(salvo em {report})")
