# Cenários independentes

Os nove JSON em `configs/` não contêm medições. S0 usa base 380 V linha/60 Hz/20 A/0,95 indutivo. S2 usa DPF=0,75; S3 muda o sinal de Q1. S4 inclui ordens harmônicas parametrizáveis; S4b usa 3 A/fase de ordem 3. S5 injeta sequência negativa 2%. S6 escala tensão e corrente juntas (admitância constante) com eventos curtos programados. S7 modula frequência com fase contínua conhecida. Consulte `methodology.md` e `config.py` para parâmetros efetivos.

S1 usa g=0,6+0,4 sin²(π(hora−6)/12), avaliado no início do segmento, multiplicado por 1,2 após 12 h. Tem duas oscilações por dia, desenhadas, não ajuste de perfil real. Degraus e fronteiras são explícitos; a energia integra o próprio modelo segmentado.

N é configurável: 1, 2, 12, 144, 1008 e 10080 são casos testados. N=1008/dt=600 s representa sete dias; N=10080/dt=600 s representa 70 dias. Interação N×hmax e segmentação tem orçamento adicional de coeficientes. Não gerar uma semana de waveform a 15.360 Hz: apenas janelas curtas.

S8 são fixtures de timestamps/valores inválidos, nunca medições exportadas. `normative_assessment` não pode ser ativado por configuração. Eventos e THD calculados não demonstram conformidade PRODIST/IEC/IEEE.
