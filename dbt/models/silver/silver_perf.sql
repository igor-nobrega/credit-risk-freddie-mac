-- GERADO por scripts/gen_silver_sql.py a partir de src/credit_risk/freddie_schema.py. NAO EDITE.
{{ config(materialized='table') }}

with src as (
  select * from {{ source('bronze', 'bronze_perf') }}
),
typed as (
  select
    nullif(trim(loan_id), '') as loan_id,
    try_cast(try_strptime(nullif(trim(monthly_reporting_period), '') || '01', '%Y%m%d') as date) as monthly_reporting_period,
    try_cast(nullif(trim(current_actual_upb), '') as double) as current_actual_upb,
    nullif(nullif(trim(current_loan_delinquency_status), ''), 'XX') as current_loan_delinquency_status,
    try_cast(nullif(trim(loan_age), '') as integer) as loan_age,
    try_cast(nullif(trim(remaining_months_to_legal_maturity), '') as integer) as remaining_months_to_legal_maturity,
    try_cast(try_strptime(nullif(trim(defect_settlement_date), '') || '01', '%Y%m%d') as date) as defect_settlement_date,
    nullif(trim(modification_flag), '') as modification_flag,
    nullif(trim(zero_balance_code), '') as zero_balance_code,
    try_cast(try_strptime(nullif(trim(zero_balance_effective_date), '') || '01', '%Y%m%d') as date) as zero_balance_effective_date,
    try_cast(nullif(trim(current_interest_rate), '') as double) as current_interest_rate,
    try_cast(nullif(trim(current_non_interest_bearing_upb), '') as double) as current_non_interest_bearing_upb,
    try_cast(try_strptime(nullif(trim(ddlpi), '') || '01', '%Y%m%d') as date) as ddlpi,
    try_cast(nullif(trim(mi_recoveries), '') as double) as mi_recoveries,
    try_cast(nullif(trim(net_sales_proceeds), '') as double) as net_sales_proceeds,
    try_cast(nullif(trim(non_mi_recoveries), '') as double) as non_mi_recoveries,
    try_cast(nullif(trim(total_expenses), '') as double) as total_expenses,
    try_cast(nullif(trim(legal_costs), '') as double) as legal_costs,
    try_cast(nullif(trim(maintenance_preservation_costs), '') as double) as maintenance_preservation_costs,
    try_cast(nullif(trim(taxes_insurance), '') as double) as taxes_insurance,
    try_cast(nullif(trim(miscellaneous_expenses), '') as double) as miscellaneous_expenses,
    try_cast(nullif(trim(actual_loss), '') as double) as actual_loss,
    try_cast(nullif(trim(cumulative_modification_costs), '') as double) as cumulative_modification_costs,
    nullif(trim(interest_rate_step_indicator), '') as interest_rate_step_indicator,
    nullif(trim(payment_deferral_flag), '') as payment_deferral_flag,
    try_cast(nullif(nullif(trim(estimated_ltv), ''), '999') as integer) as estimated_ltv,
    try_cast(nullif(trim(zero_balance_removal_upb), '') as double) as zero_balance_removal_upb,
    try_cast(nullif(trim(delinquent_accrued_interest), '') as double) as delinquent_accrued_interest,
    nullif(trim(delinquency_due_to_disaster), '') as delinquency_due_to_disaster,
    nullif(trim(borrower_assistance_plan), '') as borrower_assistance_plan,
    try_cast(nullif(trim(current_period_modification_costs), '') as double) as current_period_modification_costs,
    try_cast(nullif(trim(current_interest_bearing_upb), '') as double) as current_interest_bearing_upb,
    nullif(nullif(trim(mi_cancellation_indicator), ''), '7') as mi_cancellation_indicator,
    nullif(trim(servicer_name), '') as servicer_name,
    try_cast(nullif(trim(bankruptcy_cramdown_costs), '') as double) as bankruptcy_cramdown_costs,
    (nullif(nullif(trim(current_loan_delinquency_status), ''), 'XX') is null) as current_loan_delinquency_status_was_missing,
    (nullif(nullif(trim(estimated_ltv), ''), '999') is null) as estimated_ltv_was_missing,
    (nullif(nullif(trim(mi_cancellation_indicator), ''), '7') is null) as mi_cancellation_indicator_was_missing,
    try_cast(_vintage as integer) as vintage_year,
    _source_file
  from src
)
select
  *,
  try_cast(current_loan_delinquency_status as integer) as dlq_months,  -- 'RA' (REO) vira NULL aqui
  (current_loan_delinquency_status = 'RA') as is_reo
from typed
