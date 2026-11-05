{{ config(severity='warn') }}
-- idade de default < 1 indica evento anterior ao primeiro pagamento (inconsistencia de datas)
select loan_id, default_age from {{ ref('gold_loan_events') }} where default_age < 1
