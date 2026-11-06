{{ config(severity='warn') }}
-- Default antes do 1o pagamento (idade < 1) que NAO se explica por first_payment_date inconsistente
-- (loans modificados/convertidos reiniciam essa data). Resultado esperado: zero linhas.
select loan_id, default_age
from {{ ref('gold_loan_events') }}
where default_age < 1 and not first_payment_inconsistent
