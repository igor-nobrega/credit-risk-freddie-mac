{{ config(materialized='table') }}
{# Por que 2022-2023 destoam? Padronizacao: aplica as taxas por CELULA da era base (2012-2017) ao perfil (mix) da era de
   teste (2022-2023). expected = taxa que 2022-2023 teria se so o PERFIL tivesse mudado; o que sobra (actual - expected)
   e risco DENTRO das mesmas celulas. Quatro definicoes de celula, de grosseira a fina. Somente agregados (1 linha cada). #}

{% set f = fico_band('credit_score') %}
{% set l = ltv_band('ltv') %}
{% set d = dti_band('dti') %}
{% set r = rate_band('original_interest_rate') %}
{% set defs = [
  ("fico_x_ltv", "(" ~ f ~ ") || '|' || (" ~ l ~ ")"),
  ("fico_x_ltv_x_dti", "(" ~ f ~ ") || '|' || (" ~ l ~ ") || '|' || (" ~ d ~ ")"),
  ("fico_x_ltv_x_dti_x_taxa", "(" ~ f ~ ") || '|' || (" ~ l ~ ") || '|' || (" ~ d ~ ") || '|' || (" ~ r ~ ")"),
  ("taxa_de_juros_apenas", "(" ~ r ~ ")"),
] %}

with base as (
  select {{ era('vintage_year') }} as era, credit_score, ltv, dti, original_interest_rate, target_24m
  from {{ ref('gold_pd_dataset') }}
  where usable_24m and vintage_year <= 2023
)
{% for name, expr in defs %}
, cells_{{ name }} as (
  select era, {{ expr }} as cell, count(*) as n, count(*) filter (where target_24m) as d
  from base where era in ('2012-2017', '2022-2023') group by all
),
res_{{ name }} as (
  select '{{ name }}' as cell_definition,
         (select count(distinct cell) from cells_{{ name }}) as n_cells,
         (select sum(d) * 1.0 / sum(n) from cells_{{ name }} where era = '2012-2017') as base_rate,
         (select sum(t.n * coalesce(b.d * 1.0 / nullif(b.n, 0),
                                    (select sum(d) * 1.0 / sum(n) from cells_{{ name }} where era = '2012-2017')))
                 / sum(t.n)
          from cells_{{ name }} t
          left join cells_{{ name }} b on b.cell = t.cell and b.era = '2012-2017'
          where t.era = '2022-2023') as expected_rate,
         (select sum(d) * 1.0 / sum(n) from cells_{{ name }} where era = '2022-2023') as actual_rate
)
{% endfor %}
select cell_definition, n_cells, base_rate, expected_rate, actual_rate,
       expected_rate - base_rate as mix_effect, actual_rate - expected_rate as rate_effect
from (
{% for name, expr in defs %}select * from res_{{ name }}{% if not loop.last %} union all {% endif %}
{% endfor %}
)
