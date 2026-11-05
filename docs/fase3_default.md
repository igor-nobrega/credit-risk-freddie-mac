# Fase 3 - Definicao de Default e Target

**Objetivo:** decidir (D-002) o que e "default" com evidencia dos proprios dados, e construir o dataset de PD sem vies.

## O que a fase constroi (schema `gold`)
| Tabela | Granularidade | Publicavel? |
|---|---|---|
| `gold_loan_events` | 1 linha por loan: todos os eventos candidatos (60/90/180+ dias, evento de credito), cura, estado terminal, idade, `upb_at_default` (insumo de EAD) | **Nao** (nivel de emprestimo) |
| `gold_pd_dataset` | 1 linha por loan ao originar: variaveis de originacao + `default_12m/24m` + `observable_12m/24m` | **Nao** |
| `gold_vintage_curves` | vintage x idade x definicao: loans em risco e default cumulativo | Sim (agregado) |
| `gold_default_summary` | por vintage: estados terminais, eventos, curas, modificacoes, observabilidade | Sim (agregado) |

## Convencoes
- **Idade** = meses desde `first_payment_date` (1 = primeiro mes), recalculada das datas (a regra R23 mostra que `loan_age` do arquivo diverge em alguns casos).
- **Defaults candidatos:** `dpd60` (>=2), `dpd90` (>=3 ou REO), `dpd180` (>=6 ou REO), `credit_event` (ZB 02/03/09/15).
- **Definicao A:** `dpd90_or_credit_event` (o que ocorrer primeiro). **Definicao B:** igual a A, mas ignorando meses 90+ sob plano de assistencia (`borrower_assistance_plan` F/R/T), atraso por desastre (`delinquency_due_to_disaster` = Y) ou adiamento (`payment_deferral_flag` C/P), campos populados desde 2014. B responde a forbearance e desastres (ex.: pandemia); a escolha entre A e B e a D-002.
- **Exclusoes:** `excluded_reason` no `gold_pd_dataset`: `first_payment_inconsistent` (1o pagamento fora de 0-8 meses do trimestre do loan_id; modificados e convertidos reiniciam a data) e `default_before_first_payment` (idade < 1). Treino: `excluded_reason is null and observable_24m`.
- **Observabilidade (anti-vies):** `observable_Nm = months_observable >= N`, onde `months_observable` = meses do 1o pagamento ate o corte dos dados. Treine so com `observable_Nm = true`. Incluir loans de janela incompleta apenas quando o desfecho ja e conhecido superestima a taxa de default.
- **Codigo do evento de credito:** `credit_event_code` (02 venda de terceiros, 03 short sale/charge-off, 09 REO, 15 venda de nota) para segmentar o LGD; `zb_code` e o ULTIMO codigo de saldo zero (estado terminal).
- **UPB no default:** `upb_at_default` = saldo no 1o mes 90+ ou, se o evento de credito veio antes, o saldo removido (`zero_balance_removal_upb`).
- **Prepagamento:** loan que liquida (ZB 01) sem default conta como "nao default" (risco competitivo: documentar e testar sensibilidade).

## Como rodar
```powershell
uv run python scripts/setup_tasks.py   # 1 vez: garante todas as tarefas poe no pyproject.toml (idempotente)
uv run poe silver          # reconstroi silver e DQ (inclui as novas regras R25 e R26)
uv run poe gold            # dbt run + dbt test da camada gold
uv run poe default-report  # docs/default_definition_report.md + 2 figuras + CSVs agregados
uv run poe inspect-dq      # exemplos (nivel de emprestimo, SO no terminal) de loans que violam regras do DQ
```

## Se o `dbt test` mostrar WARN em `assert_default_age_positive`
Significa que ha loans com default ANTES do primeiro pagamento (idade < 1). Rode `uv run poe diagnose-age`: ele
mostra quantos sao, por gatilho, codigo do evento, vintage e a idade da primeira linha de cada loan. A saida fica em
`data/tmp/diagnose_default_age.txt`. Decida na D-002 se esses loans ficam, sao ajustados para idade 1 ou saem da amostra.

## Como decidir a D-002 (proposta inicial a validar com os numeros)
1. **Gatilho:** 90+ dias ou REO ou evento de credito, o primeiro que ocorrer. Conferir na secao 4 do relatorio se "so evento de credito" e raro (se for, 90+ dias ja captura quase tudo).
2. **Cura:** conferir a secao 5. Se uma fatia grande dos 90+ volta a ficar em dia, o default "ever 90+" mistura casos de perda real com atrasos passageiros. Opcoes: default absorvente (padrao), ou exigir 90+ persistente / evento de credito (sensibilidade).
3. **Janela:** 24 meses para o scorecard de originacao; 12 meses para PD do ECL.
4. **Amostra:** so `observable_24m`. Conferir na secao 3 quais vintages tem janela completa e quais tem poucos eventos (alerta `< 100 eventos`): elas limitam o split out-of-time.
5. **Validacao de ciclo:** as curvas devem mostrar 2005-2008 bem acima de 2012+. Se nao mostrarem, ha erro no target.

## Template da D-002 (copie para docs/decision_log.md)
```
## D-002 - Definicao de default
- Data: AAAA-MM-DD
- Evidencia: docs/default_definition_report.md (secoes 2-5)
- Gatilho: ...
- Janela de performance: ...
- Cura: ...
- Prepagamento: ...
- Amostra (vintages e observabilidade): ...
- Alternativas descartadas e por que: ...
- Sensibilidade a rodar depois: ...
```
