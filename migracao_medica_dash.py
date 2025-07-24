import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State, ctx # Removido ALL, importado ctx

print("--- Preparando a Aplicação Dash (Versão com Correção Final) ---")

# --- 1. PREPARAÇÃO DOS DADOS ---
ARQUIVO_ENTRADA = 'jornada_medicos_trimestral.xlsx'
CORES_CATEGORIAS = {
    '1': '#1f77b4', '2': '#2ca02c', '3': '#ff7f0e', '4': '#d62728', '5': '#9467bd', 
    'SEM CAT': '#7f7f7f', 'default': '#cccccc'
}

def limpar_e_padronizar_categoria(cat):
    if pd.isna(cat) or str(cat).strip() == '': return 'SEM CAT'
    try: return str(int(float(str(cat))))
    except (ValueError, TypeError): return str(cat).strip()

def preparar_dados_sankey():
    try:
        df = pd.read_excel(ARQUIVO_ENTRADA)
        print(f" Arquivo '{ARQUIVO_ENTRADA}' carregado com sucesso.")
    except FileNotFoundError:
        print(f" ERRO: Arquivo '{ARQUIVO_ENTRADA}' não encontrado."); exit()
        
    df['CATEGORIA'] = df['CATEGORIA'].apply(limpar_e_padronizar_categoria)
    df['TRIMESTRE'] = df['TRIMESTRE'].astype(str).str.strip()
    
    trimestres = sorted(df['TRIMESTRE'].unique())
    all_transitions = []
    for i in range(len(trimestres) - 1):
        t1, t2 = trimestres[i], trimestres[i+1]
        df_t1 = df[df['TRIMESTRE'] == t1]; df_t2 = df[df['TRIMESTRE'] == t2]
        df_merged = pd.merge(df_t1, df_t2, on='CRM LINK', suffixes=(f'_{t1}', f'_{t2}'))
        transitions = df_merged.groupby([f'CATEGORIA_{t1}', f'CATEGORIA_{t2}', f'NO_PAINEL_{t2}']).size().reset_index(name='value')
        transitions = transitions.rename(columns={f'CATEGORIA_{t1}': 'cat_source', f'CATEGORIA_{t2}': 'cat_target', f'NO_PAINEL_{t2}': 'no_painel'})
        transitions['trimestre_source'] = t1; transitions['trimestre_target'] = t2
        all_transitions.append(transitions)
        
    if not all_transitions: print(" ERRO: Nenhuma transição encontrada."); exit()
    return pd.concat(all_transitions, ignore_index=True), trimestres

df_sankey_data, trimestres = preparar_dados_sankey()

def chave_de_ordenacao(categoria):
    try: return (0, int(categoria))
    except ValueError: return (1, categoria)

all_cats = pd.unique(df_sankey_data[['cat_source', 'cat_target']].values.ravel('K'))
categorias_ordenadas = sorted(all_cats, key=chave_de_ordenacao)
print(f"Ordem hierárquica final das categorias: {categorias_ordenadas}")

app = dash.Dash(__name__)
server = app.server  # Necessário para o Gunicorn

app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif'}, children=[
    html.H1("Dashboard de Jornada de Categoria dos Médicos", style={'textAlign': 'center'}),
    
    html.Div(className='controls-container', style={'width': '90%', 'margin': 'auto', 'padding': '10px', 'border': '1px solid #ddd', 'borderRadius': '5px'}, children=[
        html.Div(style={'display': 'flex', 'gap': '40px'}, children=[
            html.Div(style={'flex': 1}, children=[
                html.Label("Analisar Universo:", style={'fontWeight': 'bold'}),
                dcc.RadioItems(id='universo-radio', options=[{'label': ' Mercado Total', 'value': 'mercado'}, {'label': ' No Painel FV', 'value': 'painel'}], value='mercado', labelStyle={'display': 'inline-block', 'margin-right': '10px'})
            ]),
            html.Div(style={'flex': 3}, children=[
                html.Label("Filtro de Categorias:", style={'fontWeight': 'bold'}),
                dcc.Checklist(id='categoria-slicer', options=[{'label': f' Cat. {cat}', 'value': cat} for cat in categorias_ordenadas], value=categorias_ordenadas, inline=True)
            ]),
        ]),
        html.Hr(),
        html.Div(children=[
            html.Label("Painel de Foco (Realçar Categoria):", style={'fontWeight': 'bold'}),
            html.Div(id='focus-buttons-container', style={'marginTop': '10px'})
        ]),
    ]),
    
    dcc.Graph(id='sankey-graph', style={'height': '75vh'}),
    dcc.Store(id='focus-category-store')
])

