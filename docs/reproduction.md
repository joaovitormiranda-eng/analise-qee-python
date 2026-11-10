# Reprodução em ambiente limpo

Use CPython 3.11 x64 em ambiente virtual. Comandos completos no README. `requirements.lock` fixa runtime, testes, auditoria e build, com hashes oficiais PyPI para portabilidade de distribuição. O download pode ser preparado com:

```powershell
python -m pip download --only-binary=:all: --require-hashes -r requirements.lock -d ../qee-wheelhouse
python -m pip install --no-index --find-links ../qee-wheelhouse --require-hashes -r requirements.lock
python -m pip install --no-deps --no-build-isolation -e ".[dev]"
python scripts/check_lock.py
python -m pytest -q
python -m jv_qee suite --output ../qee-reproduction
python scripts/verify_artifacts.py ../qee-reproduction
```

Não reutilize uma pasta de resultados ocupada. O manifesto registra modelo/configuração/unidades/versões e hashes numéricos canônicos; compare estes hashes e resultados físicos. Hash do código muda após refatoração. XLSX contém timestamps de container; IDs SVG podem variar. Igualdade byte a byte não é requisito de determinismo científico.

Seed PCG64 explícita; jitter opcional até 5% sem ajuste à base antiga. Os presets com jitter=0 não dependem da seed. O leitor valida fases, potências, duração e reconstrução dos fasores; alterações de tabelas não são aceitas só por terem extensão XLSX. Não há armazenamento remoto ou telemetria.
