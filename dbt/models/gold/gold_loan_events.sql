{{ config(materialized='table') }}
{# Uma linha por loan com TODOS os eventos candidatos a default. Idade = meses desde first_payment_date (1 = 1o mes).
   Definicao A (simples): 90+ dias de atraso (ou REO) OU evento de credito (ZB 02/03/09/15), o que ocorrer primeiro.
   Definicao B (sem assistencia): igual a A, mas ignora meses 90+ sob plano de assistencia (forbearance/repayment/trial),
   atraso por desastre ou adiamento de pagamento (campos populados desde 2014). Os demais gatilhos ficam para sensibilidade.
   A escolha final e a D-002 (decision_log). #}

with cutoff as (
  select max(monthly_reporting_period) as cutoff_period from {{ ref('silver_perf') }}
),
perf as (
  select p.loan_id,
         p.monthly_reporting_period as period,
         p.dlq_months, p.is_reo, p.zero_balance_code, p.zero_balance_removal_upb as zb_upb,
         p.current_actual_upb as upb, p.modification_flag,
         coalesce(p.borrower_assistance_plan in ('F', 'R', 'T')
                  or p.delinquency_due_to_disaster = 'Y'
                  or p.payment_deferral_flag in ('C', 'P'), false) as assisted,
         date_diff('month', o.first_payment_date, p.monthly_reporting_period) + 1 as age_m
  from {{ ref('silver_perf') }} p
  join {{ ref('silver_orig') }} o using (loan_id)
),
oq as (
  -- meses entre o inicio do trimestre de originacao (do loan_id PYYQn...) e o 1o pagamento; tipico: 1 a 5
  select loan_id,
         case when regexp_matches(loan_id, '^[FA][0-9]{2}Q[1-4]')
              then date_diff('month',
                     make_date(case when try_cast(substr(loan_id, 2, 2) as integer) = 99 then 1999
                                    else 2000 + try_cast(substr(loan_id, 2, 2) as integer) end,
                               (try_cast(substr(loan_id, 5, 1) as integer) - 1) * 3 + 1, 1),
                     first_payment_date) end as months_to_first_payment
  from {{ ref('silver_orig') }}
),
agg as (
  select
    loan_id,
    count(*) as n_perf_rows,
    min(period) as first_period,
    max(period) as last_period,
    min(period) filter (where dlq_months >= 2) as dpd60_period,
    arg_min(age_m, period) filter (where dlq_months >= 2) as dpd60_age,
    min(period) filter (where dlq_months >= 3 or is_reo) as dpd90_period,
    arg_min(age_m, period) filter (where dlq_months >= 3 or is_reo) as dpd90_age,
    min(period) filter (where (dlq_months >= 3 or is_reo) and not assisted) as dpd90_na_period,
    arg_min(age_m, period) filter (where (dlq_months >= 3 or is_reo) and not assisted) as dpd90_na_age,
    bool_or(assisted) filter (where dlq_months >= 3 or is_reo) as assisted_while_dpd90,
    min(period) filter (where dlq_months >= 6 or is_reo) as dpd180_period,
    arg_min(age_m, period) filter (where dlq_months >= 6 or is_reo) as dpd180_age,
    min(period) filter (where zero_balance_code in ('02', '03', '09', '15')) as credit_event_period,
    arg_min(age_m, period) filter (where zero_balance_code in ('02', '03', '09', '15')) as credit_event_age,
    arg_min(zero_balance_code, period) filter (where zero_balance_code in ('02', '03', '09', '15')) as credit_event_code,
    arg_min(upb, period) filter (where dlq_months >= 3 or is_reo) as upb_at_dpd90,
    max(zb_upb) filter (where zero_balance_code in ('02', '03', '09', '15')) as upb_at_credit_event,
    arg_max(zero_balance_code, period) filter (where zero_balance_code is not null) as zb_code,
    arg_max(age_m, period) filter (where zero_balance_code is not null) as zb_age,
    max(period) filter (where dlq_months = 0) as last_current_period,
    max(dlq_months) as max_dlq_months,
    bool_or(modification_flag is not null) as ever_modified,
    arg_max(upb, period) filter (where upb > 0) as last_positive_upb
  from perf
  group by loan_id
)
select
  o.loan_id,
  o.vintage_year,
  a.n_perf_rows is not null as has_perf,
  a.n_perf_rows, a.first_period, a.last_period,
  a.dpd60_period, a.dpd60_age, a.dpd90_period, a.dpd90_age, a.dpd90_na_period, a.dpd90_na_age,
  a.dpd180_period, a.dpd180_age,
  a.credit_event_period, a.credit_event_age, a.credit_event_code, a.upb_at_dpd90, a.upb_at_credit_event,
  case when a.dpd90_period is null then a.credit_event_period
       when a.credit_event_period is null then a.dpd90_period
       else least(a.dpd90_period, a.credit_event_period) end as default_period,
  case when a.dpd90_period is null then a.credit_event_age
       when a.credit_event_period is null then a.dpd90_age
       when a.dpd90_period <= a.credit_event_period then a.dpd90_age
       else a.credit_event_age end as default_age,
  case when a.dpd90_period is not null and a.credit_event_period is not null then 'both'
       when a.dpd90_period is not null then 'dpd90'
       when a.credit_event_period is not null then 'credit_event' end as default_trigger,
  case when a.dpd90_na_period is null then a.credit_event_period
       when a.credit_event_period is null then a.dpd90_na_period
       else least(a.dpd90_na_period, a.credit_event_period) end as default_na_period,
  case when a.dpd90_na_period is null then a.credit_event_age
       when a.credit_event_period is null then a.dpd90_na_age
       when a.dpd90_na_period <= a.credit_event_period then a.dpd90_na_age
       else a.credit_event_age end as default_na_age,
  coalesce(a.assisted_while_dpd90, false) as assisted_while_dpd90,
  -- UPB no momento do default (insumo de EAD): saldo no 1o mes 90+ ou, se o evento de credito veio antes, o saldo removido
  case when a.dpd90_period is not null and (a.credit_event_period is null or a.dpd90_period <= a.credit_event_period)
         then a.upb_at_dpd90
       else a.upb_at_credit_event end as upb_at_default,
  coalesce(a.dpd90_period is not null and a.last_current_period > a.dpd90_period, false) as cured_after_dpd90,
  a.zb_code, a.zb_age,
  case when a.zb_code in ('02', '03', '09', '15') then 'credit_event'
       when a.zb_code = '01' then 'prepaid_or_matured'
       when a.zb_code is not null then 'other_removal'
       when a.n_perf_rows is not null then 'active' end as terminal_state,
  a.max_dlq_months, a.ever_modified, a.last_positive_upb,
  c.cutoff_period,
  date_diff('month', o.first_payment_date, c.cutoff_period) + 1 as months_observable,
  q.months_to_first_payment,
  coalesce(q.months_to_first_payment < 0 or q.months_to_first_payment > 8, false) as first_payment_inconsistent
from {{ ref('silver_orig') }} o
cross join cutoff c
left join agg a using (loan_id)
left join oq q using (loan_id)
