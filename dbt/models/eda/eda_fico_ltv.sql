{{ config(materialized='table') }}
{# FICO x LTV por era de originacao (agregado). #}

select {{ era('vintage_year') }} as era,
       {{ fico_band('credit_score') }} as fico_band,
       {{ ltv_band('ltv') }} as ltv_band,
       count(*) as n_loans,
       count(*) filter (where target_24m) as n_defaults
from {{ ref('gold_pd_dataset') }}
where usable_24m and vintage_year <= 2023
group by all
