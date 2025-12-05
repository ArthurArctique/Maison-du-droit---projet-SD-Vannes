import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import json
import os

# =============================================================================
# 1. GESTION DES DONNÉES (ROBUSTE)
# =============================================================================
def get_data():
    """Charge SQL ou génère des données bidon si le fichier manque."""
    db_filename = "../database.db"
    
    if os.path.exists(db_filename):
        try:
            conn = sqlite3.connect(db_filename)
            df = pd.read_sql_query("SELECT * FROM ENTRETIEN", conn)
            conn.close()
            return df
        except Exception as e:
            print(f"⚠️ Erreur lecture DB: {e}")

df_global = get_data()

# =============================================================================
# 2. CONFIGURATION DASH
# =============================================================================
COLOR_NAVY = "#003366"
COLOR_GOLD = "#D4AF37"
COLOR_BG = "#F4F6F9"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX], suppress_callback_exceptions=True)
app.title = "Reporting MDD"

def clean_layout(fig):
    fig.update_layout(
        plot_bgcolor=COLOR_BG, paper_bgcolor=COLOR_BG, 
        font={'color': COLOR_NAVY}, 
        margin=dict(t=40, l=10, r=10, b=10), 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# SIDEBAR (Simplifiée et corrigée)
sidebar = html.Div([
    html.Div([
        html.H3("MDD", style={'color': COLOR_GOLD, 'fontWeight': 'bold'}), 
        html.H5("Vannes", style={'color': 'white'})
    ], className="text-center mb-4"),
    
    dbc.Nav([
        dbc.NavLink("📊 Tableau de Bord", href="/", active="exact", className="nav-link-custom"),
        dbc.NavLink("📝 Questionnaire", href="/form", active="exact", className="nav-link-custom"),
        dbc.NavLink("📋 Données", href="/data", active="exact", className="nav-link-custom"),
        dbc.NavLink("📥 Export PDF", href="/export", active="exact", className="nav-link-custom"),
    ], vertical=True, pills=True, className="mb-4"),
    
    html.Div([
        html.H5("FILTRES", style={'color': COLOR_GOLD, 'fontWeight': 'bold', 'borderBottom': '1px solid white'}),
        html.Label("Période", style={'color': 'white', 'marginTop': '10px'}),
        dcc.Dropdown(
            id='filter-period', 
            options=[
                {'label': 'Toute l\'année', 'value': 'ALL'}, 
                {'label': 'Trimestre 1', 'value': 'T1'}
            ], 
            value='ALL', 
            style={'borderRadius': '5px'}
        ),
    ], className="filter-box")
], style={
    "position": "fixed", "top": 0, "left": 0, "bottom": 0, "width": "18rem", 
    "padding": "2rem 1rem", "backgroundColor": COLOR_NAVY, "color": "white", 
    "display": "flex", "flexDirection": "column", "overflowY": "auto"
}, className="no-print")

content = html.Div(id="page-content", style={"marginLeft": "20rem", "padding": "2rem", "backgroundColor": COLOR_BG, "minHeight": "100vh"})

app.layout = html.Div([
    dcc.Location(id="url"), 
    dcc.Store(id='client-view-index', data=0), 
    dcc.Store(id='activity-view-index', data=0), 
    dcc.Store(id='store-current-tab', data="btn-activite"), 
    sidebar, 
    content
])

# =============================================================================
# 3. FORMULAIRE
# =============================================================================
def create_form_layout():
    return html.Div([
        html.H2("Nouveau Dossier", style={'color': COLOR_NAVY}),
        html.Hr(style={'borderColor': COLOR_GOLD}),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([dbc.Label("Numéro"), dbc.Input(id="in-num")], width=4),
                    dbc.Col([dbc.Label("Mode"), dbc.Select(id="in-mode", options=[{"label": "RDV", "value": "RDV"}, {"label": "Email", "value": "Email"}])], width=4),
                    dbc.Col([dbc.Label("Durée"), dbc.Input(id="in-duree", type="number")], width=4),
                ], className="mb-3"),
                # ... Tu peux remettre les autres champs ici si nécessaire ...
                dbc.Button("Valider", id="btn-submit-form", color="warning", className="w-100 mt-3"),
                html.Div(id="form-output", className="mt-3")
            ])
        ])
    ])

