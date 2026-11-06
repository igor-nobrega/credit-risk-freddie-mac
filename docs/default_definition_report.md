# Relatorio de Definicao de Default

Gerado em 2026-11-06 06:38 por `uv run poe default-report` (somente agregados). **Layout v3: definicoes A e B, assistencia e exclusoes.**
Corte de dados (ultimo periodo de performance): **2026-03**. Idade = meses desde o primeiro pagamento.

## 1. Estados terminais (todas as vintages)
| estado_terminal | loans | pct |
|---|---|---|
| ativo no corte (censurado) | 342.587 | 25.38% |
| liquidado: prepago ou vencido (ZB 01) | 976.210 | 72.31% |
| liquidado: evento de credito (ZB 02/03/09/15) | 21.156 | 1.57% |
| liquidado: outra remocao (ZB 16/96) | 10.042 | 0.74% |

## 2. Candidatos a default por vintage (vida inteira, % dos loans)
Vintages recentes ainda estao censuradas: as taxas delas vao subir com o tempo.

| vintage | loans | dpd60 | dpd90 | dpd180 | evento_credito | dpd90_ou_evento_A | B_sem_assistencia |
|---|---|---|---|---|---|---|---|
| 1999 | 50.000 | 6.55% | 3.46% | 1.93% | 0.94% | 3.46% | 3.44% |
| 2000 | 50.000 | 6.67% | 3.50% | 2.20% | 1.31% | 3.50% | 3.49% |
| 2001 | 50.000 | 5.80% | 3.23% | 1.98% | 1.21% | 3.24% | 3.21% |
| 2002 | 50.000 | 5.57% | 3.40% | 2.31% | 1.34% | 3.40% | 3.34% |
| 2003 | 50.000 | 6.00% | 4.07% | 2.78% | 1.46% | 4.07% | 3.98% |
| 2004 | 50.000 | 9.70% | 7.10% | 5.20% | 3.09% | 7.11% | 6.92% |
| 2005 | 50.000 | 13.69% | 11.00% | 8.58% | 5.70% | 11.03% | 10.85% |
| 2006 | 50.000 | 16.85% | 14.33% | 11.73% | 8.14% | 14.43% | 14.22% |
| 2007 | 50.000 | 18.98% | 16.49% | 13.48% | 8.97% | 16.53% | 16.23% |
| 2008 | 50.000 | 11.26% | 9.32% | 7.23% | 4.27% | 9.34% | 9.10% |
| 2009 | 50.000 | 4.26% | 3.19% | 2.21% | 1.09% | 3.21% | 2.74% |
| 2010 | 50.000 | 4.30% | 3.24% | 2.13% | 1.00% | 3.26% | 2.70% |
| 2011 | 50.000 | 4.24% | 3.09% | 2.00% | 0.76% | 3.09% | 2.23% |
| 2012 | 50.000 | 4.60% | 3.43% | 2.20% | 0.76% | 3.44% | 2.12% |
| 2013 | 50.000 | 5.33% | 3.82% | 2.34% | 0.62% | 3.82% | 2.25% |
| 2014 | 50.000 | 5.40% | 3.87% | 2.37% | 0.42% | 3.87% | 2.13% |
| 2015 | 50.000 | 5.44% | 4.10% | 2.44% | 0.27% | 4.10% | 1.83% |
| 2016 | 50.000 | 6.30% | 4.73% | 2.75% | 0.19% | 4.73% | 1.66% |
| 2017 | 50.000 | 7.49% | 5.83% | 3.63% | 0.20% | 5.83% | 2.09% |
| 2018 | 50.000 | 6.88% | 5.42% | 3.46% | 0.14% | 5.42% | 1.72% |
| 2019 | 50.000 | 6.99% | 5.57% | 3.40% | 0.10% | 5.57% | 1.45% |
| 2020 | 50.000 | 3.13% | 2.26% | 1.29% | 0.05% | 2.26% | 0.89% |
| 2021 | 50.000 | 3.06% | 2.01% | 1.00% | 0.05% | 2.01% | 1.39% |
| 2022 | 50.000 | 5.15% | 3.49% | 1.69% | 0.12% | 3.49% | 2.76% |
| 2023 | 50.000 | 3.56% | 2.43% | 1.19% | 0.10% | 2.43% | 2.03% |
| 2024 | 50.000 | 1.89% | 1.23% | 0.49% | 0.02% | 1.23% | 1.01% |
| 2025 | 49.995 | 0.37% | 0.14% | 0.04% | 0.00% | 0.14% | 0.11% |

