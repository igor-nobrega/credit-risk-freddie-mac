from credit_risk.duck import connect


def test_sentinel_and_blank_become_null(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("700|a\n9999|b\n|c\n", encoding="utf-8")
    con = connect(":memory:")
    rows = con.execute(f"""
        SELECT try_cast(nullif(nullif(trim(a), ''), '9999') AS INTEGER)
        FROM read_csv('{f.as_posix()}', delim='|', header=false, all_varchar=true,
                      columns={{'a':'VARCHAR','b':'VARCHAR'}})
    """).fetchall()
    assert [r[0] for r in rows] == [700, None, None]


def test_try_cast_does_not_raise_on_garbage():
    con = connect(":memory:")
    assert con.execute("SELECT try_cast('abc' AS INTEGER)").fetchone()[0] is None
