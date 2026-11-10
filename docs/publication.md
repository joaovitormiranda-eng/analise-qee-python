# Publicação futura e controles do proprietário

O envio de código para revisão em PR não publica resultados no site. O site Hugo continua intacto; seu link para este GitHub não executa o pacote. A integração exigirá outro PR para substituir os gráficos e alegações antigos, com revisão de autoria, alt, legendas, tamanhos, 29 URLs, 20 aliases e demais estudos preservados. SVGs devem ser incorporados por `<img>` ou componente estático equivalente, com dimensões reservadas e lazy loading. Não usar HTML ativo nem presumir que o `title` SVG substitui alt contextual. Cinco candidatas em `docs/figures/`; não são cinco novos estudos.

## Checklist administrativo — conferir evidências do PR

- Habilitar/confirmar PR obrigatório, revisão, CI QEE QA (Ubuntu/Windows), bloqueio de force push/exclusão e ausência de bypass indevido.
- Confirmar Dependabot alerts/security updates, dependency graph, secret scanning e push protection; o YAML semanal não ativa esses recursos administrativos.
- Habilitar private vulnerability reporting se disponível e conferir o canal SECURITY.md.
- Licença MIT autorizada pelo titular para a nova implementação; preservar o escopo e os avisos em docs/licensing.md.
- Após push/PR autorizado, observar instalação dos hashes, Actions Node, matriz Linux/Windows e artefatos. A validação local não prova execução remota.
- Conferir antes de cada merge se não há dados privados, caminhos pessoais, credenciais ou saídas reais. Não reescrever histórico sem plano específico de incidente.

Descrição GitHub sugerida: “Análise didática de qualidade da energia trifásica com dados sintéticos, Python, XLSX e gráficos SVG reproduzíveis.” Tópicos sugeridos: python, power-quality, synthetic-data, electrical-engineering, scientific-computing, three-phase, pytest. Nenhuma configuração foi alterada.
