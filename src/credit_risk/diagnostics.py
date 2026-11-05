"""Diagnosticos sobre as tabelas gold (somente leitura)."""

from __future__ import annotations


def _t(frame) -> str:
    return "(nenhum)" if len(frame) == 0 else frame.to_string(index=False)


def default_age_report(con) -> str:
    """Explica os loans com default_age < 1 (default antes do 1o pagamento), alvo do WARN do dbt test."""
    q = lambda sql: con.execute(sql).fetchdf()  # noqa: E731
    out: list[str] = []

    s = q("""
        select count(*) filter (where has_perf) as loans_com_performance,
               count(*) filter (where default_age is not null) as defaults,
               count(*) filter (where default_age < 1) as defaults_com_idade_menor_que_1
        from gold.gold_loan_events""")
    n_def, n_bad = int(s["defaults"][0]), int(s["defaults_com_idade_menor_que_1"][0])
    pct = f"{100 * n_bad / n_def:.3f}%" if n_def else "n/a"
    out += ["=== A. RESUMO ===", _t(s), f"-> {pct} dos defaults tem idade < 1", ""]

    out += [
        "=== F. IDADE DA PRIMEIRA LINHA DE PERFORMANCE (normal: 0; maior = loan so entra no dataset na aquisicao) ===",
        _t(
            q("""
            select case when i < -1 then '< -1 (inconsistente)' when i = -1 then '-1' when i = 0 then '0'
                        when i = 1 then '1' when i between 2 and 3 then '2 a 3'
                        when i between 4 and 12 then '4 a 12' else '> 12' end as idade_1a_linha,
                   count(*) as loans, round(100.0 * count(*) / sum(count(*)) over (), 2) as pct
            from (select date_diff('month', o.first_payment_date, e.first_period) + 1 as i
                  from gold.gold_loan_events e join silver.silver_orig o using (loan_id) where e.has_perf)
            group by 1 order by min(i)""")
        ),
        "",
        "=== H. MESES ENTRE O TRIMESTRE DE ORIGINACAO (loan_id) E O 1o PAGAMENTO (tipico 1 a 5; fora de 0-8 = inconsistente) ===",
        _t(
            q("""
            select case when m < 0 then '< 0' when m > 8 then '> 8' else cast(m as varchar) end as meses,
                   count(*) as loans
            from (select months_to_first_payment as m from gold.gold_loan_events where months_to_first_payment is not null)
            group by 1 order by min(m)""")
        ),
        "",
    ]
    if n_bad == 0:
        out.append("Nenhum loan com default_age < 1: o WARN, se existir, vem de outro teste.")
        return "\n".join(out)

    out += [
        "=== B. POR GATILHO E IDADE (idade 0 = mes anterior ao 1o pagamento) ===",
        _t(
            q("""
            select default_trigger as gatilho, default_age as idade, count(*) as loans
            from gold.gold_loan_events where default_age < 1
            group by all order by loans desc limit 15""")
        ),
        "",
        "=== C. CODIGO DO EVENTO DE CREDITO desses loans (02 terceiros, 03 short sale, 09 REO, 15 venda de nota) ===",
        _t(
            q("""
            select coalesce(credit_event_code, '(sem evento de credito)') as credit_event_code, default_trigger as gatilho, count(*) as loans
            from gold.gold_loan_events where default_age < 1
            group by all order by loans desc limit 15""")
        ),
        "",
        "=== D. POR VINTAGE (top 10) ===",
        _t(
            q("""
            select vintage_year as vintage, count(*) as loans
            from gold.gold_loan_events where default_age < 1
            group by all order by loans desc limit 10""")
        ),
        "",
        "=== E. CADA GATILHO CANDIDATO com idade < 1 ===",
        _t(
            q("""
            select count(*) filter (where dpd60_age < 1) as dpd60,
                   count(*) filter (where dpd90_age < 1) as dpd90,
                   count(*) filter (where dpd180_age < 1) as dpd180,
                   count(*) filter (where credit_event_age < 1) as evento_credito
            from gold.gold_loan_events""")
        ),
        "",
        "=== G. EXEMPLOS (nivel de emprestimo; so para voce, nao publique) ===",
        _t(
            q("""
            select loan_id, vintage_year, default_trigger as gatilho, default_age as idade, default_period,
                   credit_event_code, dpd90_age, credit_event_age, round(upb_at_default, 0) as upb_default
            from gold.gold_loan_events where default_age < 1
            order by default_age, vintage_year limit 8""")
        ),
    ]
    return "\n".join(out)
