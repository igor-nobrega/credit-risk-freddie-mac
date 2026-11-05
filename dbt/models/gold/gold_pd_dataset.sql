{{ config(materialized='table') }}
{# Uma linha por loan AO ORIGINAR: so variaveis de originacao + alvos. Dados em nivel de emprestimo:
   uso LOCAL, nunca versionar. vantage_score_4 e removida (100% sentinela no Sample).
   observable_Nm = o loan tem >= N meses de historico ATE O CORTE. Treinar so com observable_Nm = true: incluir
   loans com janela incompleta apenas quando o desfecho ja e conhecido (default ou saida) superestima a taxa de default. #}

select
  o.* exclude (vantage_score_4, vantage_score_4_was_missing, _source_file, _ingested_at, _n_source_rows),
  e.default_period, e.default_age, e.default_trigger, e.cured_after_dpd90, e.ever_modified,
  e.terminal_state, e.zb_age as terminal_age, e.months_observable,
  coalesce(e.default_age <= 12, false) as default_12m,
  coalesce(e.default_age <= 24, false) as default_24m,
  coalesce(e.months_observable >= 12, false) as observable_12m,
  coalesce(e.months_observable >= 24, false) as observable_24m
from {{ ref('silver_orig') }} o
join {{ ref('gold_loan_events') }} e using (loan_id)
where e.has_perf
