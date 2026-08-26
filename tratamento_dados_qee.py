"""
Pipeline ETL e Analytics para Qualidade de Energia Elétrica (QEE)
Compliance: PRODIST/ANEEL Módulo 8
Autor: João Vitor (Engenharia de Dados & Sistemas Elétricos)
"""

import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Configuração de Logging Corporativo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ------------------------------------------------------------
# CONSTANTES E CONFIGURAÇÕES
# ------------------------------------------------------------
ARQUIVO_XLSX = "Dados_Medições.xlsx"

PASTA_FIGURAS = Path("figuras")
PASTA_RESULTADOS = Path("resultados")

# Garante a criação dos diretórios de saída
PASTA_FIGURAS.mkdir(exist_ok=True)
PASTA_RESULTADOS.mkdir(exist_ok=True)

# ------------------------------------------------------------
# FUNÇÕES DE ETL E SANITIZAÇÃO
# ------------------------------------------------------------
def carregar_planilha(caminho: str) -> pd.DataFrame:
    """Carrega log bruto do analisador de energia e sanitiza a série temporal."""
    try:
        logging.info(f"Iniciando ingestão do arquivo: {caminho}")
        df = pd.read_excel(caminho)
        
        # Remove colunas "fantasmas" geradas pelo Excel
        df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]

        if "Time" not in df.columns:
            raise ValueError("O log não possui a coluna de timestamp 'Time'.")

        # Conversão de datas seriais do Excel (origin 1899-12-30)
        if np.issubdtype(df["Time"].dtype, np.number):
            df["DataHora"] = pd.to_datetime(df["Time"], unit="D", origin="1899-12-30")
        else:
            df["DataHora"] = pd.to_datetime(df["Time"], errors="coerce")

        df = df.dropna(subset=["DataHora"]).sort_values("DataHora").reset_index(drop=True)
        logging.info(f"Ingestão concluída. Total de amostras sanitizadas: {len(df)}")
        return df
        
    except FileNotFoundError:
        logging.error(f"Arquivo '{caminho}' não encontrado.")
        raise
    except Exception as e:
        logging.error(f"Erro durante a leitura da planilha: {e}")
        raise

def auditar_colunas(df: pd.DataFrame, colunas_esperadas: List[str]) -> None:
    """Valida a existência das métricas necessárias para a análise vetorial."""
    faltantes = [c for c in colunas_esperadas if c not in df.columns]
    if faltantes:
        logging.warning("Métricas ausentes no log de entrada:")
        for c in faltantes:
            logging.warning(f" - {c}")

def gerar_estatisticas_basicas(df: pd.DataFrame, colunas: List[str], escala: float = 1.0) -> pd.DataFrame:
    """Calcula estatísticas descritivas (Média, Mínimo e Máximo) das séries."""
    linhas = []
    for col in colunas:
        if col in df.columns:
            serie = pd.to_numeric(df[col], errors="coerce") / escala
            linhas.append({
                "Grandeza": col,
                "Media": serie.mean(),
                "Minimo": serie.min(),
                "Maximo": serie.max()
            })
    return pd.DataFrame(linhas)

def formatar_br(valor: float, casas: int = 2) -> str:
    """Converte padrão decimal internacional para o padrão PT-BR para uso no LaTeX."""
    if pd.isna(valor):
        return "N/A"
    return f"{valor:.{casas}f}".replace(".", ",")

