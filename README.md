# ⚡ Análise de Qualidade de Energia Elétrica (QEE)

Este projeto consiste em um **Pipeline ETL e Analytics** desenvolvido em Python para o processamento de dados massivos de analisadores de energia elétrica. 

**O Problema:** A análise tradicional de Qualidade de Energia costuma ser um processo manual, lento e suscetível a erros, exigindo o manuseio de milhares de linhas no Excel. Além disso, a falta de precisão no monitoramento do Fator de Potência resulta em multas regulatórias pesadas (faturamento de energia reativa excedente).

**A Solução:** Desenvolvi este script para automatizar 100% da extração, tratamento e diagnóstico das grandezas elétricas, gerando laudos técnicos precisos e em conformidade com o **Módulo 8 do PRODIST/ANEEL** em segundos.

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.12
* **Manipulação e Transformação de Dados (ETL):** Pandas, NumPy
* **Data Visualization:** Matplotlib
* **Documentação Técnica:** Exportação automatizada de tabelas e laudos para **LaTeX**

## 📊 Principais Funcionalidades (Pipeline de Dados)
1. **Ingestão e Limpeza (Data Quality):** Tratamento automático de timestamps, preenchimento de *missing values* e correção de dados corrompidos oriundos dos arquivos `.xlsx` do analisador.
2. **Feature Engineering:** Cálculo vetorial avançado de potências (Ativa, Reativa, Aparente) e Fator de Potência (FP).
3. **Análise de Harmônicas:** Avaliação das componentes de corrente e Distorção Harmônica Total (THD).
4. **Prescriptive Analytics (Ação Proposta):** Cálculo automático e dimensionamento do banco de capacitores ideal focado na mitigação do pico de demanda.
5. **Automação de Relatórios:** Criação de dashboards executivos (PNG) e tabelas formatadas prontas para compilação em relatórios oficiais.

## 📈 Impacto e Resumo do Último Diagnóstico (Exemplo prático)
O script processou e diagnosticou **1.666 amostras** instantaneamente, entregando os seguintes *insights* acionáveis:
* **Demanda Máxima Identificada:** 51,39 kW
* **Risco Regulatório (Fator de Potência):** Média de 0,949, com **298 ocorrências abaixo do limite normativo** (0,92).
* **Solução Proposta:** Instalação de Banco Capacitivo de **2,85 kvar** no pico de demanda para mitigar o pagamento de multas.

## 🚀 Como Executar

1. Clone o repositório.
2. Insira o arquivo de medições na raiz do projeto (configurado no `.gitignore` para proteção dos dados originais).
3. Execute o script principal:
   ```bash
   python tratamento_dados_qee.py
