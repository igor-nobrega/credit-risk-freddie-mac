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
