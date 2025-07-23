import pandas as pd
import numpy as np
from datetime import datetime

# Função robusta que converte trimestre (string ou Timestamp) para intervalo de datas
def trimestre_para_intervalo(trimestre):
    if isinstance(trimestre, pd.Timestamp) or isinstance(trimestre, datetime):
        ano = trimestre.year
        mes = trimestre.month
        tri = (mes - 1) // 3 + 1
    elif isinstance(trimestre, str):
        try:
            ano, tri = trimestre.split("-T")
            ano = int(ano)
            tri = int(tri)
        except:
            raise ValueError(f"Formato inválido de trimestre: {trimestre}")
    else:
        raise ValueError(f"Tipo de dado inesperado: {type(trimestre)}")

    mes_inicio = 1 + (tri - 1) * 3
    mes_fim = mes_inicio + 2
    data_inicio = pd.Timestamp(ano, mes_inicio, 1)
    if mes_fim == 12:
        data_fim = pd.Timestamp(ano, mes_fim, 31)
    else:
        data_fim = pd.Timestamp(ano, mes_fim + 1, 1) - pd.Timedelta(days=1)
    return data_inicio, data_fim

# Leitura dos arquivos
base_mercado = pd.read_excel("base_longitudinal_mercado.xlsx")
painel = pd.read_excel("PAINEL_FV_GERAL.xlsx")

# Conversão de datas
painel["DT_INCLUSAO"] = pd.to_datetime(painel["DT_INCLUSAO"], dayfirst=True, errors='coerce')
painel["DT_INATIVACAO"] = pd.to_datetime(painel["DT_INATIVACAO"], dayfirst=True, errors='coerce')

# ✅ Converter coluna TRIMESTRE para formato YYYYQn
base_mercado["TRIMESTRE"] = pd.to_datetime(base_mercado["TRIMESTRE"], errors='coerce')
base_mercado["TRIMESTRE"] = base_mercado["TRIMESTRE"].dt.to_period("Q").astype(str)

# Função para verificar se o médico estava no painel no trimestre
def verificar_presenca_no_painel(crm, trimestre):
    inicio_trim, fim_trim = trimestre_para_intervalo(trimestre)
    entradas_medico = painel[painel["CRM LINK"] == crm]
    for _, row in entradas_medico.iterrows():
        dt_in = row["DT_INCLUSAO"]
        dt_out = row["DT_INATIVACAO"]
        if pd.isnull(dt_out):
            dt_out = pd.Timestamp.today()
        if dt_in <= fim_trim and dt_out >= inicio_trim:
            return "Sim"
    return "Não"

# Aplicar a lógica à base de mercado
base_mercado["NO_PAINEL"] = base_mercado.apply(
    lambda row: verificar_presenca_no_painel(row["CRM LINK"], row["TRIMESTRE"]), axis=1
)

# Exportar
base_mercado.to_excel("tabela_longitudinal_final.xlsx", index=False)

print(" Arquivo gerado com sucesso: tabela_longitudinal_final.xlsx")
