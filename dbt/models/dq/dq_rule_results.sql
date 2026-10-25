{{ config(materialized='table') }}
{# Regras de consistencia de negocio. Cada linha = uma regra com n_checked e n_failed.
   Nao interrompe o build: o objetivo e MEDIR a sujeira para o relatorio de qualidade. #}

with
o as (select * from {{ ref('silver_orig') }}),
p as (select * from {{ ref('silver_perf') }}),

r01 as (
  select 'R01' as rule_id, 'orig' as table_name,
         'loan_id duplicado na bronze_orig (loans com mais de uma linha)' as description,
         'warn' as severity, count(*) as n_checked, count(*) filter (where c > 1) as n_failed,
         'manter 1 linha por loan (arquivo mais recente) e registrar' as suggested_action
  from (select loan_id, count(*) as c from {{ source('bronze', 'bronze_orig') }} group by loan_id)
),
r02 as (
  select 'R02', 'orig', 'credit_score fora de 300-850 (apos sentinela)', 'warn',
         count(credit_score), count(*) filter (where credit_score < 300 or credit_score > 850),
         'tratar como ausente' from o
),
r03 as (
  select 'R03', 'orig', 'dti fora de 0-65 (apos sentinela)', 'warn',
         count(dti), count(*) filter (where dti < 0 or dti > 65), 'tratar como ausente' from o
),
r04 as (
  select 'R04', 'orig', 'mi_pct fora de 0-55 (apos sentinela)', 'warn',
         count(mi_pct), count(*) filter (where mi_pct < 0 or mi_pct > 55), 'tratar como ausente' from o
),
r05 as (
  select 'R05', 'orig', 'cltv menor que ltv (o guia diz que cltv seria "nao disponivel")', 'warn',
         count(*) filter (where cltv is not null and ltv is not null),
         count(*) filter (where cltv < ltv), 'investigar; flag' from o
),
r06 as (
  select 'R06', 'orig', 'maturity_date <= first_payment_date', 'warn',
         count(*) filter (where maturity_date is not null and first_payment_date is not null),
         count(*) filter (where maturity_date <= first_payment_date), 'excluir ou flag' from o
),
r07 as (
  select 'R07', 'orig', 'original_loan_term diferente de (maturity - first_payment + 1) em meses', 'warn',
         count(*) filter (where original_loan_term is not null and maturity_date is not null and first_payment_date is not null),
         count(*) filter (where original_loan_term != date_diff('month', first_payment_date, maturity_date) + 1),
         'flag' from o
),
r08 as (
  select 'R08', 'orig', 'original_upb nulo ou <= 0', 'error',
         count(*), count(*) filter (where original_upb is null or original_upb <= 0), 'excluir' from o
),
r09 as (
  select 'R09', 'orig', 'original_interest_rate fora de (0, 20]', 'warn',
         count(original_interest_rate),
         count(*) filter (where original_interest_rate <= 0 or original_interest_rate > 20), 'investigar' from o
),
r10 as (
  select 'R10', 'orig', 'property_state diferente de 2 letras maiusculas', 'warn',
         count(*), count(*) filter (where property_state is null or not regexp_matches(property_state, '^[A-Z]{2}$')),
         'flag' from o
),
r11 as (
  select 'R11', 'orig', 'loan_id fora do formato PYYQnXXXXXXX', 'error',
         count(*), count(*) filter (where loan_id is null or not regexp_matches(loan_id, '^[FA][0-9]{2}Q[1-4][0-9]{7}$')),
         'investigar' from o
),
r12 as (
  select 'R12', 'orig', 'ano do loan_id difere da vintage do arquivo', 'warn',
         count(*) filter (where try_cast(substr(loan_id, 2, 2) as integer) is not null),
         count(*) filter (
           where try_cast(substr(loan_id, 2, 2) as integer) is not null
             and (case when try_cast(substr(loan_id, 2, 2) as integer) = 99 then 1999
                       else 2000 + try_cast(substr(loan_id, 2, 2) as integer) end) != vintage_year),
         'investigar' from o
),

loans_perf as (select loan_id, count(*) as n_rows, min(monthly_reporting_period) as d_min,
                      max(monthly_reporting_period) as d_max
               from p group by loan_id),
r13 as (
  select 'R13', 'perf', 'loans na performance sem registro de originacao (orfaos)', 'error',
         count(*), count(*) filter (where o.loan_id is null), 'excluir da modelagem'
  from loans_perf lp left join o using (loan_id)
),
r14 as (
  select 'R14', 'orig', 'loans na originacao sem nenhuma linha de performance', 'warn',
         count(*), count(*) filter (where lp.loan_id is null), 'excluir da modelagem'
  from o left join loans_perf lp using (loan_id)
),
r15 as (
  select 'R15', 'perf', 'linhas duplicadas por (loan_id, periodo)', 'error',
         sum(c), sum(case when c > 1 then c - 1 else 0 end), 'deduplicar'
  from (select count(*) as c from p group by loan_id, monthly_reporting_period)
),
r16 as (
  select 'R16', 'perf', 'current_actual_upb nulo ou negativo', 'warn',
         count(*), count(*) filter (where current_actual_upb is null or current_actual_upb < 0), 'flag' from p
),
r17 as (
  select 'R17', 'perf', 'zero_balance_code preenchido com current_actual_upb > 0', 'warn',
         count(*) filter (where zero_balance_code is not null),
         count(*) filter (where zero_balance_code is not null and current_actual_upb > 0), 'investigar' from p
),
zb as (select loan_id, min(zero_balance_effective_date) as d from p
       where zero_balance_code is not null and zero_balance_effective_date is not null group by loan_id),
r18 as (
  select 'R18', 'perf', 'linhas com periodo posterior ao evento de saldo zero', 'warn',
         count(*), count(*) filter (where p.monthly_reporting_period > zb.d), 'excluir linhas pos-evento'
  from p join zb using (loan_id)
),
r19 as (
  select 'R19', 'perf', 'loans com buraco na serie mensal (meses esperados != linhas)', 'warn',
         count(*), count(*) filter (where date_diff('month', d_min, d_max) + 1 != n_rows), 'flag; tratar na construcao do painel'
  from loans_perf
),
r20 as (
  select 'R20', 'perf', 'actual_loss preenchido com zero_balance_code fora de 02/03/09/15', 'warn',
         count(*) filter (where actual_loss is not null),
         count(*) filter (where actual_loss is not null and coalesce(zero_balance_code, '') not in ('02', '03', '09', '15')),
         'investigar' from p
),
r21 as (
  select 'R21', 'perf', 'actual_loss ausente em zero_balance_code 02/03/09/15 (esperado nos 3 ultimos meses e em defeitos)', 'info',
         count(*) filter (where zero_balance_code in ('02', '03', '09', '15')),
         count(*) filter (where zero_balance_code in ('02', '03', '09', '15') and actual_loss is null),
         'censura no LGD: tratar na modelagem' from p
),
r22 as (
  select 'R22', 'perf', 'net_sales_proceeds positivo (guia: recuperacoes sao negativas)', 'info',
         count(net_sales_proceeds), count(*) filter (where net_sales_proceeds > 0), 'verificar convencao de sinal' from p
),
r23 as (
  select 'R23', 'perf', 'loan_age difere dos meses desde first_payment_date (loans nao modificados)', 'warn',
         count(*) filter (where p.modification_flag is null and p.loan_age is not null and o.first_payment_date is not null),
         count(*) filter (where p.modification_flag is null and p.loan_age is not null and o.first_payment_date is not null
                            and p.loan_age != date_diff('month', o.first_payment_date, p.monthly_reporting_period) + 1),
         'usar idade recalculada'
  from p join o using (loan_id)
),
r24 as (
  select 'R24', 'perf', 'loan_id fora do formato PYYQnXXXXXXX', 'error',
         count(*), count(*) filter (where loan_id is null or not regexp_matches(loan_id, '^[FA][0-9]{2}Q[1-4][0-9]{7}$')),
         'investigar' from p
),

allr as (
  select * from r01 union all select * from r02 union all select * from r03 union all select * from r04
  union all select * from r05 union all select * from r06 union all select * from r07 union all select * from r08
  union all select * from r09 union all select * from r10 union all select * from r11 union all select * from r12
  union all select * from r13 union all select * from r14 union all select * from r15 union all select * from r16
  union all select * from r17 union all select * from r18 union all select * from r19 union all select * from r20
  union all select * from r21 union all select * from r22 union all select * from r23 union all select * from r24
)
select rule_id, table_name, description, severity,
       cast(n_checked as bigint) as n_checked, cast(n_failed as bigint) as n_failed,
       case when n_checked > 0 then round(100.0 * n_failed / n_checked, 4) end as pct_failed,
       suggested_action
from allr
order by rule_id