# ------------------------------------------------------------
# FUNÇÕES DE VISUALIZAÇÃO E ENGENHARIA ELÉTRICA
# ------------------------------------------------------------
def plotar_serie_temporal(
    nome_arquivo: str,
    titulo: str,
    ylabel: str,
    colunas: List[str],
    labels: List[str],
    df: pd.DataFrame,
    escala: float = 1.0,
    ylim: Optional[Tuple[float, float]] = None
) -> None:
    """Motor padronizado de renderização de gráficos executivos temporais."""
    fig, ax = plt.subplots(figsize=(11, 4.5))

    for col, label in zip(colunas, labels):
        if col in df.columns:
            y = pd.to_numeric(df[col], errors="coerce") / escala
            ax.plot(df["DataHora"], y, linewidth=0.8, label=label, alpha=0.9)

    ax.set_title(titulo, fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Data", fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    
    if ylim:
        ax.set_ylim(ylim)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    ax.grid(True, linestyle="--", alpha=0.4)
    
    plt.tight_layout()
    plt.savefig(PASTA_FIGURAS / nome_arquivo, dpi=300)
    plt.close()

def plotar_fator_potencia(df: pd.DataFrame) -> None:
    """Gera gráfico do fator de potência com limites normativos."""
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(df["DataHora"], df["FP_calc"], linewidth=0.8, label="FP = P/S", alpha=0.85)
    ax.axhline(0.92, linestyle="--", linewidth=1.2, color="orange", label="Referência 0,92")
    ax.axhline(0.95, linestyle=":", linewidth=1.4, color="red", label="Meta 0,95")
    
    ax.set_title("Fator de Potência ao Longo do Período de Medição", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Data", fontsize=10)
    ax.set_ylabel("Fator de Potência", fontsize=10)
    ax.set_ylim(0, 1.05)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    ax.grid(True, linestyle="--", alpha=0.4)
    
    plt.tight_layout()
    plt.savefig(PASTA_FIGURAS / "fatorpotencia.png", dpi=300)
    plt.close()

def plotar_harmonicas_corrente(df: pd.DataFrame) -> pd.DataFrame:
    """Gera gráfico de barras das componentes harmônicas médias de corrente."""
    ordens = [3, 5, 7, 9, 11, 13, 15, 17]
    fases = ["I1", "I2", "I3"]

    tabela = []
    for ordem in ordens:
        linha = {"Ordem": ordem}
        for fase in fases:
            col = f"har{ordem:02d}{fase}_Avg [A]"
            if col in df.columns:
                linha[fase] = pd.to_numeric(df[col], errors="coerce").abs().mean()
            else:
                linha[fase] = np.nan
        tabela.append(linha)

    tab = pd.DataFrame(tabela)
    x = np.arange(len(ordens))
    largura = 0.25

    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.bar(x - largura, tab["I1"], largura, label="Fase 1")
    ax.bar(x, tab["I2"], largura, label="Fase 2")
    ax.bar(x + largura, tab["I3"], largura, label="Fase 3")

    ax.set_title("Componentes Harmônicas Médias de Corrente", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Ordem Harmônica", fontsize=10)
    ax.set_ylabel("Corrente Média [A]", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels([str(o) for o in ordens])
    
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    
    plt.tight_layout()
    plt.savefig(PASTA_FIGURAS / "harmonicascorrente.png", dpi=300)
    plt.close()

    return tab

def plotar_energia_diaria(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula energia ativa estimada por dia via integração vetorial."""
    df_calc = df.copy()
    df_calc["Data"] = df_calc["DataHora"].dt.date

    delta_horas = df_calc["DataHora"].diff().dt.total_seconds().median() / 3600
    if pd.isna(delta_horas) or delta_horas <= 0:
        delta_horas = 5 / 60  # Fallback de 5 minutos

    energia = (
        df_calc.groupby("Data")["P_kW"]
        .sum()
        .mul(delta_horas)
        .reset_index()
        .rename(columns={"P_kW": "Energia_kWh"})
    )

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(energia["Data"].astype(str), energia["Energia_kWh"], color="#1f77b4", alpha=0.85)
    
    ax.set_title("Energia Ativa Estimada por Dia", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Data", fontsize=10)
    ax.set_ylabel("Energia Ativa [kWh]", fontsize=10)
    ax.tick_params(axis="x", rotation=30)
    
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    
    plt.tight_layout()
    plt.savefig(PASTA_FIGURAS / "energiadiaria.png", dpi=300)
    plt.close()

    return energia

def calcular_dimensionamento_capacitivo(df: pd.DataFrame, fp_meta: float = 0.95) -> Dict:
    """Dimensionamento analítico do banco de capacitores focado no pico de demanda."""
    idx_pico = df["P_kW"].idxmax()
    linha_pico = df.loc[idx_pico]

    p_kw = float(linha_pico["P_kW"])
    q_kvar = float(linha_pico["Q_liq_kvar"])

    s_kva = math.sqrt(p_kw**2 + q_kvar**2)
    fp_atual = p_kw / s_kva if s_kva > 0 else np.nan

    if pd.isna(fp_atual) or fp_atual >= fp_meta:
        q_c = 0.0
    else:
        phi_atual = math.acos(fp_atual)
        phi_meta = math.acos(fp_meta)
        q_c = p_kw * (math.tan(phi_atual) - math.tan(phi_meta))

    return {
        "DataHora_pico": linha_pico["DataHora"],
        "P_kW": p_kw,
        "Q_kvar": q_kvar,
        "FP_atual": fp_atual,
        "FP_desejado": fp_meta,
        "phi1_graus": math.degrees(math.acos(fp_atual)) if not pd.isna(fp_atual) else np.nan,
        "phi2_graus": math.degrees(math.acos(fp_meta)),
        "Qc_kvar": max(q_c, 0.0)
    }

# ------------------------------------------------------------
# FUNÇÃO DE REPORTING (LATEX)
# ------------------------------------------------------------
def exportar_tabelas_latex(
    tensoes: pd.DataFrame, correntes: pd.DataFrame, thd: pd.DataFrame, 
    potencias: pd.DataFrame, fp_stats: dict, harmonicas: pd.DataFrame, 
    energia: pd.DataFrame, banco: dict
) -> None:
    """Gera bloco de código LaTeX compilável."""
    saida = []

    def add_table(titulo, df, nomes_map):
        saida.extend([f"\n% --- {titulo} ---", "\\begin{tabular}{lrrr}", "\\hline", "Grandeza & Média & Mínimo & Máximo \\\\", "\\hline"])
        for _, r in df.iterrows():
            nome = nomes_map.get(r['Grandeza'], r['Grandeza'])
            saida.append(f"{nome} & {formatar_br(r['Media'])} & {formatar_br(r['Minimo'])} & {formatar_br(r['Maximo'])} \\\\")
        saida.extend(["\\hline", "\\end{tabular}"])

    add_table("TABELA DE TENSÕES", tensoes, {
        "V1_Avg [V]": "$V_1$", "V2_Avg [V]": "$V_2$", "V3_Avg [V]": "$V_3$",
        "V12_Avg [V]": "$V_{12}$", "V23_Avg [V]": "$V_{23}$", "V31_Avg [V]": "$V_{31}$"
    })

    add_table("TABELA DE CORRENTES", correntes, {
        "I1_Avg [A]": "$I_1$", "I2_Avg [A]": "$I_2$", "I3_Avg [A]": "$I_3$", "In_Avg [A]": "$I_n$"
    })

    add_table("TABELA DE POTÊNCIAS", potencias, {
        "P_kW": "$P$ [kW]", "Q_liq_kvar": "$Q$ [kvar]", "S_kVA": "$S$ [kVA]"
    })

    # Tabela de Harmônicas
    saida.extend(["\n% --- TABELA DE HARMÔNICAS ---"])
    for _, r in harmonicas.iterrows():
        saida.append(f"{int(r['Ordem'])}ª & {formatar_br(r['I1'])} & {formatar_br(r['I2'])} & {formatar_br(r['I3'])} \\\\")

    # Tabela Banco de Capacitores
    saida.extend([
        "\n% --- DIMENSIONAMENTO CAPACITIVO ---",
        f"Potência ativa considerada $P$ & {formatar_br(banco['P_kW'])} kW \\\\",
        f"Fator de potência atual $FP_1$ & {formatar_br(banco['FP_atual'], 3)} \\\\",
        f"Fator de potência desejado $FP_2$ & {formatar_br(banco['FP_desejado'], 2)} \\\\",
        f"Potência reativa capacitiva $Q_c$ & {formatar_br(banco['Qc_kvar'])} kvar \\\\"
    ])

    (PASTA_RESULTADOS / "tabelas_latex.tex").write_text("\n".join(saida), encoding="utf-8")
    logging.info("Artefatos em LaTeX exportados com sucesso.")

# ------------------------------------------------------------
# PIPELINE PRINCIPAL
# ------------------------------------------------------------
def main() -> None:
    try:
        logging.info("--- INICIANDO PIPELINE DE DIAGNÓSTICO DE QEE ---")
        df = carregar_planilha(ARQUIVO_XLSX)

        colunas_necessarias = [
            "V1_Avg [V]", "V2_Avg [V]", "V3_Avg [V]",
            "I1_Avg [A]", "I2_Avg [A]", "I3_Avg [A]",
            "Pt+_Avg [W]", "Qti+_Avg [VAR]", "Qtc+_Avg [VAR]", "St+_Avg [VA]"
        ]
        auditar_colunas(df, colunas_necessarias)

        # 1. Feature Engineering
        df["P_kW"] = pd.to_numeric(df["Pt+_Avg [W]"], errors="coerce") / 1000
        df["S_kVA"] = pd.to_numeric(df["St+_Avg [VA]"], errors="coerce") / 1000
        df["Q_liq_kvar"] = (pd.to_numeric(df["Qti+_Avg [VAR]"], errors="coerce") - 
                            pd.to_numeric(df["Qtc+_Avg [VAR]"], errors="coerce")) / 1000
        
        df["FP_calc"] = df["P_kW"] / df["S_kVA"]
        df.loc[~np.isfinite(df["FP_calc"]), "FP_calc"] = np.nan

        # 2. Estatísticas Agregadas
        logging.info("Processando cálculos estatísticos vetoriais...")
        tensoes = gerar_estatisticas_basicas(df, ["V1_Avg [V]", "V2_Avg [V]", "V3_Avg [V]", "V12_Avg [V]", "V23_Avg [V]", "V31_Avg [V]"])
        correntes = gerar_estatisticas_basicas(df, ["I1_Avg [A]", "I2_Avg [A]", "I3_Avg [A]", "In_Avg [A]"])
        thd = gerar_estatisticas_basicas(df, ["thdV1_Avg [%]", "thdV2_Avg [%]", "thdV3_Avg [%]", "thdI1_Avg [%]", "thdI2_Avg [%]", "thdI3_Avg [%]"])
        potencias = gerar_estatisticas_basicas(df, ["P_kW", "Q_liq_kvar", "S_kVA"])
        
        fp_stats = {
            "media": df["FP_calc"].mean(),
            "minimo": df["FP_calc"].min(),
            "maximo": df["FP_calc"].max(),
            "abaixo_092": int((df["FP_calc"] < 0.92).sum()),
            "abaixo_095": int((df["FP_calc"] < 0.95).sum()),
        }

        # 3. Geração de Artefatos Visuais
        logging.info("Renderizando painéis gráficos (300 DPI)...")
        plotar_serie_temporal("curvacarga.png", "Curva de Carga do Bloco", "Potência Ativa [kW]", ["P_kW"], ["Potência Ativa"], df)
        plotar_serie_temporal("tensoesfase.png", "Variação das Tensões de Fase", "Tensão [V]", ["V1_Avg [V]", "V2_Avg [V]", "V3_Avg [V]"], ["V1", "V2", "V3"], df)
        plotar_serie_temporal("correntes.png", "Variação das Correntes", "Corrente [A]", ["I1_Avg [A]", "I2_Avg [A]", "I3_Avg [A]", "In_Avg [A]"], ["I1", "I2", "I3", "In"], df)
        plotar_serie_temporal("thdtensao.png", "Distorção Harmônica Total de Tensão", "THD [%]", ["thdV1_Avg [%]", "thdV2_Avg [%]", "thdV3_Avg [%]"], ["THD V1", "THD V2", "THD V3"], df)
        plotar_serie_temporal("thdcorrente.png", "Distorção Harmônica Total de Corrente", "THD [%]", ["thdI1_Avg [%]", "thdI2_Avg [%]", "thdI3_Avg [%]"], ["THD I1", "THD I2", "THD I3"], df, ylim=(0, 100))
        plotar_serie_temporal("potencias.png", "Potências Ativa, Reativa Líquida e Aparente", "Potência", ["P_kW", "Q_liq_kvar", "S_kVA"], ["P [kW]", "Q líq [kvar]", "S [kVA]"], df)

        plotar_fator_potencia(df)
        harmonicas = plotar_harmonicas_corrente(df)
        energia = plotar_energia_diaria(df)
        banco_cap = calcular_dimensionamento_capacitivo(df, fp_meta=0.95)

        # Gráficos Opcionais
        if "freq_Avg [Hz]" in df.columns:
            plotar_serie_temporal("frequencia.png", "Frequência", "Freq [Hz]", ["freq_Avg [Hz]"], ["Hz"], df)

        # 4. Exportação
        logging.info("Exportando dataframes para CSV e LaTeX...")
        tensoes.to_csv(PASTA_RESULTADOS / "estatisticas_tensoes.csv", index=False, sep=";", decimal=",")
        correntes.to_csv(PASTA_RESULTADOS / "estatisticas_correntes.csv", index=False, sep=";", decimal=",")
        potencias.to_csv(PASTA_RESULTADOS / "estatisticas_potencias.csv", index=False, sep=";", decimal=",")
        
        exportar_tabelas_latex(tensoes, correntes, thd, potencias, fp_stats, harmonicas, energia, banco_cap)

        # 5. Resumo Executivo TXT
        resumo = [
            "RESUMO EXECUTIVO - PIPELINE QEE",
            f"Período: {df['DataHora'].min().strftime('%d/%m/%Y')} a {df['DataHora'].max().strftime('%d/%m/%Y')}",
            f"Amostras Auditadas: {len(df)}",
            f"Demanda Máxima: {df['P_kW'].max():.2f} kW",
            f"Fator de Potência Médio: {fp_stats['media']:.3f} | Ocorrências < 0,92: {fp_stats['abaixo_092']}",
            f"Banco Capacitivo Sugerido (Pico): {banco_cap['Qc_kvar']:.2f} kvar"
        ]
        (PASTA_RESULTADOS / "resumo_executivo.txt").write_text("\n".join(resumo), encoding="utf-8")

        logging.info("--- PIPELINE CONCLUÍDO COM SUCESSO ---")

    except Exception as e:
        logging.error(f"Falha crítica na execução do pipeline: {e}")

if __name__ == "__main__":
    main()