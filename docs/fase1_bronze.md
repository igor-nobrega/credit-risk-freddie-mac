# Fase 1 - Ingestao Bronze

**Objetivo:** trazer os arquivos brutos do Freddie Mac para Parquet **sem perder nenhuma linha** e provar isso.

## Contrato da camada bronze
| Regra | Como e garantida |
|---|---|
| Nada de limpeza | Todas as colunas sao `VARCHAR`; sentinelas (9999, 999...) permanecem como texto |
| Linhagem | `_source_file`, `_vintage`, `_ingested_at` em toda linha |
| Estrutura validada antes da carga | Histograma de campos por linha; layout dominante diferente do esquema = `LAYOUT_MISMATCH` e o arquivo NAO e carregado |
| Linhas malformadas nao somem | Vao para `data/bronze/rejects/` com a linha original e o tipo de erro |
| Reconciliacao | `linhas nao vazias = carregadas + rejeitadas`, senao `RECON_FAIL` |
| Idempotente | Arquivo ja ingerido (mesmo tamanho) e pulado; `--force` reingere |

## Como rodar
```powershell
uv run poe ingest                 # orig + perf
uv run python scripts/ingest_bronze.py --kind orig --force
```

## Saidas
- `data/bronze/{orig,perf}/*.parquet` (fora do Git)
- `data/bronze/_log/*.json` - um log por arquivo (histograma de campos, contagens, status)
- `data/bronze/rejects/*.parquet` - linhas rejeitadas (fora do Git)
- Views no warehouse: `bronze_orig`, `bronze_perf`, `bronze_ingestion_log`
- `reports/tables/bronze_reconciliation.csv` - contagens por arquivo (agregado, publicavel)

## Quando algo falha
| Status | Significado | O que fazer |
|---|---|---|
| `LAYOUT_MISMATCH` | O numero de campos dominante nao e 31 (orig) / 35 (perf) | Comparar com o arquivo de layout do Clarity; ajustar `freddie_schema.py`; registrar no decision log |
| `RECON_FAIL` | Linhas nao fecham | Investigar o arquivo (aspas, quebras de linha embutidas); nao seguir para silver |
| `ERROR` | Excecao | Ler o `detail` no log JSON |

## Perguntas para o relatorio de qualidade
1. Quantas linhas rejeitadas por vintage e por tipo de erro?
2. Algum arquivo com `pct_expected_fields` < 99,9%?
3. Linhas por vintage batem com o esperado (50.000 loans por ano cheio no Sample)?
