{{ config(materialized='table') }}
{# Uma linha por loan AO ORIGINAR: so variaveis de originacao + alvos. Dados em nivel de emprestimo:
   uso LOCAL, nunca versionar. vantage_score_4 e removida (100% sentinela no Sample).
   observable_Nm = o loan tem >= N meses de historico ATE O CORTE. Treinar so com usable_Nm = true: incluir
   loans com janela incompleta apenas quando o desfecho ja e conhecido (default ou saida) superestima a taxa de default.
   Exclusoes (excluded_reason, por prioridade):
     first_payment_inconsistent - 1o pagamento fora de 0-8 meses do trimestre do loan_id (modificados/convertidos);
     default_before_first_payment - default em idade < 1;
     late_entry - 1a linha de performance com idade > 3: o historico inicial nao foi observado (vies de sobrevivente).
   Um 90+ so pode ocorrer a partir do ~3o mes, por isso entrada ate a idade 3 nao perde nenhum default. #}

with base as (
  select
    o.* exclude (vantage_score_4, vantage_score_4_was_missing, _source_file, _ingested_at, _n_source_rows),
    e.default_period, e.default_age, e.default_trigger, e.cured_after_dpd90, e.ever_modified,
    e.terminal_state, e.zb_age as terminal_age, e.months_observable,
    -- alvo A (simples) e alvo B (ignora atraso sob assistencia/desastre/adiamento)
    coalesce(e.default_age <= 12, false) as default_12m,
    coalesce(e.default_age <= 24, false) as default_24m,
    e.default_na_age,
    coalesce(e.default_na_age <= 12, false) as default_na_12m,
    coalesce(e.default_na_age <= 24, false) as default_na_24m,
    -- ALVO OFICIAL (D-002): definicao B
    coalesce(e.default_na_age <= 12, false) as target_12m,
    coalesce(e.default_na_age <= 24, false) as target_24m,
    e.assisted_while_dpd90, e.months_to_first_payment, e.first_row_age,
    case when e.first_payment_inconsistent then 'first_payment_inconsistent'
         when coalesce(e.default_age < 1, false) then 'default_before_first_payment'
         when e.first_row_age > 3 then 'late_entry' end as excluded_reason,
    coalesce(e.months_observable >= 12, false) as observable_12m,
    coalesce(e.months_observable >= 24, false) as observable_24m
  from {{ ref('silver_orig') }} o
  join {{ ref('gold_loan_events') }} e using (loan_id)
  where e.has_perf
)
select *,
       -- treino/validacao: janela completa E nenhuma exclusao
       (excluded_reason is null and observable_12m) as usable_12m,
       (excluded_reason is null and observable_24m) as usable_24m
from base