# =============================================================================
# 4. CALLBACKS
# =============================================================================

# Navigation principale
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname"), Input("filter-period", "value")] # Suppression de filter-year/city
)
def render_main(path, fp):
    dff = df_global.copy()
    
    if path in ["/", "/dashboard", None]:
        return html.Div([
            dbc.Row([dbc.Col(dbc.Card([html.H2(len(dff), style={'color': COLOR_GOLD}), html.H6("Dossiers")], body=True, className="shadow-sm text-center"), width=4)]),
            html.Div([
                dbc.Button("Activité", id="btn-activite", className="me-2", color="primary"),
                dbc.Button("Clients", id="btn-clients", className="me-2", color="light"),
                dbc.Button("Carte", id="btn-carte", className="me-2", color="light"),
            ], className="mb-4 mt-4"),
            html.Div(id="dashboard-content")
        ])
    elif path == "/form":
        return create_form_layout()
    elif path == "/data":
        return html.Div([dash_table.DataTable(data=dff.to_dict('records'), page_size=10)])
    elif path == "/export":
        return html.Div([html.Button("Imprimer", id="btn-print", className="btn btn-warning mb-3 no-print"), html.H1("Rapport PDF")])
    return html.Div("404")

# Logique Dashboard
@app.callback(
    [Output("dashboard-content", "children"), Output("btn-activite", "color"), Output("btn-clients", "color"), Output("btn-carte", "color")],
    [Input("btn-activite", "n_clicks"), Input("btn-clients", "n_clicks"), Input("btn-carte", "n_clicks")],
    [State("store-current-tab", "data")]
)
def update_dashboard(b1, b2, b3, current_tab):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else "btn-activite"
    
    # Couleurs boutons
    c_act, c_cli, c_map = "light", "light", "light"
    content = html.Div("Chargement...")

    if trigger == "btn-activite":
        c_act = "primary"
        fig = px.bar(df_global['MODE'].value_counts(), title="Modes de Contact", color_discrete_sequence=[COLOR_NAVY])
        content = dcc.Graph(figure=clean_layout(fig))
    elif trigger == "btn-clients":
        c_cli = "primary"
        fig = px.histogram(df_global, x="AGE", title="Âges", color_discrete_sequence=[COLOR_GOLD])
        content = dcc.Graph(figure=clean_layout(fig))
    elif trigger == "btn-carte":
        c_map = "primary"
        # Vérifie si lat/lon existent
        if 'Latitude' in df_global.columns:
            fig = px.scatter_mapbox(df_global, lat="Latitude", lon="Longitude", zoom=10)
            fig.update_layout(mapbox_style="carto-positron")
            content = dcc.Graph(figure=fig)
        else:
            content = html.Div("Pas de coordonnées GPS dans les données.")

    return content, c_act, c_cli, c_map

# Enregistrement Formulaire (Simplifié)
@app.callback(
    Output("form-output", "children"),
    Input("btn-submit-form", "n_clicks"),
    [State("in-num", "value"), State("in-mode", "value"), State("in-duree", "value")]
)
def save_form(n, num, mode, duree):
    if n:
        print(f"📥 Nouveau dossier : {num}, {mode}")
        conn = sqlite3.connect("../database.db") 
        cur = conn.cursor()

        req = f"""
                INSERT INTO ENTRETIEN (NUM, MODE, DUREE)
                VALUES ("{num}","{mode}","{duree}")
               """
        print(req)
        cur.execute(req)
        conn.commit()
        conn.close()
        return dbc.Alert("Enregistré (voir console pour le détail)", color="success")
    return ""

# Impression JS
app.clientside_callback(
    """function(n) { if (n > 0) { window.print(); } return ""; }""",
    Output("btn-print", "children"), Input("btn-print", "n_clicks"), prevent_initial_call=True
)

if __name__ == '__main__':
    app.run(debug=True)