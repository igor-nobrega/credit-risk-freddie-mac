"""
Esquema das duas tabelas do Freddie Mac Single-Family Loan-Level Dataset (Standard).
Formato de cada coluna: (nome, tipo, [valores sentinela = "nao informado"])
Tipos: str | int | double | yyyymm

ATENCAO: montado a partir do General User Guide. A ordem e os sentinelas PODEM mudar
entre releases. A fonte da verdade e o guia da release que voce baixou (registre a versao
em docs/decision_log.md). A ingestao valida a contagem de campos por arquivo.
"""

ORIG_COLS = [
    ("credit_score", "int", ["9999"]),
    ("first_payment_date", "yyyymm", []),
    ("first_time_homebuyer_flag", "str", ["9"]),
    ("maturity_date", "yyyymm", []),
    ("msa", "str", []),
    ("mi_pct", "int", ["999"]),
    ("number_of_units", "int", ["99"]),
    ("occupancy_status", "str", ["9"]),
    ("cltv", "int", ["999"]),
    ("dti", "int", ["999"]),
    ("original_upb", "double", []),
    ("ltv", "int", ["999"]),
    ("original_interest_rate", "double", []),
    ("channel", "str", ["9"]),
    ("ppm_flag", "str", []),
    ("amortization_type", "str", []),
    ("property_state", "str", []),
    ("property_type", "str", ["99"]),
    ("postal_code", "str", []),
    ("loan_sequence_number", "str", []),
    ("loan_purpose", "str", ["9"]),
    ("original_loan_term", "int", []),
    ("number_of_borrowers", "int", ["99"]),
    ("seller_name", "str", []),
    ("servicer_name", "str", []),
    ("super_conforming_flag", "str", []),
    ("pre_harp_loan_sequence_number", "str", []),
    ("program_indicator", "str", ["9"]),
    ("harp_indicator", "str", []),
    ("property_valuation_method", "int", ["9"]),
    ("io_indicator", "str", []),
    ("mi_cancellation_indicator", "str", ["7", "9"]),
]

PERF_COLS = [
    ("loan_sequence_number", "str", []),
    ("monthly_reporting_period", "yyyymm", []),
    ("current_actual_upb", "double", []),
    ("current_loan_delinquency_status", "str", ["XX"]),  # 0,1,2,3.. ou RA (REO)
    ("loan_age", "int", []),
    ("remaining_months_to_legal_maturity", "int", []),
    ("defect_settlement_date", "yyyymm", []),
    ("modification_flag", "str", []),
    ("zero_balance_code", "str", []),
    ("zero_balance_effective_date", "yyyymm", []),
    ("current_interest_rate", "double", []),
    ("current_deferred_upb", "double", []),
    ("ddlpi", "yyyymm", []),
    ("mi_recoveries", "double", []),
    ("net_sale_proceeds", "str", []),  # pode ter flags alfabeticos: tratar a parte
    ("non_mi_recoveries", "double", []),
    ("total_expenses", "double", []),
    ("legal_costs", "double", []),
    ("maintenance_preservation_costs", "double", []),
    ("taxes_insurance", "double", []),
    ("misc_expenses", "double", []),
    ("actual_loss_calculation", "double", []),
    ("cumulative_modification_cost", "double", []),
    ("step_modification_flag", "str", []),
    ("payment_deferral", "str", []),
    ("estimated_ltv", "int", ["999"]),
    ("zero_balance_removal_upb", "double", []),
    ("delinquent_accrued_interest", "double", []),
    ("delinquency_due_to_disaster", "str", []),
    ("borrower_assistance_status_code", "str", []),
    ("current_month_modification_cost", "double", []),
    ("interest_bearing_upb", "double", []),
]