![Sensibilidade a definicao](../reports/figures/default_definitions_compare.png)

## 3. Taxa de default em 24 meses: A (90+ dias ou evento de credito) vs B (A sem atraso sob assistencia)
A = qualquer mes 90+ conta. B ignora meses 90+ sob plano de assistencia (forbearance/repayment/trial), atraso por desastre ou adiamento de pagamento (campos populados desde 2014).

| vintage | loans_obs_24m | eventos_A | taxa_A | eventos_B | taxa_B | alerta |
|---|---|---|---|---|---|---|
| 1999 | 50.000 | 446 | 0.89% | 446 | 0.89% |  |
| 2000 | 50.000 | 760 | 1.52% | 760 | 1.52% |  |
| 2001 | 50.000 | 560 | 1.12% | 560 | 1.12% |  |
| 2002 | 50.000 | 437 | 0.87% | 437 | 0.87% |  |
| 2003 | 50.000 | 216 | 0.43% | 216 | 0.43% |  |
| 2004 | 50.000 | 395 | 0.79% | 395 | 0.79% |  |
| 2005 | 50.000 | 526 | 1.05% | 526 | 1.05% |  |
| 2006 | 50.000 | 968 | 1.94% | 968 | 1.94% |  |
| 2007 | 50.000 | 2.449 | 4.90% | 2.449 | 4.90% |  |
| 2008 | 50.000 | 1.988 | 3.98% | 1.987 | 3.97% |  |
| 2009 | 50.000 | 317 | 0.63% | 317 | 0.63% |  |
| 2010 | 50.000 | 343 | 0.69% | 343 | 0.69% |  |
| 2011 | 50.000 | 316 | 0.63% | 316 | 0.63% |  |
| 2012 | 50.000 | 284 | 0.57% | 281 | 0.56% |  |
| 2013 | 50.000 | 234 | 0.47% | 227 | 0.45% |  |
| 2014 | 50.000 | 247 | 0.49% | 236 | 0.47% |  |
| 2015 | 50.000 | 253 | 0.51% | 213 | 0.43% |  |
| 2016 | 50.000 | 330 | 0.66% | 235 | 0.47% |  |
| 2017 | 50.000 | 397 | 0.79% | 306 | 0.61% |  |
| 2018 | 50.000 | 1.279 | 2.56% | 295 | 0.59% |  |
| 2019 | 50.000 | 2.292 | 4.58% | 225 | 0.45% |  |
| 2020 | 50.000 | 807 | 1.61% | 175 | 0.35% |  |
| 2021 | 50.000 | 456 | 0.91% | 215 | 0.43% |  |
| 2022 | 49.998 | 908 | 1.82% | 648 | 1.30% |  |
| 2023 | 49.964 | 886 | 1.77% | 723 | 1.45% |  |
| 2024 | 7.479 | 161 | 2.15% | 132 | 1.76% |  |
| 2025 | 0 | 0 |  | 0 |  | sem janela de 24m |

![Curvas por vintage](../reports/figures/vintage_default_curves.png)

