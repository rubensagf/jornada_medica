import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

print(" Gerando gráficos de cobertura INDIVIDUAIS por categoria...")

# --- 1. CONFIGURAÇÕES ---
ARQUIVO_ENTRADA = 'jornada_medicos_trimestral.xlsx' # Nome do seu arquivo
PASTA_SAIDA = 'Graficos_por_Categoria'

if not os.path.exists(PASTA_SAIDA):
    os.makedirs(PASTA_SAIDA)
    print(f" Pasta '{PASTA_SAIDA}' criada para salvar os gráficos.")

# --- 2. CARREGAR E PREPARAR OS DADOS ---
try:
    df = pd.read_excel(ARQUIVO_ENTRADA)
    print(f" Arquivo '{ARQUIVO_ENTRADA}' carregado com sucesso.")
except FileNotFoundError:
    print(f" ERRO: Arquivo '{ARQUIVO_ENTRADA}' não encontrado.")
    exit()

# ##########################################################################
# ## CORREÇÃO: Converte a coluna CATEGORIA para texto (string) ##
# ##########################################################################
# Isso garante que não haverá mistura de tipos (números e texto) ao ordenar
df['CATEGORIA'] = df['CATEGORIA'].astype(str) # <--- CORREÇÃO AQUI

df['no_painel_num'] = df['NO_PAINEL'].map({'Sim': 1, 'Não': 0})

print(" Calculando os totais por trimestre e por categoria...")
dados_agregados = df.groupby(['TRIMESTRE', 'CATEGORIA']).agg(
    total_categoria=('CRM LINK', 'count'),
    total_painel=('no_painel_num', 'sum')
).reset_index()

dados_agregados['percentual_cobertura'] = np.where(
    dados_agregados['total_categoria'] > 0,
    (dados_agregados['total_painel'] / dados_agregados['total_categoria']) * 100,
    0
)
dados_agregados = dados_agregados.sort_values(['TRIMESTRE', 'CATEGORIA'])

# --- 3. GERAR UM GRÁFICO PARA CADA CATEGORIA USANDO UM LOOP ---

categorias_unicas = dados_agregados['CATEGORIA'].unique()
# Agora o sorted() funcionará, pois todos os elementos são strings
print(f"Identificadas {len(categorias_unicas)} categorias para gerar gráficos: {sorted(categorias_unicas)}")

for categoria in sorted(categorias_unicas):
    print(f"\n Gerando gráfico para a Categoria {categoria}...")

    df_categoria_atual = dados_agregados[dados_agregados['CATEGORIA'] == categoria]

    if df_categoria_atual.empty:
        print(f"-> Aviso: Não há dados para a Categoria {categoria}. Pulando.")
        continue

    df_plot = df_categoria_atual.melt(
        id_vars=['TRIMESTRE', 'CATEGORIA', 'percentual_cobertura'],
        value_vars=['total_categoria', 'total_painel'],
        var_name='Tipo',
        value_name='Contagem'
    )
    df_plot['Tipo'] = df_plot['Tipo'].map({'total_categoria': 'Total na Categoria', 'total_painel': 'No Painel FV'})

    plt.figure(figsize=(15, 8))
    ax = sns.barplot(
        data=df_plot,
        x='TRIMESTRE',
        y='Contagem',
        hue='Tipo',
        palette={'Total na Categoria': '#a1c9f4', 'No Painel FV': '#2e7d32'}
    )

    for container in ax.containers:
        ax.bar_label(container, fmt='%.0f', fontsize=10, weight='bold', padding=3)

    for i, trimestre in enumerate(df_categoria_atual['TRIMESTRE']):
        dados_trimestre = df_categoria_atual[df_categoria_atual['TRIMESTRE'] == trimestre]
        total_medicos = dados_trimestre['total_categoria'].iloc[0]
        percentual = dados_trimestre['percentual_cobertura'].iloc[0]
        ax.text(
            x=i,
            y=total_medicos * 1.05,
            s=f'{percentual:.1f}%',
            ha='center',
            fontsize=12,
            fontweight='bold',
            color='#c92a2a'
        )

    ax.set_title(f'Cobertura do Painel FV na Categoria {categoria}', fontsize=18, pad=20)
    ax.set_xlabel('Trimestre', fontsize=12)
    ax.set_ylabel('Número de Médicos', fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Legenda', fontsize=11)
    plt.tight_layout()

    arquivo_saida_individual = os.path.join(PASTA_SAIDA, f'grafico_cobertura_categoria_{categoria}.png')
    
    plt.savefig(arquivo_saida_individual, dpi=300)
    print(f" Gráfico salvo com sucesso como '{arquivo_saida_individual}'")

    plt.close()

print("\n\n Processo finalizado! Todos os gráficos foram gerados e salvos na pasta 'Graficos_por_Categoria'.")