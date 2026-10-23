"""Gera docs/raw_manifest.sha256 (hash, tamanho, caminho) dos arquivos em data/raw. Multiplataforma."""

import hashlib
from pathlib import Path

from credit_risk import config

OUT = Path("docs/raw_manifest.sha256")


def sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


OUT.parent.mkdir(parents=True, exist_ok=True)
files = sorted(
    p
    for p in config.RAW_DIR.rglob("*")
    if p.is_file() and p.suffix.lower() in {".txt", ".zip", ".csv"}
)
with OUT.open("w", encoding="utf-8", newline="\n") as f:
    for p in files:
        f.write(f"{sha256(p)}  {p.stat().st_size}  {p.relative_to(config.DATA_DIR).as_posix()}\n")
print(f"{len(files)} arquivo(s) no manifesto -> {OUT}")
