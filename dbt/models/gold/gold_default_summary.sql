{{ config(materialized='table') }}
{# Resumo por vintage (agregado, publicavel): estados terminais, eventos, curas, modificacoes, observabilidade. #}

select
  e.vintage_year,
  count(*) as n_loans,
  count(*) filter (where e.has_perf) as n_with_perf,
  count(*) filter (where e.terminal_state = 'active') as n_active,
  count(*) filter (where e.terminal_state = 'prepaid_or_matured') as n_prepaid,
  count(*) filter (where e.terminal_state = 'credit_event') as n_credit_event_terminal,
  count(*) filter (where e.terminal_state = 'other_removal') as n_other_removal,
  count(*) filter (where e.dpd60_period is not null) as n_ever_dpd60,
  count(*) filter (where e.dpd90_period is not null) as n_ever_dpd90,
  count(*) filter (where e.dpd180_period is not null) as n_ever_dpd180,
  count(*) filter (where e.credit_event_period is not null) as n_ever_credit_event,
  count(*) filter (where e.default_period is not null) as n_ever_default,
  count(*) filter (where e.default_trigger = 'dpd90') as n_trigger_dpd90_only,
  count(*) filter (where e.default_trigger = 'credit_event') as n_trigger_credit_event_only,
  count(*) filter (where e.default_trigger = 'both') as n_trigger_both,
  count(*) filter (where e.cured_after_dpd90) as n_cured_after_dpd90,
  count(*) filter (where e.dpd90_period is not null and e.credit_event_period is null and e.terminal_state = 'prepaid_or_matured') as n_dpd90_then_prepaid,
  count(*) filter (where e.ever_modified) as n_ever_modified,
  count(*) filter (where e.default_period is not null and e.ever_modified) as n_default_and_modified,
  count(*) filter (where e.has_perf and e.months_observable >= 12) as n_obs_12m,
  count(*) filter (where e.has_perf and e.months_observable >= 24) as n_obs_24m,
  count(*) filter (where e.has_perf and e.default_age <= 12 and e.months_observable >= 12) as n_default_12m,
  count(*) filter (where e.has_perf and e.default_age <= 24 and e.months_observable >= 24) as n_default_24m,
  max(e.cutoff_period) as cutoff_period
from {{ ref('gold_loan_events') }} e
group by e.vintage_year
order by e.vintage_year
