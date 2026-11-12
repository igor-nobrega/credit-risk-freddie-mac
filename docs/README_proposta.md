# Risco de Crédito Ponta a Ponta com Dados Reais do Freddie Mac

> **Status:** Fases 0 a 4 concluídas (ingestão, qualidade de dados, definição de default e EDA). Próxima: scorecard de PD.

Pipeline completo de risco de crédito (Score, PD, LGD, EAD e ECL) sobre o **Freddie Mac Single-Family Loan-Level Dataset**:
arquivos pipe-delimited sem header, valores sentinela, eventos de término codificados, perdas realizadas e censura.
Roda **100% local e offline** (DuckDB + Parquet + dbt), sem cotas de nuvem, com testes automatizados e CI em Linux e Windows.

## Por que este projeto
Dados públicos de crédito *loan-level* com defaults, recuperações e saldos são raros. Aqui a dificuldade não é "dado corrompido":
o próprio dataset já marca valores fora de faixa como "não disponível". O desafio real é **semântico e de escala**: sentinelas
informativas, ausência estrutural, layout que muda entre releases, histórico que começa na aquisição do empréstimo, planos de
assistência que inflam atrasos sem perda real, e censura à direita.

## Resultados até aqui
| Etapa | Resultado |
|---|---|
| Ingestão | 27 vintages (1999-2025), 1.350.000 loans e 74.919.968 registros mensais; 0 linhas rejeitadas; reconciliação de 100% |
| Qualidade de dados | 28 regras de negócio medidas em SQL; sem valores fora de faixa; problemas pequenos quantificados (ex.: 195 loans com buraco na série, 0,01%) |
| Definição de default | 90+ dias ou evento de crédito, **ignorando atraso sob assistência ao mutuário/desastre/adiamento** (decisão D-002) |
| Validação do ciclo | Default em 24 meses: 4,90% (vintage 2007) contra 0,43% a 0,57% (2012-2015) |
| Efeito das moratórias | Vintage 2019: 4,58% sem o filtro contra **0,45%** com ele; 91,7% dos loans de 2019 que chegaram a 90+ dias tinham assistência |

![Curvas de default por vintage](reports/figures/vintage_default_curves.png)
![Sensibilidade à definição](reports/figures/default_definitions_compare.png)

## Arquitetura
```
Freddie Clarity (download) → data/raw → BRONZE (fiel, tudo texto) → SILVER (tipado, sentinela→NULL)
        → DQ (28 regras) → GOLD (default, dataset de PD, curvas) → EDA (agregados) → modelos → relatório
```

## Estrutura
```
src/credit_risk/   código reutilizável (config, conexão DuckDB, esquemas, ingestão, estatísticas da EDA, doctor)
scripts/           utilitários e relatórios (ingest, relatórios de DQ/default/EDA, diagnósticos)
dbt/               modelos SQL (silver, dq, gold, eda), macros e testes de qualidade
docs/              decision log, relatórios de qualidade/default/EDA, decisão D-002, PROJECT_STATE
reports/           figuras e tabelas agregadas publicáveis
tests/             testes automatizados (oráculo independente sobre dados sintéticos)
```

## Como reproduzir (Windows 11 / Linux / macOS)
```powershell
git clone https://github.com/SEU_USUARIO/credit-risk-freddie-mac.git
cd credit-risk-freddie-mac
uv sync --locked      # ambiente com versões travadas
uv run poe test       # testes (dados sintéticos)
uv run poe doctor     # painel de saúde do projeto
```
Os **dados não estão no repositório** (termos de uso da Freddie Mac e tamanho). Baixe o dataset *Sample* no Clarity Data
Intelligence, coloque os `.txt` em `data/raw/orig` e `data/raw/perf` e rode, em ordem:
`ingest → silver → gold → eda → dq-report → default-report → eda-report`.

## Limitações
- Hipotecas conformes de taxa fixa (viés de população); sem rotativo/cartão (CCF não se aplica).
- Roda no arquivo **Sample** (50.000 loans por vintage); pipeline parametrizado para escalar.
- Os campos de assistência/desastre só existem desde 2014: antes disso as definições A e B coincidem.

## Roadmap
- [x] 0 Ambiente · [x] 1 Ingestão bronze · [x] 2 Silver e qualidade de dados · [x] 3 Definição de default e target · [x] 4 EDA
- [ ] 5 Scorecard/PD · [ ] 6 PD alternativo (GBM/sobrevivência) · [ ] 7 LGD · [ ] 8 EAD · [ ] 9 ECL e relatório final

## Licença e créditos
Código sob licença MIT. Dados © Freddie Mac, sujeitos aos termos de uso do dataset (consulte o Clarity).
Uso não comercial; somente agregados são publicados neste repositório.