### 3b. Loans que chegaram a 90+ dias e tiveram assistencia/desastre/adiamento no periodo
| vintage | loans_90mais | com_assistencia | pct_com_assistencia |
|---|---|---|---|
| 1999 | 1.731 | 79 | 4.56% |
| 2000 | 1.748 | 70 | 4.00% |
| 2001 | 1.617 | 121 | 7.48% |
| 2002 | 1.699 | 204 | 12.01% |
| 2003 | 2.033 | 360 | 17.71% |
| 2004 | 3.551 | 628 | 17.69% |
| 2005 | 5.500 | 863 | 15.69% |
| 2006 | 7.166 | 1.064 | 14.85% |
| 2007 | 8.244 | 1.339 | 16.24% |
| 2008 | 4.658 | 841 | 18.05% |
| 2009 | 1.593 | 635 | 39.86% |
| 2010 | 1.621 | 734 | 45.28% |
| 2011 | 1.544 | 896 | 58.03% |
| 2012 | 1.714 | 1.129 | 65.87% |
| 2013 | 1.909 | 1.349 | 70.67% |
| 2014 | 1.936 | 1.479 | 76.39% |
| 2015 | 2.050 | 1.691 | 82.49% |
| 2016 | 2.367 | 2.104 | 88.89% |
| 2017 | 2.916 | 2.600 | 89.16% |
| 2018 | 2.708 | 2.469 | 91.17% |
| 2019 | 2.786 | 2.556 | 91.74% |
| 2020 | 1.128 | 949 | 84.13% |
| 2021 | 1.004 | 729 | 72.61% |
| 2022 | 1.747 | 1.271 | 72.75% |
| 2023 | 1.213 | 812 | 66.94% |
| 2024 | 615 | 370 | 60.16% |
| 2025 | 71 | 32 | 45.07% |

Os campos de assistencia e desastre so existem desde 2014 e so marcam meses 90+ ocorridos de 2014 em diante: vintages antigas (1999-2008) tem percentuais menores porque a maior parte dos atrasos delas veio antes.

## 4. Gatilhos dos defaults
| gatilho | loans | pct_dos_defaults |
|---|---|---|
| so 90+ dias (sem evento de credito) | 45.855 | 68.43% |
| so evento de credito (sem 90+ previo) | 142 | 0.21% |
| ambos | 21.014 | 31.36% |

## 5. Curas (loans que chegaram a 90+ dias)
| grupo | loans | pct_dos_90plus |
|---|---|---|
| chegaram a 90+ dias | 66.869 | 100.00% |
| voltaram a ficar em dia depois (cura) | 43.576 | 65.17% |
| 90+ e depois prepagaram (sem evento de credito) | 23.449 | 35.07% |

## 6. Modificacoes
| grupo | loans | pct |
|---|---|---|
| loans modificados em algum momento | 18.359 | 1.36% |
| defaults que foram modificados | 17.626 | 26.30% |

## 7. Exclusoes da amostra de PD (coluna `excluded_reason` do `gold_pd_dataset`)
| motivo | loans | defaults_entre_eles | pct_dos_loans |
|---|---|---|---|
| sem nenhuma linha de performance | 5 | 0 | 0.00% |
| 1o pagamento incompativel com o loan_id | 5.628 | 221 | 0.42% |
| default antes do 1o pagamento (idade < 1), nao explicado acima | 0 | 0 | 0.00% |

## 8. Prontidao para LGD
Eventos de credito com `actual_loss` ausente (regra R21): 1.517 de 21.156 (7.17%). Esperado nos 3 ultimos meses antes do corte e em defeitos; tratar como censura.

## 9. Decisao (D-002)
> **D-002, proposta v1.** Confirme ou ajuste antes de publicar. A evidência está nas seções 2 a 7 deste relatório.

### Decisão
- **Evento de default (alvo oficial, "definição B"):** o primeiro mês em que ocorrer qualquer um dos dois:
  1. 90 ou mais dias de atraso (ou REO) **fora** de plano de assistência (forbearance, repayment ou trial), de atraso por desastre e de adiamento de pagamento;
  2. evento de crédito: saldo zero com código 02, 03, 09 ou 15.
