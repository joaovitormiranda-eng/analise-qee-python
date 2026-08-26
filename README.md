# ⚡ Análise de Qualidade de Energia Elétrica (QEE)

Este projeto consiste em um **Pipeline ETL e Analytics** desenvolvido em Python para o processamento de dados massivos de analisadores de energia elétrica. O objetivo é automatizar o diagnóstico de grandezas elétricas e gerar laudos técnicos em conformidade com o **Módulo 8 do PRODIST/ANEEL**.

## 🛠️ Tecnologias Utilizadas
* **Linguagem:** Python 3.12
* **Manipulação de Dados:** Pandas, NumPy
* **Visualização:** Matplotlib
* **Documentação Técnica:** Exportação automatizada de tabelas para **LaTeX**

## 📊 Principais Funcionalidades
1. **Ingestão e Limpeza:** Tratamento automático de timestamps e dados corrompidos provenientes de arquivos `.xlsx` do analisador.
2. **Feature Engineering:** Cálculo vetorial de potências (Ativa, Reativa, Aparente) e Fator de Potência (FP).
3. **Análise de Harmônicas:** Avaliação das componentes de corrente e Distorção Harmônica Total (THD).
4. **Dimensionamento Capacitivo:** Cálculo automático do banco de capacitores ideal focado no pico de demanda.
5. **Geração de Relatórios:** Criação de dashboards executivos (PNG) e tabelas formatadas prontas para compilação em relatórios LaTeX.

## 📈 Resumo do Último Diagnóstico (Exemplo)
Os resultados do processamento de **1.666 amostras** no período analisado indicaram:
* **Demanda Máxima:** 51,39 kW
* **Fator de Potência Médio:** 0,949 (298 ocorrências abaixo de 0,92)
* **Banco Capacitivo Sugerido (Pico):** 2,85 kvar

## 🚀 Como Executar

1. Clone o repositório.
2. Insira o arquivo de medições na raiz do projeto (configurado no `.gitignore` para não subir ao repositório).
3. Execute o script principal:
   ```bash
   python tratamento_dados_qee.py