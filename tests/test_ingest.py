import json

from credit_risk.duck import connect
from credit_risk.ingest import ingest_all
from credit_risk.synth import make_synthetic


def _run(tmp_path, **kw):
    return ingest_all(
        raw_dir=tmp_path / "raw",
        bronze_dir=tmp_path / "bronze",
        db_path=tmp_path / "wh.duckdb",
        **kw,
    )


def test_bronze_reconciles_and_rejects_bad_lines(tmp_path):
    make_synthetic(tmp_path / "raw", year=2010, n_loans=60)
    res = {r.kind: r for r in _run(tmp_path)}
    o, p = res["orig"], res["perf"]
    assert o.status == "OK" and p.status == "OK"
    # 60 loans + 1 duplicado + 1 linha curta = 62 linhas nao vazias; a curta vai para rejeitados
    assert (o.lines_nonblank, o.rows_loaded, o.rows_rejected) == (62, 61, 1)
    assert p.lines_nonblank == p.rows_loaded + p.rows_rejected and p.rows_rejected == 1
    assert (tmp_path / "bronze" / "rejects").exists()


def test_lineage_columns_and_views(tmp_path):
    make_synthetic(tmp_path / "raw", year=2011, n_loans=120)
    _run(tmp_path)
    con = connect(tmp_path / "wh.duckdb", read_only=True)
    cols = [c[0] for c in con.execute("DESCRIBE bronze_orig").fetchall()]
    assert {"_source_file", "_vintage", "_ingested_at", "loan_id", "credit_score"} <= set(cols)
    assert con.execute("SELECT DISTINCT _vintage FROM bronze_orig").fetchall() == [("2011",)]
    # bronze nao limpa nada: a sentinela continua la, como texto
    assert (
        con.execute(
            "SELECT count(*) FROM bronze_orig WHERE credit_score = '9999' OR dti = '999'"
        ).fetchone()[0]
        > 0
    )
    assert con.execute("SELECT count(*) FROM bronze_ingestion_log").fetchone()[0] == 2
    con.close()


def test_second_run_is_idempotent_and_force_reingests(tmp_path):
    make_synthetic(tmp_path / "raw", year=2012, n_loans=15)
    _run(tmp_path)
    assert {r.status for r in _run(tmp_path)} == {"SKIPPED"}
    assert {r.status for r in _run(tmp_path, force=True)} == {"OK"}


def test_layout_mismatch_blocks_file(tmp_path):
    d = tmp_path / "raw" / "orig"
    d.mkdir(parents=True)
    (d / "sample_orig_2009.txt").write_text(
        "\n".join("|".join(["x"] * 28) for _ in range(50)) + "\n"
    )
    (r,) = _run(tmp_path, kinds=("orig",))
    assert r.status == "LAYOUT_MISMATCH" and r.field_histogram == {28: 50}
    assert not (tmp_path / "bronze" / "orig" / "sample_orig_2009.parquet").exists()
    log = json.loads((tmp_path / "bronze" / "_log" / "orig__sample_orig_2009.json").read_text())
    assert log["status"] == "LAYOUT_MISMATCH"
