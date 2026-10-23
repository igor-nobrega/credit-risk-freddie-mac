"""Teste de fumaca: DuckDB le arquivo pipe sem header, trata sentinela e grava Parquet."""

from credit_risk import config
from credit_risk.duck import connect

config.ensure_dirs()
src = config.TMP_DIR / "smoke.txt"
src.write_text("700|202001|A\n9999|202002|B\n||C\n", encoding="utf-8")

con = connect(config.TMP_DIR / "smoke.duckdb")
rows = con.execute(f"""
    SELECT credit_score,
           try_cast(nullif(nullif(trim(credit_score), ''), '9999') AS INTEGER) AS fico_clean
    FROM read_csv('{src.as_posix()}', delim='|', header=false, all_varchar=true,
                  columns={{'credit_score':'VARCHAR','dt':'VARCHAR','flag':'VARCHAR'}})
""").fetchall()
print(rows)
assert rows[0][1] == 700 and rows[1][1] is None and rows[2][1] is None

out = config.TMP_DIR / "smoke.parquet"
con.execute(
    f"COPY (SELECT * FROM read_csv('{src.as_posix()}', delim='|', header=false, all_varchar=true)) "
    f"TO '{out.as_posix()}' (FORMAT parquet)"
)
assert con.execute(f"SELECT count(*) FROM '{out.as_posix()}'").fetchone()[0] == 3
mem = con.execute("SELECT current_setting('memory_limit')").fetchone()[0]
con.close()
print(f"DuckDB OK | memory_limit={mem} | threads={config.DUCKDB_THREADS} | tmp={config.TMP_DIR}")