@app.callback(
    Output('focus-buttons-container', 'children'),
    Input('categoria-slicer', 'value')
)
def update_focus_buttons(categorias_selecionadas):
    buttons = [html.Button('Visão Geral', id={'type': 'focus-button', 'index': 'geral'}, n_clicks=0, style={'marginRight': '5px'})]
    if categorias_selecionadas:
        for cat in categorias_ordenadas:
            if cat in categorias_selecionadas:
                buttons.append(html.Button(f'Focar em Cat. {cat}', id={'type': 'focus-button', 'index': cat}, n_clicks=0, style={'marginRight': '5px'}))
    return buttons

# --- CORREÇÃO AQUI ---
# A biblioteca Dash espera que o Input para múltiplos botões seja declarado sem a função ALL
@app.callback(
    Output('focus-category-store', 'data'),
    Input({'type': 'focus-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def store_focus_category(n_clicks):
    # 'ctx' (callback_context) nos diz qual botão foi clicado
    return ctx.triggered_id['index'] if ctx.triggered_id else 'geral'

@app.callback(
    Output('sankey-graph', 'figure'),
    [Input('universo-radio', 'value'),
     Input('categoria-slicer', 'value'),
     Input('focus-category-store', 'data')]
)
def update_graph(universo, categorias_selecionadas, categoria_foco):
    if not categorias_selecionadas:
        return go.Figure().update_layout(title_text="Selecione ao menos uma categoria no filtro")

    if universo == 'painel':
        data = df_sankey_data[df_sankey_data['no_painel'] == 'Sim']
    else:
        data = df_sankey_data.groupby(['cat_source', 'cat_target', 'trimestre_source', 'trimestre_target']).agg(value=('value', 'sum')).reset_index()

    data = data[data['cat_source'].isin(categorias_selecionadas) & data['cat_target'].isin(categorias_selecionadas)]
    
    if data.empty:
        return go.Figure().update_layout(title_text="Nenhuma transição encontrada")

    current_cats_ordered = [cat for cat in categorias_ordenadas if cat in pd.unique(data[['cat_source', 'cat_target']].values.ravel('K'))]
    labels, node_map = [], {}
    
    for i, trimestre in enumerate(trimestres):
        cats_no_trimestre = pd.unique(data[data['trimestre_source'] == trimestre]['cat_source'])
        for j, categoria in enumerate(current_cats_ordered):
            if categoria in cats_no_trimestre:
                label = f"Cat. {categoria}<br>({trimestre})"
                labels.append(label)
                node_map[f"{trimestre}: Cat {categoria}"] = len(labels) - 1
                
    link_source, link_target, link_value, link_color, link_cat_source, link_cat_target = [], [], [], [], [], []
    for _, row in data.iterrows():
        source_key, target_key = f"{row['trimestre_source']}: Cat {row['cat_source']}", f"{row['trimestre_target']}: Cat {row['cat_target']}"
        if source_key in node_map and target_key in node_map:
            link_source.append(node_map[source_key]); link_target.append(node_map[target_key])
            link_value.append(row['value'])
            source_color_hex = CORES_CATEGORIAS.get(row['cat_source'], CORES_CATEGORIAS['default'])
            link_color.append(f'rgba({int(source_color_hex[1:3], 16)}, {int(source_color_hex[3:5], 16)}, {int(source_color_hex[5:7], 16)}, 0.6)')
            link_cat_source.append(row['cat_source']); link_cat_target.append(row['cat_target'])

    cor_link_final = link_color
    if categoria_foco and categoria_foco != 'geral':
        cores_foco = []
        for i in range(len(link_cat_source)):
            if link_cat_source[i] == categoria_foco or link_cat_target[i] == categoria_foco:
                cores_foco.append(link_color[i])
            else:
                cores_foco.append('rgba(230, 230, 230, 0.05)')
        cor_link_final = cores_foco
        
    fig = go.Figure(go.Sankey(
        arrangement='snap',
        node={'pad': 25, 'thickness': 20, 'line': {'color': 'black', 'width': 0.5}, 'label': labels, 'color': [CORES_CATEGORIAS.get(cat.split('<br>')[0].replace('Cat. ', ''), CORES_CATEGORIAS['default']) for cat in labels]},
        link={'source': link_source, 'target': link_target, 'value': link_value, 'color': cor_link_final}
    ))
    fig.update_layout(title_text=f"Jornada de Médicos - {universo.replace('_', ' ').title()}", transition_duration=250)
    return fig

if __name__ == '__main__':
    print("\n--- Aplicação pronta! Acesse o endereço abaixo no seu navegador. ---")
    print("Use CTRL+C no terminal para encerrar o servidor.")
    app.run(debug=False)
