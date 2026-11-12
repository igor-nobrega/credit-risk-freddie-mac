# PROJECT_STATE — credit-risk-freddie-mac

> Documento de continuidade. Resume TUDO que foi decidido, construído, medido e aprendido até a **Fase 4 (EDA)**.
> Leia a seção 1 para retomar. Atualize a seção 12 (log de sessões) ao fim de cada sessão.

## 1. Como retomar ("vamos continuar o projeto")
**Usuário (terminal do VS Code, sem administrador):**
```powershell
cd C:\Users\Igor\Desktop\projetos\20261201_HipotecasAmericanas
git pull --rebase
uv sync --locked
uv run poe doctor        # painel de saúde: [ OK ]/[WARN]/[FAIL], última camada válida e PRÓXIMO PASSO
```
Cole a saída do `doctor` na conversa. Se tudo estiver `OK`, seguimos da etapa indicada em "Próximos passos" (seção 11).

**Assistente (se o ambiente de trabalho tiver sido reiniciado):** o sandbox perde arquivos entre sessões. Reconstrução rápida:
1. `git clone https://github.com/<USUARIO>/credit-risk-freddie-mac` (github.com é acessível pelo sandbox) **ou** extrair `credit-risk_snapshot_fase4b.zip` (anexado pelo usuário);
2. `uv sync --locked` e `uv run poe test` (esperado: todos os testes passam, ~1-3 min);
3. só então continuar. Nunca prometer algo que dependa de arquivos que não estejam no repositório/snapshot.

> Preencha: `<USUARIO>` = seu login do GitHub. URL do repositório: `https://github.com/<USUARIO>/credit-risk-freddie-mac`

