import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import os

print("--- Preparando a Aplicação Dash (Abordagem Final de Limpeza de Dados) ---")

# --- 1. CONFIGURAÇÕES ---
ARQUIVO_ENTRADA = 'jornada_medicos_trimestral.xlsx'
PASTA_SAIDA = 'Analise_de_Fluxo_Final_Interativo'

if not os.path.exists(PASTA_SAIDA):
    os.makedirs(PASTA_SAIDA)

CORES_CATEGORIAS = {
    '1': '#1f77b4', '2': '#2ca02c', '3': '#ff7f0e', '4': '#d62728', '5': '#9467bd', 
    'SEM CAT': '#7f7f7f', 'default': '#cccccc'
}

# --- NOVA FUNÇÃO DE LIMPEZA E PADRONIZAÇÃO DE DADOS ---
def limpar_e_padronizar_categoria(cat):
    if cat is None:
        return 'SEM CAT'
    try:
        # Tenta converter para float e depois para int para tratar '1' e '1.0' da mesma forma
        return str(int(float(cat)))
    except (ValueError, TypeError):
        # Se não for um número, retorna como texto (ex: "SEM CAT")
        return str(cat).strip()

def preparar_dados_sankey():
    try:
        df = pd.read_excel(ARQUIVO_ENTRADA)
        print(f" Arquivo '{ARQUIVO_ENTRADA}' carregado com sucesso.")
    except FileNotFoundError:
        print(f" ERRO: Arquivo '{ARQUIVO_ENTRADA}' não encontrado. O script será encerrado.")
        exit()
        
    # --- APLICA A LIMPEZA DEFINITIVA NA COLUNA CATEGORIA ---
    df['CATEGORIA'] = df['CATEGORIA'].apply(limpar_e_padronizar_categoria)
    df['TRIMESTRE'] = df['TRIMESTRE'].astype(str).str.strip()
    
    trimestres = sorted(df['TRIMESTRE'].unique())
    
    all_transitions = []
    for i in range(len(trimestres) - 1):
        t1, t2 = trimestres[i], trimestres[i+1]
        df_t1 = df[df['TRIMESTRE'] == t1]
        df_t2 = df[df['TRIMESTRE'] == t2]
        df_merged = pd.merge(df_t1, df_t2, on='CRM LINK', suffixes=(f'_{t1}', f'_{t2}'))
        
        transitions = df_merged.groupby([f'CATEGORIA_{t1}', f'CATEGORIA_{t2}', f'NO_PAINEL_{t2}']).size().reset_index(name='value')
        transitions = transitions.rename(columns={
            f'CATEGORIA_{t1}': 'cat_source', f'CATEGORIA_{t2}': 'cat_target', f'NO_PAINEL_{t2}': 'no_painel'
        })
        transitions['trimestre_source'] = t1
        transitions['trimestre_target'] = t2
        all_transitions.append(transitions)
        
    if not all_transitions:
        print(" ERRO: Nenhuma transição entre trimestres foi encontrada.")
        exit()
        
    df_sankey_data = pd.concat(all_transitions, ignore_index=True)
    return df_sankey_data, trimestres

df_sankey_data, trimestres = preparar_dados_sankey()

def ordenar_categorias(lista_categorias):
    """Ordena categorias: números crescentes (1,2,3,4,5) + 'SEM CAT' por último"""
    num_keys = []
    txt_keys = []
    sem_cat = []
    
    for c in lista_categorias:
        if c == 'SEM CAT':
            sem_cat.append(c)
        else:
            try: 
                num_keys.append((int(c), c))
            except (ValueError, TypeError): 
                txt_keys.append(c)
    
    # Ordena números crescente, depois textos alfabético, depois SEM CAT
    resultado = [item[1] for item in sorted(num_keys)] + sorted(txt_keys) + sem_cat
    return resultado

