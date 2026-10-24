"""
Esquema do Freddie Mac Single-Family Loan-Level Dataset (Standard), General User Guide
Release 47 (julho/2026). Ordem das colunas = ordem do glossario do guia ("listed in the order
in which they appear in the files"). Arquivos pipe-delimited SEM header.

CONFIRME contra o arquivo de header/layout baixado do Clarity. Se a contagem de campos de um
arquivo divergir (31 em origination, 35 em performance), pare e investigue antes de ingerir.

Formato de cada coluna: (nome, tipo, [sentinelas = "nao informado"]). Tipos: str | int | double | yyyymm
Observacoes do guia: recuperacoes/ganhos sao NEGATIVOS e despesas/perdas POSITIVAS.
"""

ORIG_COLS = [
    ("credit_score", "int", ["9999"]),
    ("first_payment_date", "yyyymm", []),
    ("first_time_homebuyer_flag", "str", ["9"]),
    ("maturity_date", "yyyymm", []),
    ("msa", "str", []),  # nulo = fora de MSA ou desconhecido
    ("mi_pct", "int", ["999"]),  # 0 = sem seguro (valor valido, NAO e sentinela)
    ("number_of_units", "int", ["99"]),
    ("occupancy_status", "str", ["9"]),
    ("cltv", "int", ["999"]),
    ("dti", "int", ["999"]),  # todos os HARP vem 999
    ("original_upb", "double", []),
    ("ltv", "int", ["999"]),
    ("original_interest_rate", "double", []),
    ("channel", "str", ["9"]),
    ("prepayment_penalty_flag", "str", []),
    ("amortization_type", "str", []),
    ("property_state", "str", []),
    ("property_type", "str", ["99"]),
    ("postal_code", "str", ["000"]),  # 3 primeiros digitos; 000 = desconhecido
    ("loan_id", "str", []),
    ("loan_purpose", "str", ["9"]),
    ("original_loan_term", "int", []),
    ("number_of_borrowers", "int", ["99"]),
    ("seller_name", "str", []),
    ("super_conforming_flag", "str", []),
    ("pre_harp_loan_id", "str", []),
    ("special_eligibility_program", "str", []),
    ("harp_indicator", "str", []),
    ("property_valuation_method", "int", ["7"]),  # 7 = nao disponivel
    ("io_indicator", "str", []),
    ("vantage_score_4", "int", ["9999"]),
]

PERF_COLS = [
    ("loan_id", "str", []),
    ("monthly_reporting_period", "yyyymm", []),
    ("current_actual_upb", "double", []),
    ("current_loan_delinquency_status", "str", ["XX"]),  # 00, 01, 02, 03... ou RA (REO)
    ("loan_age", "int", []),
    ("remaining_months_to_legal_maturity", "int", []),
    ("defect_settlement_date", "yyyymm", []),
    ("modification_flag", "str", []),
    ("zero_balance_code", "str", []),
    ("zero_balance_effective_date", "yyyymm", []),
    ("current_interest_rate", "double", []),
    ("current_non_interest_bearing_upb", "double", []),
    ("ddlpi", "yyyymm", []),
    ("mi_recoveries", "double", []),
    ("net_sales_proceeds", "double", []),
    ("non_mi_recoveries", "double", []),
    ("total_expenses", "double", []),
    ("legal_costs", "double", []),
    ("maintenance_preservation_costs", "double", []),
    ("taxes_insurance", "double", []),
    ("miscellaneous_expenses", "double", []),
    ("actual_loss", "double", []),
    ("cumulative_modification_costs", "double", []),
    ("interest_rate_step_indicator", "str", []),
    ("payment_deferral_flag", "str", []),
    ("estimated_ltv", "int", ["999"]),
    ("zero_balance_removal_upb", "double", []),
    ("delinquent_accrued_interest", "double", []),
    ("delinquency_due_to_disaster", "str", []),
    ("borrower_assistance_plan", "str", []),
    ("current_period_modification_costs", "double", []),
    ("current_interest_bearing_upb", "double", []),
    ("mi_cancellation_indicator", "str", ["7"]),
    ("servicer_name", "str", []),
    ("bankruptcy_cramdown_costs", "double", []),
]

# Codigos de saldo zero (guia, secao "Zero Balance Codes")
ZERO_BALANCE_CODES = {
    "01": "Prepaid or Matured (Voluntary Payoff)",
    "02": "Third Party Sale",
    "03": "Short Sale or Charge Off",
    "09": "REO Disposition",
    "15": "Whole Loan Sales",
    "16": "Reperforming Loan Securitizations",
    "96": "Confirmed Underwriting Defect or Major Servicing Defect prior to credit event",
}

# Codigos para os quais o guia calcula Actual Loss. Candidatos a "evento de credito":
# a decisao final vai para docs/decision_log.md (D-002).
ZB_WITH_ACTUAL_LOSS = {"02", "03", "09", "15"}