## 2. Identidade e ambiente
- **Objetivo:** pipeline de risco de crédito ponta a ponta (Score/PD, LGD, EAD, ECL) com dados REAIS e sujos do Freddie Mac, 100% local e offline, para portfólio no GitHub.
- **Usuário:** Igor. Windows 11, VS Code, terminal PowerShell **sem administrador**. 20 GB de RAM utilizáveis (DuckDB `memory_limit` 12 GB). Downloads em `C:\Downloads\`.
- **Pasta do projeto:** `C:\Users\Igor\Desktop\projetos\20261201_HipotecasAmericanas\` (raiz do repositório; repositório GitHub `credit-risk-freddie-mac`, público).
- **Stack:** Python 3.12 · uv (lockfile universal, 196 pacotes) · DuckDB + Parquet · dbt-core + dbt-duckdb · pandas/polars/pyarrow · matplotlib · scikit-learn/statsmodels/lightgbm/lifelines/optbinning/shap · pytest/ruff/pre-commit/poethepoet · GitHub Actions (Linux + Windows). Quarto ainda NÃO instalado (`winget install --id Posit.Quarto -e`, fase final).
- **Dados:** Freddie Mac Single-Family Loan-Level Dataset, **Sample** (Standard), 27 vintages (1999-2025), 1.350.000 loans, 74.919.968 registros mensais. Layout **Release 47** (jul/2026): originação 31 campos, performance 35, pipe-delimited sem header. (O guia público já mostra Release 48; layout 31/35 conferido.) Corte de performance: **2026-03**.
- **Termos de uso:** não redistribuir dados; só agregados/derivados não comerciais; nada em nível de empréstimo no Git. Dúvidas: clarity@freddiemac.com.

## 3. Arquitetura
```
data/raw/{orig,perf}/*.txt ──ingest──► BRONZE  data/bronze/{orig,perf}/*.parquet  + _log/*.json + rejects/ + views bronze_orig/bronze_perf
        └─(dbt)─► SILVER  silver.silver_orig / silver.silver_perf     (gerados de src/credit_risk/freddie_schema.py: `poe gen-sql`)
        └─(dbt)─► DQ      dq.dq_rule_results (R01-R28) / dq_column_profile / dq_missing_by_vintage
        └─(dbt)─► GOLD    gold.gold_loan_events / gold_pd_dataset (LOCAL, nível de loan) / gold_vintage_curves / gold_default_summary
        └─(dbt)─► EDA     eda.eda_features / eda_exclusion_check / eda_fico_ltv / eda_mix_decomposition   (agregados, publicáveis)
        └─(scripts)─► docs/*_report.md + reports/tables/*.csv + reports/figures/*.png
```
Código: `src/credit_risk/` (config, duck, freddie_schema, ingest, synth, silver_gen, pyproject_tasks, diagnostics, eda_stats, reportlib, doctor) · `scripts/` · `dbt/` (models silver/dq/gold/eda, macros, tests) · `tests/` · `docs/`.

## 4. Comandos (`uv run poe <tarefa>`)
| Tarefa | O que faz |
|---|---|
| `doctor` | Painel de saúde do projeto (usar sempre ao retomar) |
| `check` / `smoke` / `manifest` | Diagnóstico do ambiente / teste do DuckDB / hashes dos arquivos brutos |
| `ingest` | Fase 1: bronze (idempotente; `--force` reingere) |
| `silver` | Fase 2: `dbt run` + `dbt test` de silver e dq (teste reprovado não bloqueia a medição) |
| `gold` | Fase 3: `dbt run` + `dbt test --exclude tag:eda` |
| `eda` | Fase 4: `dbt run` + `dbt test` da camada eda |
| `dq-report` / `default-report` / `eda-report` | Relatórios `docs/*.md` (somente agregados) |
| `inspect-dq` / `diagnose-age` | Exemplos de violações e diagnóstico de idade < 1 (nível de loan: só no terminal) |
| `gen-sql` | Regenera SQL silver/dq a partir do esquema (um teste impede divergência) |
| `lint` / `fmt` / `test` | ruff / ruff format / pytest |
Outros: `scripts/report_bronze.py` (resumo da ingestão) · `scripts/setup_tasks.py` (completa/atualiza as tarefas poe no `pyproject.toml`; **rodar após aplicar qualquer atualização**).
**Ordem de reconstrução completa:** `ingest → silver → gold → eda → dq-report → default-report → eda-report`.

## 5. Decisões (numeração canônica; registrar em `docs/decision_log.md`)
| ID | Decisão |
|---|---|
| D-001 | Escopo: Sample, vintages 1999-2025 (27 arquivos). |
| **D-002** | **Default (alvo oficial = definição B), CONFIRMADA pelo usuário.** Primeiro mês com (1) 90+ dias de atraso (ou REO) **fora** de plano de assistência (`borrower_assistance_plan` F/R/T), desastre (`delinquency_due_to_disaster`=Y) ou adiamento (`payment_deferral_flag` C/P); ou (2) evento de crédito (saldo zero 02, 03, 09, 15). Absorvente. Janela 24 meses (scorecard) e 12 meses (ECL), idade = meses desde o 1º pagamento. Prepagamento sem default = não default. Treino: `usable_24m` e vintages 1999-2023 (2024 parcial = só monitoramento; 2025 sem janela). Detalhes e evidências: `docs/default_decision.md`. |
| D-003 | Bronze tudo texto + linhagem + rejeitados + reconciliação (linhas = carregadas + rejeitadas). |
| D-004 | Sentinelas → NULL com flag `*_was_missing` (ausência é informação). |
| D-005 | Duplicatas na originação: manter arquivo mais recente (nenhuma encontrada). |
| D-006 | Valores fora de faixa não são corrigidos na silver; são medidos (R02-R11: 0 falhas). |
| D-007 | Exclusões do dataset de PD (`excluded_reason`): 5 loans sem performance; 5.628 (0,42%) com 1º pagamento fora de 0-8 meses do trimestre do `loan_id` (modificados/convertidos reiniciam a data); os 9 loans com default em idade < 1 estão dentro desse grupo. **Confirmada pela EDA**: loans excluídos (>8 meses, 5.520) têm risco parecido (24m 1,29% / alguma vez 3,75% vs 1,08% / 4,20%); a faixa 6-8 (1.455) é mantida. |
| D-008 | Observabilidade: `usable_Nm` exige `months_observable >= N` (janela completa até o corte). Incluir só desfechos já conhecidos superestima a taxa. |
| D-009 | Variáveis: `vantage_score_4` removida (100% sentinela); `property_valuation_method` (77% sentinela) suspeita de proxy de tempo → não usar sem tratar; `special_eligibility_program`/`pre_harp_loan_id` = ausência estrutural (virar categoria/indicador, sem imputar). **EDA confirmou:** `property_valuation_method` é 100% ausente até 2016 e 0% de 2020 em diante (relógio, não risco). |
| D-010 | **Entrada tardia:** excluir do treino loans com `first_row_age > 3` (`excluded_reason='late_entry'`, 26.352 loans, ~2,1%). Racional: a vida inicial não foi observada e um 90+ só ocorre a partir do ~3º-4º mês; a taxa de 24m desses loans é subestimada (idade > 12: 0,12% vs 1,08% média). |
| D-011 | **Seleção de variáveis** por IV corrigido do ruído amostral e por **IV intra-vintage** (não pelo IV agregado, inflado por proxies de época como taxa de juros). |

## 6. Fatos medidos nos dados reais (agregados)
- **Ingestão:** 27+27 arquivos, 1.350.000 / 74.919.968 linhas, 0 rejeitadas, 0 duplicatas, 0 órfãos. Estados terminais: ativo 25,38% (342.587) · prepago 72,31% · evento de crédito 1,57% (21.156) · outra remoção (ZB 16/96) 0,74%.
- **DQ (28 regras):** valores fora de faixa 0 (o guia já marca "não disponível"); problemas pequenos: 5 loans sem performance (R14), 7 linhas pós-encerramento (R18), 195 loans com buraco na série (R19), 20.508 linhas com `loan_age` divergente (R23, 0,03%), 72 `net_sales_proceeds` positivos (R22), 1 loan com ano do `loan_id` ≠ vintage (R12), R25/R26 = 0. **Dificuldade real do dataset = semântica e escala, não formato** (dizer isso no README).
- **LGD:** 19.639 perdas realizadas (de 21.156 eventos de crédito); 1.517 (7,17%) sem `actual_loss` = censura recente. No encerramento `current_actual_upb` = 0; saldo anterior em `zero_balance_removal_upb`.
- **Ciclo (24m, definição B):** 2007 = 4,90% · 2008 = 3,97% · 2012-2015 = 0,43-0,57% · eventos por vintage 175 (2020) a 2.449 (2007), todas ≥100 em 1999-2023.
- **Distorção da definição A (qualquer 90+):** vintage 2019 = 4,58% (A) vs 0,45% (B); 2018: 2,56% vs 0,59%; 2020: 1,61% vs 0,35%. 91,7% dos loans de 2019 que chegaram a 90+ tiveram assistência/desastre/adiamento. Cura após 90+ (A): 65,17%. Só 0,21% dos defaults têm evento de crédito sem 90+ prévio.
- **2022/2023:** continuam altos na B (1,30% / 1,45%; 2024 parcial 1,76%) vs 0,35-0,61% em 2012-2021. **EDA:** o perfil FICO×LTV não explica (esperado 0,51% vs observado 1,37%; efeito perfil +0,01 p.p., residual +0,87 p.p.). A v6 do relatório controla também DTI e taxa (decomposição aninhada) — resultado ainda não visto.
- **Idade:** primeira linha de performance com idade 0 em 87,44% dos loans; 8,18% idade 1; 2,42% 2-3; 0,94% 4-12; 1,02% > 12 (entrada tardia: possível viés de sobrevivente).
- **EDA (dados reais, antes da exclusão de entrada tardia):** 1.244.442 loans `usable_24m` (1999-2023), 13.428 defaults, taxa 1,08%. FICO: 7,09% (<620) → 0,21% (≥780), IV agregado 1,04. Taxa de juros IV agregado 0,525 (suspeita de proxy de época). LTV 0,256, DTI 0,250, nº de mutuários 0,196, canal 0,187, MI 0,162, estado 0,077 (54 faixas), `property_valuation_method` 0,036 (espúrio). Sem poder (IV ≤ 0,007): upb, HARP, special program, unidades, ocupação, primeira casa, penalidade, IO (constante). DTI ausente (7,65%): risco 1,47%. ~40% dos defaults em 3 vintages (2006-2008).
- **Entrada tardia (EDA):** `first_row_age` ≤ 0: 87,0% dos loans (24m 1,10%); 1: 8,4% (0,94%); 2-3: 2,5% (1,29%); 4-12: 1,0% (1,19%; "alguma vez" 7,18%); > 12: 1,1% (**0,12%**; "alguma vez" 3,88%).
- **Modificações:** 1,36% dos loans; 26,3% dos defaults (A) foram modificados.
- **Guia (Release 47/48):** campos de assistência/desastre só existem desde 2014; `first_payment_date` é reiniciado em modificados/convertidos; performance começa na aquisição pela Freddie; `Actual Loss` nulo para liquidados nos 3 meses antes do corte; status `00` pode ser "em dia" ou "ciclo antes do 1º pagamento" até set/2025.

## 7. Estado por fase
| Fase | Entrega | Status |
|---|---|---|
| 0 | Ambiente (uv, DuckDB, dbt, CI, hooks), GitHub sincronizado | ✅ concluída |
| 1 | Bronze (ingestão, reconciliação, `report_bronze`) | ✅ concluída (real) |
| 2 | Silver + 28 regras de DQ + relatório | ✅ concluída (real) |
| 3 | Gold (eventos, curvas, dataset de PD), D-002 | ✅ concluída (real); D-002 confirmada |
| 4 | EDA (modelos `eda`, relatório, IV, padronização 2022-2023, calibração de exclusões) | ✅ executada nos dados reais pelo usuário (v5); relatório analisado |
| 4b | Refinamentos pós-EDA: exclusão `late_entry` (D-010), IV corrigido + intra-vintage + por era, decomposição aninhada 2022-2023, `docs/eda_insights.md` (rascunho) | 🟡 **construído e testado (61 testes, dados sintéticos); aguardando o usuário aplicar o snapshot `fase4b`, rodar `gold → eda → eda-report` e enviar o relatório novo** |
| 5-9 | Scorecard, PD alternativo, LGD, EAD, ECL, relatório final | ⏳ |
Testes: 61 (dados sintéticos). Tags planejadas: `v0.1-bronze`, `v0.2-silver-dq`, `v0.3-default`, `v0.4-eda` (o `doctor` mostra a última tag existente).

## 8. Convenções de qualidade (o que o usuário exige)
- **Nunca entregar a primeira versão:** revisar, testar, reiterar. Verificar duas vezes; prever entraves.
- Toda entrega relevante vem com testes. **Oráculo independente** em Python sobre dados **sintéticos** (`synth.py`) com asserts de cobertura (para o teste não passar "no vazio"). Simular o estado do usuário (aplicar o pacote sobre um clone limpo) antes de entregar.
- Relatórios **recusam rodar** sobre camada desatualizada (mensagem com o comando de correção) e trazem selo de versão ("Layout v3").
- Textos escritos à mão ficam em arquivos próprios incluídos pelos relatórios (não se perdem na regeneração): `docs/dq_conclusions.md`, `docs/default_decision.md`, `docs/eda_insights.md`.
- Somente agregados vão ao GitHub; `data/` é ignorada; hook bloqueia arquivos > 1 MB.
- Resposta sempre em **português**, passo a passo em PowerShell no terminal do VS Code, com "o que esperar" e "o que me mandar".

## 9. Armadilhas já resolvidas (não repetir)
- `poe sequence`: itens precisam ser `{ cmd = "..." }`; strings soltas são referências a tarefas e **quebram todas as tarefas**. Use `setup_tasks.py`, nunca edição manual.
- `dbt test --select gold` puxa testes singulares que referenciam modelos gold: isolar com `tags` e `--exclude tag:eda`. Dentro do pytest, rodar dbt em **subprocesso** (a conexão em processo trava o `.duckdb`).
- DuckDB: um escritor por arquivo; notebooks devem usar `connect(read_only=True)` e fechar a conexão antes de rodar dbt. `try_cast`/`try_strptime` (nunca `CAST` em dado sujo); concatenação com `||` (o `concat()` ignora NULL).
- Hooks do pre-commit: relatórios gerados devem terminar com UM `\n`; `read_text` converte CRLF → ler com `newline=""` ao editar arquivos do usuário.
- Windows: rodar sem administrador (pastas de temp do pytest viram "Acesso negado"); `Expand-Archive -Force` com caminho `C:\Downloads\...`; OneDrive não pode sincronizar o projeto; `.vscode/settings.json` do usuário pode ter ajustes próprios (`git.useEditorAsCommitInput`).
- Sandbox do assistente: shell é `sh` (sem `time`, sem expansão `{a,b}`, sem `PIPESTATUS`); arquivos são perdidos entre sessões → manter tudo no repositório/zips.
- Geradores de relatório precisam criar `docs/`/`reports/` (clone novo); figuras: eixos inteiros, esconder pontos com poucos loans.

## 10. Riscos e dívida técnica conhecidos
- Tudo foi testado em **Linux com dados sintéticos**; o comportamento no Windows foi validado apenas pelo usuário em etapas anteriores e pelo CI (primeiro resultado do CI no Windows ainda não confirmado aqui).
- Tempos em dados reais são estimativas; `gold`/`eda` levam minutos.
- A regra de exclusão do 1º pagamento (0-8 meses) e a política para entrada tardia (idade da 1ª linha > 3) dependem da EDA seção 6.
- README público ainda com placeholders; `docs/README_proposta.md` traz versão atualizada com resultados reais.
- Quarto/GitHub Pages: pendente (fase final).

## 11. Próximos passos
1. **Usuário:** aplicar o snapshot `fase4b` (`docs/COMO_APLICAR_SNAPSHOT.md`), `uv run poe doctor`, depois `gold → eda → eda-report` e colar o `docs/eda_report.md` novo. Copiar `docs/eda_insights.md` (já no snapshot como rascunho só se não existir; ver `docs/_templates/`) e revisar.
2. **Juntos (com o relatório novo):** ler IV intra-vintage (taxa de juros é proxy de época?), a decomposição aninhada de 2022-2023 (DTI e taxa explicam?), confirmar D-010 com os números pós-exclusão; finalizar `eda_insights.md`.
3. **Fase 5 — Scorecard de PD** (alvo `target_24m`, amostra `usable_24m`, vintages 1999-2023): split **out-of-time por vintage** com a crise no treino (proposta: treino 1999-2015, validação 2016-2019, OOT 2020-2023; 2024 só monitoramento); binning (optbinning) e WoE; seleção por IV corrigido/intra-vintage (D-011); regressão logística; escala em pontos (base 600, PDO 20, odds 50:1); KS/Gini/AUC **por vintage**, calibração (esperada que degrade em 2022-2023: recalibrar por época), PSI; sensibilidades (definição A, 180+, só evento de crédito, janela 12m); *model card*.
4. **Fase 6:** GBM (LightGBM) e/ou modelo de sobrevivência (tempo discreto/Cox) vs scorecard; SHAP.
5. **Fase 7 — LGD:** perda realizada descontada, modelo em dois estágios (P(perda>0) × severidade), censura (7,17%), segmentação por `credit_event_code`.
6. **Fase 8 — EAD:** `upb_at_default`/`zero_balance_removal_upb` (amortizante; CCF não se aplica).
7. **Fase 9 — ECL e fecho:** ECL = PD × LGD × EAD, PSI, backtest, overlay macro (séries FRED baixadas manualmente), relatório Quarto + GitHub Pages, README final.

## 12. Log de sessões
- Sessões 1-N (até 2026-11): Fases 0-4 construídas; ver `git log` e tags. Este documento foi criado ao compactar o projeto antes de enviar os resultados da EDA.
- Sessão de refinamento pós-EDA: relatório de EDA real analisado (12 insights); implementados `late_entry`, IV corrigido do ruído (validado por simulação), IV intra-vintage/por era, `eda_mix_decomposition` (validado contra oráculo em Python) e `docs/eda_insights.md`. Snapshot `fase4b`.
