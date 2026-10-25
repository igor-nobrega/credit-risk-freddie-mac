-- GERADO por scripts/gen_silver_sql.py a partir de src/credit_risk/freddie_schema.py. NAO EDITE.
{{ config(materialized='table') }}

with
o as (
  select vintage_year, count(*) as n_rows,
    cast(sum(case when credit_score_was_missing then 1 else 0 end) as bigint) as credit_score,
    cast(sum(case when first_time_homebuyer_flag_was_missing then 1 else 0 end) as bigint) as first_time_homebuyer_flag,
    cast(sum(case when mi_pct_was_missing then 1 else 0 end) as bigint) as mi_pct,
    cast(sum(case when number_of_units_was_missing then 1 else 0 end) as bigint) as number_of_units,
    cast(sum(case when occupancy_status_was_missing then 1 else 0 end) as bigint) as occupancy_status,
    cast(sum(case when cltv_was_missing then 1 else 0 end) as bigint) as cltv,
    cast(sum(case when dti_was_missing then 1 else 0 end) as bigint) as dti,
    cast(sum(case when ltv_was_missing then 1 else 0 end) as bigint) as ltv,
    cast(sum(case when channel_was_missing then 1 else 0 end) as bigint) as channel,
    cast(sum(case when property_type_was_missing then 1 else 0 end) as bigint) as property_type,
    cast(sum(case when postal_code_was_missing then 1 else 0 end) as bigint) as postal_code,
    cast(sum(case when loan_purpose_was_missing then 1 else 0 end) as bigint) as loan_purpose,
    cast(sum(case when number_of_borrowers_was_missing then 1 else 0 end) as bigint) as number_of_borrowers,
    cast(sum(case when property_valuation_method_was_missing then 1 else 0 end) as bigint) as property_valuation_method,
    cast(sum(case when vantage_score_4_was_missing then 1 else 0 end) as bigint) as vantage_score_4
  from {{ ref('silver_orig') }}
  group by vintage_year
),
p as (
  select vintage_year, count(*) as n_rows,
    cast(sum(case when current_loan_delinquency_status_was_missing then 1 else 0 end) as bigint) as current_loan_delinquency_status,
    cast(sum(case when estimated_ltv_was_missing then 1 else 0 end) as bigint) as estimated_ltv,
    cast(sum(case when mi_cancellation_indicator_was_missing then 1 else 0 end) as bigint) as mi_cancellation_indicator
  from {{ ref('silver_perf') }}
  group by vintage_year
)
select 'orig' as table_name, 'credit_score' as column_name, vintage_year, n_rows, credit_score as n_missing, credit_score * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'first_time_homebuyer_flag' as column_name, vintage_year, n_rows, first_time_homebuyer_flag as n_missing, first_time_homebuyer_flag * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'mi_pct' as column_name, vintage_year, n_rows, mi_pct as n_missing, mi_pct * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'number_of_units' as column_name, vintage_year, n_rows, number_of_units as n_missing, number_of_units * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'occupancy_status' as column_name, vintage_year, n_rows, occupancy_status as n_missing, occupancy_status * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'cltv' as column_name, vintage_year, n_rows, cltv as n_missing, cltv * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'dti' as column_name, vintage_year, n_rows, dti as n_missing, dti * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'ltv' as column_name, vintage_year, n_rows, ltv as n_missing, ltv * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'channel' as column_name, vintage_year, n_rows, channel as n_missing, channel * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'property_type' as column_name, vintage_year, n_rows, property_type as n_missing, property_type * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'postal_code' as column_name, vintage_year, n_rows, postal_code as n_missing, postal_code * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'loan_purpose' as column_name, vintage_year, n_rows, loan_purpose as n_missing, loan_purpose * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'number_of_borrowers' as column_name, vintage_year, n_rows, number_of_borrowers as n_missing, number_of_borrowers * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'property_valuation_method' as column_name, vintage_year, n_rows, property_valuation_method as n_missing, property_valuation_method * 1.0 / n_rows as pct_missing from o
union all
select 'orig' as table_name, 'vantage_score_4' as column_name, vintage_year, n_rows, vantage_score_4 as n_missing, vantage_score_4 * 1.0 / n_rows as pct_missing from o
union all
select 'perf' as table_name, 'current_loan_delinquency_status' as column_name, vintage_year, n_rows, current_loan_delinquency_status as n_missing, current_loan_delinquency_status * 1.0 / n_rows as pct_missing from p
union all
select 'perf' as table_name, 'estimated_ltv' as column_name, vintage_year, n_rows, estimated_ltv as n_missing, estimated_ltv * 1.0 / n_rows as pct_missing from p
union all
select 'perf' as table_name, 'mi_cancellation_indicator' as column_name, vintage_year, n_rows, mi_cancellation_indicator as n_missing, mi_cancellation_indicator * 1.0 / n_rows as pct_missing from p
