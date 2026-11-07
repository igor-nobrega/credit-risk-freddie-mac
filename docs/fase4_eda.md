# Fase 4 - EDA e Insights

**Objetivo:** entender onde esta o risco, resolver os pontos em aberto da D-002 e escolher variaveis com evidencia,
publicando somente agregados.

## O que a fase constroi (schema `eda`, todos agregados e publicaveis)
| Tabela | Conteudo |
|---|---|
| `eda_features` | Default em 24m (alvo oficial `target_24m`) por variavel, faixa e vintage (`usable_24m`, vintages <= 2023) |
| `eda_exclusion_check` | Risco por faixa de `first_payment_months` e `first_row_age` em toda a populacao com janela de 24m (inclui excluidos) |
| `eda_fico_ltv` | FICO x LTV por era de originacao |

As faixas ficam em macros (`dbt/macros/eda_bands.sql`), reutilizadas pelos modelos. O teste
`assert_eda_features_partition_population` garante que toda variavel particiona a MESMA populacao.

## Como rodar
```powershell
uv run python scripts/setup_tasks.py   # 1 vez: tarefas eda e eda-report (e gold atualizada)
uv run poe gold                         # reconstroi a gold (agora com first_row_age)
uv run poe eda                          # modelos e testes da EDA
uv run poe eda-report                   # docs/eda_report.md + CSVs agregados + 3 figuras
```

## Perguntas que o relatorio responde
1. **Quais variaveis discriminam?** IV univariado (secao 1) e perfis das 4 mais fortes (secao 2).
2. **FICO x LTV:** onde esta a fronteira de risco, e ela mudou entre eras? (secao 3)
3. **Por que 2022-2023 destoam?** Padronizacao: separa o efeito do PERFIL (mix FICO x LTV) do efeito do RISCO dentro
   das celulas (secao 4). Efeito residual grande aponta para assistencia nao marcada ou macro, nao para o perfil.
4. **`property_valuation_method` e proxy de tempo?** (secao 5) Se a ausencia mudar de ~100% para ~0% numa vintage, a variavel
   identifica a epoca: nao use no scorecard sem tratar.
5. **A regra de exclusao do 1o pagamento esta bem calibrada? E a entrada tardia?** (secao 6) Compare `taxa_alguma_vez` entre as
   faixas: se as faixas 6-8 e >8 tem risco parecido com 0-5, a exclusao e desnecessaria; se forem muito diferentes, e justificada.
   O mesmo vale para `first_row_age` > 3 (loans que entram no dataset depois da originacao: sobreviventes).

## Formato dos insights (`docs/eda_insights.md`, incluido na secao 7 do relatorio)
> **Observacao** -> **Evidencia** (tabela/figura/numero) -> **Por que** (hipotese) -> **Implicacao** (feature, restricao ou decisao)

Escreva 8 a 12. O relatorio inclui esse arquivo a cada execucao, entao o texto nao se perde.
