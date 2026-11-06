{{ config(materialized='table') }}
{# Uma linha por loan AO ORIGINAR: so variaveis de originacao + alvos. Dados em nivel de emprestimo:
   uso LOCAL, nunca versionar. vantage_score_4 e removida (100% sentinela no Sample).
   observable_Nm = o loan tem >= N meses de historico ATE O CORTE. Treinar so com observable_Nm = true: incluir
   loans com janela incompleta apenas quando o desfecho ja e conhecido (default ou saida) superestima a taxa de default. #}

select
  o.* exclude (vantage_score_4, vantage_score_4_was_missing, _source_file, _ingested_at, _n_source_rows),
  e.default_period, e.default_age, e.default_trigger, e.cured_after_dpd90, e.ever_modified,
  e.terminal_state, e.zb_age as terminal_age, e.months_observable,
  -- alvo A (simples) e alvo B (ignora atraso sob assistencia/desastre/adiamento). A D-002 define qual e o oficial
  coalesce(e.default_age <= 12, false) as default_12m,
  coalesce(e.default_age <= 24, false) as default_24m,
  e.default_na_age,
  coalesce(e.default_na_age <= 12, false) as default_na_12m,
  coalesce(e.default_na_age <= 24, false) as default_na_24m,
  -- ALVO OFICIAL (D-002): definicao B. Treino/validacao: usable_Nm = true
  coalesce(e.default_na_age <= 12, false) as target_12m,
  coalesce(e.default_na_age <= 24, false) as target_24m,
  coalesce(not e.first_payment_inconsistent and not coalesce(e.default_age < 1, false)
           and e.months_observable >= 12, false) as usable_12m,
  coalesce(not e.first_payment_inconsistent and not coalesce(e.default_age < 1, false)
           and e.months_observable >= 24, false) as usable_24m,
  e.assisted_while_dpd90, e.months_to_first_payment,
  -- exclusoes: 1o pagamento incompativel com o loan_id (loans modificados/convertidos) ou default antes do 1o pagamento
  case when e.first_payment_inconsistent then 'first_payment_inconsistent'
       when e.default_age < 1 then 'default_before_first_payment' end as excluded_reason,
  coalesce(e.months_observable >= 12, false) as observable_12m,
  coalesce(e.months_observable >= 24, false) as observable_24m
from {{ ref('silver_orig') }} o
join {{ ref('gold_loan_events') }} e using (loan_id)
where e.has_perf
