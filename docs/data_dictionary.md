# Dicionário e unidades

Todos os dados são sintéticos. A folha dictionary completa os campos das amostras; este documento cobre o contrato entre tabelas.

| Campo | Convenção |
|---|---|
| data_origin | Aviso sintético permanente, sem origem em medições reais. |
| scenario | S0–S7/S4b; S8 é somente fixtures inválidas. |
| sample_id | Inteiro a partir de0 por cenário; identifica intervalo. |
| segment_id | Inteiro a partir de0 por cenário; associa harmônicos ao segmento. |
| timestamp_start_utc/end_utc | ISO8601UTC, início inclusivo/fim exclusivo; precisão fracionária preservada. |
| dt_s | Duração conhecida em segundos; inferência por mediana/fallback proibida. |
| V_rms_A/B/C, V_line_A/B/C | RMS [V]; VlineA=Va−Vb, B=Vb−Vc, C=Vc−Va. |
| I_rms_A/B/C, I_neutral_A | RMS [A]. Neutro por soma complexa por ordem, seguido de RMS. |
| P_W, Q1_var, S_sum_VA | W ativos; var fundamental assinado; VA por soma aparente de fases. |
| FP_sum | P/SΣ por intervalo; sem unidade; não fator tarifário. |
| DPF1 | Razão fundamental agregada por segmento; média temporal desses valores no intervalo. |
| THDV_pct_A/B/C, THDI_pct_A/B/C | % relativo à fundamental; h2..hmax; na agregação, razão das energias dos coeficientes de segmentos. |
| FD_pct | % sequência negativa/positiva; média temporal segmentar no intervalo. |
| flags | Qualificações de agregação/modelo, sem descarte implícito. |
| order, phase | Ordem1..hmax e fase A/B/C na representação esparsa; ordens ausentes são zero. |
| V_real_V/V_imag_V | Partes real/imaginária do fasor RMS de tensão [V]. |
| I_real_A/I_imag_A | Partes real/imaginária do fasor RMS de corrente [A]. |
| start_s/end_s/voltage_pu | Evento programado relativo ao início do cenário, segundos e pu da tensão nominal. |
| time_s/phase_rad/frequency_Hz | Trecho de forma de onda, tempo relativo, fase analítica/frequência do modelo. |
| V_A_V...I_C_A | Grandezas instantâneas de waveform, não RMS. |
| energy_kWh, covered_s, coverage_ratio | Integral ativa, tempo coberto, fração sobre span observado. Não interpolam lacunas. |

Excel: metadados e parâmetros são parte obrigatória; timestamps com timezone não são escritos como datetime Excel ingênuo. Strings são gravadas explicitamente como texto, inclusive as iniciadas por “=”. Fórmulas são rejeitadas na importação. Harmônicos omitidos são zeros, não dados faltantes.

Configuração inclui bases v_ll[V], current[A], f0[Hz], dpf[1], n, interval_s[s], seed, jitter relativo0..0,05, hmax1..50 e fs[Hz]. Em S4, os mapas voltage_harmonics/current_harmonics substituem presets por razões da fundamental; deslocamento angular harmônico de corrente padrão é −0,3rad. S4b triplen_A[A]; S5 negative_sequence_pct[%]; S7 frequency_deviation_Hz/frequency_modulation_Hz[Hz]. Não há limites regulatórios nesses parâmetros. Eventos S6 são um preset explicitamente registrado em events, não uma descoberta de campo.
