# Matriz V01–V32

Os testes `tests/unit/`, `tests/physics/` e `tests/integration/` mantêm os IDs da matriz da Fase1. Parametrizações aumentam o número de casos sem criar novos grupos. Os resultados executados e detalhes estão nos relatórios externos desta entrega.

V01 imports; V02 configuração; V03 potência nominal; V04 waveform/FFT; V05 balanço; V06 sequência negativa; V07 triplen; V08 THD/zero/customização; V09 THD>100%; V10 propriedades de potência; V11 sinais/exportação; V12 compensação restrita; V13 energia; V14 lacunas; V15 meia-noite/eventos; V16 RMS/razões; V17 eventos; V18 fase variável; V19 seeds; V20 prefixos/ordem/chunking de tabelas; V21 quantidades; V22 Excel/reconstrução; V23 limites/chunking; V24 inválidos; V25 fórmulas/limites; V26 figuras/relatório; V27 independência; V28 CLI/ambiente limpo; V29 not_assessed.

V30 e V31 são explicitamente skipped: dependem da futura integração com o site e não representam testes de produção aprovados. V32 testa preparação local do pacote, sem alegar retirada de imagens históricas ou publicação. A remoção de ativos do site não é autorizada nesta rodada.

Tolerâncias: oráculos fasoriais rtol1e−10/atol1e−8; waveform/FFT rtol1e−9/atol1e−8; round-trip Excel rtol1e−12/atol1e−9. S7 usa a equação independente da fase, recuperação por projeção e erro de derivada limitado a3e−8Hz no interior. As tolerâncias foram estabelecidas antes dos ensaios e não afrouxadas após falhas. Os ensaios iniciais identificaram parser temporal de segundos/fracionários incompatível; o parser foi corrigido, sem mudar oráculos.

V23 verifica aritmeticamente1.512.000linhas e faz round-trip real com limite artificial reduzido a5registros por folha, exercitando o mesmo particionador. Não houve escrita física de1,5milhão de linhas nesta rodada. Testes de propriedades usam excitações aleatórias próprias e verificam Cauchy-Schwarz, sem importar a base antiga. A revisão por equações/oráculos não substitui revisão independente por outro profissional.


Fase 2C: V26 exige SVG vetorial principal e preview PNG opcional. Os oráculos e as tolerâncias físicas anteriores permanecem. Novos testes em `tests/security/` validam limites, conteúdo ativo, não sobrescrita, configuração imutável e invariantes do CI.
