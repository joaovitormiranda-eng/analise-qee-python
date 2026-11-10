# Contribuição e manutenção

O código autoral da nova implementação é MIT: leia LICENSE e docs/licensing.md. Contribua somente com material próprio ou autorizado sob termos compatíveis, preservando avisos de terceiros. Não aplique MIT a dependências, fontes ou dados de terceiros por suposição.

Use uma branch e PR revisado, dados exclusivamente sintéticos e descrição da hipótese física. Toda mudança de equação precisa de oráculo independente e unidades; não afrouxe tolerâncias para aprovar testes. Não importe dados privados, macros ou arquivos do estudo antigo. Execute os comandos de QA do README e descreva limitações, skips e ambientes efetivamente executados.

Atualizações de dependências: examine advisories e notas oficiais, altere pins justificados, resolva o conjunto em ambiente limpo, gere hashes SHA-256 dos arquivos oficiais PyPI, atualize `requirements.lock` e `constraints.txt`, execute `scripts/check_lock.py`, `pip check`, auditoria e testes. O lock é revisão explícita: Dependabot pode atualizar `pyproject.toml` sem regenerar esse lock personalizado; o CI deve falhar até sincronização revisada. Não use atualização forçada ou ignore advisories para obter aprovação.

Actions devem permanecer em SHAs completos com release verificada e comentário de versão. Nenhum auto-merge ou deploy foi configurado. A decisão de tornar CI obrigatório cabe ao proprietário; veja `docs/publication.md`.

O CI aceita somente wheels para dependências externas (`--only-binary=:all:`) e falha se uma plataforma não tiver distribuição compatível. O pacote local usa o backend de build já fixado, sem isolamento que baixe ferramentas adicionais.
