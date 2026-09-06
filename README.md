# Análise de Qualidade de Energia Elétrica (QEE)

Script em Python desenvolvido para automatizar o processamento, tratamento e análise de dados provenientes de analisadores de energia elétrica.

O processo tradicional de análise de qualidade de energia costuma ser manual e suscetível a erros devido ao alto volume de dados exportados em planilhas. Este projeto automatiza a extração, o tratamento das grandezas elétricas e o diagnóstico final, gerando resultados em conformidade com o Módulo 8 do PRODIST/ANEEL. O foco principal é a precisão no monitoramento do Fator de Potência para evitar multas de energia reativa excedente.

## Stack e Tecnologias

* **Linguagem:** Python 3.12
* **Processamento e Tratamento de Dados:** Pandas, NumPy
* **Visualização:** Matplotlib
* **Documentação Técnica:** Exportação automatizada de tabelas e resultados formatados para integração direta em relatórios LaTeX.

## Estrutura do Pipeline

1. **Ingestão e Tratamento:** Correção automática de timestamps, tratamento de valores nulos (missing values) e higienização de dados corrompidos oriundos dos arquivos `.xlsx` brutos.
2. **Cálculos Elétricos:** Cálculo vetorial de potências (Ativa, Reativa, Aparente) e Fator de Potência (FP).
3. **Análise Harmônica:** Avaliação das componentes de corrente e Distorção Harmônica Total (THD).
4. **Dimensionamento Automático:** Cálculo do banco de capacitores ideal, focado na correção do fator de potência durante o pico de demanda.
5. **Automação de Saídas:** Geração de gráficos de análise e tabelas padronizadas para anexação em laudos técnicos.

## Estudo de Caso Prático

Em uma execução de validação, o script processou uma base de 1.666 amostras elétricas, entregando os seguintes resultados para tomada de decisão:

* **Demanda Máxima Identificada:** 51,39 kW
* **Fator de Potência (Risco Regulatório):** Média geral de 0,949, com identificação precisa de 298 ocorrências abaixo do limite normativo da ANEEL (0,92).
* **Solução Proposta:** Dimensionamento e indicação técnica para instalação de um Banco Capacitivo de 2,85 kvar focado no horário de ponta.

## Como Executar

1. Clone o repositório em sua máquina local.
2. Insira o arquivo bruto de medições na raiz do projeto (o arquivo está configurado no `.gitignore` para proteção dos dados originais do cliente/equipamento).
3. Execute o script principal:

   ```bash
   python tratamento_dados_qee.py
