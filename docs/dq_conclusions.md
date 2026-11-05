> Rascunho gerado a partir dos números do relatório. **Revise e ajuste** antes de publicar.

### Leitura geral
- **A estrutura está íntegra:** 27 arquivos por tabela, 1.350.000 loans e 74.919.968 registros mensais reconciliados sem perda (0 rejeitadas), sem duplicatas na originação nem na performance e sem órfãos.
- **Valores fora de faixa não aparecem** (R02 a R11 sem falhas). O guia da Freddie Mac já marca valores fora do intervalo como "não disponível", então a dificuldade deste dataset é **semântica** (sentinelas, ausência estrutural, censura, evolução do layout) e de **escala**, não de formato.
- **Todas as séries sem evento de saldo zero chegam ao corte dos dados** (R25 = 0): não há loans "sumidos" no meio do período.
- No encerramento de todo loan com saldo zero, o saldo atual é 0 (R17 = 0). O saldo anterior ao evento está em `zero_balance_removal_upb`, a base natural do EAD.

### Problemas encontrados e tratamento
| Achado | Tamanho | Tratamento |
|---|---|---|
| Loans na originação sem nenhuma linha de performance (R14) | 5 | Fora do dataset de PD (`has_perf = false`) |
| Linhas com período posterior ao saldo zero (R18) | 7 linhas | Impacto desprezível; documentado, sem filtro especial |
| Buracos na série mensal (R19) | 195 loans (0,01%) | Mantidos; idade recalculada pelas datas |
| `loan_age` do arquivo diverge da idade recalculada (R23) | 20.508 linhas (0,03%) | Usar sempre a idade recalculada |
| Ano do `loan_id` difere da vintage do arquivo (R12) | 1 loan | Investigar com `uv run poe inspect-dq`; sem impacto no modelo |
| `net_sales_proceeds` positivo (R22) | 72 de 19.638 (0,37%) | Verificar a convenção de sinal na fase de LGD |
| `actual_loss` ausente em evento de crédito (R21) | 1.517 de 21.156 (7,17%) | **Censura no LGD**: esperada nos 3 últimos meses antes do corte; tratar na modelagem |

Há perda realizada para 19.639 eventos de crédito (21.156 − 1.517), o universo disponível para o LGD.

### Variáveis: o que a ausência significa
| Variável | Ausente | Interpretação e decisão |
|---|---|---|
| `vantage_score_4` | 100% | Sem informação no Sample: **removida** do dataset de PD |
| `property_valuation_method` | 77,23% | Hipótese: campo só informado em safras recentes. Se confirmado em `reports/tables/dq_missing_by_vintage.csv`, é um **proxy de tempo** e arrisca vazamento no split out-of-time: não usar no scorecard sem tratar |
| `special_eligibility_program` | 96,96% | Ausência **estrutural** (sem programa especial): virar categoria "nenhum", não imputar |
| `pre_harp_loan_id` | 93,82% | Só existe em refinanciamentos HARP: derivar indicador `is_harp_refi` e descartar o id |
| `msa` | 21,07% | Branco = fora de MSA: categoria "sem MSA" |
| `dti` | 7,07% | Manter com `dti_was_missing`; testar se a ausência é preditiva (hipótese: parte vem de loans HARP) |
| `credit_score` | 0,16% | Manter com `credit_score_was_missing` |

Na performance, a ausência de custos, recuperações e perda (~99,97%) é **estrutural**: esses campos só são preenchidos no encerramento de loans com evento de crédito.

### Implicações para a modelagem
1. Eventos de crédito são raros (21.156 em 1,35 milhão de loans, cerca de 1,6%): a validação out-of-time precisa checar o número de eventos por vintage.
2. A ausência de informação precisa de tratamento explícito (flags e categorias) e **não** de imputação cega.
3. O LGD parte de ~19,6 mil perdas realizadas e precisa lidar com a censura recente.
