# Metodologia científica

**DADOS SINTÉTICOS — SIMULAÇÃO COMPUTACIONAL DIDÁTICA — NÃO REPRESENTAM MEDIÇÕES REAIS.**

## Modelo físico

Fonte trifásica rígida, quatro fios, neutro ideal, DC=0. Fasores RMS complexos por fase e ordem; fases A=0,B=−120°,C=+120°. Não se resolve fluxo de potência, impedância da rede, saturação, ressonância, instrumentação ou transitório eletromagnético. Correntes são excitações prescritas; isso não é identificação de uma carga industrial real.

`vφ(t)=√2 Re Σh Vφ,h exp(j h θ(t))`, corrente análoga. Vlinha,h=Va,h−Vb,h. RMS=√Σ|Xh|² em regimes harmônicos coerentes. `P=Σφ,h Re(Vh Ih*)`; `Q1=Σφ Im(V1 I1*)` fundamental assinado; `SΣ=Σφ Vrmsφ Irmsφ`; `FPΣ=P/SΣ`. Q1>0 indutivo, Q1<0 capacitivo. P pode ser negativo apenas quando a análise for explicitamente autorizada a tratar exportação. Os cenários padrão não exportam potência.

SΣ não é potência aparente efetiva IEEE1459. Não usar P²+Q1²=SΣ² como identidade universal; só o caso fundamental equilibrado adequado é testado como triângulo. DPF1 por segmento é P1/Σ|V1||I1|, acompanhado de sinal Q1, e não é sinônimo de FP sob distorção. Na tabela de intervalos, DPF1 e FD são médias temporais de seus indicadores por segmento, identificadas nos flags. Não usá-las como grandezas de faturamento.

`THD_X=100√Σ(h=2..H)|Xh|²/|X1|`; fundamental zero → NaN/indisponível no núcleo, nunca 0. Dataset exportável exige grandezas disponíveis; configuração degenerada deve falhar, não descartar linhas. THDI pode ultrapassar100%. TDD, Pst e classificação completa de eventos normativos não são implementados.

`a=exp(j2π/3)`; V+=(Va+aVb+a²Vc)/3; V−=(Va+a²Vb+aVc)/3; FD=100|V−|/|V+|, só fundamental. In,h=−Σφ Iφ,h; seu RMS soma quadrados por ordem. Ordem3 de3A/fase produz9A no neutro.

## Tempo e integração

Intervalos [start,end), duração explícita em segundos. Antes da agregação são criados segmentos em meia-noite local, degrau de S1 e fronteiras dos eventos de S6. As excitações são constantes em cada segmento. P/Q1 têm média ponderada por duração; RMS é raiz da média ponderada de quadrados. FP do intervalo usa P médio e SΣ calculado dos RMS agregados, não média de fatores. THD agregada usa energias dos coeficientes fundamental/harmônicos dos segmentos; não é a FFT completa de uma janela contendo bordas/transientes.

Energia=ΣPmédio·Δt/3.600.000[kWh]. O relatório diário integra os segmentos e respeita dias locais; não distribui uma média de evento sobre ambos os dias. Lacunas são preservadas no leitor temporal e expressas pela cobertura, sem preenchimento. A geração padrão produz cobertura completa.

S1 usa retenção de ordem zero: `g=.6+.4 sin²(π(hora−6)/12)` avaliada no início de cada segmento; degrau×1,2 em t=12h. Essa função desenhada tem duas oscilações por dia; não foi ajustada a consumo real. Corrente é escalada por g; tensão permanece rígida. Diferentemente da sugestão preliminar de integração contínua do perfil, a implementação declara explicitamente a aproximação de retenção, preservando integração exata do seu próprio modelo segmentado. S6 escala tensão e corrente juntas: admitância constante, P/Q/S escalam com o quadrado do envelope.

## Formas de onda e frequência

fs=15360Hz, duração nominal0,2s=12ciclos/3072amostras a60Hz; sem endpoint duplicado. Harmônicos até50 abaixo de Nyquist. FFT: normalização RMS `√2 FFT(x)[bin]/N`, somente janela coerente. Testes comparam RMS/média vi/espectro com oráculos fasoriais independentes.

S6: trechos4s, afundamento0,7pu/200ms, elevação1,15pu/300ms, interrupção0,01pu/500ms. O gráfico RMS móvel de um ciclo é ilustrativo; não há reivindicação de detector IEC/PRODIST. Formas estacionárias dos outros cenários representam o ponto inicial, não uma semana inteira.

S7: `f=f0+Δf sin(2πfm t)` e `θ=2πf0t+(Δf/fm)(1−cos(2πfm t))`, continuidade de fase exata. Projeção por mínimos quadrados em √2cos(hθ),−√2sin(hθ) recupera fasores usando a fase conhecida do gerador. Não aplicar FFT fixa como se a janela fosse coerente. Não se afirma rastreamento de frequência desconhecida, rejeição a ruído arbitrário ou desempenho metrológico.

Compensação: só exercício ideal fundamental equilibrado indutivo, P1>0,Q1>0, `Qc=max(0,Q1−P1 tan acos alvo)`. Outros regimes → não aplicável. Sem dimensionamento físico ou recomendação de instalação.

Referências de implementação: [normalização NumPy FFT](https://numpy.org/doc/stable/reference/routines.fft.html), [openpyxl streaming](https://openpyxl.readthedocs.io/en/stable/optimized.html). Versões executadas estão no lock e no manifesto; documentação latest não implica execução da versão latest.
