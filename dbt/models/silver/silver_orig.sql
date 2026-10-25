-- GERADO por scripts/gen_silver_sql.py a partir de src/credit_risk/freddie_schema.py. NAO EDITE.
{{ config(materialized='table') }}

with src as (
  select * from {{ source('bronze', 'bronze_orig') }}
),
typed as (
  select
    try_cast(nullif(nullif(trim(credit_score), ''), '9999') as integer) as credit_score,
    try_cast(try_strptime(nullif(trim(first_payment_date), '') || '01', '%Y%m%d') as date) as first_payment_date,
    nullif(nullif(trim(first_time_homebuyer_flag), ''), '9') as first_time_homebuyer_flag,
    try_cast(try_strptime(nullif(trim(maturity_date), '') || '01', '%Y%m%d') as date) as maturity_date,
    nullif(trim(msa), '') as msa,
    try_cast(nullif(nullif(trim(mi_pct), ''), '999') as integer) as mi_pct,
    try_cast(nullif(nullif(trim(number_of_units), ''), '99') as integer) as number_of_units,
    nullif(nullif(trim(occupancy_status), ''), '9') as occupancy_status,
    try_cast(nullif(nullif(trim(cltv), ''), '999') as integer) as cltv,
    try_cast(nullif(nullif(trim(dti), ''), '999') as integer) as dti,
    try_cast(nullif(trim(original_upb), '') as double) as original_upb,
    try_cast(nullif(nullif(trim(ltv), ''), '999') as integer) as ltv,
    try_cast(nullif(trim(original_interest_rate), '') as double) as original_interest_rate,
    nullif(nullif(trim(channel), ''), '9') as channel,
    nullif(trim(prepayment_penalty_flag), '') as prepayment_penalty_flag,
    nullif(trim(amortization_type), '') as amortization_type,
    nullif(trim(property_state), '') as property_state,
    nullif(nullif(trim(property_type), ''), '99') as property_type,
    nullif(nullif(trim(postal_code), ''), '000') as postal_code,
    nullif(trim(loan_id), '') as loan_id,
    nullif(nullif(trim(loan_purpose), ''), '9') as loan_purpose,
    try_cast(nullif(trim(original_loan_term), '') as integer) as original_loan_term,
    try_cast(nullif(nullif(trim(number_of_borrowers), ''), '99') as integer) as number_of_borrowers,
    nullif(trim(seller_name), '') as seller_name,
    nullif(trim(super_conforming_flag), '') as super_conforming_flag,
    nullif(trim(pre_harp_loan_id), '') as pre_harp_loan_id,
    nullif(trim(special_eligibility_program), '') as special_eligibility_program,
    nullif(trim(harp_indicator), '') as harp_indicator,
    try_cast(nullif(nullif(trim(property_valuation_method), ''), '7') as integer) as property_valuation_method,
    nullif(trim(io_indicator), '') as io_indicator,
    try_cast(nullif(nullif(trim(vantage_score_4), ''), '9999') as integer) as vantage_score_4,
    (nullif(nullif(trim(credit_score), ''), '9999') is null) as credit_score_was_missing,
    (nullif(nullif(trim(first_time_homebuyer_flag), ''), '9') is null) as first_time_homebuyer_flag_was_missing,
    (nullif(nullif(trim(mi_pct), ''), '999') is null) as mi_pct_was_missing,
    (nullif(nullif(trim(number_of_units), ''), '99') is null) as number_of_units_was_missing,
    (nullif(nullif(trim(occupancy_status), ''), '9') is null) as occupancy_status_was_missing,
    (nullif(nullif(trim(cltv), ''), '999') is null) as cltv_was_missing,
    (nullif(nullif(trim(dti), ''), '999') is null) as dti_was_missing,
    (nullif(nullif(trim(ltv), ''), '999') is null) as ltv_was_missing,
    (nullif(nullif(trim(channel), ''), '9') is null) as channel_was_missing,
    (nullif(nullif(trim(property_type), ''), '99') is null) as property_type_was_missing,
    (nullif(nullif(trim(postal_code), ''), '000') is null) as postal_code_was_missing,
    (nullif(nullif(trim(loan_purpose), ''), '9') is null) as loan_purpose_was_missing,
    (nullif(nullif(trim(number_of_borrowers), ''), '99') is null) as number_of_borrowers_was_missing,
    (nullif(nullif(trim(property_valuation_method), ''), '7') is null) as property_valuation_method_was_missing,
    (nullif(nullif(trim(vantage_score_4), ''), '9999') is null) as vantage_score_4_was_missing,
    try_cast(_vintage as integer) as vintage_year,
    _source_file,
    _ingested_at
  from src
),
ranked as (
  select
    *,
    count(*) over (partition by loan_id) as _n_source_rows,
    row_number() over (partition by loan_id order by _source_file desc) as _rn
  from typed
)
select * exclude (_rn)
from ranked
where _rn = 1
