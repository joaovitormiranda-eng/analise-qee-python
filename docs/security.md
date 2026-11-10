# Ameaças e controles

Ativos: integridade científica, arquivos locais, código público, credenciais GitHub e artefatos. Fronteiras: JSON/XLSX → parser → cálculos → pasta de saída; contribuições → CI; PyPI/Actions → execução de ferramentas. Não existe banco de dados, login ou API de servidor neste projeto.

| Ameaça plausível | Controle e limitação |
|---|---|
| XLSX com expansão excessiva, links, macros ou fórmulas | Preflight ZIP, 150 MB comprimido/250 MB expandido, 4000 entradas, razão 500; defusedxml; 256 folhas, 64 colunas, 500 mil linhas/tabela e 3 milhões de células; rejeição explícita. Não executar arquivos suspeitos só porque passaram no preflight |
| JSON ambíguo ou alocação excessiva | 100 KB, sem chaves duplicadas/NaN/Inf; configuração imutável; coeficientes limitados a 3 milhões, waveform a 5 milhões de produtos amostra×ordem ativa |
| Escrita destrutiva ou path injection | Destino explícito novo/vazio, nomes runtime fixos, symlinks recusados, publicação por temporário. Não é defesa absoluta contra corrida em host multiusuário malicioso |
| Injeção gráfica | SVG estático gerado internamente, validação segura sem scripts/imagens/referências externas |
| Alteração da física em PR | Oráculos analíticos e revisão humana; cobertura não comprova correção universal |
| Dependência ou Action comprometida | Lock com hashes oficiais, pins SHA, dependências mínimas; hashes não comprovam autoria independente nem corrigem upstream comprometido |
| Exfiltração em CI | contents:read, sem secrets/PAT/deploy, checkout sem credenciais persistidas. Código de PR continua executável no runner; não conceder permissões adicionais |
| Divulgação de planilha privada | Sem dados externos no source/artefatos; guards, .gitignore, checklist humano. Histórico anterior não é apagado pela reconstrução |

Os limites são budgets de segurança operacional, não limites normativos. Um arquivo gerado com configuração grande pode exceder o perfil seguro de importação; o leitor falha explicitamente. Não aumentar limites silenciosamente. Rode no ambiente virtual e fora de pastas com arquivos importantes. Nenhuma entrada controla comandos shell. Dependências devem ser atualizadas com testes e consulta a advisories.
