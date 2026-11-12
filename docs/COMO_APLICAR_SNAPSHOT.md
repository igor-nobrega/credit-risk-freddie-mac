# Como aplicar o snapshot (terminal do VS Code, sem administrador)

O snapshot (`credit-risk_snapshot_fase4b.zip`) substitui TODOS os patches anteriores. Ele traz código, testes, dbt, scripts
e documentação técnica. **Não sobrescreve nada que é seu**: `README.md`, `pyproject.toml`, `uv.lock`, `.gitignore`,
`.vscode/`, `data/` e os textos que você escreve (`docs/decision_log.md`, `docs/dq_conclusions.md`,
`docs/default_decision.md`, `docs/eda_insights.md`). Cópias de referência desses textos (`*.template.md`) ficam em `docs/_templates/`.

## 1. Aplicar
```powershell
cd C:\Users\Igor\Desktop\projetos\20261201_HipotecasAmericanas
$tmp = "$env:TEMP\credit-risk-snapshot"
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -Path "C:\Downloads\credit-risk_snapshot_fase4b.zip" -DestinationPath $tmp
robocopy $tmp . /E /XF decision_log.md dq_conclusions.md default_decision.md eda_insights.md README.md pyproject.toml uv.lock .gitignore /XD .git .venv data .vscode /NFL /NDL /NJH /NJS /NP
if ($LASTEXITCODE -ge 8) { "ERRO no robocopy (codigo $LASTEXITCODE)" } else { "Snapshot aplicado (codigo $LASTEXITCODE = sucesso)" }
```
O `robocopy` usa códigos de saída de 0 a 7 para sucesso; 8 ou mais indica erro.

Se ainda nao existir, copie o rascunho dos insights da EDA (e revise-o depois):
```powershell
if (-not (Test-Path docs\eda_insights.md)) { Copy-Item docs\_templates\eda_insights.template.md docs\eda_insights.md }
```

## 2. Completar o `pyproject.toml` e validar
```powershell
uv sync --locked
uv run python scripts/setup_tasks.py
uv run poe lint
uv run poe test
uv run poe doctor
```
Esperado: `All checks passed!`, todos os testes passando e o `doctor` sem `[FAIL]`. O `doctor` indica a última camada
válida do seu warehouse e o PRÓXIMO PASSO. Se a gold ou a EDA estiverem desatualizadas, ele diz qual comando rodar.

## 3. Sincronizar com o GitHub
```powershell
git add -A
git commit -m "chore: snapshot da fase 4b (EDA refinada)"
git push
```