- **Absorvente** para o PD: uma cura posterior não desfaz o evento.
- **Janela:** 24 meses para o scorecard de originação e 12 meses para o PD do ECL, contados a partir do primeiro pagamento.
- **Prepagamento sem default** conta como "não default" (risco competitivo). A sensibilidade a esse tratamento fica para a modelagem.
- **Amostra de treino e validação:** `usable_24m` (janela completa até o corte e nenhuma exclusão), vintages 1999 a 2023. A vintage 2024 tem janela completa em apenas ~15% dos loans (7.479 de 50.000) e entra só como monitoramento. A 2025 não tem janela de 24 meses.
- **Exclusões:** 5 loans sem performance e 5.628 (0,42%) com primeiro pagamento incompatível com o trimestre do `loan_id` (empréstimos modificados ou convertidos reiniciam essa data). Os 9 loans com default em idade menor que 1 estão dentro desse segundo grupo.

### Evidência
| Observação | Números |
|---|---|
| O ciclo de crédito aparece e a definição B o preserva | 24m: 2007 = 4,90% (A e B); 2008 = 3,98% (A) e 3,97% (B); 2012 a 2015 entre 0,43% e 0,57% |
| A definição A (qualquer 90+) é distorcida por forbearance e desastres | 24m na vintage 2019: A = 4,58% (2.292 eventos) contra B = 0,45% (225 eventos); em 2018: 2,56% contra 0,59%; em 2020: 1,61% contra 0,35% |
| A distorção é de assistência, não de perda | Em 2019, 91,7% dos loans que chegaram a 90+ dias tiveram assistência, desastre ou adiamento; só 0,10% tiveram evento de crédito |
| Eventos suficientes em todas as vintages do treino | B tem de 175 (2020) a 2.449 (2007) eventos em 24 meses nas vintages 1999 a 2023 |
| 90+ dias quase sempre precede o evento de crédito | Só 0,21% dos defaults têm evento de crédito sem 90+ prévio (definição A) |

### Por que B e não A
A mistura crise de crédito com moratórias e desastres: faz a vintage 2019 parecer pior que a de 2008, e um modelo treinado nela aprenderia o efeito de planos de assistência, não risco de crédito. A B corrige isso sem perder o sinal da crise de 2007 e 2008, em que o campo de assistência ainda não existia e, portanto, A e B coincidem.

### Alternativas descartadas
- **A (qualquer 90+):** distorção descrita acima. Fica como sensibilidade.
- **180+ dias:** ainda carrega o efeito da assistência (3,40% de 180+ na vintage 2019, contra 0,10% de evento de crédito).
- **Só evento de crédito:** quase nenhum evento nas vintages recentes (0,10% na vintage 2019) e viés de censura pela demora da liquidação.

### Riscos e pontos em aberto
1. **Vintages 2022 e 2023 (B = 1,30% e 1,45%) e 2024 parcial (1,76%) ainda estão acima de 2012 a 2021 (0,35% a 0,61%).** Pode ser deterioração real ou assistência não marcada. Investigar na EDA por perfil de originação (FICO, LTV, DTI, taxa) e por estado.
2. **Os campos de assistência só existem desde 2014:** antes disso, B coincide com A. Isso vale para a crise de 2007 e 2008.
3. **A regra de primeiro pagamento (0 a 8 meses após o trimestre do `loan_id`) exclui 5.628 loans.** Calibrar com a distribuição de `uv run poe diagnose-age` (seção H) e conferir se a taxa de default dos excluídos difere da amostra.
4. **Censura:** 25,4% dos loans estão ativos no corte, e as vintages recentes ainda vão acumular eventos.

### Sensibilidades a rodar na modelagem
Definição A, 180+ dias, só evento de crédito, janela de 12 meses e a amostra sem as exclusões.
