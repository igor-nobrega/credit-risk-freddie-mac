import tomllib
from pathlib import Path

from credit_risk.pyproject_tasks import SEQUENCES, SIMPLE, ensure_tasks

ROOT = Path(__file__).resolve().parents[1]

# pyproject do pacote inicial (so as tarefas da Fase 0), como o usuario o recebeu
BOOT = """[project]
name = "x"
version = "0.1.0"

[tool.ruff]
line-length = 100

[tool.poe.tasks]
check = "python scripts/check_env.py"
smoke = "python scripts/smoke_test.py"
manifest = "python scripts/make_manifest.py"
lint = "ruff check ."
fmt = "ruff format ."
test = "pytest -q"
dbt-debug = "dbt debug --project-dir dbt --profiles-dir dbt"
dbt-smoke = "dbt build --project-dir dbt --profiles-dir dbt"
lab = "jupyter lab"
"""


def _tasks(text):
    return tomllib.loads(text.replace("\r\n", "\n"))["tool"]["poe"]["tasks"]


def _complete(text):
    t = _tasks(text)
    assert set(SIMPLE) | set(SEQUENCES) <= set(t)
    for name in SEQUENCES:  # cada passo e um { cmd = ... } (nunca uma string solta)
        assert all(isinstance(s, dict) and "cmd" in s for s in t[name]["sequence"])
    assert "--select smoke" in t["dbt-smoke"]


def test_adds_everything_to_phase0_file_and_is_idempotent():
    new, changes = ensure_tasks(BOOT)
    assert changes
    _complete(new)
    assert "[tool.ruff]" in new and "line-length = 100" in new  # nao mexe no resto
    again, changes2 = ensure_tasks(new)
    assert changes2 == [] and again == new


def test_keeps_windows_line_endings():
    crlf = BOOT.replace("\n", "\r\n")
    new, _ = ensure_tasks(crlf)
    assert "\r\n" in new and "\n" not in new.replace("\r\n", "")
    _complete(new)


def test_repairs_old_string_style_silver_and_old_smoke():
    old = BOOT + '\nsilver = "dbt build --select silver dq"\n'
    # 'silver' como string solta no meio da tabela e invalida? Nao: e uma chave de [tool.poe.tasks]
    new, changes = ensure_tasks(old)
    _complete(new)
    assert any("silver" in c for c in changes)


def test_project_pyproject_is_already_complete():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    new, changes = ensure_tasks(text)
    assert changes == [] and new == text, (
        f"faltam tarefas no pyproject.toml: rode `uv run python scripts/setup_tasks.py` ({changes})"
    )


def test_invalid_toml_is_not_touched():
    import pytest

    with pytest.raises(tomllib.TOMLDecodeError):
        ensure_tasks("[tool.poe.tasks\nx = 1")


def test_apply_to_file_preserves_crlf_bytes_and_makes_backup(tmp_path):
    from credit_risk.pyproject_tasks import apply_to_file

    f = tmp_path / "pyproject.toml"
    f.write_bytes(BOOT.replace("\n", "\r\n").encode())
    changes = apply_to_file(f, tmp_path / "bak")
    raw = f.read_bytes()
    assert changes and raw.count(b"\n") == raw.count(b"\r\n")  # nenhum LF solto
    assert (tmp_path / "bak" / "pyproject.toml.bak").read_bytes() == BOOT.replace(
        "\n", "\r\n"
    ).encode()
    assert apply_to_file(f, tmp_path / "bak") == []  # idempotente
    _complete(raw.decode())
