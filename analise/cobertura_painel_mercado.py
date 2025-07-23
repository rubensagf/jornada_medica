import pandas as pd
import matplotlib.pyplot as plt

# === LER ARQUIVO ===
df = pd.read_excel('jornada_medicos_trimestral.xlsx')
df['TRIMESTRE'] = df['TRIMESTRE'].astype(str)
df['CATEGORIA'] = df['CATEGORIA'].astype(str)

# === CALCULA % COBERTURA ===
cobertura = (
    df.groupby(['TRIMESTRE', 'CATEGORIA'])['NO_PAINEL']
    .apply(lambda x: (x == 'Sim').sum() / len(x) * 100)
    .reset_index(name='PERCENTUAL_COBERTURA')
)

# === PLOT ===
plt.figure(figsize=(12, 6))
for categoria in cobertura['CATEGORIA'].unique():
    dados = cobertura[cobertura['CATEGORIA'] == categoria]
    plt.plot(dados['TRIMESTRE'], dados['PERCENTUAL_COBERTURA'], label=f'CAT {categoria}', marker='o')

plt.title('% Cobertura da Força de Vendas por Categoria e Trimestre')
plt.xlabel('Trimestre')
plt.ylabel('% de Médicos no Painel')
plt.legend()
plt.xticks(rotation=45)
plt.grid(True)
plt.tight_layout()
plt.show()
