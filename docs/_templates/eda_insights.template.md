> Rascunho escrito a partir do relatório de EDA executado nos dados reais (versão anterior à exclusão de entrada tardia).
> **Revise e ajuste.** Os números vão mudar um pouco na próxima execução (ver insight 8). Formato: Observação → Evidência → Por quê → Implicação.

### 1. O FICO é o principal discriminador, com gradiente monótono
- **Evidência:** a taxa de default em 24 meses vai de 7,09% (FICO < 620) a 0,21% (≥ 780), um fator de ~34 (lift 6,57 contra 0,20). IV agregado = 1,04.
- **Por quê:** o score resume o histórico de crédito do tomador.
- **Implicação:** variável central do scorecard. Usar faixas monótonas e uma faixa própria para "sem FICO" (0,16% dos loans, risco 1,96%, parecido com a faixa 660-699).

### 2. DTI e LTV elevam o risco, mas as faixas altas se parecem
- **Evidência:** DTI > 50 chega a 3,43% (lift 3,18) com só 3,64% dos loans; LTV > 95 chega a 2,98%. As faixas de LTV 81-90 e 91-95 são praticamente iguais (1,81% e 1,82%).
- **Implicação:** o binning deve agrupar LTV 81-95 e respeitar monotonicidade; o risco só se separa de verdade acima de 95 (loans HARP e de LTV extremo).

### 3. DTI ausente não é aleatório
- **Evidência:** 7,65% dos loans não têm DTI e têm risco de 1,47% (lift 1,36), entre as faixas 41-45 e 46-50.
- **Implicação:** manter "DTI ausente" como categoria própria no WoE, em vez de imputar. O flag `dti_was_missing` já existe na silver.

### 4. A taxa de juros discrimina, mas o IV agregado exagera
- **Evidência:** o risco sobe de 0,23% (taxa < 3%) a 2,28% (≥ 7%) e o IV agregado é 0,525. A taxa embute o preço do risco **e** a época (vintages de 2000, 2006-2008 e 2022-2023 têm taxas altas).
- **Implicação:** decidir por `IV_intra_vintage` e pela razão intra/agregado do relatório novo, não pelo agregado. Se a taxa se confirmar como proxy de época, tratá-la como variável de mercado com cuidado no split temporal.

### 5. Várias variáveis não têm poder
- **Evidência:** `upb_band`, `harp_indicator`, `special_eligibility_program`, `number_of_units`, `occupancy_status`, `first_time_homebuyer_flag` e `prepayment_penalty_flag` têm IV ≤ 0,007, e `io_indicator` tem uma única faixa (constante).
- **Implicação:** candidatas a remoção. O fato de `occupancy_status` não ter poder é contraintuitivo (imóveis de investimento costumam ser mais arriscados): checar por era antes de descartar.

### 6. `property_valuation_method` é um relógio, não uma variável de risco
- **Evidência:** a ausência é 100% de 1999 a 2016, 99,11% em 2017, 96,97% em 2018, 89,11% em 2019 e **0% de 2020 em diante**. O IV de 0,036 é espúrio.
- **Implicação:** excluir do scorecard (D-009 confirmada). O mesmo raciocínio vale para qualquer variável cuja disponibilidade mude no tempo.

### 7. O perfil de originação não explica o excesso de 2022-2023
- **Evidência:** controlando por FICO × LTV, a taxa esperada para 2022-2023 seria 0,51% (base 2012-2017: 0,50%) e a observada é 1,37%. O efeito do perfil é +0,01 p.p. e o residual é **+0,87 p.p.**
- **Por quê (hipóteses):** macro (juros e custos de moradia), assistência não marcada, ou DTI e taxa de juros, que não entraram nessa primeira padronização. A versão nova do relatório controla DTI e taxa de forma aninhada.
- **Implicação:** o scorecard deve manter bom *ranking* nessas safras, mas provavelmente descalibrar. Planejar recalibração por época e monitorar PSI.

### 8. Entrada tardia é viés de sobrevivente
- **Evidência:** loans cuja primeira linha de performance tem idade > 12 (13.703) mostram 24m = 0,12%, contra 1,08% na média, mas "alguma vez" = 3,88%, normal. Os de idade 4 a 12 (12.649) têm a maior taxa "alguma vez": 7,18%.
- **Por quê:** a vida inicial desses empréstimos não foi observada, e um default 90+ só pode ocorrer a partir do 3º ou 4º mês. Quem entra até a idade 3 não perde nenhum default.
- **Implicação:** excluir `first_row_age > 3` do treino (D-010; 26.352 loans, 2,1%).

### 9. A regra do primeiro pagamento é segura
- **Evidência:** os loans com primeiro pagamento > 8 meses após o trimestre do `loan_id` (5.520) têm 24m = 1,29% e "alguma vez" = 3,75%; a faixa 6-8 (1.455) tem 1,10% e 3,02%; o normal (0-5) tem 1,08% e 4,20%.
- **Implicação:** o risco é parecido, então a exclusão não distorce a taxa. Manter a regra 0-8 (D-007 confirmada).

### 10. Os eventos se concentram na crise
- **Evidência:** cerca de 40% dos defaults de 24 meses estão em três vintages (2006: 968, 2007: 2.449, 2008: 1.987, de 13.499 antes das exclusões).
- **Implicação:** o split out-of-time precisa manter a crise no treino, senão o modelo nunca vê estresse. Reportar métricas **por vintage** e nunca usar split aleatório.

### 11. Muitas faixas inflam o IV por ruído
- **Evidência:** `property_state` tem 54 faixas e IV agregado de 0,077. Por vintage (~200 defaults em safras benignas) o ruído amostral esperado passa de 0,2.
- **Implicação:** o relatório novo subtrai esse ruído (IV corrigido). Para estado, preferir agrupamentos por risco (regiões ou clusters) em vez de 54 dummies.

### 12. Canal, número de mutuários e MI são candidatos médios
- **Evidência:** `number_of_borrowers` (IV 0,196), `channel` (0,187) e `mi_band` (0,162).
- **Implicação:** `mi_band` tende a ser colinear com LTV: checar correlação antes de incluir os dois.

## Decisões decorrentes (copie para `docs/decision_log.md`)
- **D-007 (confirmada pela EDA):** manter a exclusão de 1º pagamento fora de 0-8 meses; os loans excluídos têm risco parecido com os demais.
- **D-009 (confirmada):** `property_valuation_method` fora do scorecard (proxy de época); `vantage_score_4` removida.
- **D-010 (nova):** excluir do treino loans com `first_row_age > 3` (entrada tardia, viés de sobrevivente). Já implementado em `excluded_reason = 'late_entry'`.
- **D-011 (nova):** selecionar variáveis por IV corrigido do ruído e por IV intra-vintage, não pelo IV agregado.
