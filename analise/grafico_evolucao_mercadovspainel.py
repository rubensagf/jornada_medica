import pandas as pd
import matplotlib.pyplot as plt

# === LER A BASE GERADA ===
df = pd.read_excel('jornada_medicos_trimestral.xlsx')

# === AJUSTE DE FORMATO DE TRIMESTRE (caso necessário) ===
df['TRIMESTRE'] = df['TRIMESTRE'].astype(str)

# === AJUSTE PARA EVITAR ERRO DE MISTURA DE TIPOS ===
df['CATEGORIA'] = df['CATEGORIA'].astype(str)

# === LISTA DE CATEGORIAS (como string) ===
categorias = sorted(df['CATEGORIA'].unique())

# === GERAR UM GRÁFICO PARA CADA CATEGORIA ===
for cat in categorias:
    df_cat = df[df['CATEGORIA'] == cat]

    # Total de médicos no mercado por trimestre
    total_mercado = df_cat.groupby('TRIMESTRE')['CRM LINK'].nunique()

    # Total de médicos NO PAINEL por trimestre
    df_painel = df_cat[df_cat['NO_PAINEL'] == 'Sim']
    total_painel = df_painel.groupby('TRIMESTRE')['CRM LINK'].nunique()

    # Garante alinhamento dos índices
    trimestres = sorted(df['TRIMESTRE'].unique())
    total_mercado = total_mercado.reindex(trimestres, fill_value=0)
    total_painel = total_painel.reindex(trimestres, fill_value=0)

    # === PLOTAR ===
    plt.figure(figsize=(10, 5))
    plt.plot(trimestres, total_mercado, label='Total no Mercado', marker='o')
    plt.plot(trimestres, total_painel, label='No Painel (ativos)', marker='o')
    plt.title(f'Evolução - Categoria {cat}')
    plt.xlabel('Trimestre')
    plt.ylabel('Número de Médicos')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
