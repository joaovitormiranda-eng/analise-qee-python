# Proveniência e reprodução

Somente configurações novas + equações + RNG opcional PCG64/SeedSequence([seed,101]). Nenhum acesso ao arquivo antigo, medições, histogramas ou calibração por gráficos. A baseline auditada é referência de origem do repositório, não fonte de dados do novo produto. O arquivo legado foi movido sem alteração de bytes para legacy/tratamento_dados_qee.py.disabled, fora dos imports.

Dependências diretas: NumPy2.3.5, pandas2.3.3, Matplotlib3.10.7, openpyxl3.1.5; defusedxml0.7.1 para XML seguro; pytest9.0.3 para testes. Lock inclui todas as transitivas e hashes dos artefatos da release oficial PyPI, verificados antes da instalação. A verificação de hash confirma integridade relativa à fonte; não é auditoria completa de segurança da dependência. Wheels externos não são vendorizados no código.

Manifesto registra código do pacote, versão1.0.0, configurações completas/seeds, versões de runtime e unidades. Hash científico: CSV com ordem de linhas/colunas definida, números em12algarismos significativos, UTF8/LF. Isso quantiza a representação para comparação científica; testes também verificam números diretamente com tolerâncias rígidas. Não é hash de todos os bits de float64. XLSX contém metadados de empacotamento; não se exige igualdade byte a byte. Hashes de arquivos publicados no pacote de evidências são uma verificação separada.

Instalação e comandos estão no README. Para verificar em ambiente limpo: criar segunda venv, instalar lock com --require-hashes, construir wheel local com --no-build-isolation/--no-deps, instalar wheel e executar testes com `python -m pytest -o pythonpath= -q`, removendo a inclusão automática de src. Gerar novamente os cenários e comparar hashes científicos/indicadores, sem exigir bytes idênticos de XLSX/SVG. Não declarar plataformas não testadas como validadas.

A classificação de direito sobre dados antigos permanece separada. Este novo conjunto não elimina arquivos antigos já publicados ou cópias históricas. Nenhuma mudança do site é feita pelo CLI.
