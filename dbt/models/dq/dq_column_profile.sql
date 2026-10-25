-- GERADO por scripts/gen_silver_sql.py a partir de src/credit_risk/freddie_schema.py. NAO EDITE.
{{ config(materialized='table') }}

with
o as (
  select count(*) as n,
    cast(sum(case when nullif(trim(credit_score), '') is null then 1 else 0 end) as bigint) as credit_score__blank,
    cast(sum(case when trim(credit_score) in ('9999') then 1 else 0 end) as bigint) as credit_score__sentinel,
    cast(sum(case when nullif(nullif(trim(credit_score), ''), '9999') is not null and try_cast(nullif(nullif(trim(credit_score), ''), '9999') as integer) is null then 1 else 0 end) as bigint) as credit_score__cast_fail,
    cast(sum(case when nullif(trim(first_payment_date), '') is null then 1 else 0 end) as bigint) as first_payment_date__blank,
    cast(0 as bigint) as first_payment_date__sentinel,
    cast(sum(case when nullif(trim(first_payment_date), '') is not null and try_cast(try_strptime(nullif(trim(first_payment_date), '') || '01', '%Y%m%d') as date) is null then 1 else 0 end) as bigint) as first_payment_date__cast_fail,
    cast(sum(case when nullif(trim(first_time_homebuyer_flag), '') is null then 1 else 0 end) as bigint) as first_time_homebuyer_flag__blank,
    cast(sum(case when trim(first_time_homebuyer_flag) in ('9') then 1 else 0 end) as bigint) as first_time_homebuyer_flag__sentinel,
    cast(sum(case when nullif(nullif(trim(first_time_homebuyer_flag), ''), '9') is not null and nullif(nullif(trim(first_time_homebuyer_flag), ''), '9') is null then 1 else 0 end) as bigint) as first_time_homebuyer_flag__cast_fail,
    cast(sum(case when nullif(trim(maturity_date), '') is null then 1 else 0 end) as bigint) as maturity_date__blank,
    cast(0 as bigint) as maturity_date__sentinel,
    cast(sum(case when nullif(trim(maturity_date), '') is not null and try_cast(try_strptime(nullif(trim(maturity_date), '') || '01', '%Y%m%d') as date) is null then 1 else 0 end) as bigint) as maturity_date__cast_fail,
    cast(sum(case when nullif(trim(msa), '') is null then 1 else 0 end) as bigint) as msa__blank,
    cast(0 as bigint) as msa__sentinel,
    cast(sum(case when nullif(trim(msa), '') is not null and nullif(trim(msa), '') is null then 1 else 0 end) as bigint) as msa__cast_fail,
    cast(sum(case when nullif(trim(mi_pct), '') is null then 1 else 0 end) as bigint) as mi_pct__blank,
    cast(sum(case when trim(mi_pct) in ('999') then 1 else 0 end) as bigint) as mi_pct__sentinel,
    cast(sum(case when nullif(nullif(trim(mi_pct), ''), '999') is not null and try_cast(nullif(nullif(trim(mi_pct), ''), '999') as integer) is null then 1 else 0 end) as bigint) as mi_pct__cast_fail,
    cast(sum(case when nullif(trim(number_of_units), '') is null then 1 else 0 end) as bigint) as number_of_units__blank,
    cast(sum(case when trim(number_of_units) in ('99') then 1 else 0 end) as bigint) as number_of_units__sentinel,
    cast(sum(case when nullif(nullif(trim(number_of_units), ''), '99') is not null and try_cast(nullif(nullif(trim(number_of_units), ''), '99') as integer) is null then 1 else 0 end) as bigint) as number_of_units__cast_fail,
    cast(sum(case when nullif(trim(occupancy_status), '') is null then 1 else 0 end) as bigint) as occupancy_status__blank,
    cast(sum(case when trim(occupancy_status) in ('9') then 1 else 0 end) as bigint) as occupancy_status__sentinel,
    cast(sum(case when nullif(nullif(trim(occupancy_status), ''), '9') is not null and nullif(nullif(trim(occupancy_status), ''), '9') is null then 1 else 0 end) as bigint) as occupancy_status__cast_fail,
    cast(sum(case when nullif(trim(cltv), '') is null then 1 else 0 end) as bigint) as cltv__blank,
    cast(sum(case when trim(cltv) in ('999') then 1 else 0 end) as bigint) as cltv__sentinel,
    cast(sum(case when nullif(nullif(trim(cltv), ''), '999') is not null and try_cast(nullif(nullif(trim(cltv), ''), '999') as integer) is null then 1 else 0 end) as bigint) as cltv__cast_fail,
    cast(sum(case when nullif(trim(dti), '') is null then 1 else 0 end) as bigint) as dti__blank,
    cast(sum(case when trim(dti) in ('999') then 1 else 0 end) as bigint) as dti__sentinel,
    cast(sum(case when nullif(nullif(trim(dti), ''), '999') is not null and try_cast(nullif(nullif(trim(dti), ''), '999') as integer) is null then 1 else 0 end) as bigint) as dti__cast_fail,
    cast(sum(case when nullif(trim(original_upb), '') is null then 1 else 0 end) as bigint) as original_upb__blank,
    cast(0 as bigint) as original_upb__sentinel,
    cast(sum(case when nullif(trim(original_upb), '') is not null and try_cast(nullif(trim(original_upb), '') as double) is null then 1 else 0 end) as bigint) as original_upb__cast_fail,
    cast(sum(case when nullif(trim(ltv), '') is null then 1 else 0 end) as bigint) as ltv__blank,
    cast(sum(case when trim(ltv) in ('999') then 1 else 0 end) as bigint) as ltv__sentinel,
    cast(sum(case when nullif(nullif(trim(ltv), ''), '999') is not null and try_cast(nullif(nullif(trim(ltv), ''), '999') as integer) is null then 1 else 0 end) as bigint) as ltv__cast_fail,
    cast(sum(case when nullif(trim(original_interest_rate), '') is null then 1 else 0 end) as bigint) as original_interest_rate__blank,
    cast(0 as bigint) as original_interest_rate__sentinel,
    cast(sum(case when nullif(trim(original_interest_rate), '') is not null and try_cast(nullif(trim(original_interest_rate), '') as double) is null then 1 else 0 end) as bigint) as original_interest_rate__cast_fail,
    cast(sum(case when nullif(trim(channel), '') is null then 1 else 0 end) as bigint) as channel__blank,
    cast(sum(case when trim(channel) in ('9') then 1 else 0 end) as bigint) as channel__sentinel,
    cast(sum(case when nullif(nullif(trim(channel), ''), '9') is not null and nullif(nullif(trim(channel), ''), '9') is null then 1 else 0 end) as bigint) as channel__cast_fail,
    cast(sum(case when nullif(trim(prepayment_penalty_flag), '') is null then 1 else 0 end) as bigint) as prepayment_penalty_flag__blank,
    cast(0 as bigint) as prepayment_penalty_flag__sentinel,
    cast(sum(case when nullif(trim(prepayment_penalty_flag), '') is not null and nullif(trim(prepayment_penalty_flag), '') is null then 1 else 0 end) as bigint) as prepayment_penalty_flag__cast_fail,
    cast(sum(case when nullif(trim(amortization_type), '') is null then 1 else 0 end) as bigint) as amortization_type__blank,
    cast(0 as bigint) as amortization_type__sentinel,
    cast(sum(case when nullif(trim(amortization_type), '') is not null and nullif(trim(amortization_type), '') is null then 1 else 0 end) as bigint) as amortization_type__cast_fail,
    cast(sum(case when nullif(trim(property_state), '') is null then 1 else 0 end) as bigint) as property_state__blank,
    cast(0 as bigint) as property_state__sentinel,
    cast(sum(case when nullif(trim(property_state), '') is not null and nullif(trim(property_state), '') is null then 1 else 0 end) as bigint) as property_state__cast_fail,
    cast(sum(case when nullif(trim(property_type), '') is null then 1 else 0 end) as bigint) as property_type__blank,
    cast(sum(case when trim(property_type) in ('99') then 1 else 0 end) as bigint) as property_type__sentinel,
    cast(sum(case when nullif(nullif(trim(property_type), ''), '99') is not null and nullif(nullif(trim(property_type), ''), '99') is null then 1 else 0 end) as bigint) as property_type__cast_fail,
    cast(sum(case when nullif(trim(postal_code), '') is null then 1 else 0 end) as bigint) as postal_code__blank,
    cast(sum(case when trim(postal_code) in ('000') then 1 else 0 end) as bigint) as postal_code__sentinel,
    cast(sum(case when nullif(nullif(trim(postal_code), ''), '000') is not null and nullif(nullif(trim(postal_code), ''), '000') is null then 1 else 0 end) as bigint) as postal_code__cast_fail,
    cast(sum(case when nullif(trim(loan_id), '') is null then 1 else 0 end) as bigint) as loan_id__blank,
    cast(0 as bigint) as loan_id__sentinel,
    cast(sum(case when nullif(trim(loan_id), '') is not null and nullif(trim(loan_id), '') is null then 1 else 0 end) as bigint) as loan_id__cast_fail,
    cast(sum(case when nullif(trim(loan_purpose), '') is null then 1 else 0 end) as bigint) as loan_purpose__blank,
    cast(sum(case when trim(loan_purpose) in ('9') then 1 else 0 end) as bigint) as loan_purpose__sentinel,
    cast(sum(case when nullif(nullif(trim(loan_purpose), ''), '9') is not null and nullif(nullif(trim(loan_purpose), ''), '9') is null then 1 else 0 end) as bigint) as loan_purpose__cast_fail,
    cast(sum(case when nullif(trim(original_loan_term), '') is null then 1 else 0 end) as bigint) as original_loan_term__blank,
    cast(0 as bigint) as original_loan_term__sentinel,
    cast(sum(case when nullif(trim(original_loan_term), '') is not null and try_cast(nullif(trim(original_loan_term), '') as integer) is null then 1 else 0 end) as bigint) as original_loan_term__cast_fail,
    cast(sum(case when nullif(trim(number_of_borrowers), '') is null then 1 else 0 end) as bigint) as number_of_borrowers__blank,
    cast(sum(case when trim(number_of_borrowers) in ('99') then 1 else 0 end) as bigint) as number_of_borrowers__sentinel,
    cast(sum(case when nullif(nullif(trim(number_of_borrowers), ''), '99') is not null and try_cast(nullif(nullif(trim(number_of_borrowers), ''), '99') as integer) is null then 1 else 0 end) as bigint) as number_of_borrowers__cast_fail,
    cast(sum(case when nullif(trim(seller_name), '') is null then 1 else 0 end) as bigint) as seller_name__blank,
    cast(0 as bigint) as seller_name__sentinel,
    cast(sum(case when nullif(trim(seller_name), '') is not null and nullif(trim(seller_name), '') is null then 1 else 0 end) as bigint) as seller_name__cast_fail,
    cast(sum(case when nullif(trim(super_conforming_flag), '') is null then 1 else 0 end) as bigint) as super_conforming_flag__blank,
    cast(0 as bigint) as super_conforming_flag__sentinel,
    cast(sum(case when nullif(trim(super_conforming_flag), '') is not null and nullif(trim(super_conforming_flag), '') is null then 1 else 0 end) as bigint) as super_conforming_flag__cast_fail,
    cast(sum(case when nullif(trim(pre_harp_loan_id), '') is null then 1 else 0 end) as bigint) as pre_harp_loan_id__blank,
    cast(0 as bigint) as pre_harp_loan_id__sentinel,
    cast(sum(case when nullif(trim(pre_harp_loan_id), '') is not null and nullif(trim(pre_harp_loan_id), '') is null then 1 else 0 end) as bigint) as pre_harp_loan_id__cast_fail,
    cast(sum(case when nullif(trim(special_eligibility_program), '') is null then 1 else 0 end) as bigint) as special_eligibility_program__blank,
    cast(0 as bigint) as special_eligibility_program__sentinel,
    cast(sum(case when nullif(trim(special_eligibility_program), '') is not null and nullif(trim(special_eligibility_program), '') is null then 1 else 0 end) as bigint) as special_eligibility_program__cast_fail,
    cast(sum(case when nullif(trim(harp_indicator), '') is null then 1 else 0 end) as bigint) as harp_indicator__blank,
    cast(0 as bigint) as harp_indicator__sentinel,
    cast(sum(case when nullif(trim(harp_indicator), '') is not null and nullif(trim(harp_indicator), '') is null then 1 else 0 end) as bigint) as harp_indicator__cast_fail,
    cast(sum(case when nullif(trim(property_valuation_method), '') is null then 1 else 0 end) as bigint) as property_valuation_method__blank,
    cast(sum(case when trim(property_valuation_method) in ('7') then 1 else 0 end) as bigint) as property_valuation_method__sentinel,
    cast(sum(case when nullif(nullif(trim(property_valuation_method), ''), '7') is not null and try_cast(nullif(nullif(trim(property_valuation_method), ''), '7') as integer) is null then 1 else 0 end) as bigint) as property_valuation_method__cast_fail,
    cast(sum(case when nullif(trim(io_indicator), '') is null then 1 else 0 end) as bigint) as io_indicator__blank,
    cast(0 as bigint) as io_indicator__sentinel,
    cast(sum(case when nullif(trim(io_indicator), '') is not null and nullif(trim(io_indicator), '') is null then 1 else 0 end) as bigint) as io_indicator__cast_fail,
    cast(sum(case when nullif(trim(vantage_score_4), '') is null then 1 else 0 end) as bigint) as vantage_score_4__blank,
    cast(sum(case when trim(vantage_score_4) in ('9999') then 1 else 0 end) as bigint) as vantage_score_4__sentinel,
    cast(sum(case when nullif(nullif(trim(vantage_score_4), ''), '9999') is not null and try_cast(nullif(nullif(trim(vantage_score_4), ''), '9999') as integer) is null then 1 else 0 end) as bigint) as vantage_score_4__cast_fail
  from {{ source('bronze', 'bronze_orig') }}
),
p as (
  select count(*) as n,
    cast(sum(case when nullif(trim(loan_id), '') is null then 1 else 0 end) as bigint) as loan_id__blank,
    cast(0 as bigint) as loan_id__sentinel,
    cast(sum(case when nullif(trim(loan_id), '') is not null and nullif(trim(loan_id), '') is null then 1 else 0 end) as bigint) as loan_id__cast_fail,
    cast(sum(case when nullif(trim(monthly_reporting_period), '') is null then 1 else 0 end) as bigint) as monthly_reporting_period__blank,
    cast(0 as bigint) as monthly_reporting_period__sentinel,
    cast(sum(case when nullif(trim(monthly_reporting_period), '') is not null and try_cast(try_strptime(nullif(trim(monthly_reporting_period), '') || '01', '%Y%m%d') as date) is null then 1 else 0 end) as bigint) as monthly_reporting_period__cast_fail,
    cast(sum(case when nullif(trim(current_actual_upb), '') is null then 1 else 0 end) as bigint) as current_actual_upb__blank,
    cast(0 as bigint) as current_actual_upb__sentinel,
    cast(sum(case when nullif(trim(current_actual_upb), '') is not null and try_cast(nullif(trim(current_actual_upb), '') as double) is null then 1 else 0 end) as bigint) as current_actual_upb__cast_fail,
    cast(sum(case when nullif(trim(current_loan_delinquency_status), '') is null then 1 else 0 end) as bigint) as current_loan_delinquency_status__blank,
    cast(sum(case when trim(current_loan_delinquency_status) in ('XX') then 1 else 0 end) as bigint) as current_loan_delinquency_status__sentinel,
    cast(sum(case when nullif(nullif(trim(current_loan_delinquency_status), ''), 'XX') is not null and nullif(nullif(trim(current_loan_delinquency_status), ''), 'XX') is null then 1 else 0 end) as bigint) as current_loan_delinquency_status__cast_fail,
    cast(sum(case when nullif(trim(loan_age), '') is null then 1 else 0 end) as bigint) as loan_age__blank,
    cast(0 as bigint) as loan_age__sentinel,
    cast(sum(case when nullif(trim(loan_age), '') is not null and try_cast(nullif(trim(loan_age), '') as integer) is null then 1 else 0 end) as bigint) as loan_age__cast_fail,
    cast(sum(case when nullif(trim(remaining_months_to_legal_maturity), '') is null then 1 else 0 end) as bigint) as remaining_months_to_legal_maturity__blank,
    cast(0 as bigint) as remaining_months_to_legal_maturity__sentinel,
    cast(sum(case when nullif(trim(remaining_months_to_legal_maturity), '') is not null and try_cast(nullif(trim(remaining_months_to_legal_maturity), '') as integer) is null then 1 else 0 end) as bigint) as remaining_months_to_legal_maturity__cast_fail,
    cast(sum(case when nullif(trim(defect_settlement_date), '') is null then 1 else 0 end) as bigint) as defect_settlement_date__blank,
    cast(0 as bigint) as defect_settlement_date__sentinel,
    cast(sum(case when nullif(trim(defect_settlement_date), '') is not null and try_cast(try_strptime(nullif(trim(defect_settlement_date), '') || '01', '%Y%m%d') as date) is null then 1 else 0 end) as bigint) as defect_settlement_date__cast_fail,
    cast(sum(case when nullif(trim(modification_flag), '') is null then 1 else 0 end) as bigint) as modification_flag__blank,
    cast(0 as bigint) as modification_flag__sentinel,
    cast(sum(case when nullif(trim(modification_flag), '') is not null and nullif(trim(modification_flag), '') is null then 1 else 0 end) as bigint) as modification_flag__cast_fail,
    cast(sum(case when nullif(trim(zero_balance_code), '') is null then 1 else 0 end) as bigint) as zero_balance_code__blank,
    cast(0 as bigint) as zero_balance_code__sentinel,
    cast(sum(case when nullif(trim(zero_balance_code), '') is not null and nullif(trim(zero_balance_code), '') is null then 1 else 0 end) as bigint) as zero_balance_code__cast_fail,
    cast(sum(case when nullif(trim(zero_balance_effective_date), '') is null then 1 else 0 end) as bigint) as zero_balance_effective_date__blank,
    cast(0 as bigint) as zero_balance_effective_date__sentinel,
    cast(sum(case when nullif(trim(zero_balance_effective_date), '') is not null and try_cast(try_strptime(nullif(trim(zero_balance_effective_date), '') || '01', '%Y%m%d') as date) is null then 1 else 0 end) as bigint) as zero_balance_effective_date__cast_fail,
    cast(sum(case when nullif(trim(current_interest_rate), '') is null then 1 else 0 end) as bigint) as current_interest_rate__blank,
    cast(0 as bigint) as current_interest_rate__sentinel,
    cast(sum(case when nullif(trim(current_interest_rate), '') is not null and try_cast(nullif(trim(current_interest_rate), '') as double) is null then 1 else 0 end) as bigint) as current_interest_rate__cast_fail,
    cast(sum(case when nullif(trim(current_non_interest_bearing_upb), '') is null then 1 else 0 end) as bigint) as current_non_interest_bearing_upb__blank,
    cast(0 as bigint) as current_non_interest_bearing_upb__sentinel,
    cast(sum(case when nullif(trim(current_non_interest_bearing_upb), '') is not null and try_cast(nullif(trim(current_non_interest_bearing_upb), '') as double) is null then 1 else 0 end) as bigint) as current_non_interest_bearing_upb__cast_fail,
    cast(sum(case when nullif(trim(ddlpi), '') is null then 1 else 0 end) as bigint) as ddlpi__blank,
    cast(0 as bigint) as ddlpi__sentinel,
    cast(sum(case when nullif(trim(ddlpi), '') is not null and try_cast(try_strptime(nullif(trim(ddlpi), '') || '01', '%Y%m%d') as date) is null then 1 else 0 end) as bigint) as ddlpi__cast_fail,
    cast(sum(case when nullif(trim(mi_recoveries), '') is null then 1 else 0 end) as bigint) as mi_recoveries__blank,
    cast(0 as bigint) as mi_recoveries__sentinel,
    cast(sum(case when nullif(trim(mi_recoveries), '') is not null and try_cast(nullif(trim(mi_recoveries), '') as double) is null then 1 else 0 end) as bigint) as mi_recoveries__cast_fail,
    cast(sum(case when nullif(trim(net_sales_proceeds), '') is null then 1 else 0 end) as bigint) as net_sales_proceeds__blank,
    cast(0 as bigint) as net_sales_proceeds__sentinel,
    cast(sum(case when nullif(trim(net_sales_proceeds), '') is not null and try_cast(nullif(trim(net_sales_proceeds), '') as double) is null then 1 else 0 end) as bigint) as net_sales_proceeds__cast_fail,
    cast(sum(case when nullif(trim(non_mi_recoveries), '') is null then 1 else 0 end) as bigint) as non_mi_recoveries__blank,
    cast(0 as bigint) as non_mi_recoveries__sentinel,
    cast(sum(case when nullif(trim(non_mi_recoveries), '') is not null and try_cast(nullif(trim(non_mi_recoveries), '') as double) is null then 1 else 0 end) as bigint) as non_mi_recoveries__cast_fail,
    cast(sum(case when nullif(trim(total_expenses), '') is null then 1 else 0 end) as bigint) as total_expenses__blank,
    cast(0 as bigint) as total_expenses__sentinel,
    cast(sum(case when nullif(trim(total_expenses), '') is not null and try_cast(nullif(trim(total_expenses), '') as double) is null then 1 else 0 end) as bigint) as total_expenses__cast_fail,
    cast(sum(case when nullif(trim(legal_costs), '') is null then 1 else 0 end) as bigint) as legal_costs__blank,
    cast(0 as bigint) as legal_costs__sentinel,
    cast(sum(case when nullif(trim(legal_costs), '') is not null and try_cast(nullif(trim(legal_costs), '') as double) is null then 1 else 0 end) as bigint) as legal_costs__cast_fail,
    cast(sum(case when nullif(trim(maintenance_preservation_costs), '') is null then 1 else 0 end) as bigint) as maintenance_preservation_costs__blank,
    cast(0 as bigint) as maintenance_preservation_costs__sentinel,
    cast(sum(case when nullif(trim(maintenance_preservation_costs), '') is not null and try_cast(nullif(trim(maintenance_preservation_costs), '') as double) is null then 1 else 0 end) as bigint) as maintenance_preservation_costs__cast_fail,
    cast(sum(case when nullif(trim(taxes_insurance), '') is null then 1 else 0 end) as bigint) as taxes_insurance__blank,
    cast(0 as bigint) as taxes_insurance__sentinel,
    cast(sum(case when nullif(trim(taxes_insurance), '') is not null and try_cast(nullif(trim(taxes_insurance), '') as double) is null then 1 else 0 end) as bigint) as taxes_insurance__cast_fail,
    cast(sum(case when nullif(trim(miscellaneous_expenses), '') is null then 1 else 0 end) as bigint) as miscellaneous_expenses__blank,
    cast(0 as bigint) as miscellaneous_expenses__sentinel,
    cast(sum(case when nullif(trim(miscellaneous_expenses), '') is not null and try_cast(nullif(trim(miscellaneous_expenses), '') as double) is null then 1 else 0 end) as bigint) as miscellaneous_expenses__cast_fail,
    cast(sum(case when nullif(trim(actual_loss), '') is null then 1 else 0 end) as bigint) as actual_loss__blank,
    cast(0 as bigint) as actual_loss__sentinel,
    cast(sum(case when nullif(trim(actual_loss), '') is not null and try_cast(nullif(trim(actual_loss), '') as double) is null then 1 else 0 end) as bigint) as actual_loss__cast_fail,
    cast(sum(case when nullif(trim(cumulative_modification_costs), '') is null then 1 else 0 end) as bigint) as cumulative_modification_costs__blank,
    cast(0 as bigint) as cumulative_modification_costs__sentinel,
    cast(sum(case when nullif(trim(cumulative_modification_costs), '') is not null and try_cast(nullif(trim(cumulative_modification_costs), '') as double) is null then 1 else 0 end) as bigint) as cumulative_modification_costs__cast_fail,
    cast(sum(case when nullif(trim(interest_rate_step_indicator), '') is null then 1 else 0 end) as bigint) as interest_rate_step_indicator__blank,
    cast(0 as bigint) as interest_rate_step_indicator__sentinel,
    cast(sum(case when nullif(trim(interest_rate_step_indicator), '') is not null and nullif(trim(interest_rate_step_indicator), '') is null then 1 else 0 end) as bigint) as interest_rate_step_indicator__cast_fail,
    cast(sum(case when nullif(trim(payment_deferral_flag), '') is null then 1 else 0 end) as bigint) as payment_deferral_flag__blank,
    cast(0 as bigint) as payment_deferral_flag__sentinel,
    cast(sum(case when nullif(trim(payment_deferral_flag), '') is not null and nullif(trim(payment_deferral_flag), '') is null then 1 else 0 end) as bigint) as payment_deferral_flag__cast_fail,
    cast(sum(case when nullif(trim(estimated_ltv), '') is null then 1 else 0 end) as bigint) as estimated_ltv__blank,
    cast(sum(case when trim(estimated_ltv) in ('999') then 1 else 0 end) as bigint) as estimated_ltv__sentinel,
    cast(sum(case when nullif(nullif(trim(estimated_ltv), ''), '999') is not null and try_cast(nullif(nullif(trim(estimated_ltv), ''), '999') as integer) is null then 1 else 0 end) as bigint) as estimated_ltv__cast_fail,
    cast(sum(case when nullif(trim(zero_balance_removal_upb), '') is null then 1 else 0 end) as bigint) as zero_balance_removal_upb__blank,
    cast(0 as bigint) as zero_balance_removal_upb__sentinel,
    cast(sum(case when nullif(trim(zero_balance_removal_upb), '') is not null and try_cast(nullif(trim(zero_balance_removal_upb), '') as double) is null then 1 else 0 end) as bigint) as zero_balance_removal_upb__cast_fail,
    cast(sum(case when nullif(trim(delinquent_accrued_interest), '') is null then 1 else 0 end) as bigint) as delinquent_accrued_interest__blank,
    cast(0 as bigint) as delinquent_accrued_interest__sentinel,
    cast(sum(case when nullif(trim(delinquent_accrued_interest), '') is not null and try_cast(nullif(trim(delinquent_accrued_interest), '') as double) is null then 1 else 0 end) as bigint) as delinquent_accrued_interest__cast_fail,
    cast(sum(case when nullif(trim(delinquency_due_to_disaster), '') is null then 1 else 0 end) as bigint) as delinquency_due_to_disaster__blank,
    cast(0 as bigint) as delinquency_due_to_disaster__sentinel,
    cast(sum(case when nullif(trim(delinquency_due_to_disaster), '') is not null and nullif(trim(delinquency_due_to_disaster), '') is null then 1 else 0 end) as bigint) as delinquency_due_to_disaster__cast_fail,
    cast(sum(case when nullif(trim(borrower_assistance_plan), '') is null then 1 else 0 end) as bigint) as borrower_assistance_plan__blank,
    cast(0 as bigint) as borrower_assistance_plan__sentinel,
    cast(sum(case when nullif(trim(borrower_assistance_plan), '') is not null and nullif(trim(borrower_assistance_plan), '') is null then 1 else 0 end) as bigint) as borrower_assistance_plan__cast_fail,
    cast(sum(case when nullif(trim(current_period_modification_costs), '') is null then 1 else 0 end) as bigint) as current_period_modification_costs__blank,
    cast(0 as bigint) as current_period_modification_costs__sentinel,
    cast(sum(case when nullif(trim(current_period_modification_costs), '') is not null and try_cast(nullif(trim(current_period_modification_costs), '') as double) is null then 1 else 0 end) as bigint) as current_period_modification_costs__cast_fail,
    cast(sum(case when nullif(trim(current_interest_bearing_upb), '') is null then 1 else 0 end) as bigint) as current_interest_bearing_upb__blank,
    cast(0 as bigint) as current_interest_bearing_upb__sentinel,
    cast(sum(case when nullif(trim(current_interest_bearing_upb), '') is not null and try_cast(nullif(trim(current_interest_bearing_upb), '') as double) is null then 1 else 0 end) as bigint) as current_interest_bearing_upb__cast_fail,
    cast(sum(case when nullif(trim(mi_cancellation_indicator), '') is null then 1 else 0 end) as bigint) as mi_cancellation_indicator__blank,
    cast(sum(case when trim(mi_cancellation_indicator) in ('7') then 1 else 0 end) as bigint) as mi_cancellation_indicator__sentinel,
    cast(sum(case when nullif(nullif(trim(mi_cancellation_indicator), ''), '7') is not null and nullif(nullif(trim(mi_cancellation_indicator), ''), '7') is null then 1 else 0 end) as bigint) as mi_cancellation_indicator__cast_fail,
    cast(sum(case when nullif(trim(servicer_name), '') is null then 1 else 0 end) as bigint) as servicer_name__blank,
    cast(0 as bigint) as servicer_name__sentinel,
    cast(sum(case when nullif(trim(servicer_name), '') is not null and nullif(trim(servicer_name), '') is null then 1 else 0 end) as bigint) as servicer_name__cast_fail,
    cast(sum(case when nullif(trim(bankruptcy_cramdown_costs), '') is null then 1 else 0 end) as bigint) as bankruptcy_cramdown_costs__blank,
    cast(0 as bigint) as bankruptcy_cramdown_costs__sentinel,
    cast(sum(case when nullif(trim(bankruptcy_cramdown_costs), '') is not null and try_cast(nullif(trim(bankruptcy_cramdown_costs), '') as double) is null then 1 else 0 end) as bigint) as bankruptcy_cramdown_costs__cast_fail
  from {{ source('bronze', 'bronze_perf') }}
)
select 'orig' as table_name, 'credit_score' as column_name, 'int' as declared_type, o.n as n_rows, o.credit_score__blank as n_blank, o.credit_score__sentinel as n_sentinel, o.credit_score__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'first_payment_date' as column_name, 'yyyymm' as declared_type, o.n as n_rows, o.first_payment_date__blank as n_blank, o.first_payment_date__sentinel as n_sentinel, o.first_payment_date__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'first_time_homebuyer_flag' as column_name, 'str' as declared_type, o.n as n_rows, o.first_time_homebuyer_flag__blank as n_blank, o.first_time_homebuyer_flag__sentinel as n_sentinel, o.first_time_homebuyer_flag__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'maturity_date' as column_name, 'yyyymm' as declared_type, o.n as n_rows, o.maturity_date__blank as n_blank, o.maturity_date__sentinel as n_sentinel, o.maturity_date__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'msa' as column_name, 'str' as declared_type, o.n as n_rows, o.msa__blank as n_blank, o.msa__sentinel as n_sentinel, o.msa__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'mi_pct' as column_name, 'int' as declared_type, o.n as n_rows, o.mi_pct__blank as n_blank, o.mi_pct__sentinel as n_sentinel, o.mi_pct__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'number_of_units' as column_name, 'int' as declared_type, o.n as n_rows, o.number_of_units__blank as n_blank, o.number_of_units__sentinel as n_sentinel, o.number_of_units__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'occupancy_status' as column_name, 'str' as declared_type, o.n as n_rows, o.occupancy_status__blank as n_blank, o.occupancy_status__sentinel as n_sentinel, o.occupancy_status__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'cltv' as column_name, 'int' as declared_type, o.n as n_rows, o.cltv__blank as n_blank, o.cltv__sentinel as n_sentinel, o.cltv__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'dti' as column_name, 'int' as declared_type, o.n as n_rows, o.dti__blank as n_blank, o.dti__sentinel as n_sentinel, o.dti__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'original_upb' as column_name, 'double' as declared_type, o.n as n_rows, o.original_upb__blank as n_blank, o.original_upb__sentinel as n_sentinel, o.original_upb__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'ltv' as column_name, 'int' as declared_type, o.n as n_rows, o.ltv__blank as n_blank, o.ltv__sentinel as n_sentinel, o.ltv__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'original_interest_rate' as column_name, 'double' as declared_type, o.n as n_rows, o.original_interest_rate__blank as n_blank, o.original_interest_rate__sentinel as n_sentinel, o.original_interest_rate__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'channel' as column_name, 'str' as declared_type, o.n as n_rows, o.channel__blank as n_blank, o.channel__sentinel as n_sentinel, o.channel__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'prepayment_penalty_flag' as column_name, 'str' as declared_type, o.n as n_rows, o.prepayment_penalty_flag__blank as n_blank, o.prepayment_penalty_flag__sentinel as n_sentinel, o.prepayment_penalty_flag__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'amortization_type' as column_name, 'str' as declared_type, o.n as n_rows, o.amortization_type__blank as n_blank, o.amortization_type__sentinel as n_sentinel, o.amortization_type__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'property_state' as column_name, 'str' as declared_type, o.n as n_rows, o.property_state__blank as n_blank, o.property_state__sentinel as n_sentinel, o.property_state__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'property_type' as column_name, 'str' as declared_type, o.n as n_rows, o.property_type__blank as n_blank, o.property_type__sentinel as n_sentinel, o.property_type__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'postal_code' as column_name, 'str' as declared_type, o.n as n_rows, o.postal_code__blank as n_blank, o.postal_code__sentinel as n_sentinel, o.postal_code__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'loan_id' as column_name, 'str' as declared_type, o.n as n_rows, o.loan_id__blank as n_blank, o.loan_id__sentinel as n_sentinel, o.loan_id__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'loan_purpose' as column_name, 'str' as declared_type, o.n as n_rows, o.loan_purpose__blank as n_blank, o.loan_purpose__sentinel as n_sentinel, o.loan_purpose__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'original_loan_term' as column_name, 'int' as declared_type, o.n as n_rows, o.original_loan_term__blank as n_blank, o.original_loan_term__sentinel as n_sentinel, o.original_loan_term__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'number_of_borrowers' as column_name, 'int' as declared_type, o.n as n_rows, o.number_of_borrowers__blank as n_blank, o.number_of_borrowers__sentinel as n_sentinel, o.number_of_borrowers__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'seller_name' as column_name, 'str' as declared_type, o.n as n_rows, o.seller_name__blank as n_blank, o.seller_name__sentinel as n_sentinel, o.seller_name__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'super_conforming_flag' as column_name, 'str' as declared_type, o.n as n_rows, o.super_conforming_flag__blank as n_blank, o.super_conforming_flag__sentinel as n_sentinel, o.super_conforming_flag__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'pre_harp_loan_id' as column_name, 'str' as declared_type, o.n as n_rows, o.pre_harp_loan_id__blank as n_blank, o.pre_harp_loan_id__sentinel as n_sentinel, o.pre_harp_loan_id__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'special_eligibility_program' as column_name, 'str' as declared_type, o.n as n_rows, o.special_eligibility_program__blank as n_blank, o.special_eligibility_program__sentinel as n_sentinel, o.special_eligibility_program__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'harp_indicator' as column_name, 'str' as declared_type, o.n as n_rows, o.harp_indicator__blank as n_blank, o.harp_indicator__sentinel as n_sentinel, o.harp_indicator__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'property_valuation_method' as column_name, 'int' as declared_type, o.n as n_rows, o.property_valuation_method__blank as n_blank, o.property_valuation_method__sentinel as n_sentinel, o.property_valuation_method__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'io_indicator' as column_name, 'str' as declared_type, o.n as n_rows, o.io_indicator__blank as n_blank, o.io_indicator__sentinel as n_sentinel, o.io_indicator__cast_fail as n_cast_fail from o
union all
select 'orig' as table_name, 'vantage_score_4' as column_name, 'int' as declared_type, o.n as n_rows, o.vantage_score_4__blank as n_blank, o.vantage_score_4__sentinel as n_sentinel, o.vantage_score_4__cast_fail as n_cast_fail from o
union all
select 'perf' as table_name, 'loan_id' as column_name, 'str' as declared_type, p.n as n_rows, p.loan_id__blank as n_blank, p.loan_id__sentinel as n_sentinel, p.loan_id__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'monthly_reporting_period' as column_name, 'yyyymm' as declared_type, p.n as n_rows, p.monthly_reporting_period__blank as n_blank, p.monthly_reporting_period__sentinel as n_sentinel, p.monthly_reporting_period__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'current_actual_upb' as column_name, 'double' as declared_type, p.n as n_rows, p.current_actual_upb__blank as n_blank, p.current_actual_upb__sentinel as n_sentinel, p.current_actual_upb__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'current_loan_delinquency_status' as column_name, 'str' as declared_type, p.n as n_rows, p.current_loan_delinquency_status__blank as n_blank, p.current_loan_delinquency_status__sentinel as n_sentinel, p.current_loan_delinquency_status__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'loan_age' as column_name, 'int' as declared_type, p.n as n_rows, p.loan_age__blank as n_blank, p.loan_age__sentinel as n_sentinel, p.loan_age__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'remaining_months_to_legal_maturity' as column_name, 'int' as declared_type, p.n as n_rows, p.remaining_months_to_legal_maturity__blank as n_blank, p.remaining_months_to_legal_maturity__sentinel as n_sentinel, p.remaining_months_to_legal_maturity__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'defect_settlement_date' as column_name, 'yyyymm' as declared_type, p.n as n_rows, p.defect_settlement_date__blank as n_blank, p.defect_settlement_date__sentinel as n_sentinel, p.defect_settlement_date__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'modification_flag' as column_name, 'str' as declared_type, p.n as n_rows, p.modification_flag__blank as n_blank, p.modification_flag__sentinel as n_sentinel, p.modification_flag__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'zero_balance_code' as column_name, 'str' as declared_type, p.n as n_rows, p.zero_balance_code__blank as n_blank, p.zero_balance_code__sentinel as n_sentinel, p.zero_balance_code__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'zero_balance_effective_date' as column_name, 'yyyymm' as declared_type, p.n as n_rows, p.zero_balance_effective_date__blank as n_blank, p.zero_balance_effective_date__sentinel as n_sentinel, p.zero_balance_effective_date__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'current_interest_rate' as column_name, 'double' as declared_type, p.n as n_rows, p.current_interest_rate__blank as n_blank, p.current_interest_rate__sentinel as n_sentinel, p.current_interest_rate__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'current_non_interest_bearing_upb' as column_name, 'double' as declared_type, p.n as n_rows, p.current_non_interest_bearing_upb__blank as n_blank, p.current_non_interest_bearing_upb__sentinel as n_sentinel, p.current_non_interest_bearing_upb__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'ddlpi' as column_name, 'yyyymm' as declared_type, p.n as n_rows, p.ddlpi__blank as n_blank, p.ddlpi__sentinel as n_sentinel, p.ddlpi__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'mi_recoveries' as column_name, 'double' as declared_type, p.n as n_rows, p.mi_recoveries__blank as n_blank, p.mi_recoveries__sentinel as n_sentinel, p.mi_recoveries__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'net_sales_proceeds' as column_name, 'double' as declared_type, p.n as n_rows, p.net_sales_proceeds__blank as n_blank, p.net_sales_proceeds__sentinel as n_sentinel, p.net_sales_proceeds__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'non_mi_recoveries' as column_name, 'double' as declared_type, p.n as n_rows, p.non_mi_recoveries__blank as n_blank, p.non_mi_recoveries__sentinel as n_sentinel, p.non_mi_recoveries__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'total_expenses' as column_name, 'double' as declared_type, p.n as n_rows, p.total_expenses__blank as n_blank, p.total_expenses__sentinel as n_sentinel, p.total_expenses__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'legal_costs' as column_name, 'double' as declared_type, p.n as n_rows, p.legal_costs__blank as n_blank, p.legal_costs__sentinel as n_sentinel, p.legal_costs__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'maintenance_preservation_costs' as column_name, 'double' as declared_type, p.n as n_rows, p.maintenance_preservation_costs__blank as n_blank, p.maintenance_preservation_costs__sentinel as n_sentinel, p.maintenance_preservation_costs__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'taxes_insurance' as column_name, 'double' as declared_type, p.n as n_rows, p.taxes_insurance__blank as n_blank, p.taxes_insurance__sentinel as n_sentinel, p.taxes_insurance__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'miscellaneous_expenses' as column_name, 'double' as declared_type, p.n as n_rows, p.miscellaneous_expenses__blank as n_blank, p.miscellaneous_expenses__sentinel as n_sentinel, p.miscellaneous_expenses__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'actual_loss' as column_name, 'double' as declared_type, p.n as n_rows, p.actual_loss__blank as n_blank, p.actual_loss__sentinel as n_sentinel, p.actual_loss__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'cumulative_modification_costs' as column_name, 'double' as declared_type, p.n as n_rows, p.cumulative_modification_costs__blank as n_blank, p.cumulative_modification_costs__sentinel as n_sentinel, p.cumulative_modification_costs__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'interest_rate_step_indicator' as column_name, 'str' as declared_type, p.n as n_rows, p.interest_rate_step_indicator__blank as n_blank, p.interest_rate_step_indicator__sentinel as n_sentinel, p.interest_rate_step_indicator__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'payment_deferral_flag' as column_name, 'str' as declared_type, p.n as n_rows, p.payment_deferral_flag__blank as n_blank, p.payment_deferral_flag__sentinel as n_sentinel, p.payment_deferral_flag__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'estimated_ltv' as column_name, 'int' as declared_type, p.n as n_rows, p.estimated_ltv__blank as n_blank, p.estimated_ltv__sentinel as n_sentinel, p.estimated_ltv__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'zero_balance_removal_upb' as column_name, 'double' as declared_type, p.n as n_rows, p.zero_balance_removal_upb__blank as n_blank, p.zero_balance_removal_upb__sentinel as n_sentinel, p.zero_balance_removal_upb__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'delinquent_accrued_interest' as column_name, 'double' as declared_type, p.n as n_rows, p.delinquent_accrued_interest__blank as n_blank, p.delinquent_accrued_interest__sentinel as n_sentinel, p.delinquent_accrued_interest__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'delinquency_due_to_disaster' as column_name, 'str' as declared_type, p.n as n_rows, p.delinquency_due_to_disaster__blank as n_blank, p.delinquency_due_to_disaster__sentinel as n_sentinel, p.delinquency_due_to_disaster__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'borrower_assistance_plan' as column_name, 'str' as declared_type, p.n as n_rows, p.borrower_assistance_plan__blank as n_blank, p.borrower_assistance_plan__sentinel as n_sentinel, p.borrower_assistance_plan__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'current_period_modification_costs' as column_name, 'double' as declared_type, p.n as n_rows, p.current_period_modification_costs__blank as n_blank, p.current_period_modification_costs__sentinel as n_sentinel, p.current_period_modification_costs__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'current_interest_bearing_upb' as column_name, 'double' as declared_type, p.n as n_rows, p.current_interest_bearing_upb__blank as n_blank, p.current_interest_bearing_upb__sentinel as n_sentinel, p.current_interest_bearing_upb__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'mi_cancellation_indicator' as column_name, 'str' as declared_type, p.n as n_rows, p.mi_cancellation_indicator__blank as n_blank, p.mi_cancellation_indicator__sentinel as n_sentinel, p.mi_cancellation_indicator__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'servicer_name' as column_name, 'str' as declared_type, p.n as n_rows, p.servicer_name__blank as n_blank, p.servicer_name__sentinel as n_sentinel, p.servicer_name__cast_fail as n_cast_fail from p
union all
select 'perf' as table_name, 'bankruptcy_cramdown_costs' as column_name, 'double' as declared_type, p.n as n_rows, p.bankruptcy_cramdown_costs__blank as n_blank, p.bankruptcy_cramdown_costs__sentinel as n_sentinel, p.bankruptcy_cramdown_costs__cast_fail as n_cast_fail from p
