# Figuras científicas vetoriais

`plots.py` separa apresentação de `physics.py` e usa `style.py` em `matplotlib.rc_context`, sem alterar configurações globais. Doze SVGs principais; PNG só é produzido com `raster_preview=True` na API e permanece derivado auxiliar.

## Tipo por figura

| Arquivo | Escolha e fundamento |
|---|---|
| 01_tensoes | Pontos por fase: três grandezas discretas; B/C coincidem fisicamente |
| 02_correntes | Linhas e tracejados: três formas de onda contínuas em janela curta |
| 03_carga | Degraus: retenção de ordem zero, mudança real do modelo em 12 h |
| 04_potencias | Três painéis: kW, kvar e kVA têm definições distintas |
| 05_energia | Linha acumulada: integral temporal, substitui barras diárias |
| 06_fp | Pares de pontos: cenários categóricos, FP e DPF1 distintos |
| 07_thd | Hastes com pontos: dois indicadores discretos em porcentagem |
| 08_desequilibrio | Magnitudes de sequência: comparação discreta, FD explícito |
| 09_neutro | Dois painéis temporais: fases e neutro em escalas próprias |
| 10_eventos | Curva RMS e envelope programado: janela suaviza fronteiras |
| 11_comparacao | Pontos horizontais: energia de condições diferentes, sem economia alegada |
| 12_espectro | Hastes: ordens harmônicas discretas, sem interpolação espectral enganosa |

Paleta azul/laranja/verde/roxo, fundo branco, grades discretas e unidades nos eixos. Não há 3D, gradientes, fotografias ou imagens raster dentro das figuras.

`svg.fonttype="path"` foi escolhido pela fidelidade com GitHub, navegador e futura incorporação Hugo sem instalar fontes. `none` mantém texto editável/pesquisável e tende a reduzir tamanho, mas depende das fontes do cliente. Contornos reduzem a acessibilidade de rótulos individuais: cada SVG tem `title`, `desc`, `role=img`, e CSV/metodologia complementares; a incorporação futura precisa de alt e legenda próprios. Não se declara conformidade universal de acessibilidade.

O aviso da DejaVu/Bitstream foi preservado em `FONT_LICENSE_DEJAVU.txt`, extraído do wheel oficial Matplotlib 3.10.7. Não licencia o código JV Engineering. O validador recusa scripts, eventos DOM, imagens raster, entidades, DOCTYPE, referências remotas e CSS externo; não pretende aceitar todo SVG arbitrário.

Cinco candidatas: **03_carga, 06_fp, 07_thd, 09_neutro, 10_eventos**. Mostram modelagem temporal, definições de potência, distorção, lei de Kirchhoff e fronteiras de eventos. Ainda não publicadas no site.
