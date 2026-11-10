# QA local e CI

`tests/unit`: configuração/imports/independência; `tests/physics`: potência, energia, THD, neutro, componentes simétricas, eventos, propriedades aleatórias; `tests/integration`: XLSX, CLI, manifesto, figuras e relatórios; `tests/security`: orçamento, fórmulas, ZIP, JSON, SVG ativo, contratos públicos e workflows.

Todos os dados são sintéticos. Tests usam tmp_path, não paths pessoais nem rede. `--import-mode=importlib` permite nomes iguais de módulos em diretórios distintos. Os 54 casos prévios são preservados com IDs V01–V32. V26 agora exige SVG vetorial e preview PNG somente auxiliar. V30/V31 são os dois skips de integração com o site ainda não autorizada. Não são aprovação em produção.

Cobertura branch mede todo `jv_qee`, incluindo CLI e visualização, com subprocessos. Não excluímos componentes difíceis para elevar o índice. Não foi configurado mypy: type hints e resolução de anotações são conferidas; schemas DataFrame são validados em runtime. Isso não equivale a prova estática completa de tipos.

O workflow executa lint, Bandit, guarda de fonte, pytest, auditoria de pins, geração e validação dos doze SVGs. Apenas uma matriz curta Python 3.11/Windows/Ubuntu; não há deploy. A auditoria de dependências usa rede somente para consultar índices e falha se a consulta falhar. A execução remota deve ser conferida nos checks de cada PR; testes locais não comprovam execução no GitHub ou em outro sistema operacional.
