# Risco de Crédito: Investigando as hipotecas americanas com Dados Reais do Freddie Mac

> **Status:** 🚧 em construção · Fase atual: **0 — ambiente e fundações**

Pipeline completo de risco de crédito (Score, PD, LGD, EAD e ECL) sobre o **Freddie Mac Single-Family Loan-Level Dataset**: arquivos pipe-delimited sem header, valores sentinela, eventos de término codificados e perdas realizadas. Roda **100% local e offline** (DuckDB + Parquet + dbt + Quarto), sem cotas de nuvem.

## Por que este projeto
Dados públicos de crédito *loan-level* com defaults, recuperações e saldos são raros. Este projeto reproduz o ciclo real de um time de modelagem: ingestão de dados sujos, definição de default, scorecard, PD/LGD/EAD e perda esperada, com decisões documentadas.

## Stack
`Python 3.12` · `uv` · `DuckDB` · `Parquet` · `dbt-duckdb` · `scikit-learn / statsmodels / LightGBM / lifelines / optbinning` · `Quarto` · `GitHub Actions` (Linux e Windows)

## Arquitetura
```
Freddie Clarity (download) → data/raw → BRONZE (fiel, tudo texto) → SILVER (tipado, sentinela→NULL)
                                                                       → GOLD (default, dataset de PD, curvas)
                                                                          → modelos → relatório Quarto
```

## Estrutura
```
src/credit_risk/   código reutilizável (config, conexão DuckDB, esquemas Freddie)
scripts/           utilitários (check_env, smoke_test, manifesto de dados)
dbt/               modelos SQL e testes de qualidade (silver/gold)
notebooks/         exploração e modelagem (Jupytext .py)
docs/              decision log, relatório de qualidade, model cards
reports/           figuras e pequenas tabelas agregadas publicáveis
tests/             testes automatizados
```

## Como reproduzir (Windows 11 / Linux / macOS)
```powershell
git clone https://github.com/igor-nobrega/credit-risk-freddie-mac.git
cd credit-risk-freddie-mac
uv sync            # cria o .venv com versões travadas (uv.lock)
uv run poe check   # diagnóstico do ambiente
uv run poe smoke   # teste de fumaça do DuckDB
```
Os **dados não estão no repositório** (termos da Freddie Mac e tamanho). Baixe-os no Clarity Data Intelligence e coloque em `data/raw/orig` e `data/raw/perf`. O manifesto SHA-256 dos arquivos usados fica em `docs/raw_manifest.sha256`.

## Resultados
_(a preencher conforme as fases avançam; sempre com número e figura)_

## Limitações
- Hipotecas conformes de taxa fixa (viés de população); sem rotativo/cartão (CCF não se aplica).
- Roda no arquivo **Sample** do dataset; pipeline parametrizado para escalar.

## Roadmap
- [ ] 0 Ambiente · [ ] 1 Ingestão bronze · [ ] 2 Silver e DQ · [ ] 3 Default e target · [ ] 4 EDA e insights
- [ ] 5 Scorecard/PD · [ ] 6 PD alternativo · [ ] 7 LGD · [ ] 8 EAD · [ ] 9 ECL e relatório final

## Licença e créditos
Código sob licença MIT. Dados © Freddie Mac, sujeitos aos termos de uso do dataset (consulte o Clarity).
