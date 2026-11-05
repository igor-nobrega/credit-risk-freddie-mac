"""Mostra EXEMPLOS (ate 5) de loans que violam cada regra de qualidade, para voce entender a sujeira.

Uso: uv run poe inspect-dq
ATENCAO: a saida e em nivel de emprestimo. Fica so no terminal: NAO copie para o repositorio.
"""

from credit_risk.duck import connect

con = connect(read_only=True)

QUERIES = {
    "R12 - ano do loan_id difere da vintage do arquivo": """
        select loan_id, vintage_year, first_payment_date, original_upb from silver.silver_orig
        where try_cast(substr(loan_id, 2, 2) as integer) is not null
          and (case when try_cast(substr(loan_id, 2, 2) as integer) = 99 then 1999
                    else 2000 + try_cast(substr(loan_id, 2, 2) as integer) end) != vintage_year limit 5""",
    "R14 - loans na originacao sem performance": """
        select o.loan_id, o.vintage_year, o.first_payment_date, o.original_upb from silver.silver_orig o
        where not exists (select 1 from silver.silver_perf p where p.loan_id = o.loan_id) limit 5""",
    "R18 - linhas apos o evento de saldo zero": """
        with zb as (select loan_id, min(zero_balance_effective_date) d from silver.silver_perf
                    where zero_balance_code is not null and zero_balance_effective_date is not null group by loan_id)
        select p.loan_id, p.monthly_reporting_period, zb.d as zb_date, p.zero_balance_code, p.current_actual_upb
        from silver.silver_perf p join zb using (loan_id) where p.monthly_reporting_period > zb.d limit 5""",
    "R19 - loans com buraco na serie mensal": """
        select loan_id, vintage_year, first_period, last_period, n_perf_rows,
               date_diff('month', first_period, last_period) + 1 as meses_esperados
        from gold.gold_loan_events where has_perf
          and date_diff('month', first_period, last_period) + 1 != n_perf_rows limit 5""",
    "R22 - net_sales_proceeds positivo": """
        select loan_id, monthly_reporting_period, zero_balance_code, net_sales_proceeds, actual_loss
        from silver.silver_perf where net_sales_proceeds > 0 limit 5""",
    "R23 - loan_age difere da idade recalculada (nao modificados)": """
        select p.loan_id, p.monthly_reporting_period, p.loan_age,
               date_diff('month', o.first_payment_date, p.monthly_reporting_period) + 1 as idade_recalculada
        from silver.silver_perf p join silver.silver_orig o using (loan_id)
        where p.modification_flag is null and p.loan_age is not null
          and p.loan_age != date_diff('month', o.first_payment_date, p.monthly_reporting_period) + 1 limit 5""",
}
for title, sql in QUERIES.items():
    print(f"\n=== {title} ===")
    try:
        print(con.execute(sql).fetchdf().to_string(index=False))
    except Exception as e:  # noqa: BLE001
        print(f"(nao foi possivel executar: {type(e).__name__}: {e})")
con.close()
