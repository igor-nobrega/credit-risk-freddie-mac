"""Diagnostico do ambiente. Uso: uv run poe check   (sai com codigo 1 se houver [FAIL])."""

from __future__ import annotations

import importlib.metadata as md
import os
import shutil
import subprocess
import sys
from pathlib import Path

from credit_risk import config
from credit_risk.duck import connect

fails = 0


def say(tag: str, msg: str) -> None:
    global fails
    fails += tag == "FAIL"
    print(f"[{tag:^4}] {msg}")


def run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=cwd)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


# 1. Python
v = sys.version_info
say(
    "OK" if (v.major, v.minor) == (3, 12) else "WARN",
    f"Python {v.major}.{v.minor}.{v.micro} em {sys.executable}",
)

# 2. Pacotes
dists = [
    "duckdb",
    "pyarrow",
    "polars",
    "pandas",
    "dbt-core",
    "dbt-duckdb",
    "scikit-learn",
    "statsmodels",
    "lightgbm",
    "lifelines",
    "optbinning",
    "shap",
    "matplotlib",
    "plotly",
    "jupyterlab",
    "jupytext",
    "ruff",
    "pytest",
    "pre-commit",
    "poethepoet",
]
missing = []
for d in dists:
    try:
        md.version(d)
    except md.PackageNotFoundError:
        missing.append(d)
say(
    "OK" if not missing else "FAIL",
    f"{len(dists) - len(missing)}/{len(dists)} pacotes instalados"
    + (f" | faltam: {missing}" if missing else ""),
)

# 3. Imports reais (pega wheels quebrados)
bad = []
for m in [
    "duckdb",
    "pyarrow",
    "polars",
    "pandas",
    "sklearn",
    "statsmodels",
    "lightgbm",
    "lifelines",
    "optbinning",
    "shap",
]:
    try:
        __import__(m)
    except Exception as e:  # noqa: BLE001
        bad.append(f"{m}: {type(e).__name__}: {e}")
say(
    "OK" if not bad else "FAIL",
    "imports" + (": " + "; ".join(bad) if bad else " ok (incl. lightgbm, optbinning, shap)"),
)

# 4. Recursos
try:
    import psutil

    gb = psutil.virtual_memory().total / 2**30
    say(
        "OK" if gb >= 16 else "WARN",
        f"RAM total visivel: {gb:.1f} GB | DuckDB memory_limit={config.DUCKDB_MEMORY_LIMIT}",
    )
except ImportError:
    say("WARN", "psutil ausente")
free = shutil.disk_usage(config.ROOT).free / 2**30
say(
    "OK" if free >= 30 else "WARN",
    f"Disco livre em {config.ROOT.anchor or config.ROOT}: {free:.0f} GB (recomendado >= 30 GB)",
)

# 5. OneDrive / caminho
r = str(config.ROOT).lower()
od = [os.environ.get(k) for k in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")]
in_od = "onedrive" in r or any(p and str(config.ROOT).lower().startswith(p.lower()) for p in od)
say(
    "WARN" if in_od else "OK",
    "projeto dentro do OneDrive (risco de travar DuckDB/venv)"
    if in_od
    else "projeto fora do OneDrive",
)
maxlen = 0
for base in (Path(sys.prefix), config.ROOT / "src"):
    for dp, _, fn in os.walk(base):
        for f in fn:
            maxlen = max(maxlen, len(dp) + 1 + len(f))
lp = None
if sys.platform == "win32":
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem"
        ) as k:
            lp = winreg.QueryValueEx(k, "LongPathsEnabled")[0] == 1
    except OSError:
        lp = False
tag = "WARN" if (maxlen > 240 and lp is False) else "OK"
say(
    tag,
    f"maior caminho no .venv: {maxlen} chars (limite classico 260)"
    + ("" if lp is None else f" | LongPathsEnabled={lp}"),
)

# 6. DuckDB funcional
try:
    con = connect(":memory:")
    p = (config.TMP_DIR / "check.parquet").as_posix()
    con.execute(f"COPY (SELECT range AS i FROM range(1000)) TO '{p}' (FORMAT parquet)")
    n = con.execute(f"SELECT count(*) FROM '{p}'").fetchone()[0]
    say("OK" if n == 1000 else "FAIL", f"DuckDB {md.version('duckdb')}: parquet ida e volta")
    con.close()
except Exception as e:  # noqa: BLE001
    say("FAIL", f"DuckDB: {e}")

# 7. CLIs (rodam via `uv run`, que poe o .venv no PATH)
for name, cmd in [
    ("dbt", ["dbt", "--version"]),
    ("quarto", ["quarto", "--version"]),
    ("ruff", ["ruff", "--version"]),
]:
    exe = shutil.which(cmd[0])
    if not exe:
        if name == "quarto":
            say(
                "WARN",
                "quarto nao encontrado (instale: winget install --id Posit.Quarto -e; so necessario na fase de relatorio)",
            )
        else:
            say("FAIL", f"{name} nao encontrado no PATH (rode via `uv run poe check`)")
        continue
    code, out = run(cmd)
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    pick = next(
        (ln for ln in lines if "installed" in ln.lower()), lines[0] if lines else "sem saida"
    )
    say("OK" if code == 0 else "WARN", f"{name}: {pick}")

# 8. Git / GitHub
if shutil.which("git"):
    code, remote = run(["git", "remote", "get-url", "origin"], config.ROOT)
    say(
        "OK" if code == 0 else "WARN",
        f"git origin = {remote}"
        if code == 0
        else "git sem remote 'origin' (ainda nao sincronizado com o GitHub)",
    )
    if code == 0:
        _, st = run(["git", "status", "-sb"], config.ROOT)
        say("OK", f"git: {st.splitlines()[0]}")
else:
    say("FAIL", "git nao encontrado")

print("\nRESULTADO:", "FALHAS ENCONTRADAS" if fails else "ambiente OK")
sys.exit(1 if fails else 0)
