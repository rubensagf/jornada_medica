import pandas as pd

# Carregar base de categorias trimestrais (formato wide)
df = pd.read_excel("evolucao_cat_trimestral.xlsx")  # ajuste o nome do arquivo

# Filtrar colunas de trimestre (assumindo que começam com "TRIM MOV")
col_trimestres = [col for col in df.columns if "TRIM MOV" in col]

# Unpivot para formato longitudinal
df_long = df.melt(
    id_vars=["CRM LINK"],  # ajuste se o nome da coluna for diferente
    value_vars=col_trimestres,
    var_name="TRIMESTRE_RAW",
    value_name="CATEGORIA"
)

# Converter "TRIM MOV 09/23" em data real (ex: 2023-09-01)
def parse_trimestre(trim_str):
    parts = trim_str.split(" ")
    mes, ano = parts[-1].split("/")
    mes = int(mes)
    ano = int("20" + ano) if len(ano) == 2 else int(ano)
    return pd.Timestamp(year=ano, month=mes, day=1)

df_long["TRIMESTRE"] = df_long["TRIMESTRE_RAW"].apply(parse_trimestre)
df_long = df_long.drop(columns=["TRIMESTRE_RAW"])

# Reordenar colunas
df_long = df_long[["CRM LINK", "TRIMESTRE", "CATEGORIA"]]

# Exportar para Excel
df_long.to_excel("base_longitudinal_mercado.xlsx", index=False)

print("Arquivo 'base_longitudinal_mercado.xlsx' exportado com sucesso!")
