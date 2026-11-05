{{ config(materialized='table') }}
{# Default cumulativo por vintage e idade, para cada definicao candidata.
   n_at_risk = loans da vintage com historico >= k meses; n_default_cum = desses, os que defaultaram ate k.
   (Agregados: publicavel.) #}

with base as (
  select e.vintage_year, e.months_observable,
         e.dpd60_age, e.dpd90_age, e.dpd180_age, e.credit_event_age, e.default_age
  from {{ ref('gold_loan_events') }} e
  where e.has_perf
),
defs as (
  select 'dpd60' as definition, vintage_year, months_observable, dpd60_age as age from base
  union all select 'dpd90', vintage_year, months_observable, dpd90_age from base
  union all select 'dpd180', vintage_year, months_observable, dpd180_age from base
  union all select 'credit_event', vintage_year, months_observable, credit_event_age from base
  union all select 'dpd90_or_credit_event', vintage_year, months_observable, default_age from base
),
agg as (
  select definition, vintage_year, months_observable, age, count(*) as n
  from defs group by all
),
ks as (select k from generate_series(1, 120) as t(k))
select
  definition, vintage_year, k as age_months,
  cast(sum(n) filter (where months_observable >= k) as bigint) as n_at_risk,
  cast(coalesce(sum(n) filter (where months_observable >= k and age <= k), 0) as bigint) as n_default_cum,
  coalesce(sum(n) filter (where months_observable >= k and age <= k), 0) * 1.0
    / sum(n) filter (where months_observable >= k) as default_rate_cum
from agg cross join ks
group by definition, vintage_year, k
having sum(n) filter (where months_observable >= k) > 0
