# Fase 2 - Silver e Qualidade de Dados

**Objetivo:** transformar a bronze (tudo texto) em tabelas tipadas e confiaveis, **medindo** a sujeira em vez de escondela.

## Contrato da camada silver
| Regra | Como |
|---|---|
| Tipagem segura | `try_cast`: valor invalido vira NULL e e contado em `dq.dq_column_profile` (nunca estoura erro) |
| Sentinela -> NULL | Valores como 9999, 999, 99, 7, `000`, `XX` viram NULL |
| Ausencia e informacao | Para toda variavel com sentinela existe `<col>_was_missing` (boolean): "nao informado" pode ser preditivo |
| Originacao | 1 linha por `loan_id` (mantem o arquivo mais recente; `_n_source_rows` registra quantas existiam) |
| Performance | **nenhuma linha removida**; `dlq_months` (inteiro) e `is_reo` derivados do status de atraso |
| Sem correcao de valores | Fora de faixa NAO e "consertado" na silver: e medido nas regras R02-R24 e tratado depois, com decisao registrada |

## Fonte unica do esquema
Os `.sql` dos modelos sao **gerados** de `src/credit_risk/freddie_schema.py` (`uv run poe gen-sql`).
Um teste garante que o SQL versionado nao diverge do esquema.

## Como rodar
```powershell
uv run poe silver       # dbt run (modelos) e depois dbt test (testes); teste reprovado nao bloqueia a medicao
uv run poe dq-report    # gera docs/data_quality_report.md, reports/tables/dq_*.csv e a figura
```

## Saidas (schemas no warehouse)
- `silver.silver_orig`, `silver.silver_perf`
- `dq.dq_rule_results` (24 regras: n_checked, n_failed, severidade, acao sugerida)
- `dq.dq_column_profile` (brancos, sentinelas, falhas de conversao por coluna)
- `dq.dq_missing_by_vintage` (ausencia por vintage e variavel)

## Testes dbt (invariantes)
`loan_id` nao nulo e unico em `silver_orig`; (`loan_id`, `monthly_reporting_period`) unico em `silver_perf`
(severidade `error`); dominios categoricos (`accepted_values`, severidade `warn`).

## Sugestoes de entradas para o decision_log
- **D-001 Escopo de dados:** Sample, vintages 1999-2025, 27 arquivos; motivo: viabilidade local e mesma estrutura do dataset completo.
- **D-002 Bronze tudo texto:** nenhuma interpretacao antes de medir; linhagem por arquivo.
- **D-003 Sentinelas viram NULL com flag `_was_missing`:** preserva o sinal de "nao informado".
- **D-004 Duplicatas na originacao:** manter o arquivo mais recente (empate dentro do mesmo arquivo e arbitrario; quantificado por R01).
- **D-005 Fora de faixa nao e corrigido na silver:** medido (R02-R12) e decidido na fase de features.
