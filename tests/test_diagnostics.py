import duckdb

from credit_risk.diagnostics import default_age_report


def _con(rows):
    con = duckdb.connect(":memory:")
    con.execute("create schema gold; create schema silver")
    con.execute("""create table gold.gold_loan_events (
        loan_id varchar, vintage_year integer, has_perf boolean, first_period date, default_period date,
        default_age integer, default_trigger varchar, credit_event_code varchar, dpd60_age integer, dpd90_age integer,
        dpd180_age integer, credit_event_age integer, upb_at_default double, months_to_first_payment integer)""")
    con.execute("create table silver.silver_orig (loan_id varchar, first_payment_date date)")
    for r in rows:
        con.execute("insert into gold.gold_loan_events values (?,?,true,?,?,?,?,?,?,?,?,?,?,2)", r)
        con.execute("insert into silver.silver_orig values (?, date '2010-03-01')", [r[0]])
    return con


D = "2010-02-01"


def test_reports_early_defaults_with_breakdowns():
    con = _con(
        [
            ("F10Q10000001", 2010, D, D, 0, "credit_event", "15", None, None, None, 0, 100000.0),
            ("F10Q10000002", 2010, D, D, 0, "credit_event", "15", None, None, None, 0, 90000.0),
            ("F10Q10000003", 2011, D, D, -1, "dpd90", None, 1, -1, 2, None, 50000.0),
            ("F10Q10000004", 2010, D, "2012-01-01", 22, "dpd90", None, 20, 22, None, None, 70000.0),
        ]
    )
    text = default_age_report(con)
    assert "A. RESUMO" in text and "75.000%" in text  # 3 de 4 defaults tem idade < 1
    assert "(nenhum)" not in text.split("=== B.")[1].split("=== C.")[0]
    assert "15" in text.split("=== C.")[1].split("=== D.")[0]  # codigo de saldo zero 15 aparece
    assert "F10Q10000001" in text.split("=== G.")[1]
    assert "F10Q10000004" not in text.split("=== G.")[1]  # idade 22 nao e exemplo


def test_no_early_defaults_returns_short_report():
    con = _con(
        [("F10Q10000009", 2010, D, "2011-01-01", 12, "dpd90", None, 10, 12, None, None, 1.0)]
    )
    text = default_age_report(con)
    assert "Nenhum loan com default_age < 1" in text and "=== G." not in text
    assert "=== F." in text and "=== H." in text  # distribuicoes da populacao aparecem sempre
