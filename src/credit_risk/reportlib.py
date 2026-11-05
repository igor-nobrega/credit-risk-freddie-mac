"""Utilitarios dos geradores de relatorio."""

from __future__ import annotations

from pathlib import Path


def read_manual(path: str | Path, placeholder: str) -> str:
    """Texto escrito a mao que sobrevive a regeneracao do relatorio.

    Se o arquivo existir e tiver conteudo, devolve-o (sem espacos nas pontas); senao, o placeholder.
    """
    p = Path(path)
    if p.exists():
        with p.open("r", encoding="utf-8", newline=None) as f:  # newline=None: CRLF vira \n
            text = f.read().strip()
        if text:
            return text
    return placeholder
