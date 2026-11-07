{{ config(materialized='table') }}
{# Default em 24m (alvo oficial) por variavel, faixa e vintage. Populacao: usable_24m, vintages <= 2023.
   Somente agregados (publicavel). #}

{% set feats = [
  ("fico_band", fico_band("credit_score")),
  ("ltv_band", ltv_band("ltv")),
  ("dti_band", dti_band("dti")),
  ("rate_band", rate_band("original_interest_rate")),
  ("upb_band", upb_band("original_upb")),
  ("mi_band", mi_band("mi_pct")),
  ("loan_purpose", cat("loan_purpose")),
  ("channel", cat("channel")),
  ("occupancy_status", cat("occupancy_status")),
  ("property_type", cat("property_type")),
  ("first_time_homebuyer_flag", cat("first_time_homebuyer_flag")),
  ("number_of_units", cat("number_of_units")),
  ("number_of_borrowers", cat("number_of_borrowers")),
  ("harp_indicator", cat("harp_indicator")),
  ("special_eligibility_program", "coalesce(cast(special_eligibility_program as varchar), 'none')"),
  ("property_valuation_method", cat("property_valuation_method")),
  ("prepayment_penalty_flag", cat("prepayment_penalty_flag")),
  ("io_indicator", cat("io_indicator")),
  ("property_state", cat("property_state")),
] %}

with base as (
  select * from {{ ref('gold_pd_dataset') }} where usable_24m and vintage_year <= 2023
)
{% for name, expr in feats %}
select '{{ name }}' as feature, {{ expr }} as bucket, vintage_year,
       count(*) as n_loans, count(*) filter (where target_24m) as n_defaults
from base group by all
{% if not loop.last %}union all{% endif %}
{% endfor %}
