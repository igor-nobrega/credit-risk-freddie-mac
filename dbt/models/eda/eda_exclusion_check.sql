{{ config(materialized='table') }}
{# Calibra as regras de exclusao: compara o risco por faixa em TODA a populacao com janela de 24m (inclui excluidos).
   n_ever_default (qualquer idade) e a medida robusta quando a idade esta errada (primeiro pagamento inconsistente). #}

with base as (
  select * from {{ ref('gold_pd_dataset') }} where observable_24m and vintage_year <= 2023
)
select 'first_payment_months' as check_name,
       case when months_to_first_payment is null then 'z missing' when months_to_first_payment < 0 then 'd <0'
            when months_to_first_payment <= 5 then 'a 0-5' when months_to_first_payment <= 8 then 'b 6-8'
            else 'c >8' end as bucket,
       count(*) as n_loans,
       count(*) filter (where target_24m) as n_defaults_24m,
       count(*) filter (where default_na_age is not null) as n_ever_default
from base group by all
union all
select 'first_row_age',
       case when first_row_age <= 0 then 'a <=0' when first_row_age = 1 then 'b 1' when first_row_age <= 3 then 'c 2-3'
            when first_row_age <= 12 then 'd 4-12' else 'e >12' end,
       count(*), count(*) filter (where target_24m), count(*) filter (where default_na_age is not null)
from base group by all