all_cats = pd.unique(df_sankey_data[['cat_source', 'cat_target']].values.ravel('K'))
categorias_ordenadas = ordenar_categorias(all_cats)
print(f"Ordem final e correta das categorias: {categorias_ordenadas}")

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif'}, children=[
    html.H1("Dashboard de Jornada de Categoria dos Médicos", style={'textAlign': 'center'}),
    html.Div(className='controls-container', style={'width': '90%', 'margin': 'auto', 'padding': '20px'}, children=[
        html.Div(style={'display': 'flex', 'gap': '40px', 'alignItems': 'center'}, children=[
            html.Div(style={'flex': 1}, children=[
                html.Label("Analisar Universo:", style={'fontWeight': 'bold'}),
                dcc.RadioItems(id='universo-radio', options=[{'label': ' Mercado Total', 'value': 'mercado'}, {'label': ' No Painel FV', 'value': 'painel'}], value='mercado', labelStyle={'display': 'inline-block', 'margin-right': '10px'})
            ]),
            html.Div(style={'flex': 2}, children=[
                html.Label("Filtro de Categorias:", style={'fontWeight': 'bold'}),
                dcc.Checklist(id='categoria-slicer', options=[{'label': f' Cat. {cat}', 'value': cat} for cat in categorias_ordenadas], value=categorias_ordenadas, inline=True)
            ]),
            html.Div(style={'flex': 1}, children=[
                html.Button('🔄 Resetar Filtro', id='reset-button', n_clicks=0, 
                           style={'padding': '8px 16px', 'backgroundColor': '#f0f0f0', 'border': '1px solid #ccc', 'borderRadius': '4px', 'cursor': 'pointer'})
            ])
        ])
    ]),
    # Store para guardar a categoria clicada
    dcc.Store(id='categoria-clicada-store', data=None),
    dcc.Graph(id='sankey-graph', style={'height': '75vh'})
])

# Callback para resetar o filtro
@app.callback(
    [Output('categoria-clicada-store', 'data'),
     Output('categoria-slicer', 'value')],
    [Input('reset-button', 'n_clicks')],
    prevent_initial_call=True
)
def reset_filter(n_clicks):
    if n_clicks > 0:
        return None, categorias_ordenadas
    return dash.no_update, dash.no_update

# Callback para capturar cliques no gráfico
@app.callback(
    [Output('categoria-clicada-store', 'data', allow_duplicate=True),
     Output('categoria-slicer', 'value', allow_duplicate=True)],
    [Input('sankey-graph', 'clickData')],
    [State('categoria-clicada-store', 'data')],
    prevent_initial_call=True
)
def handle_graph_click(clickData, categoria_atual):
    if clickData and clickData['points']:
        # Extrai a categoria do label clicado
        clicked_node_label = clickData['points'][0].get('label', '')
        if 'Cat.' in clicked_node_label:
            # Extrai categoria do formato "Cat. 1<br>(2023Q1)"
            categoria_clicada = clicked_node_label.split('<br>')[0].replace('Cat. ', '')
            
            # Se já está filtrado pela mesma categoria, reseta
            if categoria_atual == categoria_clicada:
                return None, categorias_ordenadas
            else:
                # Filtra pela nova categoria
                return categoria_clicada, [categoria_clicada]
    
    return dash.no_update, dash.no_update

