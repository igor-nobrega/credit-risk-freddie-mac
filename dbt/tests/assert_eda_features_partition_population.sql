{{ config(tags=['eda']) }}
-- Cada variavel particiona a MESMA populacao: o total de loans por variavel e igual entre variaveis
-- e igual a quantidade de loans usable_24m (vintages <= 2023) do gold_pd_dataset.
with t as (
  select feature, sum(n_loans) as n from {{ ref('eda_features') }} group by feature
),
pop as (
  select count(*) as n from {{ ref('gold_pd_dataset') }} where usable_24m and vintage_year <= 2023
)
select feature, n from t where n != (select n from pop)
union all
select 'eda_fico_ltv', sum(n_loans) from {{ ref('eda_fico_ltv') }} having sum(n_loans) != (select n from pop)
