from credit_risk.reportlib import read_manual

PH = "_(a preencher)_"


def test_missing_or_empty_file_returns_placeholder(tmp_path):
    assert read_manual(tmp_path / "nao_existe.md", PH) == PH
    empty = tmp_path / "vazio.md"
    empty.write_text("  \n\n", encoding="utf-8")
    assert read_manual(empty, PH) == PH


def test_existing_text_is_used_and_normalized(tmp_path):
    f = tmp_path / "c.md"
    f.write_bytes("\n### Titulo\r\ntexto com acentuação\r\n\r\n".encode())
    assert read_manual(f, PH) == "### Titulo\ntexto com acentuação"