@app.callback(
    Output('sankey-graph', 'figure'),
    [Input('universo-radio', 'value'),
     Input('categoria-slicer', 'value'),
     Input('categoria-clicada-store', 'data')]
)
def update_graph(universo_selecionado, categorias_selecionadas, categoria_clicada):
    
    if universo_selecionado == 'painel':
        data = df_sankey_data[df_sankey_data['no_painel'] == 'Sim']
    else:
        data = df_sankey_data.groupby(['cat_source', 'cat_target', 'trimestre_source', 'trimestre_target']).agg(value=('value', 'sum')).reset_index()

    if not categorias_selecionadas:
        return go.Figure().update_layout(title_text="Selecione ao menos uma categoria no filtro")
    
    data = data[data['cat_source'].isin(categorias_selecionadas) & data['cat_target'].isin(categorias_selecionadas)]
    
    if data.empty:
        return go.Figure().update_layout(title_text="Nenhuma transição encontrada para a seleção atual")

    # Usa a ordenação correta das categorias
    current_cats_ordered = [cat for cat in categorias_ordenadas if cat in pd.unique(data[['cat_source', 'cat_target']].values.ravel('K'))]
    labels, node_colors, node_x, node_y, node_map = [], [], [], [], {}
    
    for i, trimestre in enumerate(trimestres):
        cats_no_trimestre = pd.unique(data[data['trimestre_source'] == trimestre]['cat_source'])
        
        # Ordena as categorias dentro de cada trimestre
        cats_ordenadas_trimestre = [cat for cat in current_cats_ordered if cat in cats_no_trimestre]
        
        for j, categoria in enumerate(cats_ordenadas_trimestre):
            label = f"Cat. {categoria}<br>({trimestre})"
            labels.append(label)
            node_map[f"{trimestre}: Cat {categoria}"] = len(labels) - 1
            node_x.append(0.01 + i * (0.98 / (len(trimestres) - 1)) if len(trimestres) > 1 else 0.5)
            node_y.append(0.01 + j * (0.98 / (len(cats_ordenadas_trimestre)-1)) if len(cats_ordenadas_trimestre) > 1 else 0.5)
            node_colors.append(CORES_CATEGORIAS.get(categoria, CORES_CATEGORIAS['default']))
                
    link_source, link_target, link_value, link_color, custom_data = [], [], [], [], []
    
    for _, row in data.iterrows():
        source_key = f"{row['trimestre_source']}: Cat {row['cat_source']}"
        target_key = f"{row['trimestre_target']}: Cat {row['cat_target']}"
        if source_key in node_map and target_key in node_map:
            link_source.append(node_map[source_key])
            link_target.append(node_map[target_key])
            link_value.append(row['value'])
            source_color = CORES_CATEGORIAS.get(row['cat_source'], CORES_CATEGORIAS['default'])
            link_color.append(f'rgba({int(source_color[1:3], 16)}, {int(source_color[3:5], 16)}, {int(source_color[5:7], 16)}, 0.5)')
            custom_data.append(f"De: Cat.{row['cat_source']} ({row['trimestre_source']})<br>Para: Cat.{row['cat_target']} ({row['trimestre_target']})")

    fig = go.Figure(go.Sankey(
        arrangement='snap',
        node={
            'pad': 25, 
            'thickness': 20, 
            'line': {'color': 'black', 'width': 0.5}, 
            'label': labels, 
            'color': node_colors,
            'hovertemplate': '%{label}<extra></extra>'
        },
        link={
            'source': link_source, 
            'target': link_target, 
            'value': link_value, 
            'color': link_color,
            'customdata': custom_data, 
            'hovertemplate': '<b>%{customdata}</b><br>Médicos: %{value}<extra></extra>'
        }
    ))
    
    # Título dinâmico baseado no filtro
    if categoria_clicada:
        title_text = f"Jornada de Médicos - Categoria {categoria_clicada} - {universo_selecionado.replace('_', ' ').title()}"
        subtitle = "<br><sub>Clique novamente na categoria para resetar | Use o botão 'Resetar Filtro' para ver todas</sub>"
    else:
        title_text = f"Jornada de Médicos - {universo_selecionado.replace('_', ' ').title()} (Categorias Ordenadas)"
        subtitle = "<br><sub>Clique em qualquer retângulo para filtrar por categoria específica</sub>"
    
    fig.update_layout(
        transition_duration=250, 
        title_text=title_text + subtitle,
        title_x=0.5
    )

    return fig

if __name__ == '__main__':
    print("\n--- Aplicação pronta! Acesse o endereço abaixo no seu navegador. ---")
    print("Use CTRL+C no terminal para encerrar o servidor.")
    app.run(debug=False)