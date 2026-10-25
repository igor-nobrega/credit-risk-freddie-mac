"""Fase 1 - Ingestao BRONZE: arquivos pipe sem header -> Parquet, sem perder nenhuma linha.

Regras da camada bronze:
  * NADA de limpeza: tudo VARCHAR (a tipagem e das sentinelas e na silver).
  * Linhagem em toda linha: _source_file, _vintage, _ingested_at.
  * Estrutura validada ANTES: se o layout do arquivo nao bate com o esquema, o arquivo e barrado.
  * Linhas malformadas nao somem: vao para data/bronze/rejects/ e entram na reconciliacao.
  * Reconciliacao obrigatoria: linhas nao vazias do arquivo = linhas carregadas + rejeitadas.
  * Idempotente: arquivos ja ingeridos (mesmo tamanho) sao pulados, salvo force=True.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import config
from .duck import connect
from .freddie_schema import ORIG_COLS, PERF_COLS

SCHEMAS = {"orig": ORIG_COLS, "perf": PERF_COLS}
MIN_PCT_EXPECTED_FIELDS = 50.0  # abaixo disso o layout dominante do arquivo NAO e o do esquema
WARN_PCT_EXPECTED_FIELDS = 99.9  # abaixo disso ha linhas malformadas (vao para rejeitados)


@dataclass
class FileResult:
    kind: str
    file: str
    vintage: str
    size_bytes: int
    expected_fields: int
    lines_nonblank: int = 0
    pct_expected_fields: float = 0.0
    field_histogram: dict = field(default_factory=dict)
    rows_loaded: int = 0
    rows_rejected: int = 0
    status: str = "PENDING"  # OK | SKIPPED | LAYOUT_MISMATCH | RECON_FAIL | ERROR
    detail: str = ""
    seconds: float = 0.0


def _q(path: Path) -> str:
    """Caminho seguro para literal SQL (aspas simples escapadas, barras normalizadas)."""
    return path.as_posix().replace("'", "''")


def _vintage(path: Path) -> str:
    m = re.findall(r"(\d{4}(?:Q[1-4])?)", path.stem)
    return m[-1] if m else "unknown"


def _columns_sql(cols) -> str:
    return "{" + ", ".join(f"'{c[0]}':'VARCHAR'" for c in cols) + "}"


def discover(raw_dir: Path, kind: str) -> list[Path]:
    return sorted((raw_dir / kind).glob("*.txt"))


def _log_path(bronze_dir: Path, kind: str, stem: str) -> Path:
    return bronze_dir / "_log" / f"{kind}__{stem}.json"


def ingest_file(kind: str, path: Path, bronze_dir: Path, force: bool = False) -> FileResult:
    cols = SCHEMAS[kind]
    res = FileResult(kind, path.name, _vintage(path), path.stat().st_size, len(cols))
    out = bronze_dir / kind / f"{path.stem}.parquet"
    log = _log_path(bronze_dir, kind, path.stem)
    t0 = time.time()

    if not force and out.exists() and log.exists():
        prev = json.loads(log.read_text(encoding="utf-8"))
        if prev.get("size_bytes") == res.size_bytes and prev.get("status") in ("OK", "SKIPPED"):
            prev.update(status="SKIPPED", detail="ja ingerido (mesmo tamanho)")
            return FileResult(**prev)

    for d in (out.parent, log.parent, bronze_dir / "rejects"):
        d.mkdir(parents=True, exist_ok=True)

    con = connect(":memory:")
    try:
        # 1) estrutura: histograma de campos por linha (leitura como coluna unica)
        hist = con.execute(f"""
            SELECT length(line) - length(replace(line, '|', '')) + 1 AS n_fields, count(*) AS n
            FROM read_csv('{_q(path)}', header=false, delim='\\x1f', quote='', escape='',
                          columns={{'line':'VARCHAR'}}, all_varchar=true)
            WHERE line IS NOT NULL
            GROUP BY 1 ORDER BY 1
        """).fetchall()
        res.field_histogram = {int(k): int(v) for k, v in hist}
        res.lines_nonblank = sum(res.field_histogram.values())
        ok_lines = res.field_histogram.get(res.expected_fields, 0)
        res.pct_expected_fields = (
            round(100 * ok_lines / res.lines_nonblank, 4) if res.lines_nonblank else 0.0
        )
        if res.lines_nonblank == 0 or res.pct_expected_fields < MIN_PCT_EXPECTED_FIELDS:
            res.status = "LAYOUT_MISMATCH"
            res.detail = (
                f"esperado {res.expected_fields} campos; histograma {res.field_histogram}. "
                "Confira o arquivo de layout do Clarity e src/credit_risk/freddie_schema.py"
            )
            return res

        if res.pct_expected_fields < WARN_PCT_EXPECTED_FIELDS:
            res.detail = f"{100 - res.pct_expected_fields:.4f}% das linhas com n de campos diferente do esperado"

        # 2) carga: tudo texto + linhagem; malformadas vao para a tabela de rejeitados
        con.execute(f"""
            COPY (
              SELECT *, '{path.name.replace("'", "''")}' AS _source_file,
                        '{res.vintage}' AS _vintage,
                        current_timestamp AS _ingested_at
              FROM read_csv('{_q(path)}', delim='|', header=false, quote='', escape='',
                            all_varchar=true, columns={_columns_sql(cols)}, store_rejects=true)
            ) TO '{_q(out)}' (FORMAT parquet, COMPRESSION zstd)
        """)
        res.rows_loaded = con.execute(f"SELECT count(*) FROM read_parquet('{_q(out)}')").fetchone()[
            0
        ]
        res.rows_rejected = con.execute(
            "SELECT count(DISTINCT line) FROM reject_errors"
        ).fetchone()[0]
        if res.rows_rejected:
            rej = bronze_dir / "rejects" / f"{kind}__{path.stem}__rejects.parquet"
            con.execute(
                f"COPY (SELECT line, column_idx, error_type, csv_line FROM reject_errors) "
                f"TO '{_q(rej)}' (FORMAT parquet)"
            )

        # 3) reconciliacao: nada pode sumir sem explicacao
        if res.lines_nonblank == res.rows_loaded + res.rows_rejected:
            res.status = "OK"
        else:
            res.status = "RECON_FAIL"
            res.detail = f"linhas={res.lines_nonblank} != carregadas={res.rows_loaded} + rejeitadas={res.rows_rejected}"
    except Exception as e:  # noqa: BLE001
        res.status, res.detail = "ERROR", f"{type(e).__name__}: {e}"
    finally:
        con.close()
        res.seconds = round(time.time() - t0, 2)
        log.write_text(json.dumps(asdict(res), indent=2), encoding="utf-8")
    return res


def build_views(bronze_dir: Path, db_path: Path | None = None) -> None:
    """Cria views bronze_orig / bronze_perf / bronze_ingestion_log no warehouse."""
    con = connect(db_path)
    try:
        for kind in SCHEMAS:
            if any((bronze_dir / kind).glob("*.parquet")):
                g = _q(bronze_dir / kind / "*.parquet")
                con.execute(
                    f"CREATE OR REPLACE VIEW bronze_{kind} AS SELECT * FROM read_parquet('{g}', union_by_name=true)"
                )
        if any((bronze_dir / "_log").glob("*.json")):
            g = _q(bronze_dir / "_log" / "*.json")
            con.execute(
                f"CREATE OR REPLACE VIEW bronze_ingestion_log AS SELECT * FROM read_json_auto('{g}')"
            )
    finally:
        con.close()


def ingest_all(
    kinds=("orig", "perf"),
    raw_dir: Path | None = None,
    bronze_dir: Path | None = None,
    db_path: Path | None = None,
    force: bool = False,
    report_csv: Path | None = None,
) -> list[FileResult]:
    raw_dir = raw_dir or config.RAW_DIR
    bronze_dir = bronze_dir or config.BRONZE_DIR
    results: list[FileResult] = []
    for kind in kinds:
        files = discover(raw_dir, kind)
        if not files:
            print(f"[WARN] nenhum .txt em {raw_dir / kind}")
        for p in files:
            r = ingest_file(kind, p, bronze_dir, force)
            results.append(r)
            print(
                f"[{r.status:^15}] {r.kind}:{r.file}  linhas={r.lines_nonblank:,}  "
                f"carregadas={r.rows_loaded:,}  rejeitadas={r.rows_rejected:,}  {r.seconds}s  {r.detail}"
            )
    build_views(bronze_dir, db_path)
    if report_csv and results:
        import csv

        report_csv.parent.mkdir(parents=True, exist_ok=True)
        with report_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(
                [
                    "kind",
                    "file",
                    "vintage",
                    "lines",
                    "loaded",
                    "rejected",
                    "pct_expected_fields",
                    "status",
                ]
            )
            for r in results:
                skipped = r.status == "SKIPPED"
                w.writerow(
                    [
                        r.kind,
                        r.file,
                        r.vintage,
                        r.lines_nonblank,
                        r.rows_loaded,
                        r.rows_rejected,
                        r.pct_expected_fields,
                        "OK" if skipped else r.status,
                        "skipped" if skipped else "ingested",
                    ]
                )
    return results
